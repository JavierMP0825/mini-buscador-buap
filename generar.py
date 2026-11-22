#!/usr/bin/env python3
# Genera las páginas HTML a partir de data/catalogo.json y data/articulos.json.
from pathlib import Path
from html import escape
import json, re, sys

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
DATA = ROOT / "data"

def cargar_json(ruta):
    with ruta.open(encoding="utf-8") as f:
        return json.load(f)

def contar_palabras(texto):
    return len(re.findall(r"\b[\wáéíóúüñÁÉÍÓÚÜÑ]+\b", texto, flags=re.UNICODE))

def validar(catalogo, articulos):
    errores = []
    facultades = {f["id"]: f for f in catalogo["facultades"]}
    docs = {a["id"]: a for a in articulos}
    if len(docs) != len(articulos):
        errores.append("Hay identificadores de artículos duplicados.")
    for f in catalogo["facultades"]:
        if len(f["articulos"]) != 20:
            errores.append(f"{f['nombre']}: el catálogo no contiene 20 títulos.")
    for a in articulos:
        if a["facultad_id"] not in facultades:
            errores.append(f"{a['id']}: facultad_id desconocido.")
        if contar_palabras(a["contenido"]) > 200:
            errores.append(f"{a['id']}: supera el límite de 200 palabras.")
        for destino in a.get("relacionados", []):
            if destino not in docs:
                errores.append(f"{a['id']}: enlace relacionado inexistente en este lote: {destino}.")
    if errores:
        print("Se encontraron problemas:")
        for e in errores: print(" -", e)
        raise SystemExit(1)
    print(f"Validación correcta: {len(facultades)} facultades en catálogo, "
          f"{sum(len(f['articulos']) for f in facultades.values())} títulos y {len(articulos)} artículos listos para publicar.")

def ruta_articulo(catalogo, articulo_id):
    for f in catalogo["facultades"]:
        for t in f["articulos"]:
            if t["id"] == articulo_id:
                return Path("facultades") / f["slug"] / t["archivo"]
    raise KeyError(articulo_id)

