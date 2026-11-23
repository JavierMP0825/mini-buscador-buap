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
    esperados = {
        tema["id"]: (fac["id"], tema["titulo"])
        for fac in catalogo["facultades"]
        for tema in fac["articulos"]
    }
    if len(facultades) != 25:
        errores.append(f"Se esperaban 25 facultades y se encontraron {len(facultades)}.")
    if len(docs) != len(articulos):
        errores.append("Hay identificadores de artículos duplicados.")
    for f in catalogo["facultades"]:
        if len(f["articulos"]) != 20:
            errores.append(f"{f['nombre']}: el catálogo no contiene 20 títulos.")
    faltantes = sorted(set(esperados) - set(docs))
    sobrantes = sorted(set(docs) - set(esperados))
    if faltantes:
        errores.append(f"Faltan {len(faltantes)} artículos del catálogo: {', '.join(faltantes[:8])}.")
    if sobrantes:
        errores.append(f"Hay {len(sobrantes)} artículos fuera del catálogo: {', '.join(sobrantes[:8])}.")
    for aid, a in docs.items():
        if a.get("facultad_id") not in facultades:
            errores.append(f"{aid}: facultad_id desconocido.")
        elif aid in esperados and a.get("facultad_id") != esperados[aid][0]:
            errores.append(f"{aid}: está asignado a una facultad distinta de la del catálogo.")
        if aid in esperados and a.get("titulo") != esperados[aid][1]:
            errores.append(f"{aid}: el título no coincide con el catálogo.")
        if contar_palabras(a.get("contenido", "")) > 200:
            errores.append(f"{aid}: supera el límite de 200 palabras.")
        if not a.get("contenido", "").strip():
            errores.append(f"{aid}: no tiene contenido.")
        for destino in a.get("relacionados", []):
            if destino not in docs:
                errores.append(f"{aid}: enlace relacionado inexistente: {destino}.")
    if errores:
        print("Se encontraron problemas:")
        for e in errores: print(" -", e)
        raise SystemExit(1)
    print(f"Validación correcta: {len(facultades)} facultades, "
          f"{len(esperados)} títulos y {len(articulos)} artículos listos para publicar.")

def ruta_articulo(catalogo, articulo_id):
    for f in catalogo["facultades"]:
        for t in f["articulos"]:
            if t["id"] == articulo_id:
                return Path("facultades") / f["slug"] / t["archivo"]
    raise KeyError(articulo_id)

