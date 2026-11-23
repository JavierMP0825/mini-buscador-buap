#!/usr/bin/env python3
"""Calcula PageRank sobre el grafo dirigido de artículos del proyecto BUAP.

Uso:
    python3 pagerank.py
    python3 pagerank.py --limite 10
    python3 pagerank.py --amortiguamiento 0.85 --iteraciones 200 --tolerancia 1e-12

El cálculo es independiente de cualquier consulta. El archivo generado puede
usarse después para ordenar los documentos recuperados por el buscador.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
INDICES = ROOT / "indices"
GRAFO_DEFAULT = INDICES / "grafo.json"
SALIDA_DEFAULT = INDICES / "pagerank.json"
RESUMEN_DEFAULT = INDICES / "resumen_pagerank.json"


class ErrorPageRank(ValueError):
    """Error controlado al validar el grafo o calcular PageRank."""


def validar_adyacencia(adyacencia: dict[str, list[str]]) -> None:
    """Comprueba que la lista de adyacencia tenga nodos y destinos válidos."""
    if not isinstance(adyacencia, dict):
        raise ErrorPageRank("La adyacencia debe ser un diccionario de listas.")

    nodos = set(adyacencia)
    for origen, destinos in adyacencia.items():
        if not isinstance(origen, str) or not origen:
            raise ErrorPageRank("Todos los identificadores de nodo deben ser cadenas no vacías.")
        if not isinstance(destinos, list):
            raise ErrorPageRank(f"Los enlaces salientes de '{origen}' deben ser una lista.")
        for destino in destinos:
            if not isinstance(destino, str) or destino not in nodos:
                raise ErrorPageRank(
                    f"El nodo '{origen}' apunta a un destino inexistente o inválido: {destino!r}."
                )
        if len(destinos) != len(set(destinos)):
            raise ErrorPageRank(f"El nodo '{origen}' contiene enlaces duplicados.")


def _calcular_pagerank_detallado(
    adyacencia: dict[str, list[str]],
    d: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-10,
) -> tuple[dict[str, float], dict[str, Any]]:
    """Calcula PageRank y devuelve puntuaciones junto con datos de convergencia.

    Se utiliza la formulación iterativa con distribución uniforme de la masa
    de los nodos colgantes (nodos sin enlaces salientes).
    """
    validar_adyacencia(adyacencia)

    if not isinstance(d, (int, float)) or isinstance(d, bool) or not math.isfinite(d) or not 0 < d < 1:
        raise ErrorPageRank("El amortiguamiento d debe ser un número entre 0 y 1, sin incluirlos.")
    if not isinstance(max_iter, int) or isinstance(max_iter, bool) or max_iter < 1:
        raise ErrorPageRank("El número máximo de iteraciones debe ser un entero positivo.")
    if not isinstance(tol, (int, float)) or isinstance(tol, bool) or not math.isfinite(tol) or tol <= 0:
        raise ErrorPageRank("La tolerancia debe ser un número positivo y finito.")

    nodos = sorted(adyacencia)
    n = len(nodos)
    if n == 0:
        return {}, {
            "convergio": True,
            "iteraciones": 0,
            "diferencia_final": 0.0,
            "nodos_colgantes": [],
        }

    # Uniforme al inicio: la suma de las puntuaciones vale 1.
    puntuaciones = {nodo: 1.0 / n for nodo in nodos}
    nodos_colgantes = [nodo for nodo in nodos if not adyacencia[nodo]]

    # Índice inverso: para cada destino, identifica quién le enlaza.
    entrantes: dict[str, list[str]] = {nodo: [] for nodo in nodos}
    for origen in nodos:
        for destino in adyacencia[origen]:
            entrantes[destino].append(origen)

    convergio = False
    diferencia = math.inf
    iteraciones_realizadas = 0

    for iteracion in range(1, max_iter + 1):
        masa_colgante = sum(puntuaciones[nodo] for nodo in nodos_colgantes)
        base = (1.0 - d) / n
        aporte_colgantes = masa_colgante / n
        nuevas: dict[str, float] = {}

        for destino in nodos:
            aporte_enlaces = 0.0
            for origen in entrantes[destino]:
                grado_salida = len(adyacencia[origen])
                # Un nodo colgante no puede aparecer en entrantes de otro nodo.
                aporte_enlaces += puntuaciones[origen] / grado_salida

            nuevas[destino] = base + d * (aporte_enlaces + aporte_colgantes)

        diferencia = sum(abs(nuevas[nodo] - puntuaciones[nodo]) for nodo in nodos)
        puntuaciones = nuevas
        iteraciones_realizadas = iteracion

        if diferencia < tol:
            convergio = True
            break

    # Protege la salida frente a pequeñas desviaciones de coma flotante.
    suma = sum(puntuaciones.values())
    if suma > 0:
        puntuaciones = {nodo: valor / suma for nodo, valor in puntuaciones.items()}

    info = {
        "convergio": convergio,
        "iteraciones": iteraciones_realizadas,
        "diferencia_final": diferencia,
        "nodos_colgantes": nodos_colgantes,
    }
    return puntuaciones, info


def calcular_pagerank(
    adyacencia: dict[str, list[str]],
    d: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-10,
) -> dict[str, float]:
    """Calcula y devuelve la puntuación PageRank de cada nodo.

    La suma de las puntuaciones es 1. Los nodos sin enlaces salientes se
    tratan distribuyendo uniformemente su masa entre todos los nodos.
    """
    puntuaciones, _ = _calcular_pagerank_detallado(adyacencia, d, max_iter, tol)
    return puntuaciones


def cargar_grafo(ruta: Path = GRAFO_DEFAULT) -> dict[str, Any]:
    """Lee y valida el JSON creado por grafo.py."""
    if not ruta.is_file():
        raise ErrorPageRank(
            f"No se encontró el grafo: {ruta}. Ejecuta primero python3 grafo.py."
        )

    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ErrorPageRank(f"No se pudo leer el JSON del grafo: {exc}") from exc

    if not isinstance(datos, dict) or "nodos" not in datos or "adyacencia" not in datos:
        raise ErrorPageRank("El archivo del grafo debe contener 'nodos' y 'adyacencia'.")

    nodos = datos["nodos"]
    adyacencia = datos["adyacencia"]
    if not isinstance(nodos, list) or not isinstance(adyacencia, dict):
        raise ErrorPageRank("La lista de nodos o la adyacencia tienen un formato inválido.")

    ids_nodos = [nodo.get("id") for nodo in nodos if isinstance(nodo, dict)]
    if len(ids_nodos) != len(nodos) or any(not isinstance(i, str) or not i for i in ids_nodos):
        raise ErrorPageRank("Cada nodo del grafo debe ser un objeto con un ID válido.")
    if len(ids_nodos) != len(set(ids_nodos)):
        raise ErrorPageRank("El grafo contiene IDs de nodos duplicados.")
    if set(ids_nodos) != set(adyacencia):
        raise ErrorPageRank("Los IDs de 'nodos' no coinciden con las claves de 'adyacencia'.")

    validar_adyacencia(adyacencia)
    return datos


def construir_resultados(
    grafo: dict[str, Any],
    puntuaciones: dict[str, float],
) -> list[dict[str, Any]]:
    """Asocia cada puntuación con metadatos y grados del nodo."""
    adyacencia = grafo["adyacencia"]
    grado_entrada = {nodo: 0 for nodo in adyacencia}
    for origen, destinos in adyacencia.items():
        for destino in destinos:
            grado_entrada[destino] += 1

    metadatos = {nodo["id"]: nodo for nodo in grafo["nodos"]}
    resultados = []
    for doc_id, puntuacion in puntuaciones.items():
        datos = metadatos[doc_id]
        resultados.append({
            "id": doc_id,
            "titulo": datos.get("titulo", doc_id),
            "facultad": datos.get("facultad", ""),
            "facultad_id": datos.get("facultad_id", ""),
            "ruta": datos.get("ruta", ""),
            "pagerank": puntuacion,
            "grado_entrada": grado_entrada[doc_id],
            "grado_salida": len(adyacencia[doc_id]),
        })

    resultados.sort(key=lambda item: (-item["pagerank"], item["id"]))
    for posicion, resultado in enumerate(resultados, start=1):
        resultado["posicion"] = posicion
    return resultados


def generar_archivos(
    grafo: dict[str, Any],
    d: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-10,
    salida: Path = SALIDA_DEFAULT,
    resumen_salida: Path = RESUMEN_DEFAULT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Calcula PageRank y escribe los archivos de puntuaciones y resumen."""
    puntuaciones, info = _calcular_pagerank_detallado(
        grafo["adyacencia"], d=d, max_iter=max_iter, tol=tol
    )
    resultados = construir_resultados(grafo, puntuaciones)
    suma = sum(puntuaciones.values())

    salida_datos = {
        "proyecto": grafo.get("proyecto", "Mini buscador académico BUAP"),
        "algoritmo": "PageRank",
        "descripcion": "Importancia global calculada a partir de los enlaces dirigidos entre artículos.",
        "parametros": {
            "amortiguamiento": d,
            "iteraciones_maximas": max_iter,
            "tolerancia": tol,
            "criterio_convergencia": "suma de diferencias absolutas (norma L1)",
        },
        "estadisticas": {
            "total_nodos": len(puntuaciones),
            "total_aristas": sum(len(destinos) for destinos in grafo["adyacencia"].values()),
            "suma_pagerank": suma,
            "pagerank_minimo": min(puntuaciones.values()) if puntuaciones else 0.0,
            "pagerank_maximo": max(puntuaciones.values()) if puntuaciones else 0.0,
            "promedio_pagerank": suma / len(puntuaciones) if puntuaciones else 0.0,
            "nodos_colgantes": len(info["nodos_colgantes"]),
            "convergio": info["convergio"],
            "iteraciones_realizadas": info["iteraciones"],
            "diferencia_final": info["diferencia_final"],
        },
        "puntuaciones": puntuaciones,
        "ranking": resultados,
    }

    resumen = {
        "algoritmo": "PageRank",
        **salida_datos["parametros"],
        **salida_datos["estadisticas"],
        "ids_nodos_colgantes": info["nodos_colgantes"],
        "top_10": [
            {"posicion": r["posicion"], "id": r["id"], "titulo": r["titulo"], "pagerank": r["pagerank"]}
            for r in resultados[:10]
        ],
    }

    salida.parent.mkdir(parents=True, exist_ok=True)
    resumen_salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(salida_datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    resumen_salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return salida_datos, resumen


def cargar_pagerank(ruta: Path) -> dict[str, Any]:
    """Carga el resultado calculado y comprueba que incluya puntuaciones."""
    if not ruta.is_file():
        raise ErrorPageRank(
            f"No se encontró el ranking PageRank: {ruta}. Ejecuta primero python3 pagerank.py."
        )
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ErrorPageRank(f"No se pudo leer el archivo de PageRank: {exc}") from exc

    puntuaciones = datos.get("puntuaciones") if isinstance(datos, dict) else None
    if not isinstance(puntuaciones, dict):
        raise ErrorPageRank("El archivo PageRank no contiene el mapa 'puntuaciones'.")
    for doc_id, valor in puntuaciones.items():
        if not isinstance(doc_id, str) or not isinstance(valor, (int, float)) or not math.isfinite(valor) or valor < 0:
            raise ErrorPageRank(f"Puntuación PageRank no válida para {doc_id!r}.")
    return datos


def aplicar_ranking_pagerank(
    respuesta_busqueda: dict[str, Any],
    datos_pagerank: dict[str, Any],
) -> dict[str, Any]:
    """Ordena los documentos recuperados según su PageRank global.

    PageRank se calcula sin conocer la consulta. Esta función solamente usa
    las puntuaciones globales para ordenar el conjunto que recuperó OR/AND.
    """
    puntuaciones = datos_pagerank.get("puntuaciones", {})
    resultados = respuesta_busqueda.get("resultados", [])
    if not isinstance(puntuaciones, dict):
        raise ErrorPageRank("El archivo PageRank no contiene un mapa de puntuaciones válido.")
    if not isinstance(resultados, list):
        raise ErrorPageRank("La respuesta de búsqueda no contiene resultados válidos.")
    for doc_id, valor in puntuaciones.items():
        if not isinstance(doc_id, str) or not isinstance(valor, (int, float)) or not math.isfinite(valor) or valor < 0:
            raise ErrorPageRank(f"Puntuación PageRank no válida para {doc_id!r}.")

    ordenados = []
    for resultado in resultados:
        doc_id = resultado.get("id")
        if doc_id not in puntuaciones:
            raise ErrorPageRank(
                f"El documento '{doc_id}' no aparece en el archivo PageRank. Recalcula PageRank después de actualizar el grafo."
            )
        copia = dict(resultado)
        copia["score_pagerank"] = float(puntuaciones[doc_id])
        ordenados.append(copia)

    ordenados.sort(key=lambda doc: (-doc["score_pagerank"], doc.get("id", "")))
    for posicion, documento in enumerate(ordenados, start=1):
        documento["posicion_pagerank"] = posicion

    respuesta = dict(respuesta_busqueda)
    respuesta["resultados"] = ordenados
    respuesta["ranking"] = "PageRank global"
    respuesta["nota"] = (
        "Los documentos se recuperan mediante OR/AND y se ordenan por PageRank. "
        "PageRank mide importancia global según los enlaces del grafo; no depende de la consulta."
    )
    return respuesta


def imprimir_top(resultados: list[dict[str, Any]], limite: int | None = 20) -> None:
    """Imprime el ranking global de artículos."""
    mostrar = resultados if limite is None else resultados[:limite]
    if not mostrar:
        print("El grafo no contiene artículos.")
        return
    print("\nRanking global PageRank")
    print("=" * 88)
    for resultado in mostrar:
        print(
            f"{resultado['posicion']:>3}. [{resultado['id']}] "
            f"{resultado['titulo']} — {resultado['pagerank']:.10f}"
        )
        print(
            f"     {resultado['facultad']} | "
            f"Entrada: {resultado['grado_entrada']} | Salida: {resultado['grado_salida']}"
        )
    if limite is not None and len(resultados) > limite:
        print(f"\nSe muestran {limite} de {len(resultados)} artículos. Usa --limite 0 para mostrar todos.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Calcula PageRank sobre el grafo de artículos BUAP.")
    parser.add_argument("--grafo", type=Path, default=GRAFO_DEFAULT, help="Archivo JSON del grafo dirigido.")
    parser.add_argument("--salida", type=Path, default=SALIDA_DEFAULT, help="Archivo JSON de puntuaciones PageRank.")
    parser.add_argument("--resumen", type=Path, default=RESUMEN_DEFAULT, help="Archivo JSON de estadísticas.")
    parser.add_argument("--amortiguamiento", type=float, default=0.85, help="Factor d entre 0 y 1 (predeterminado: 0.85).")
    parser.add_argument("--iteraciones", type=int, default=100, help="Número máximo de iteraciones (predeterminado: 100).")
    parser.add_argument("--tolerancia", type=float, default=1e-10, help="Tolerancia de convergencia (predeterminado: 1e-10).")
    parser.add_argument("--limite", type=int, default=20, help="Artículos que se muestran (0 muestra todos).")
    args = parser.parse_args()

    if args.limite < 0:
        parser.error("--limite no puede ser negativo.")

    try:
        grafo = cargar_grafo(args.grafo)
        resultado, resumen = generar_archivos(
            grafo,
            d=args.amortiguamiento,
            max_iter=args.iteraciones,
            tol=args.tolerancia,
            salida=args.salida,
            resumen_salida=args.resumen,
        )
    except ErrorPageRank as exc:
        print(f"Error PageRank: {exc}", file=sys.stderr)
        return 2

    estadisticas = resultado["estadisticas"]
    print("\nPageRank calculado correctamente.")
    print(f"  Nodos:                 {estadisticas['total_nodos']}")
    print(f"  Aristas:               {estadisticas['total_aristas']}")
    print(f"  Amortiguamiento:       {args.amortiguamiento}")
    print(f"  Iteraciones:           {estadisticas['iteraciones_realizadas']}/{args.iteraciones}")
    print(f"  Convergencia:          {'Sí' if estadisticas['convergio'] else 'No (alcanzó el límite de iteraciones)'}")
    print(f"  Diferencia final:      {estadisticas['diferencia_final']:.12g}")
    print(f"  Suma de PageRank:      {estadisticas['suma_pagerank']:.12f}")
    print(f"  Nodos colgantes:       {estadisticas['nodos_colgantes']}")
    print(f"  Archivo de resultados: {args.salida}")
    print(f"  Archivo de resumen:    {args.resumen}")

    imprimir_top(resultado["ranking"], limite=None if args.limite == 0 else args.limite)
    if not estadisticas["convergio"]:
        print("\nAVISO: aumenta --iteraciones o ajusta --tolerancia para alcanzar convergencia.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
