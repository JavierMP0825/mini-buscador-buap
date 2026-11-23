"""Pruebas de la capa que alimenta la API web."""
from pathlib import Path
import unittest

from servicio_busqueda import ErrorSolicitud, ServicioBusqueda

ROOT = Path(__file__).resolve().parents[1]


class PruebasServicioBusqueda(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servicio = ServicioBusqueda(ROOT)

    def test_health_reporta_los_500_documentos(self):
        health = self.servicio.health()
        self.assertEqual(health["status"], "ok")
        self.assertEqual(health["corpus"]["facultades"], 25)
        self.assertEqual(health["corpus"]["documentos"], 500)
        self.assertEqual(health["corpus"]["terminos_unicos"], 2604)

    def test_lista_las_25_facultades(self):
        facultades = self.servicio.listar_facultades()
        self.assertEqual(len(facultades), 25)
        self.assertTrue(all(f["id"] and f["slug"] and f["nombre"] for f in facultades))

    def test_busqueda_tfidf_devuelve_url_y_fragmento(self):
        respuesta = self.servicio.buscar({"q": "inteligencia artificial"})
        self.assertGreater(respuesta["total_resultados"], 0)
        documento = respuesta["resultados"][0]
        self.assertTrue(documento["url"].startswith("/facultades/"))
        self.assertTrue(documento["fragmento"])
        self.assertIn("score_tfidf", documento)

    def test_filtro_por_id_de_facultad(self):
        respuesta = self.servicio.buscar({"q": "derechos humanos", "facultad": "der"})
        self.assertTrue(respuesta["resultados"])
        self.assertTrue(all(d["facultad_id"] == "der" for d in respuesta["resultados"]))
        self.assertEqual(respuesta["facultad_filtro"], "Facultad de Derecho")

    def test_filtro_por_slug_de_facultad(self):
        respuesta = self.servicio.buscar({"q": "derechos humanos", "faculty": "derecho"})
        self.assertTrue(respuesta["resultados"])
        self.assertTrue(all(d["facultad_id"] == "der" for d in respuesta["resultados"]))

    def test_ordenamiento_pagerank(self):
        respuesta = self.servicio.buscar({"q": "derechos humanos", "ranking": "pagerank"})
        self.assertEqual(respuesta["ranking"], "PageRank global")
        self.assertIn("score_pagerank", respuesta["resultados"][0])

    def test_ordenamiento_hibrido_con_peso_personalizado(self):
        respuesta = self.servicio.buscar({"q": "derechos humanos", "ranking": "hibrido", "weight": 0.6})
        self.assertEqual(respuesta["parametros"]["peso_tfidf"], 0.6)
        self.assertIn("score_hibrido", respuesta["resultados"][0])
        self.assertIn("score_tfidf", respuesta["resultados"][0])
        self.assertIn("score_pagerank", respuesta["resultados"][0])

    def test_ranking_ninguno_ordenado_por_id(self):
        respuesta = self.servicio.buscar({"q": "derechos humanos", "ranking": "ninguno"})
        ids = [d["id"] for d in respuesta["resultados"]]
        self.assertEqual(ids, sorted(ids))
        self.assertNotIn("score_tfidf", respuesta["resultados"][0])

    def test_paginacion_no_duplica_ni_omite_resultados(self):
        primera = self.servicio.buscar({"q": "sistemas", "por_pagina": 5, "pagina": 1})
        self.assertGreater(primera["total_resultados"], 5)
        segunda = self.servicio.buscar({"q": "sistemas", "por_pagina": 5, "pagina": 2})
        ids_primera = {d["id"] for d in primera["resultados"]}
        ids_segunda = {d["id"] for d in segunda["resultados"]}
        self.assertEqual(len(primera["resultados"]), 5)
        self.assertTrue(ids_primera.isdisjoint(ids_segunda))
        self.assertTrue(primera["paginacion"]["hay_siguiente"])

    def test_consulta_sin_coincidencias_devuelve_lista_vacia(self):
        respuesta = self.servicio.buscar({"q": "terminoquenoexiste"})
        self.assertEqual(respuesta["total_resultados"], 0)
        self.assertEqual(respuesta["resultados"], [])

    def test_rechaza_consulta_vacia(self):
        with self.assertRaises(ErrorSolicitud):
            self.servicio.buscar({"q": "   "})

    def test_rechaza_ranking_invalido(self):
        with self.assertRaises(ErrorSolicitud):
            self.servicio.buscar({"q": "salud", "ranking": "random"})

    def test_rechaza_peso_fuera_de_rango(self):
        with self.assertRaises(ErrorSolicitud):
            self.servicio.buscar({"q": "salud", "weight": 1.2})

    def test_rechaza_tamano_de_pagina_mayor_a_50(self):
        with self.assertRaises(ErrorSolicitud):
            self.servicio.buscar({"q": "salud", "per_page": 100})

    def test_rechaza_facultad_inexistente(self):
        with self.assertRaises(ErrorSolicitud):
            self.servicio.buscar({"q": "salud", "faculty": "facultad-inventada"})


if __name__ == "__main__":
    unittest.main()
