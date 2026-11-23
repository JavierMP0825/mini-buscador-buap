#!/usr/bin/env python3
"""Genera estadísticas de integridad y tamaño del corpus BUAP."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def leer(ruta: Path):
    return json.loads(ruta.read_text(encoding="utf-8"))


def main() -> int:
    catalogo = leer(ROOT / "data/catalogo.json")
    datos = leer(ROOT / "data/articulos.json")["articulos"]
    por_fac = {f["id"]: f for f in catalogo["facultades"]}
    conteos = Counter(a["facultad_id"] for a in datos)
    palabras_por_articulo = {
        a["id"]: len(re.findall(r"\b[\wáéíóúüñÁÉÍÓÚÜÑ]+\b", a["contenido"], flags=re.UNICODE))
        for a in datos
    }
    por_fac_palabras = {
        fid: [palabras_por_articulo[a["id"]] for a in datos if a["facultad_id"] == fid]
        for fid in por_fac
    }
    html_articulos = list((ROOT / "public/facultades").glob("*/articulo-*.html"))
    paginas_facultad = list((ROOT / "public/facultades").glob("*/index.html"))
    grafo = leer(ROOT / "indices/resumen_grafo.json")
    indice = leer(ROOT / "indices/resumen_indexacion.json")
    pagerank = leer(ROOT / "indices/resumen_pagerank.json")

    total_palabras = sum(palabras_por_articulo.values())
    resumen = {
        "proyecto": "Mini buscador académico BUAP",
        "fase": "Fase 2: corpus completo",
        "total_facultades": len(por_fac),
        "total_articulos": len(datos),
        "total_paginas_html_articulos": len(html_articulos),
        "total_paginas_indice_facultad": len(paginas_facultad),
        "total_paginas_html_incluyendo_inicio": len(html_articulos) + len(paginas_facultad) + 1,
        "palabras_por_articulo": {
            "minimo": min(palabras_por_articulo.values()),
            "maximo": max(palabras_por_articulo.values()),
            "promedio": round(total_palabras / len(datos), 2),
            "maximo_permitido": 200,
        },
        "articulos_por_facultad": [
            {
                "id": fid,
                "nombre": fac["nombre"],
                "total_articulos": conteos[fid],
                "palabras_minimas": min(por_fac_palabras[fid]),
                "palabras_maximas": max(por_fac_palabras[fid]),
            }
            for fid, fac in por_fac.items()
        ],
        "grafo": {
            "nodos": grafo["total_nodos"],
            "aristas": grafo["total_aristas"],
            "componentes_fuertemente_conexas": grafo["componentes_fuertemente_conexas"],
            "fuertemente_conexo": grafo["grafo_fuertemente_conexo"],
            "nodos_sin_enlaces_salientes": len(grafo["nodos_sin_enlaces_salientes"]),
        },
        "indice_invertido": {
            "documentos": indice["total_documentos"],
            "tokens_indexados": indice["total_tokens_sin_stopwords"],
            "terminos_unicos": indice["total_terminos_unicos"],
            "promedio_terminos_por_documento": indice["promedio_terminos_por_documento"],
        },
        "pagerank": {
            "nodos": pagerank["total_nodos"],
            "convergio": pagerank["convergio"],
            "iteraciones": pagerank["iteraciones_realizadas"],
            "suma_puntuaciones": pagerank["suma_pagerank"],
        },
        "contenido": "Artículos demostrativos; no son publicaciones oficiales de la BUAP.",
    }
    salida = ROOT / "indices/resumen_corpus.json"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Resumen del corpus guardado en: {salida}")
    print(f"Facultades: {resumen['total_facultades']} | Artículos: {resumen['total_articulos']}")
    print(f"HTML: {resumen['total_paginas_html_articulos']} artículos + {resumen['total_paginas_indice_facultad']} índices + inicio")
    print(f"Palabras por artículo: {resumen['palabras_por_articulo']['minimo']}–{resumen['palabras_por_articulo']['maximo']} (máximo permitido: 200)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
