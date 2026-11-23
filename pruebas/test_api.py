"""Pruebas HTTP de Flask (se activan después de instalar requirements.txt)."""
import importlib.util
import unittest

FLASK_DISPONIBLE = importlib.util.find_spec("flask") is not None


@unittest.skipUnless(FLASK_DISPONIBLE, "Instala Flask con: python3 -m pip install -r requirements.txt")
class PruebasAPIFlask(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        cls.client = create_app().test_client()

    def test_health_responde_ok(self):
        respuesta = self.client.get("/api/health")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.get_json()["corpus"]["documentos"], 500)

    def test_facultades_devuelve_25(self):
        respuesta = self.client.get("/api/facultades")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.get_json()["facultades"]), 25)

    def test_busqueda_get(self):
        respuesta = self.client.get("/api/search?q=inteligencia%20artificial&ranking=tfidf")
        self.assertEqual(respuesta.status_code, 200)
        self.assertGreater(respuesta.get_json()["total_resultados"], 0)

    def test_busqueda_post_con_filtro(self):
        respuesta = self.client.post(
            "/api/search",
            json={"q": "derechos humanos", "modo": "AND", "ranking": "hibrido", "facultad": "der"},
        )
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.get_json()
        self.assertTrue(datos["resultados"])
        self.assertTrue(all(doc["facultad_id"] == "der" for doc in datos["resultados"]))

    def test_rechaza_cuerpo_no_json(self):
        respuesta = self.client.post("/api/search", data="esto no es json", content_type="text/plain")
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("error", respuesta.get_json())


if __name__ == "__main__":
    unittest.main()
