"""Pruebas de integridad para la ampliación del corpus a 500 artículos."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def cargar_json(relativo):
    with (ROOT / relativo).open(encoding="utf-8") as archivo:
        return json.load(archivo)


class PruebasCorpusCompleto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogo = cargar_json("data/catalogo.json")
        cls.articulos = cargar_json("data/articulos.json")["articulos"]
        cls.facultades = cls.catalogo["facultades"]
        cls.por_id = {a["id"]: a for a in cls.articulos}
        cls.temas = {
            tema["id"]: (fac, tema)
            for fac in cls.facultades
            for tema in fac["articulos"]
        }

    def test_existen_25_facultades(self):
        self.assertEqual(len(self.facultades), 25)

    def test_cada_facultad_tiene_20_temas(self):
        for facultad in self.facultades:
            with self.subTest(facultad=facultad["id"]):
                self.assertEqual(len(facultad["articulos"]), 20)

    def test_existen_500_articulos_sin_ids_duplicados_ni_faltantes(self):
        ids_catalogo = set(self.temas)
        ids_articulos = [a["id"] for a in self.articulos]
        self.assertEqual(len(self.articulos), 500)
        self.assertEqual(len(ids_articulos), len(set(ids_articulos)))
        self.assertEqual(set(ids_articulos), ids_catalogo)

    def test_todos_los_textos_tienen_menos_de_200_palabras(self):
        for articulo in self.articulos:
            cantidad = len(re.findall(r"\b[\wáéíóúüñÁÉÍÓÚÜÑ]+\b", articulo["contenido"]))
            with self.subTest(articulo=articulo["id"]):
                self.assertGreater(cantidad, 0)
                self.assertLessEqual(cantidad, 200)

    def test_todos_los_enlaces_relacionados_existen_y_no_se_repiten(self):
        ids = set(self.por_id)
        for articulo in self.articulos:
            relacionados = articulo.get("relacionados", [])
            with self.subTest(articulo=articulo["id"]):
                self.assertGreaterEqual(len(relacionados), 2)
                self.assertEqual(len(relacionados), len(set(relacionados)))
                self.assertNotIn(articulo["id"], relacionados)
                self.assertTrue(set(relacionados).issubset(ids))

    def test_se_generaron_los_500_archivos_html(self):
        faltantes = []
        por_facultad = {f["id"]: f for f in self.facultades}
        for articulo in self.articulos:
            facultad = por_facultad[articulo["facultad_id"]]
            tema = next(t for t in facultad["articulos"] if t["id"] == articulo["id"])
            ruta = ROOT / "public" / "facultades" / facultad["slug"] / tema["archivo"]
            if not ruta.is_file():
                faltantes.append(str(ruta.relative_to(ROOT)))
        self.assertEqual(faltantes, [])

    def test_grafo_real_es_fuertemente_conexo(self):
        resumen = cargar_json("indices/resumen_grafo.json")
        self.assertEqual(resumen["total_nodos"], 500)
        self.assertEqual(resumen["componentes_fuertemente_conexas"], 1)
        self.assertTrue(resumen["grafo_fuertemente_conexo"])
        self.assertEqual(resumen["nodos_sin_enlaces_salientes"], [])

    def test_indice_y_pagerank_incluyen_500_documentos(self):
        resumen_indice = cargar_json("indices/resumen_indexacion.json")
        resumen_pr = cargar_json("indices/resumen_pagerank.json")
        self.assertEqual(resumen_indice["total_documentos"], 500)
        self.assertGreater(resumen_indice["total_terminos_unicos"], 1000)
        self.assertEqual(resumen_pr["total_nodos"], 500)
        self.assertTrue(resumen_pr["convergio"])
        self.assertAlmostEqual(resumen_pr["suma_pagerank"], 1.0, places=9)

    def test_reporte_del_corpus_refleja_los_526_html(self):
        resumen = cargar_json("indices/resumen_corpus.json")
        self.assertEqual(resumen["total_articulos"], 500)
        self.assertEqual(resumen["total_paginas_html_articulos"], 500)
        self.assertEqual(resumen["total_paginas_indice_facultad"], 25)
        self.assertEqual(resumen["total_paginas_html_incluyendo_inicio"], 526)
        self.assertLessEqual(resumen["palabras_por_articulo"]["maximo"], 200)


if __name__ == "__main__":
    unittest.main()
