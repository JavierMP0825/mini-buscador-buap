"""Pruebas unitarias de TF-IDF y similitud del coseno."""

import math
import unittest

from buscador import buscar
from ranking import (
    ErrorRanking,
    aplicar_ranking_tfidf,
    construir_modelo_tfidf,
)


INDICE_PRUEBA = {
    "configuracion": {"eliminacion_stopwords": True},
    "estadisticas": {"total_documentos": 3},
    "documentos": {
        "adm-01": {"titulo": "Administración general", "facultad": "Administración"},
        "adm-02": {"titulo": "Gestión financiera", "facultad": "Administración"},
        "arq-01": {"titulo": "Diseño arquitectónico", "facultad": "Arquitectura"},
    },
    "indice_invertido": {
        "administracion": {"frecuencia_documental": 1, "postings": {"adm-01": 2}},
        "gestion": {"frecuencia_documental": 2, "postings": {"adm-01": 1, "adm-02": 3}},
        "financiera": {"frecuencia_documental": 1, "postings": {"adm-02": 2}},
        "diseño": {"frecuencia_documental": 1, "postings": {"arq-01": 2}},
        "arquitectonico": {"frecuencia_documental": 1, "postings": {"arq-01": 1}},
    },
}


class PruebasTFIDF(unittest.TestCase):
    def setUp(self):
        self.modelo = construir_modelo_tfidf(INDICE_PRUEBA)

    def test_calcula_idf_con_suavizado(self):
        esperado = math.log((3 + 1) / (1 + 1)) + 1
        self.assertAlmostEqual(self.modelo["idf"]["financiera"], esperado)

    def test_termino_mas_especifico_tiene_idf_mayor(self):
        self.assertGreater(
            self.modelo["idf"]["financiera"],
            self.modelo["idf"]["gestion"],
        )

    def test_calcula_normas_para_todos_los_documentos(self):
        self.assertEqual(set(self.modelo["normas_documentos"]), set(INDICE_PRUEBA["documentos"]))
        self.assertTrue(all(valor > 0 for valor in self.modelo["normas_documentos"].values()))

    def test_tfidf_ordena_documento_con_ambos_terminos_primero(self):
        recuperacion = buscar("gestión financiera", INDICE_PRUEBA, set(), "OR")
        respuesta = aplicar_ranking_tfidf(recuperacion, INDICE_PRUEBA, self.modelo)
        self.assertEqual(respuesta["resultados"][0]["id"], "adm-02")
        self.assertEqual(respuesta["ranking"], "TF-IDF + similitud del coseno")

    def test_puntuaciones_estan_entre_cero_y_uno(self):
        recuperacion = buscar("gestión financiera", INDICE_PRUEBA, set(), "OR")
        respuesta = aplicar_ranking_tfidf(recuperacion, INDICE_PRUEBA, self.modelo)
        for documento in respuesta["resultados"]:
            self.assertGreaterEqual(documento["score_tfidf"], 0.0)
            self.assertLessEqual(documento["score_tfidf"], 1.0)

    def test_modo_and_sigue_respetando_la_interseccion(self):
        recuperacion = buscar("gestión financiera", INDICE_PRUEBA, set(), "AND")
        respuesta = aplicar_ranking_tfidf(recuperacion, INDICE_PRUEBA, self.modelo)
        self.assertEqual([doc["id"] for doc in respuesta["resultados"]], ["adm-02"])

    def test_termino_desconocido_no_rompe_ranking_or(self):
        recuperacion = buscar("gestión desconocido", INDICE_PRUEBA, set(), "OR")
        respuesta = aplicar_ranking_tfidf(recuperacion, INDICE_PRUEBA, self.modelo)
        self.assertEqual(respuesta["total_resultados"], 2)
        self.assertTrue(all("score_tfidf" in doc for doc in respuesta["resultados"]))

    def test_consulta_sin_documentos_mantiene_lista_vacia(self):
        recuperacion = buscar("terminoinexistente", INDICE_PRUEBA, set(), "OR")
        respuesta = aplicar_ranking_tfidf(recuperacion, INDICE_PRUEBA, self.modelo)
        self.assertEqual(respuesta["resultados"], [])
        self.assertEqual(respuesta["total_resultados"], 0)

    def test_empates_se_resuelven_por_identificador(self):
        # Dos documentos idénticos respecto al único término consultado.
        indice = {
            "documentos": {"doc-b": {}, "doc-a": {}},
            "indice_invertido": {
                "prueba": {
                    "frecuencia_documental": 2,
                    "postings": {"doc-b": 1, "doc-a": 1},
                }
            },
        }
        modelo = construir_modelo_tfidf(indice)
        recuperacion = {
            "resultados": [{"id": "doc-b"}, {"id": "doc-a"}],
            "terminos_en_indice": ["prueba"],
            "total_resultados": 2,
        }
        respuesta = aplicar_ranking_tfidf(recuperacion, indice, modelo)
        self.assertEqual([doc["id"] for doc in respuesta["resultados"]], ["doc-a", "doc-b"])
        self.assertAlmostEqual(
            respuesta["resultados"][0]["score_tfidf"],
            respuesta["resultados"][1]["score_tfidf"],
        )

    def test_rechaza_indice_vacio(self):
        with self.assertRaises(ErrorRanking):
            construir_modelo_tfidf({"documentos": {}, "indice_invertido": {}})


if __name__ == "__main__":
    unittest.main(verbosity=2)
