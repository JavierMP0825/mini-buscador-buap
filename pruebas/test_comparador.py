"""Pruebas unitarias de comparación y ranking híbrido."""

import unittest

from buscador import buscar
from comparador import (
    ErrorComparacion,
    aplicar_ranking_hibrido,
    comparar_resultados,
    normalizar_pagerank_candidatos,
)
from pagerank import ErrorPageRank
from ranking import aplicar_ranking_tfidf


INDICE_PRUEBA = {
    "configuracion": {"eliminacion_stopwords": False},
    "estadisticas": {"total_documentos": 3},
    "documentos": {
        "doc-a": {"titulo": "Panel solar doméstico", "facultad": "Ingeniería"},
        "doc-b": {"titulo": "Energía solar", "facultad": "Ingeniería"},
        "doc-c": {"titulo": "Panel de control", "facultad": "Administración"},
    },
    "indice_invertido": {
        "solar": {
            "frecuencia_documental": 2,
            "postings": {"doc-a": 2, "doc-b": 2},
        },
        "panel": {
            "frecuencia_documental": 2,
            "postings": {"doc-a": 2, "doc-c": 2},
        },
        "domestico": {
            "frecuencia_documental": 1,
            "postings": {"doc-a": 1},
        },
        "energia": {
            "frecuencia_documental": 1,
            "postings": {"doc-b": 1},
        },
        "control": {
            "frecuencia_documental": 1,
            "postings": {"doc-c": 1},
        },
    },
}

PAGERANK_PRUEBA = {
    "puntuaciones": {
        "doc-a": 0.01,
        "doc-b": 0.03,
        "doc-c": 0.06,
    }
}


class PruebasNormalizacionPageRank(unittest.TestCase):
    def test_normaliza_al_intervalo_cero_uno(self):
        resultados = [
            {"id": "a", "score_pagerank": 0.1},
            {"id": "b", "score_pagerank": 0.3},
            {"id": "c", "score_pagerank": 0.5},
        ]
        normalizados = normalizar_pagerank_candidatos(resultados)
        self.assertEqual(normalizados["a"], 0.0)
        self.assertAlmostEqual(normalizados["b"], 0.5)
        self.assertEqual(normalizados["c"], 1.0)

    def test_si_todas_las_puntuaciones_son_iguales_no_discrimina(self):
        resultados = [
            {"id": "a", "score_pagerank": 0.2},
            {"id": "b", "score_pagerank": 0.2},
        ]
        self.assertEqual(normalizar_pagerank_candidatos(resultados), {"a": 0.0, "b": 0.0})

    def test_lista_vacia(self):
        self.assertEqual(normalizar_pagerank_candidatos([]), {})

    def test_rechaza_score_negativo(self):
        with self.assertRaises(ErrorComparacion):
            normalizar_pagerank_candidatos([{"id": "a", "score_pagerank": -0.1}])

    def test_rechaza_id_ausente(self):
        with self.assertRaises(ErrorComparacion):
            normalizar_pagerank_candidatos([{"score_pagerank": 0.1}])