def plantilla_inicio(catalogo, generados):
    cards = []
    for f in catalogo["facultades"]:
        disponibles = sum(1 for a in generados if a["facultad_id"] == f["id"])
        if disponibles:
            href = f"facultades/{f['slug']}/index.html"
            estado = f'<a href="{href}">Explorar artículos →</a>'
            badge = f'<span class="pill">{disponibles}/20 artículos generados</span>'
        else:
            estado = '<span class="muted">Contenido pendiente de generación</span>'
            badge = '<span class="pill pending">En preparación</span>'
        cards.append(f'''<section class="card"><span class="count">{escape(f['id'].upper())}</span><h2>{escape(f['nombre'])}</h2>{badge}<p>{estado}</p></section>''')
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BUAP Search | Inicio</title><link rel="stylesheet" href="css/estilos.css"></head><body><header class="top"><div class="wrap"><div class="brand">BUAP Search</div><h1>Mini buscador académico</h1><p class="sub">Corpus demostrativo para la materia de Recuperación de Información.</p></div></header><main class="main wrap"><div class="notice"><strong>Primera entrega:</strong> catálogo de 25 facultades y 500 temas. En esta etapa están publicados los 20 artículos de Administración y los 20 de Arquitectura.</div><p class="count">Selecciona una facultad para consultar los documentos disponibles.</p><div class="grid">{''.join(cards)}</div></main><footer class="footer"><div class="wrap">Proyecto académico demostrativo. El contenido no representa publicaciones oficiales de la BUAP.</div></footer></body></html>'''

def generar(catalogo, articulos):
    PUBLIC.mkdir(parents=True, exist_ok=True)
    (PUBLIC / "css").mkdir(exist_ok=True)
    # Copia/asegura CSS en la salida pública.
    css_origen = ROOT / "public" / "css" / "estilos.css"
    generados_por_fac = {}
    por_id = {a["id"]: a for a in articulos}
    for a in articulos:
        fac = next(f for f in catalogo["facultades"] if f["id"] == a["facultad_id"])
        generados_por_fac.setdefault(fac["id"], []).append(a)
        carpeta = PUBLIC / "facultades" / fac["slug"]
        carpeta.mkdir(parents=True, exist_ok=True)
        rel_css = "../../css/estilos.css"
        etiquetas = "".join(f'<span class="tag">{escape(k)}</span>' for k in a.get("palabras_clave", []))
        relacionados = []
        for rid in a.get("relacionados", []):
            destino = por_id[rid]
            destino_fac = next(f for f in catalogo["facultades"] if f["id"] == destino["facultad_id"])
            href = f"../{destino_fac['slug']}/{next(x['archivo'] for x in destino_fac['articulos'] if x['id']==rid)}"
            relacionados.append(f'<li><a class="link" href="{href}">{escape(destino["titulo"])}</a> <span class="muted">— {escape(destino_fac["nombre"])}</span></li>')
        body = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(a['titulo'])} | BUAP Search</title><meta name="description" content="{escape(a['contenido'][:150])}"><link rel="stylesheet" href="{rel_css}"></head><body><header class="top"><div class="wrap"><div class="brand"><a href="../../index.html">BUAP Search</a></div><p class="sub">Corpus académico demostrativo</p></div></header><main class="main wrap"><div class="breadcrumb"><a href="../../index.html">Inicio</a> / <a href="index.html">{escape(fac['nombre'])}</a> / {escape(a['id'])}</div><article class="article"><span class="pill">{escape(fac['nombre'])}</span><h1>{escape(a['titulo'])}</h1><div class="meta"><span class="count">ID: {escape(a['id'])}</span><span class="count">Documento HTML</span></div><p>{escape(a['contenido'])}</p><h3>Palabras clave</h3><div class="taglist">{etiquetas}</div><section class="related"><h2>Artículos relacionados</h2><ul>{''.join(relacionados)}</ul></section><p class="count">{escape(a.get('fuente','Contenido demostrativo'))}</p><p><a class="link" href="index.html">← Volver a {escape(fac['nombre'])}</a></p></article></main><footer class="footer"><div class="wrap">Documento de simulación para fines académicos.</div></footer></body></html>'''
        (carpeta / next(x["archivo"] for x in fac["articulos"] if x["id"] == a["id"])).write_text(body, encoding="utf-8")

    # Índice de cada facultad que ya tiene documentos generados.
    for fac_id, docs in generados_por_fac.items():
        fac = next(f for f in catalogo["facultades"] if f["id"] == fac_id)
        items=[]
        for a in sorted(docs, key=lambda x: x["id"]):
            archivo = next(x["archivo"] for x in fac["articulos"] if x["id"] == a["id"])
            items.append(f'<section class="card"><span class="count">{escape(a["id"])}</span><h2>{escape(a["titulo"])}</h2><p>{escape(a["contenido"][:165])}…</p><a href="{archivo}">Leer artículo →</a></section>')
        html = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(fac['nombre'])} | BUAP Search</title><link rel="stylesheet" href="../../css/estilos.css"></head><body><header class="top"><div class="wrap"><div class="brand"><a href="../../index.html">BUAP Search</a></div><h1>{escape(fac['nombre'])}</h1><p class="sub">Artículos demostrativos disponibles: {len(docs)} de 20.</p></div></header><main class="main wrap"><p class="breadcrumb"><a href="../../index.html">← Volver al inicio</a></p><div class="grid">{''.join(items)}</div></main><footer class="footer"><div class="wrap">Proyecto académico demostrativo.</div></footer></body></html>'''
        carpeta = PUBLIC / "facultades" / fac["slug"]
        (carpeta / "index.html").write_text(html, encoding="utf-8")

    (PUBLIC / "index.html").write_text(plantilla_inicio(catalogo, articulos), encoding="utf-8")

if __name__ == "__main__":
    catalogo = cargar_json(DATA / "catalogo.json")
    articulos = cargar_json(DATA / "articulos.json")["articulos"]
    validar(catalogo, articulos)
    generar(catalogo, articulos)
    print(f"HTML generado correctamente en: {PUBLIC}")
