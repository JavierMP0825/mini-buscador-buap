#!/usr/bin/env python3
"""Ranking textual de documentos mediante TF-IDF y similitud del coseno.

El módulo consume el índice invertido generado por indexador.py. No modifica
la recuperación OR/AND: recibe sus resultados y los reordena por relevancia.

Fórmulas utilizadas:
    tf_ponderada(t,d) = 1 + ln(tf(t,d))
    idf(t) = ln((N + 1) / (df(t) + 1)) + 1
    tfidf(t,d) = tf_ponderada(t,d) * idf(t)

La consulta se representa como un vector binario (los términos repetidos ya
fueron eliminados durante su preparación) y se compara con cada documento
mediante similitud del coseno.
"""

from __future__ import annotations

import math
from typing import Any


class ErrorRanking(ValueError):
    """Error controlado en la construcción o aplicación del ranking."""


def construir_modelo_tfidf(indice: dict[str, Any]) -> dict[str, Any]:
    """Precalcula IDF y la norma TF-IDF de cada documento.

    La norma se calcula usando TODO el vocabulario de cada documento, no solo
    los términos presentes en una consulta particular. Esto es necesario para
    que la similitud del coseno sea matemáticamente consistente.
    """
    try:
        documentos = indice["documentos"]
        vocabulario = indice["indice_invertido"]
    except (KeyError, TypeError) as exc:
        raise ErrorRanking("El índice no tiene la estructura necesaria para TF-IDF.") from exc

    if not isinstance(documentos, dict) or not isinstance(vocabulario, dict):
        raise ErrorRanking("Los documentos o el vocabulario del índice tienen un formato inválido.")

    total_documentos = len(documentos)
    if total_documentos == 0:
        raise ErrorRanking("No se puede calcular TF-IDF sin documentos.")

    idf: dict[str, float] = {}
    suma_cuadrados: dict[str, float] = {doc_id: 0.0 for doc_id in documentos}

    for termino, registro in vocabulario.items():
        postings = registro.get("postings")
        if not isinstance(postings, dict):
            raise ErrorRanking(f"Los postings del término '{termino}' no son válidos.")

        df = len(postings)
        if df == 0 or df > total_documentos:
            raise ErrorRanking(f"Frecuencia documental inválida para el término '{termino}'.")

        peso_idf = math.log((total_documentos + 1) / (df + 1)) + 1
        idf[termino] = peso_idf

        for doc_id, frecuencia in postings.items():
            if doc_id not in suma_cuadrados:
                raise ErrorRanking(
                    f"El término '{termino}' referencia un documento inexistente: {doc_id}."
                )
            if not isinstance(frecuencia, int) or frecuencia <= 0:
                raise ErrorRanking(
                    f"Frecuencia TF inválida para '{termino}' en el documento '{doc_id}'."
                )

            tf_ponderada = 1 + math.log(frecuencia)
            peso = tf_ponderada * peso_idf
            suma_cuadrados[doc_id] += peso * peso

    normas = {
        doc_id: math.sqrt(suma)
        for doc_id, suma in suma_cuadrados.items()
    }

    return {
        "total_documentos": total_documentos,
        "idf": idf,
        "normas_documentos": normas,
        "formula_tf": "1 + ln(tf)",
        "formula_idf": "ln((N + 1) / (df + 1)) + 1",
        "similitud": "coseno",
    }


def aplicar_ranking_tfidf(
    respuesta_busqueda: dict[str, Any],
    indice: dict[str, Any],
    modelo: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Añade puntuaciones TF-IDF y ordena los documentos recuperados.

    La lista de candidatos procede de buscador.buscar(), por lo que se respetan
    los modos OR y AND. En OR, el coseno considera los términos de la consulta
    que sí existen en el vocabulario; los términos desconocidos no aportan peso.
    """
    if modelo is None:
        modelo = construir_modelo_tfidf(indice)

    resultados = respuesta_busqueda.get("resultados", [])
    if not isinstance(resultados, list):
        raise ErrorRanking("La respuesta de búsqueda no contiene una lista de resultados válida.")

    idf = modelo.get("idf", {})
    normas_documentos = modelo.get("normas_documentos", {})
    vocabulario = indice.get("indice_invertido", {})

    terminos_consulta = [
        termino
        for termino in respuesta_busqueda.get("terminos_en_indice", [])
        if termino in idf and termino in vocabulario
    ]

    # Cada término de consulta aparece una sola vez: q_tf = 1 y su peso es IDF.
    pesos_consulta = {termino: idf[termino] for termino in terminos_consulta}
    norma_consulta = math.sqrt(sum(peso * peso for peso in pesos_consulta.values()))

    resultados_ordenados: list[dict[str, Any]] = []
    for resultado in resultados:
        doc_id = resultado.get("id")
        norma_documento = normas_documentos.get(doc_id, 0.0)
        producto_punto = 0.0

        if norma_documento > 0 and norma_consulta > 0:
            for termino, peso_consulta in pesos_consulta.items():
                frecuencia = vocabulario[termino]["postings"].get(doc_id)
                if frecuencia is None:
                    continue
                peso_documento = (1 + math.log(frecuencia)) * idf[termino]
                producto_punto += peso_documento * peso_consulta
            puntuacion = producto_punto / (norma_documento * norma_consulta)
        else:
            puntuacion = 0.0

        # Evita pequeñas desviaciones numéricas fuera del intervalo teórico.
        puntuacion = min(1.0, max(0.0, puntuacion))
        copia = dict(resultado)
        copia["score_tfidf"] = puntuacion
        resultados_ordenados.append(copia)

    resultados_ordenados.sort(
        key=lambda documento: (-documento["score_tfidf"], documento.get("id", ""))
    )

    for posicion, documento in enumerate(resultados_ordenados, start=1):
        documento["posicion_tfidf"] = posicion

    respuesta = dict(respuesta_busqueda)
    respuesta["resultados"] = resultados_ordenados
    respuesta["ranking"] = "TF-IDF + similitud del coseno"
    respuesta["nota"] = (
        "Los documentos se recuperan mediante OR/AND y se ordenan por similitud "
        "TF-IDF del coseno. La puntuación está entre 0 y 1; un valor mayor indica "
        "mayor coincidencia textual con la consulta."
    )
    respuesta["terminos_usados_en_ranking"] = terminos_consulta
    return respuesta
