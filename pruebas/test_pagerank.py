"""Pruebas unitarias de PageRank e integración con el motor de consultas."""

import json
import math
import tempfile
import unittest
from pathlib import Path

from pagerank import (
    ErrorPageRank,
    _calcular_pagerank_detallado,
    aplicar_ranking_pagerank,
    calcular_pagerank,
    generar_archivos,
)


class PruebasCalculoPageRank(unittest.TestCase):
    def test_ciclo_regular_asigna_puntuacion_uniforme(self):
        grafo = {"a": ["b"], "b": ["c"], "c": ["a"]}
        resultado = calcular_pagerank(grafo)
        for valor in resultado.values():
            self.assertAlmostEqual(valor, 1 / 3, places=9)

    def test_puntuaciones_suman_uno(self):
        grafo = {
            "a": ["b", "c"],
            "b": ["c"],
            "c": ["a"],
            "d": ["a", "c"],
        }
        resultado = calcular_pagerank(grafo)
        self.assertAlmostEqual(sum(resultado.values()), 1.0, places=12)

    def test_nodo_con_mas_importancia_en_cadena_obtiene_mayor_pagerank(self):
        grafo = {"a": ["b"], "b": ["c"], "c": ["c"]}
        resultado = calcular_pagerank(grafo)
        self.assertGreater(resultado["c"], resultado["b"])
        self.assertGreater(resultado["b"], resultado["a"])
        self.assertAlmostEqual(resultado["c"], 0.8575, places=7)

    def test_distribuye_masa_de_nodos_colgantes(self):
        grafo = {"a": ["b"], "b": []}
        resultado, info = _calcular_pagerank_detallado(grafo)
        self.assertAlmostEqual(sum(resultado.values()), 1.0, places=12)
        self.assertEqual(info["nodos_colgantes"], ["b"])
        self.assertGreater(resultado["b"], resultado["a"])

    def test_grafo_vacio_devuelve_diccionario_vacio(self):
        self.assertEqual(calcular_pagerank({}), {})

    def test_grafo_de_un_solo_nodo_sin_enlaces(self):
        resultado = calcular_pagerank({"unico": []})
        self.assertEqual(resultado, {"unico": 1.0})

    def test_informa_convergencia(self):
        grafo = {"a": ["b"], "b": ["c"], "c": ["a"]}
        resultado, info = _calcular_pagerank_detallado(grafo)
        self.assertTrue(info["convergio"])
        self.assertGreaterEqual(info["iteraciones"], 1)
        self.assertLess(info["diferencia_final"], 1e-10)

    def test_rechaza_amortiguamiento_fuera_de_rango(self):
        with self.assertRaises(ErrorPageRank):
            calcular_pagerank({"a": []}, d=1.0)
        with self.assertRaises(ErrorPageRank):
            calcular_pagerank({"a": []}, d=0.0)

    def test_rechaza_parametros_invalidos(self):
        with self.assertRaises(ErrorPageRank):
            calcular_pagerank({"a": []}, max_iter=0)
        with self.assertRaises(ErrorPageRank):
            calcular_pagerank({"a": []}, tol=0)

    def test_rechaza_destino_inexistente(self):
        with self.assertRaises(ErrorPageRank):
            calcular_pagerank({"a": ["b"]})

    def test_rechaza_enlaces_duplicados(self):
        with self.assertRaises(ErrorPageRank):
            calcular_pagerank({"a": ["a", "a"]})

    def test_rechaza_destinos_que_no_son_cadenas(self):
        with self.assertRaises(ErrorPageRank):
            calcular_pagerank({"a": [[]]})


class PruebasIntegracionPageRank(unittest.TestCase):
    def setUp(self):
        self.grafo = {
            "proyecto": "Corpus de prueba",
            "nodos": [
                {"id": "doc-a", "titulo": "Documento A", "facultad": "Facultad A", "ruta": "a.html"},
                {"id": "doc-b", "titulo": "Documento B", "facultad": "Facultad B", "ruta": "b.html"},
                {"id": "doc-c", "titulo": "Documento C", "facultad": "Facultad C", "ruta": "c.html"},
            ],
            "adyacencia": {"doc-a": ["doc-b"], "doc-b": ["doc-c"], "doc-c": ["doc-c"]},
        }

    def test_genera_json_de_puntuaciones_y_resumen(self):
        with tempfile.TemporaryDirectory() as temporal:
            salida = Path(temporal) / "pagerank.json"
            resumen = Path(temporal) / "resumen_pagerank.json"
            datos, resumen_datos = generar_archivos(
                self.grafo, salida=salida, resumen_salida=resumen
            )
            self.assertTrue(salida.is_file())
            self.assertTrue(resumen.is_file())
            leido = json.loads(salida.read_text(encoding="utf-8"))
            self.assertEqual(leido["algoritmo"], "PageRank")
            self.assertEqual(leido["estadisticas"]["total_nodos"], 3)
            self.assertAlmostEqual(leido["estadisticas"]["suma_pagerank"], 1.0, places=12)
            self.assertEqual(leido["ranking"][0]["id"], "doc-c")
            self.assertTrue(resumen_datos["convergio"])

    def test_ordena_documentos_recuperados_por_pagerank_global(self):
        respuesta_busqueda = {
            "total_resultados": 3,
            "resultados": [{"id": "doc-a"}, {"id": "doc-b"}, {"id": "doc-c"}],
        }
        datos = {"puntuaciones": {"doc-a": 0.05, "doc-b": 0.10, "doc-c": 0.85}}
        resultado = aplicar_ranking_pagerank(respuesta_busqueda, datos)
        self.assertEqual(
            [doc["id"] for doc in resultado["resultados"]],
            ["doc-c", "doc-b", "doc-a"],
        )
        self.assertEqual(resultado["ranking"], "PageRank global")
        self.assertIn("score_pagerank", resultado["resultados"][0])
        self.assertEqual(resultado["resultados"][0]["posicion_pagerank"], 1)

    def test_falla_si_a_un_documento_le_falta_puntuacion(self):
        respuesta = {"resultados": [{"id": "doc-a"}]}
        datos = {"puntuaciones": {"doc-b": 1.0}}
        with self.assertRaises(ErrorPageRank):
            aplicar_ranking_pagerank(respuesta, datos)

    def test_rechaza_conjunto_de_puntuaciones_invalido(self):
        respuesta = {"resultados": [{"id": "doc-a"}]}
        datos = {"puntuaciones": {"doc-a": -0.1}}
        with self.assertRaises(ErrorPageRank):
            aplicar_ranking_pagerank(respuesta, datos)


if __name__ == "__main__":
    unittest.main(verbosity=2)
