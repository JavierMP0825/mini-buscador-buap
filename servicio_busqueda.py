#!/usr/bin/env python3
"""Capa de servicio para la API web del mini buscador BUAP.

Mantiene la lógica de recuperación en los módulos académicos existentes y
prepara una respuesta lista para consumir desde una interfaz web.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from buscador import (
    ErrorConsulta,
    buscar,
    cargar_indice,
    cargar_stopwords_para_indice,
)
from comparador import ErrorComparacion, aplicar_ranking_hibrido
from pagerank import ErrorPageRank, aplicar_ranking_pagerank, cargar_pagerank
from ranking import ErrorRanking, aplicar_ranking_tfidf, construir_modelo_tfidf

ROOT = Path(__file__).resolve().parent


class ErrorSolicitud(ValueError):
    """Error de validación en los parámetros que envía la interfaz."""


class ServicioBusqueda:
    """Carga los índices una vez y procesa las solicitudes de búsqueda."""

    RANKINGS = {"tfidf", "pagerank", "hibrido", "ninguno"}
    MODOS = {"OR", "AND"}
    MAX_QUERY_LENGTH = 200
    MAX_PER_PAGE = 50

    def __init__(self, root: Path = ROOT) -> None:
        self.root = Path(root)
        self.ruta_indice = self.root / "indices" / "indice_invertido.json"
        self.ruta_pagerank = self.root / "indices" / "pagerank.json"
        self.ruta_stopwords = self.root / "data" / "stopwords_es.txt"
        self.ruta_catalogo = self.root / "data" / "catalogo.json"
        self.ruta_articulos = self.root / "data" / "articulos.json"

        self.indice = cargar_indice(self.ruta_indice)
        self.stopwords = cargar_stopwords_para_indice(self.indice, self.ruta_stopwords)
        self.modelo_tfidf = construir_modelo_tfidf(self.indice)
        self.datos_pagerank = cargar_pagerank(self.ruta_pagerank)

        self.catalogo = self._leer_json(self.ruta_catalogo)
        datos_articulos = self._leer_json(self.ruta_articulos)
        self.articulos = {
            articulo["id"]: articulo
            for articulo in datos_articulos.get("articulos", [])
            if isinstance(articulo, dict) and isinstance(articulo.get("id"), str)
        }

        facultades = self.catalogo.get("facultades", [])
        self.facultades_por_id = {
            facultad["id"]: facultad
            for facultad in facultades
            if isinstance(facultad, dict) and facultad.get("id")
        }
        self.facultades_por_slug = {
            facultad["slug"]: facultad
            for facultad in facultades
            if isinstance(facultad, dict) and facultad.get("slug")
        }

        total_indice = len(self.indice.get("documentos", {}))
        if total_indice != len(self.articulos):
            raise RuntimeError(
                "El índice invertido y articulos.json no contienen el mismo número de documentos. "
                "Reconstruye el corpus y los índices antes de iniciar la API."
            )
        if set(self.indice["documentos"]) != set(self.articulos):
            raise RuntimeError(
                "Los identificadores de articulos.json no coinciden con el índice invertido. "
                "Ejecuta generar.py, grafo.py, indexador.py y pagerank.py."
            )

    @staticmethod
    def _leer_json(ruta: Path) -> dict[str, Any]:
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise RuntimeError(f"No se encontró el archivo necesario: {ruta}") from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"No se pudo leer {ruta}: {exc}") from exc
        if not isinstance(datos, dict):
            raise RuntimeError(f"El archivo {ruta} debe contener un objeto JSON.")
        return datos

    def health(self) -> dict[str, Any]:
        """Devuelve el estado del motor y estadísticas básicas del corpus."""
        estadisticas_indice = self.indice.get("estadisticas", {})
        estadisticas_pr = self.datos_pagerank.get("estadisticas", {})
        return {
            "status": "ok",
            "proyecto": "Mini buscador académico BUAP",
            "corpus": {
                "facultades": len(self.facultades_por_id),
                "documentos": len(self.indice.get("documentos", {})),
                "terminos_unicos": estadisticas_indice.get("total_terminos_unicos", 0),
                "aristas": estadisticas_pr.get("total_aristas", 0),
            },
            "algoritmos": ["tfidf", "pagerank", "hibrido", "ninguno"],
            "recuperacion": ["OR", "AND"],
        }

    def listar_facultades(self) -> list[dict[str, Any]]:
        """Devuelve las facultades en el orden del catálogo."""
        salida = []
        for facultad in self.catalogo.get("facultades", []):
            salida.append({
                "id": facultad["id"],
                "slug": facultad["slug"],
                "nombre": facultad["nombre"],
                "total_articulos": facultad.get("total_articulos", 20),
            })
        return salida

    @staticmethod
    def _entero_positivo(valor: Any, nombre: str, maximo: int | None = None) -> int:
        if isinstance(valor, bool):
            raise ErrorSolicitud(f"{nombre} debe ser un número entero.")
        try:
            numero = int(valor)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ErrorSolicitud(f"{nombre} debe ser un número entero.") from exc
        if str(valor).strip() not in {str(numero), f"+{numero}"} and not isinstance(valor, int):
            raise ErrorSolicitud(f"{nombre} debe ser un número entero.")
        if numero < 1:
            raise ErrorSolicitud(f"{nombre} debe ser mayor que cero.")
        if maximo is not None and numero > maximo:
            raise ErrorSolicitud(f"{nombre} no puede ser mayor que {maximo}.")
        return numero

    def buscar(self, parametros: dict[str, Any]) -> dict[str, Any]:
        """Valida parámetros, recupera, ordena, filtra y pagina los resultados."""
        if not isinstance(parametros, dict):
            raise ErrorSolicitud("El cuerpo de la solicitud debe ser un objeto JSON.")

        consulta = parametros.get("q", parametros.get("consulta", ""))
        if not isinstance(consulta, str):
            raise ErrorSolicitud("La consulta debe ser una cadena de texto.")
        consulta = consulta.strip()
        if not consulta:
            raise ErrorSolicitud("Escribe una consulta antes de buscar.")
        if len(consulta) > self.MAX_QUERY_LENGTH:
            raise ErrorSolicitud(
                f"La consulta no puede superar {self.MAX_QUERY_LENGTH} caracteres."
            )

        modo = str(parametros.get("modo", parametros.get("mode", "OR"))).upper()
        if modo not in self.MODOS:
            raise ErrorSolicitud("El modo de búsqueda debe ser OR o AND.")

        ranking = str(parametros.get("ranking", "tfidf")).lower()
        if ranking not in self.RANKINGS:
            raise ErrorSolicitud("El ranking debe ser tfidf, pagerank, hibrido o ninguno.")

        peso_bruto = parametros.get("peso_tfidf", parametros.get("weight", 0.7))
        if isinstance(peso_bruto, bool):
            raise ErrorSolicitud("El peso de TF-IDF debe ser un número entre 0 y 1.")
        try:
            peso_tfidf = float(peso_bruto)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ErrorSolicitud("El peso de TF-IDF debe ser un número entre 0 y 1.") from exc
        if not math.isfinite(peso_tfidf) or not 0.0 <= peso_tfidf <= 1.0:
            raise ErrorSolicitud("El peso de TF-IDF debe estar entre 0 y 1.")

        pagina = self._entero_positivo(parametros.get("pagina", parametros.get("page", 1)), "La página")
        por_pagina = self._entero_positivo(
            parametros.get("por_pagina", parametros.get("per_page", 10)),
            "El tamaño de página",
            self.MAX_PER_PAGE,
        )

        facultad_solicitada = parametros.get("facultad", parametros.get("faculty"))
        facultad = None
        if facultad_solicitada not in (None, "", "all", "todas"):
            if not isinstance(facultad_solicitada, str):
                raise ErrorSolicitud("El filtro de facultad no es válido.")
            facultad = (
                self.facultades_por_id.get(facultad_solicitada)
                or self.facultades_por_slug.get(facultad_solicitada)
            )
            if facultad is None:
                raise ErrorSolicitud("La facultad seleccionada no existe en el catálogo.")

        respuesta = buscar(consulta, self.indice, self.stopwords, modo)

        # El filtro se aplica antes del ranking para que las posiciones y la
        # normalización del ranking híbrido correspondan a esa facultad.
        if facultad is not None:
            respuesta["resultados"] = [
                documento for documento in respuesta["resultados"]
                if documento.get("facultad_id") == facultad["id"]
            ]

        respuesta["total_resultados"] = len(respuesta["resultados"])
        respuesta["facultad_filtro"] = facultad["nombre"] if facultad else None

        if ranking == "tfidf":
            respuesta = aplicar_ranking_tfidf(respuesta, self.indice, self.modelo_tfidf)
        elif ranking == "pagerank":
            respuesta = aplicar_ranking_pagerank(respuesta, self.datos_pagerank)
        elif ranking == "hibrido":
            respuesta = aplicar_ranking_hibrido(
                respuesta,
                self.indice,
                self.datos_pagerank,
                peso_tfidf=peso_tfidf,
                modelo_tfidf=self.modelo_tfidf,
            )
        else:
            respuesta["resultados"].sort(key=lambda documento: documento["id"])
            respuesta["ranking"] = "Sin ranking (orden por identificador)"
            respuesta["nota"] = "Los documentos se muestran por identificador, sin puntuación de relevancia."

        resultados = respuesta["resultados"]
        total = len(resultados)
        total_paginas = math.ceil(total / por_pagina) if total else 0
        if total_paginas and pagina > total_paginas:
            raise ErrorSolicitud(
                f"La página solicitada no existe. Hay {total_paginas} páginas de resultados."
            )
        if not total_paginas and pagina > 1:
            raise ErrorSolicitud("No hay resultados; la página solicitada no existe.")

        inicio = (pagina - 1) * por_pagina
        fin = min(inicio + por_pagina, total)
        articulos_pagina = resultados[inicio:fin]
        preparados = []
        for documento in articulos_pagina:
            copia = dict(documento)
            articulo = self.articulos.get(copia["id"], {})
            contenido = " ".join(str(articulo.get("contenido", "")).split())
            copia["fragmento"] = contenido[:240] + ("…" if len(contenido) > 240 else "")
            copia["url"] = "/" + str(copia.get("ruta", "")).replace("\\", "/").lstrip("/")
            preparados.append(copia)

        respuesta["resultados"] = preparados
        respuesta["paginacion"] = {
            "pagina": pagina,
            "por_pagina": por_pagina,
            "total_resultados": total,
            "total_paginas": total_paginas,
            "desde": inicio + 1 if total else 0,
            "hasta": fin,
            "hay_anterior": pagina > 1 and total > 0,
            "hay_siguiente": pagina < total_paginas,
        }
        respuesta["parametros"] = {
            "modo": modo,
            "ranking": ranking,
            "peso_tfidf": peso_tfidf,
            "facultad_id": facultad["id"] if facultad else None,
        }
        return respuesta
