"""Comprueba que el generador conserva la interfaz y los archivos web."""
import unittest
from pathlib import Path

from generar import cargar_json, plantilla_inicio

ROOT = Path(__file__).resolve().parents[1]


class PruebasInterfazWeb(unittest.TestCase):
    def test_generador_incluye_formulario_y_script_de_busqueda(self):
        catalogo = cargar_json(ROOT / "data" / "catalogo.json")
        articulos = cargar_json(ROOT / "data" / "articulos.json")["articulos"]
        pagina = plantilla_inicio(catalogo, articulos)
        self.assertIn('id="search-form"', pagina)
        self.assertIn('id="ranking"', pagina)
        self.assertIn('id="faculty"', pagina)
        self.assertIn('src="js/buscador.js"', pagina)

    def test_javascript_llama_a_la_api(self):
        script = (ROOT / "public" / "js" / "buscador.js").read_text(encoding="utf-8")
        self.assertIn('fetch("/api/search"', script)
        self.assertIn('fetch("/api/facultades"', script)
        self.assertIn('fetch("/api/health"', script)

    def test_configuracion_apache_incluye_proxy_y_document_root(self):
        configuracion = (ROOT / "deploy" / "apache-mini-buscador.conf").read_text(encoding="utf-8")
        self.assertIn("DocumentRoot", configuracion)
        self.assertIn("ProxyPass        /api/", configuracion)
        self.assertIn("ProxyPassReverse", configuracion)


if __name__ == "__main__":
    unittest.main()
