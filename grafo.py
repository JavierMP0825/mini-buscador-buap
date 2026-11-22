#!/usr/bin/env python3
"""Extrae enlaces de los artículos HTML y construye el grafo dirigido.

Uso:
    python3 grafo.py

Genera:
    indices/grafo.json
    indices/resumen_grafo.json
    indices/grafo.dot

Solo los artículos son nodos. Los enlaces a páginas de inicio/índice se
validan, pero no se agregan como aristas del grafo de artículos.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict, deque
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
DATA = ROOT / "data"
INDICES = ROOT / "indices"


class ExtractorEnlaces(HTMLParser):
    """Obtiene el valor href de todas las etiquetas <a> de un HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.enlaces: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() != "a":
            return
        for nombre, valor in attrs:
            if nombre.lower() == "href" and valor:
                self.enlaces.append(valor.strip())
                break

    def handle_startendtag(self, tag: str, attrs) -> None:
        self.handle_starttag(tag, attrs)


def cargar_json(ruta: Path):
    try:
        with ruta.open("r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except FileNotFoundError:
        raise SystemExit(f"No se encontró el archivo requerido: {ruta}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"JSON inválido en {ruta}: {exc}")


def crear_mapa_documentos(catalogo: dict, articulos: list[dict]):
    """Devuelve ID -> metadatos y ruta relativa -> ID."""
    facultades = {f["id"]: f for f in catalogo["facultades"]}
    articulos_por_id = {a["id"]: a for a in articulos}

    if len(articulos_por_id) != len(articulos):
        raise SystemExit("Hay identificadores de artículos duplicados en articulos.json.")

    por_ruta: dict[str, str] = {}
    documentos: dict[str, dict] = {}

    for articulo in articulos:
        facultad_id = articulo["facultad_id"]
        if facultad_id not in facultades:
            raise SystemExit(
                f"{articulo['id']}: facultad_id '{facultad_id}' no existe en catalogo.json."
            )

        facultad = facultades[facultad_id]
        ficha = next(
            (x for x in facultad["articulos"] if x["id"] == articulo["id"]),
            None,
        )
        if ficha is None:
            raise SystemExit(
                f"{articulo['id']}: no aparece en la lista de artículos de su facultad."
            )

        ruta_relativa = Path("facultades") / facultad["slug"] / ficha["archivo"]
        clave_ruta = ruta_relativa.as_posix()
        if clave_ruta in por_ruta:
            raise SystemExit(f"Hay dos artículos asociados a la ruta {clave_ruta}.")

        por_ruta[clave_ruta] = articulo["id"]
        documentos[articulo["id"]] = {
            "id": articulo["id"],
            "facultad_id": facultad_id,
            "facultad": facultad["nombre"],
            "titulo": articulo["titulo"],
            "ruta": clave_ruta,
        }

    return documentos, por_ruta


def resolver_enlace(origen_html: Path, href: str, raiz_publica: Path):
    """Resuelve un href local. Retorna None para enlaces externos/anclas."""
    partes = urlsplit(href)
    if partes.scheme or partes.netloc:
        return None  # HTTP, HTTPS, mailto, tel, etc.

    ruta = unquote(partes.path)
    if not ruta:
        return None  # Solo fragmento, por ejemplo href="#seccion".

    destino = (origen_html.parent / ruta).resolve()
    raiz = raiz_publica.resolve()
    try:
        destino.relative_to(raiz)
    except ValueError:
        raise ValueError(f"El enlace intenta salir de public/: {href}")
    return destino


def extraer_grafo(documentos: dict, por_ruta: dict[str, str]):
    """Lee cada artículo HTML y convierte enlaces a otros artículos en aristas."""
    adyacencia = {doc_id: [] for doc_id in documentos}
    errores = []
    enlaces_locales_rotos = []
    enlaces_no_articulo = 0

    for doc_id, datos in documentos.items():
        archivo = (PUBLIC / datos["ruta"]).resolve()
        if not archivo.is_file():
            errores.append(f"No existe el HTML de {doc_id}: {archivo}")
            continue

        parser = ExtractorEnlaces()
        try:
            parser.feed(archivo.read_text(encoding="utf-8"))
            parser.close()
        except (OSError, UnicodeError) as exc:
            errores.append(f"No se pudo leer {archivo}: {exc}")
            continue

        vistos = set()
        for href in parser.enlaces:
            try:
                destino = resolver_enlace(archivo, href, PUBLIC)
            except ValueError as exc:
                errores.append(f"{doc_id}: {exc}")
                continue

            if destino is None:
                continue

            if not destino.exists():
                enlaces_locales_rotos.append(f"{doc_id} -> {href}")
                continue

            try:
                ruta_relativa = destino.relative_to(PUBLIC.resolve()).as_posix()
            except ValueError:
                errores.append(f"{doc_id}: destino fuera de public/: {href}")
                continue

            destino_id = por_ruta.get(ruta_relativa)
            if destino_id is None:
                enlaces_no_articulo += 1
                continue  # Por ejemplo, enlace al índice de la facultad.

            if destino_id not in vistos:
                adyacencia[doc_id].append(destino_id)
                vistos.add(destino_id)

    if errores or enlaces_locales_rotos:
        print("Se encontraron problemas al extraer el grafo:")
        for error in errores:
            print(f"  ERROR: {error}")
        for enlace in enlaces_locales_rotos:
            print(f"  ENLACE ROTO: {enlace}")
        raise SystemExit(1)

    for origen in adyacencia:
        adyacencia[origen].sort()

    return adyacencia, enlaces_no_articulo


def componentes_debilmente_conexas(adyacencia: dict[str, list[str]]):
    """Calcula componentes conexas ignorando la dirección de las aristas."""
    no_dirigido = {nodo: set() for nodo in adyacencia}
    for origen, destinos in adyacencia.items():
        for destino in destinos:
            no_dirigido[origen].add(destino)
            no_dirigido[destino].add(origen)

    visitados = set()
    componentes = []
    for inicio in adyacencia:
        if inicio in visitados:
            continue
        pila = [inicio]
        visitados.add(inicio)
        componente = []
        while pila:
            actual = pila.pop()
            componente.append(actual)
            for vecino in no_dirigido[actual]:
                if vecino not in visitados:
                    visitados.add(vecino)
                    pila.append(vecino)
        componentes.append(sorted(componente))

    return componentes


def componentes_fuertemente_conexas(adyacencia: dict[str, list[str]]):
    """Calcula componentes fuertemente conexas mediante Kosaraju."""
    inverso = {nodo: [] for nodo in adyacencia}
    for origen, destinos in adyacencia.items():
        for destino in destinos:
            inverso[destino].append(origen)

    visitados = set()
    orden = []

    def dfs1(nodo):
        visitados.add(nodo)
        for vecino in adyacencia[nodo]:
            if vecino not in visitados:
                dfs1(vecino)
        orden.append(nodo)

    for nodo in adyacencia:
        if nodo not in visitados:
            dfs1(nodo)

    visitados.clear()
    componentes = []

    def dfs2(nodo, componente):
        visitados.add(nodo)
        componente.append(nodo)
        for vecino in inverso[nodo]:
            if vecino not in visitados:
                dfs2(vecino, componente)

    for nodo in reversed(orden):
        if nodo not in visitados:
            componente = []
            dfs2(nodo, componente)
            componentes.append(sorted(componente))

    return componentes


def construir_resumen(adyacencia: dict[str, list[str]], enlaces_no_articulo: int):
    entrada = defaultdict(int)
    for origen, destinos in adyacencia.items():
        for destino in destinos:
            entrada[destino] += 1

    nodos_sin_salida = sorted(n for n, destinos in adyacencia.items() if not destinos)
    nodos_sin_entrada = sorted(n for n in adyacencia if entrada[n] == 0)
    componentes_debiles = componentes_debilmente_conexas(adyacencia)
    componentes_fuertes = componentes_fuertemente_conexas(adyacencia)

    return {
        "total_nodos": len(adyacencia),
        "total_aristas": sum(len(destinos) for destinos in adyacencia.values()),
        "total_enlaces_a_paginas_no_articulo": enlaces_no_articulo,
        "nodos_sin_enlaces_salientes": nodos_sin_salida,
        "nodos_sin_enlaces_entrantes": nodos_sin_entrada,
        "componentes_debilmente_conexas": len(componentes_debiles),
        "tamano_componentes_debiles": [len(c) for c in componentes_debiles],
        "componentes_fuertemente_conexas": len(componentes_fuertes),
        "tamano_componentes_fuertes": [len(c) for c in componentes_fuertes],
        "grafo_fuertemente_conexo": len(adyacencia) > 0 and len(componentes_fuertes) == 1,
        "grado_salida_promedio": (
            round(sum(len(v) for v in adyacencia.values()) / len(adyacencia), 3)
            if adyacencia else 0
        ),
        "grado_entrada": dict(sorted(entrada.items())),
        "grado_salida": {n: len(v) for n, v in sorted(adyacencia.items())},
    }


def escapar_dot(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def generar_dot(documentos: dict, adyacencia: dict[str, list[str]]) -> str:
    lineas = [
        "digraph BUAP {",
        '  graph [label="Grafo de artículos BUAP", labelloc="t", fontsize=18, rankdir=LR];',
        '  node [shape=box, style="rounded,filled", fillcolor="#e8f1ff", color="#315b8a", fontname="Arial"];',
        '  edge [color="#718096", arrowsize=0.7];',
    ]
    for doc_id, datos in sorted(documentos.items()):
        etiqueta = f"{doc_id}\n{datos['facultad']}"
        lineas.append(f'  "{doc_id}" [label="{escapar_dot(etiqueta)}"];')
    for origen, destinos in sorted(adyacencia.items()):
        for destino in destinos:
            lineas.append(f'  "{origen}" -> "{destino}";')
    lineas.append("}")
    return "\n".join(lineas) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Construye el grafo dirigido a partir de los HTML.")
    parser.add_argument(
        "--permitir-desconectado",
        action="store_true",
        help="No termina con error si el grafo no es fuertemente conexo.",
    )
    args = parser.parse_args()

    catalogo = cargar_json(DATA / "catalogo.json")
    datos_articulos = cargar_json(DATA / "articulos.json")
    articulos = datos_articulos["articulos"]

    documentos, por_ruta = crear_mapa_documentos(catalogo, articulos)
    adyacencia, enlaces_no_articulo = extraer_grafo(documentos, por_ruta)
    resumen = construir_resumen(adyacencia, enlaces_no_articulo)

    INDICES.mkdir(parents=True, exist_ok=True)
    grafo = {
        "proyecto": "Mini buscador académico BUAP",
        "version_esquema": 1,
        "descripcion": "Grafo dirigido de artículos. Una arista A -> B indica que el HTML de A contiene un enlace a B.",
        "nodos": list(documentos.values()),
        "adyacencia": adyacencia,
        "total_nodos": resumen["total_nodos"],
        "total_aristas": resumen["total_aristas"],
    }

    (INDICES / "grafo.json").write_text(
        json.dumps(grafo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (INDICES / "resumen_grafo.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (INDICES / "grafo.dot").write_text(
        generar_dot(documentos, adyacencia), encoding="utf-8"
    )

    print("\nGrafo construido correctamente desde los enlaces HTML.")
    print(f"  Nodos (artículos):          {resumen['total_nodos']}")
    print(f"  Aristas (enlaces artículo): {resumen['total_aristas']}")
    print(f"  Enlaces a índices/páginas:  {enlaces_no_articulo}")
    print(f"  Componentes débiles:        {resumen['componentes_debilmente_conexas']}")
    print(f"  Componentes fuertes:        {resumen['componentes_fuertemente_conexas']}")
    print(f"  Grado de salida promedio:   {resumen['grado_salida_promedio']}")
    print(f"  Nodos sin salida:           {len(resumen['nodos_sin_enlaces_salientes'])}")
    print("\nArchivos generados:")
    print(f"  - {INDICES / 'grafo.json'}")
    print(f"  - {INDICES / 'resumen_grafo.json'}")
    print(f"  - {INDICES / 'grafo.dot'}")

    if resumen["grafo_fuertemente_conexo"]:
        print("\nValidación: todos los nodos pueden alcanzar a los demás siguiendo la dirección de los enlaces.")
    else:
        print("\nAVISO: el grafo no es fuertemente conexo.")
        print("Esto no impide ejecutar PageRank, pero conviene revisar las conexiones.")
        if not args.permitir_desconectado:
            raise SystemExit(2)


if __name__ == "__main__":
    main()
