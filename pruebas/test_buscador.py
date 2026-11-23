"""Pruebas unitarias del módulo de consulta (biblioteca estándar unittest)."""

import unittest

from buscador import ErrorConsulta, buscar


INDICE_PRUEBA = {
    "configuracion": {"eliminacion_stopwords": True},
    "estadisticas": {"total_documentos": 3},
    "documentos": {
        "adm-01": {
            "titulo": "Administración general",
            "facultad": "Facultad de Administración",
            "facultad_id": "adm",
            "ruta": "facultades/administracion/articulo-01.html",
        },
        "adm-02": {
            "titulo": "Gestión financiera",
            "facultad": "Facultad de Administración",
            "facultad_id": "adm",
            "ruta": "facultades/administracion/articulo-02.html",
        },
        "arq-01": {
            "titulo": "Diseño arquitectónico",
            "facultad": "Facultad de Arquitectura",
            "facultad_id": "arq",
            "ruta": "facultades/arquitectura/articulo-01.html",
        },
    },
    "indice_invertido": {
        "administracion": {
            "frecuencia_documental": 1,
            "postings": {"adm-01": 2},
        },
        "gestion": {
            "frecuencia_documental": 2,
            "postings": {"adm-01": 1, "adm-02": 3},
        },
        "financiera": {
            "frecuencia_documental": 1,
            "postings": {"adm-02": 2},
        },
        "diseño": {
            "frecuencia_documental": 1,
            "postings": {"arq-01": 2},
        },
        "arquitectonico": {
            "frecuencia_documental": 1,
            "postings": {"arq-01": 1},
        },
    },
}


class PruebasBuscador(unittest.TestCase):
    def test_or_recupera_documentos_con_al_menos_un_termino(self):
        respuesta = buscar("gestión financiera", INDICE_PRUEBA, set(), "OR")
        self.assertEqual(respuesta["total_resultados"], 2)
        self.assertEqual(
            {doc["id"] for doc in respuesta["resultados"]},
            {"adm-01", "adm-02"},
        )

    def test_and_recupera_documentos_con_todos_los_terminos(self):
        respuesta = buscar("gestión financiera", INDICE_PRUEBA, set(), "AND")
        self.assertEqual(respuesta["total_resultados"], 1)
        self.assertEqual(respuesta["resultados"][0]["id"], "adm-02")

    def test_normaliza_acentos(self):
        respuesta = buscar("diseño arquitectónico", INDICE_PRUEBA, set(), "AND")
        self.assertEqual(respuesta["total_resultados"], 1)
        self.assertEqual(respuesta["resultados"][0]["id"], "arq-01")

    def test_termino_desconocido_en_modo_and_no_devuelve_resultados(self):
        respuesta = buscar("gestion palabrafantasma", INDICE_PRUEBA, set(), "AND")
        self.assertEqual(respuesta["total_resultados"], 0)
        self.assertIn("palabrafantasma", respuesta["terminos_no_encontrados"])

    def test_termino_desconocido_en_modo_or_no_impide_otros_resultados(self):
        respuesta = buscar("gestion palabrafantasma", INDICE_PRUEBA, set(), "OR")
        self.assertEqual(respuesta["total_resultados"], 2)

    def test_consulta_vacia_es_rechazada(self):
        with self.assertRaises(ErrorConsulta):
            buscar("   ", INDICE_PRUEBA, set(), "OR")

    def test_consulta_solo_stopwords_es_rechazada(self):
        with self.assertRaises(ErrorConsulta):
            buscar("de la y", INDICE_PRUEBA, {"de", "la", "y"}, "OR")

    def test_consulta_repetida_no_duplica_terminos(self):
        respuesta = buscar("gestion gestion", INDICE_PRUEBA, set(), "OR")
        self.assertEqual(respuesta["terminos_procesados"], ["gestion"])
        self.assertEqual(respuesta["total_resultados"], 2)

    def test_modo_invalido_es_rechazado(self):
        with self.assertRaises(ErrorConsulta):
            buscar("gestion", INDICE_PRUEBA, set(), "XOR")


if __name__ == "__main__":
    unittest.main(verbosity=2)