def plantilla_inicio(catalogo, generados):
    """Construye la portada interactiva sin perder el catálogo de facultades."""
    cards = []
    for f in catalogo["facultades"]:
        disponibles = sum(1 for a in generados if a["facultad_id"] == f["id"])
        if disponibles:
            href = f"facultades/{f['slug']}/index.html"
            estado = f'<a href="{href}">Explorar artículos →</a>'
            badge = f'<span class="pill">{disponibles}/20 artículos</span>'
        else:
            estado = '<span class="muted">Contenido pendiente de generación</span>'
            badge = '<span class="pill pending">En preparación</span>'
        cards.append(
            f'<section class="faculty-card"><span class="faculty-code">{escape(f["id"].upper())}</span>'
            f'<h3>{escape(f["nombre"])}</h3>{badge}<p>{estado}</p></section>'
        )

    total_publicados = len(generados)
    total_catalogados = sum(len(f["articulos"]) for f in catalogo["facultades"])
    return f'''<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="description" content="Buscador académico demostrativo con documentos HTML de 25 facultades de la BUAP.">
  <title>BUAP Search | Buscador académico</title>
  <link rel="stylesheet" href="css/estilos.css">
  <script src="js/buscador.js" defer></script>
</head>
<body>
  <header class="search-hero">
    <div class="wrap hero-inner">
      <div class="brand-row"><a class="brand" href="index.html">BUAP <span>Search</span></a><span class="hero-label">PROYECTO ACADÉMICO</span></div>
      <p class="eyebrow">RECUPERACIÓN DE INFORMACIÓN</p>
      <h1>Explora el conocimiento<br><span>de las facultades BUAP</span></h1>
      <p class="hero-copy">Busca entre artículos demostrativos de 25 facultades y compara distintas formas de ordenar la información.</p>
      <section class="search-panel" aria-label="Formulario de búsqueda">
        <form id="search-form">
          <label class="sr-only" for="query">¿Qué información estás buscando?</label>
          <div class="search-input-row">
            <span class="search-symbol" aria-hidden="true">⌕</span>
            <input id="query" name="q" type="search" maxlength="200" placeholder="Ej. inteligencia artificial, derecho laboral, nutrición animal…" autocomplete="off" required>
            <button id="search-button" type="submit">Buscar <span aria-hidden="true">→</span></button>
          </div>
          <div class="search-options">
            <label>Coincidencia
              <select id="mode" name="modo"><option value="OR">OR · cualquiera de los términos</option><option value="AND">AND · todos los términos</option></select>
            </label>
            <label>Ordenar resultados
              <select id="ranking" name="ranking">
                <option value="tfidf">Relevancia textual · TF-IDF</option>
                <option value="pagerank">Importancia de enlaces · PageRank</option>
                <option value="hibrido">Combinado · Híbrido</option>
                <option value="ninguno">Sin ranking · ID de documento</option>
              </select>
            </label>
            <label>Facultad
              <select id="faculty" name="facultad"><option value="all">Todas las facultades</option></select>
            </label>
          </div>
          <div class="weight-row" id="weight-row" hidden>
            <label for="weight">Peso de TF-IDF en el ranking híbrido</label>
            <input id="weight" type="range" min="0" max="1" value="0.7" step="0.05">
            <output id="weight-value" for="weight">70 % TF-IDF · 30 % PageRank</output>
          </div>
        </form>
        <div class="quick-searches"><span>Prueba:</span>
          <button type="button" class="quick-query" data-query="inteligencia artificial">inteligencia artificial</button>
          <button type="button" class="quick-query" data-query="derechos humanos">derechos humanos</button>
          <button type="button" class="quick-query" data-query="salud bucal">salud bucal</button>
        </div>
      </section>
      <div class="hero-status" id="api-status" role="status">Conectando con el motor de búsqueda…</div>
    </div>
  </header>

  <main class="wrap page-main">
    <section class="stats-strip" aria-label="Estadísticas del corpus">
      <div><strong id="stat-documents">{total_publicados}</strong><span>artículos HTML</span></div>
      <div><strong id="stat-faculties">{len(catalogo["facultades"])}</strong><span>facultades</span></div>
      <div><strong id="stat-terms">—</strong><span>términos indexados</span></div>
      <div><strong id="stat-links">—</strong><span>enlaces en el grafo</span></div>
    </section>

    <section class="results-section" id="results-section" aria-live="polite" aria-busy="false">
      <div class="section-heading"><div><p class="eyebrow dark-eyebrow">RECUPERACIÓN DE DOCUMENTOS</p><h2>Resultados de búsqueda</h2></div><span class="result-counter" id="result-count">Aún no has realizado una búsqueda</span></div>
      <div id="results-message" class="empty-state"><div class="empty-icon" aria-hidden="true">⌕</div><h3>¿Qué te gustaría investigar?</h3><p>Escribe una consulta para encontrar artículos de las facultades de la BUAP.</p></div>
      <div id="results-list" class="results-list"></div>
      <nav id="pagination" class="pagination" aria-label="Paginación de resultados" hidden>
        <button id="previous-page" type="button" disabled>← Anterior</button>
        <span id="page-indicator">Página 1 de 1</span>
        <button id="next-page" type="button" disabled>Siguiente →</button>
      </nav>
    </section>

    <section class="faculties-section" id="facultades">
      <div class="section-heading"><div><p class="eyebrow dark-eyebrow">CORPUS ACADÉMICO</p><h2>Explora por facultad</h2></div><span class="result-counter">{total_publicados} de {total_catalogados} artículos publicados</span></div>
      <div class="faculty-grid">{''.join(cards)}</div>
    </section>
  </main>
  <footer class="site-footer"><div class="wrap"><strong>BUAP Search</strong><span>Proyecto académico demostrativo para la materia de Recuperación de Información.</span><p>Los artículos son contenido simulado y no representan publicaciones oficiales ni contenido institucional de la BUAP.</p></div></footer>
</body>
</html>'''

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