class PruebasRankingHibrido(unittest.TestCase):
    def setUp(self):
        self.recuperacion = buscar("solar panel", INDICE_PRUEBA, set(), "OR")

    def test_peso_uno_reproduce_el_orden_tfidf(self):
        hibrido = aplicar_ranking_hibrido(
            self.recuperacion, INDICE_PRUEBA, PAGERANK_PRUEBA, peso_tfidf=1.0
        )
        tfidf = aplicar_ranking_tfidf(self.recuperacion, INDICE_PRUEBA)
        self.assertEqual(
            [doc["id"] for doc in hibrido["resultados"]],
            [doc["id"] for doc in tfidf["resultados"]],
        )

    def test_peso_cero_reproduce_el_orden_pagerank(self):
        resultado = aplicar_ranking_hibrido(
            self.recuperacion, INDICE_PRUEBA, PAGERANK_PRUEBA, peso_tfidf=0.0
        )
        self.assertEqual(
            [doc["id"] for doc in resultado["resultados"]],
            ["doc-c", "doc-b", "doc-a"],
        )

    def test_puntuacion_hibrida_es_ponderacion_de_ambos_componentes(self):
        resultado = aplicar_ranking_hibrido(
            self.recuperacion, INDICE_PRUEBA, PAGERANK_PRUEBA, peso_tfidf=0.6
        )
        for documento in resultado["resultados"]:
            esperado = (
                0.6 * documento["score_tfidf"]
                + 0.4 * documento["pagerank_normalizado"]
            )
            self.assertAlmostEqual(documento["score_hibrido"], esperado)

    def test_no_cambia_el_conjunto_de_documentos_recuperados(self):
        resultado = aplicar_ranking_hibrido(
            self.recuperacion, INDICE_PRUEBA, PAGERANK_PRUEBA
        )
        self.assertEqual(
            {doc["id"] for doc in resultado["resultados"]},
            {doc["id"] for doc in self.recuperacion["resultados"]},
        )

    def test_agrega_posiciones_y_scores_de_los_tres_metodos(self):
        resultado = aplicar_ranking_hibrido(
            self.recuperacion, INDICE_PRUEBA, PAGERANK_PRUEBA
        )
        for posicion, documento in enumerate(resultado["resultados"], start=1):
            self.assertEqual(documento["posicion_hibrido"], posicion)
            self.assertIn("score_tfidf", documento)
            self.assertIn("score_pagerank", documento)
            self.assertIn("score_hibrido", documento)

    def test_rechaza_peso_fuera_de_rango(self):
        with self.assertRaises(ErrorComparacion):
            aplicar_ranking_hibrido(
                self.recuperacion, INDICE_PRUEBA, PAGERANK_PRUEBA, peso_tfidf=1.5
            )

    def test_rechaza_page_rank_incompleto(self):
        datos_incompletos = {"puntuaciones": {"doc-a": 0.4}}
        with self.assertRaises(ErrorPageRank):
            aplicar_ranking_hibrido(self.recuperacion, INDICE_PRUEBA, datos_incompletos)

    def test_comparacion_calcula_coincidencia_y_tabla(self):
        reporte = comparar_resultados(
            self.recuperacion,
            INDICE_PRUEBA,
            PAGERANK_PRUEBA,
            top_k=2,
            peso_tfidf=0.7,
        )
        self.assertEqual(reporte["total_documentos_recuperados"], 3)
        self.assertEqual(len(reporte["tabla_comparativa"]), 3)
        self.assertIn("tfidf_vs_pagerank", reporte["coincidencias_top_k"])
        self.assertEqual(reporte["coincidencias_top_k"]["tfidf_vs_pagerank"]["k_evaluado"], 2)

    def test_comparacion_con_cero_documentos(self):
        recuperacion_vacia = buscar("termino_que_no_existe", INDICE_PRUEBA, set(), "OR")
        reporte = comparar_resultados(
            recuperacion_vacia, INDICE_PRUEBA, PAGERANK_PRUEBA, top_k=10
        )
        self.assertEqual(reporte["total_documentos_recuperados"], 0)
        self.assertEqual(reporte["tabla_comparativa"], [])
        self.assertEqual(
            reporte["coincidencias_top_k"]["tfidf_vs_pagerank"]["coincidencia_porcentual"],
            0.0,
        )

    def test_rechaza_top_k_no_positivo(self):
        with self.assertRaises(ErrorComparacion):
            comparar_resultados(
                self.recuperacion, INDICE_PRUEBA, PAGERANK_PRUEBA, top_k=0
            )

    def test_advierte_si_top_k_incluye_todos_los_candidatos(self):
        reporte = comparar_resultados(
            self.recuperacion, INDICE_PRUEBA, PAGERANK_PRUEBA, top_k=10
        )
        self.assertIsNotNone(reporte["advertencia_top_k"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
