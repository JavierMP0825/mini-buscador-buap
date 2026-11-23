#!/usr/bin/env python3
"""Compara TF-IDF y PageRank y calcula un ranking híbrido para el corpus BUAP.

Ejemplos:
    python3 comparador.py "construcción sostenible"
    python3 comparador.py "diseño arquitectónico" --modo AND --top 5
    python3 comparador.py "construcción sostenible" --peso-tfidf 0.6

El programa recupera primero los candidatos mediante OR/AND. Sobre exactamente
ese mismo conjunto aplica TF-IDF, PageRank y una combinación ponderada.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from pagerank import (
    ErrorPageRank,
    aplicar_ranking_pagerank,
    cargar_pagerank,
)
from ranking import (
    ErrorRanking,
    aplicar_ranking_tfidf,
    construir_modelo_tfidf,
)

ROOT = Path(__file__).resolve().parent
INDICE_DEFAULT = ROOT / "indices" / "indice_invertido.json"
PAGERANK_DEFAULT = ROOT / "indices" / "pagerank.json"
STOPWORDS_DEFAULT = ROOT / "data" / "stopwords_es.txt"
SALIDA_DEFAULT = ROOT / "indices" / "comparacion.json"


class ErrorComparacion(ValueError):
    """Error controlado al comparar algoritmos de ranking."""


def _validar_parametros(top_k: int, peso_tfidf: float) -> None:
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise ErrorComparacion("top_k debe ser un entero positivo.")
    if (
        not isinstance(peso_tfidf, (int, float))
        or isinstance(peso_tfidf, bool)
        or not math.isfinite(peso_tfidf)
        or not 0.0 <= peso_tfidf <= 1.0
    ):
        raise ErrorComparacion("El peso de TF-IDF debe ser un número entre 0 y 1.")


def normalizar_pagerank_candidatos(resultados: list[dict[str, Any]]) -> dict[str, float]:
    """Normaliza PageRank al intervalo [0, 1] usando min-max entre candidatos.

    La normalización se hace sobre los documentos recuperados para que la
    escala del componente estructural sea comparable con la similitud coseno.
    Si todos los candidatos tienen la misma puntuación, el componente se fija
    en cero para indicar que PageRank no discrimina entre ellos.
    """
    valores: dict[str, float] = {}
    for resultado in resultados:
        doc_id = resultado.get("id")
        valor = resultado.get("score_pagerank")
        if not isinstance(doc_id, str) or not doc_id:
            raise ErrorComparacion("Cada resultado debe incluir un ID de documento válido.")
        if (
            not isinstance(valor, (int, float))
            or isinstance(valor, bool)
            or not math.isfinite(valor)
            or valor < 0
        ):
            raise ErrorComparacion(f"PageRank no válido para el documento {doc_id!r}.")
        valores[doc_id] = float(valor)

    if not valores:
        return {}

    minimo = min(valores.values())
    maximo = max(valores.values())
    amplitud = maximo - minimo
    if amplitud <= 0.0:
        return {doc_id: 0.0 for doc_id in valores}
    return {doc_id: (valor - minimo) / amplitud for doc_id, valor in valores.items()}


def aplicar_ranking_hibrido(
    respuesta_busqueda: dict[str, Any],
    indice: dict[str, Any],
    datos_pagerank: dict[str, Any],
    peso_tfidf: float = 0.7,
    modelo_tfidf: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Combina similitud textual y PageRank en una puntuación ponderada.

    score_hibrido = peso_tfidf * TFIDF + (1 - peso_tfidf) * PageRank_normalizado

    TF-IDF ya está en [0, 1]. PageRank se normaliza con min-max dentro del
    conjunto de candidatos de la consulta. El conjunto recuperado por OR/AND
    no se altera; solamente cambia el orden de los documentos.
    """
    _validar_parametros(1, peso_tfidf)
    if not isinstance(respuesta_busqueda, dict):
        raise ErrorComparacion("La respuesta de búsqueda debe ser un objeto.")

    respuesta_tfidf = aplicar_ranking_tfidf(respuesta_busqueda, indice, modelo_tfidf)
    respuesta_pagerank = aplicar_ranking_pagerank(respuesta_busqueda, datos_pagerank)

    resultados_tfidf = respuesta_tfidf["resultados"]
    resultados_pagerank = respuesta_pagerank["resultados"]
    normalizados = normalizar_pagerank_candidatos(resultados_pagerank)

    tfidf_por_id = {doc["id"]: doc for doc in resultados_tfidf}
    pagerank_por_id = {doc["id"]: doc for doc in resultados_pagerank}

    combinados: list[dict[str, Any]] = []
    peso_pagerank = 1.0 - float(peso_tfidf)
    for doc_id, doc_tfidf in tfidf_por_id.items():
        doc_pagerank = pagerank_por_id[doc_id]
        score_tfidf = float(doc_tfidf["score_tfidf"])
        score_pagerank = float(doc_pagerank["score_pagerank"])
        score_pagerank_normalizado = normalizados[doc_id]
        score_hibrido = (
            float(peso_tfidf) * score_tfidf
            + peso_pagerank * score_pagerank_normalizado
        )

        combinados.append({
            **doc_tfidf,
            "score_pagerank": score_pagerank,
            "pagerank_normalizado": score_pagerank_normalizado,
            "score_hibrido": score_hibrido,
            "posicion_pagerank": doc_pagerank["posicion_pagerank"],
        })

    combinados.sort(key=lambda doc: (-doc["score_hibrido"], doc["id"]))
    for posicion, documento in enumerate(combinados, start=1):
        documento["posicion_hibrido"] = posicion

    respuesta = dict(respuesta_busqueda)
    respuesta["resultados"] = combinados
    respuesta["ranking"] = "Híbrido (TF-IDF + PageRank)"
    respuesta["parametros_ranking_hibrido"] = {
        "peso_tfidf": float(peso_tfidf),
        "peso_pagerank": peso_pagerank,
        "formula": "peso_tfidf * score_tfidf + peso_pagerank * pagerank_normalizado",
        "normalizacion_pagerank": "min-max sobre los documentos recuperados por la consulta",
    }
    respuesta["nota"] = (
        "El ranking híbrido combina similitud textual TF-IDF y PageRank global. "
        "PageRank se normaliza entre los documentos recuperados por esta consulta. "
        "Los documentos candidatos siguen determinados por el modo OR/AND."
    )
    return respuesta


def _resumen_coincidencia(
    ids_a: list[str],
    ids_b: list[str],
    top_k: int,
) -> dict[str, Any]:
    k_evaluado = min(top_k, len(ids_a), len(ids_b))
    conjunto_a = set(ids_a[:k_evaluado])
    conjunto_b = set(ids_b[:k_evaluado])
    comunes = conjunto_a & conjunto_b
    union = conjunto_a | conjunto_b
    porcentaje = (len(comunes) / k_evaluado * 100.0) if k_evaluado else 0.0
    jaccard = (len(comunes) / len(union)) if union else 0.0
    return {
        "k_solicitado": top_k,
        "k_evaluado": k_evaluado,
        "documentos_comunes": len(comunes),
        "ids_comunes": sorted(comunes),
        "coincidencia_porcentual": porcentaje,
        "indice_jaccard": jaccard,
    }


def comparar_resultados(
    respuesta_busqueda: dict[str, Any],
    indice: dict[str, Any],
    datos_pagerank: dict[str, Any],
    top_k: int = 10,
    peso_tfidf: float = 0.7,
    modelo_tfidf: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Genera rankings paralelos, tabla comparativa y métricas de coincidencia."""
    _validar_parametros(top_k, peso_tfidf)

    resultado_tfidf = aplicar_ranking_tfidf(respuesta_busqueda, indice, modelo_tfidf)
    resultado_pagerank = aplicar_ranking_pagerank(respuesta_busqueda, datos_pagerank)
    resultado_hibrido = aplicar_ranking_hibrido(
        respuesta_busqueda,
        indice,
        datos_pagerank,
        peso_tfidf=peso_tfidf,
        modelo_tfidf=modelo_tfidf,
    )

    tfidf = resultado_tfidf["resultados"]
    pagerank = resultado_pagerank["resultados"]
    hibrido = resultado_hibrido["resultados"]

    def ids_top(resultados: list[dict[str, Any]]) -> list[str]:
        return [doc["id"] for doc in resultados]

    ids_tfidf = ids_top(tfidf)
    ids_pagerank = ids_top(pagerank)
    ids_hibrido = ids_top(hibrido)

    por_id_tfidf = {doc["id"]: doc for doc in tfidf}
    por_id_pagerank = {doc["id"]: doc for doc in pagerank}
    por_id_hibrido = {doc["id"]: doc for doc in hibrido}

    tabla = []
    for documento in hibrido:
        doc_id = documento["id"]
        tabla.append({
            "id": doc_id,
            "titulo": documento.get("titulo", doc_id),
            "facultad": documento.get("facultad", ""),
            "score_tfidf": por_id_tfidf[doc_id]["score_tfidf"],
            "posicion_tfidf": por_id_tfidf[doc_id]["posicion_tfidf"],
            "score_pagerank": por_id_pagerank[doc_id]["score_pagerank"],
            "pagerank_normalizado": documento["pagerank_normalizado"],
            "posicion_pagerank": por_id_pagerank[doc_id]["posicion_pagerank"],
            "score_hibrido": documento["score_hibrido"],
            "posicion_hibrido": por_id_hibrido[doc_id]["posicion_hibrido"],
        })

    coincidencias = {
        "tfidf_vs_pagerank": _resumen_coincidencia(ids_tfidf, ids_pagerank, top_k),
        "tfidf_vs_hibrido": _resumen_coincidencia(ids_tfidf, ids_hibrido, top_k),
        "pagerank_vs_hibrido": _resumen_coincidencia(ids_pagerank, ids_hibrido, top_k),
    }

    advertencia_top_k = None
    if len(tfidf) <= top_k and len(tfidf) > 0:
        advertencia_top_k = (
            f"La consulta recuperó {len(tfidf)} documentos y top_k={top_k}; "
            "se están comparando todos los candidatos. Para estudiar diferencias "
            "de pertenencia en esta muestra, reduce --top."
        )

    return {
        "consulta": respuesta_busqueda.get("consulta_original", ""),
        "modo_recuperacion": respuesta_busqueda.get("modo", "OR"),
        "total_documentos_recuperados": len(tfidf),
        "parametros": {
            "top_k": top_k,
            "peso_tfidf": float(peso_tfidf),
            "peso_pagerank": 1.0 - float(peso_tfidf),
            "formula_hibrida": "score = peso_tfidf * TFIDF + peso_pagerank * PageRank_normalizado",
            "normalizacion_pagerank": "min-max sobre los documentos recuperados por la consulta",
        },
        "coincidencias_top_k": coincidencias,
        "advertencia_top_k": advertencia_top_k,
        "rankings": {
            "tfidf": [
                {"posicion": doc["posicion_tfidf"], "id": doc["id"], "titulo": doc["titulo"], "score": doc["score_tfidf"]}
                for doc in tfidf[:top_k]
            ],
            "pagerank": [
                {"posicion": doc["posicion_pagerank"], "id": doc["id"], "titulo": doc["titulo"], "score": doc["score_pagerank"]}
                for doc in pagerank[:top_k]
            ],
            "hibrido": [
                {"posicion": doc["posicion_hibrido"], "id": doc["id"], "titulo": doc["titulo"], "score": doc["score_hibrido"]}
                for doc in hibrido[:top_k]
            ],
        },
        "tabla_comparativa": tabla,
    }


def guardar_comparacion(comparacion: dict[str, Any], ruta: Path) -> None:
    """Guarda el reporte comparativo en JSON."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(
        json.dumps(comparacion, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def imprimir_comparacion(comparacion: dict[str, Any], top_k: int = 10) -> None:
    """Imprime tabla ordenada por el score híbrido y métricas top-k."""
    print(f"\nConsulta: {comparacion['consulta']}")
    print(f"Modo de recuperación: {comparacion['modo_recuperacion']}")
    print(f"Documentos recuperados: {comparacion['total_documentos_recuperados']}")
    parametros = comparacion["parametros"]
    print(
        "Ranking híbrido: "
        f"{parametros['peso_tfidf']:.2f} TF-IDF + {parametros['peso_pagerank']:.2f} PageRank"
    )

    print("\nComparación de rankings (orden híbrido)")
    print("-" * 126)
    print(
        f"{'ID':<9} {'Artículo':<43} {'TF-IDF':>10} {'Pos.TF':>7} "
        f"{'PageRank':>12} {'Pos.PR':>7} {'Híbrido':>10} {'Pos.H':>7}"
    )
    print("-" * 126)
    for fila in comparacion["tabla_comparativa"][:top_k]:
        titulo = fila["titulo"]
        if len(titulo) > 41:
            titulo = titulo[:38] + "..."
        print(
            f"{fila['id']:<9} {titulo:<43} {fila['score_tfidf']:>10.6f} "
            f"{fila['posicion_tfidf']:>7} {fila['score_pagerank']:>12.10f} "
            f"{fila['posicion_pagerank']:>7} {fila['score_hibrido']:>10.6f} "
            f"{fila['posicion_hibrido']:>7}"
        )

    print("\nCoincidencia de los primeros resultados")
    for comparacion_id, titulo in (
        ("tfidf_vs_pagerank", "TF-IDF vs PageRank"),
        ("tfidf_vs_hibrido", "TF-IDF vs Híbrido"),
        ("pagerank_vs_hibrido", "PageRank vs Híbrido"),
    ):
        datos = comparacion["coincidencias_top_k"][comparacion_id]
        print(
            f"  {titulo:<23}: {datos['documentos_comunes']}/"
            f"{datos['k_evaluado']} ({datos['coincidencia_porcentual']:.2f} %); "
            f"Jaccard={datos['indice_jaccard']:.4f}"
        )

    if comparacion.get("advertencia_top_k"):
        print("\nAdvertencia: " + comparacion["advertencia_top_k"])
    print("\nNota: el porcentaje de coincidencia compara conjuntos top-k; "
          "el índice Jaccard divide la intersección entre la unión. "
          "La tabla también permite comparar los puestos exactos de cada documento.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compara TF-IDF y PageRank y calcula un ranking híbrido para el buscador BUAP."
    )
    parser.add_argument("consulta", help="Consulta que se desea evaluar.")
    parser.add_argument("--modo", choices=["OR", "AND", "or", "and"], default="OR")
    parser.add_argument("--top", type=int, default=5, dest="top_k", help="Cantidad de resultados para comparar (predeterminado: 5; usa 10 para el corpus de 500 artículos).")
    parser.add_argument("--peso-tfidf", type=float, default=0.7, help="Peso de TF-IDF entre 0 y 1; PageRank usa el complemento (predeterminado: 0.7).")
    parser.add_argument("--indice", type=Path, default=INDICE_DEFAULT)
    parser.add_argument("--pagerank", type=Path, default=PAGERANK_DEFAULT)
    parser.add_argument("--stopwords", type=Path, default=STOPWORDS_DEFAULT)
    parser.add_argument("--salida", type=Path, default=SALIDA_DEFAULT, help="Archivo JSON donde guardar la comparación.")
    parser.add_argument("--sin-guardar", action="store_true", help="No guardar el reporte JSON.")
    parser.add_argument("--json", action="store_true", dest="salida_json", help="Imprimir el reporte completo como JSON.")
    args = parser.parse_args()

    if args.top_k < 1:
        parser.error("--top debe ser un entero positivo.")
    if not 0.0 <= args.peso_tfidf <= 1.0:
        parser.error("--peso-tfidf debe estar entre 0 y 1.")

    try:
        # Import local para evitar un ciclo: buscador.py también expone el
        # ranking híbrido al importar este módulo.
        from buscador import (
            ErrorConsulta,
            buscar,
            cargar_indice,
            cargar_stopwords_para_indice,
        )

        indice = cargar_indice(args.indice)
        stopwords = cargar_stopwords_para_indice(indice, args.stopwords)
        recuperacion = buscar(args.consulta, indice, stopwords, args.modo)
        datos_pagerank = cargar_pagerank(args.pagerank)
        modelo_tfidf = construir_modelo_tfidf(indice)
        comparacion = comparar_resultados(
            recuperacion,
            indice,
            datos_pagerank,
            top_k=args.top_k,
            peso_tfidf=args.peso_tfidf,
            modelo_tfidf=modelo_tfidf,
        )
    except (ErrorConsulta, ErrorRanking, ErrorPageRank, ErrorComparacion, SystemExit) as exc:
        print(f"Error en la comparación: {exc}", file=sys.stderr)
        return 2

    if not args.sin_guardar:
        try:
            guardar_comparacion(comparacion, args.salida)
        except OSError as exc:
            print(f"No se pudo guardar el reporte JSON: {exc}", file=sys.stderr)
            return 2

    if args.salida_json:
        print(json.dumps(comparacion, ensure_ascii=False, indent=2))
    else:
        imprimir_comparacion(comparacion, top_k=args.top_k)
        if not args.sin_guardar:
            print(f"\nReporte JSON guardado en: {args.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
