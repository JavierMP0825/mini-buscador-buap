#!/usr/bin/env python3
"""Construye un índice invertido a partir de los artículos HTML del corpus BUAP.

Uso:
    python3 generar.py
    python3 grafo.py
    python3 indexador.py

El índice se construye leyendo el contenido publicado en los archivos HTML.
El archivo grafo.json se utiliza como inventario de documentos y metadatos.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
INDICES = ROOT / "indices"
STOPWORDS_DEFAULT = ROOT / "data" / "stopwords_es.txt"

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}
IGNORED_CLASSES = {"meta", "related", "count", "pill"}
IGNORED_TAGS = {"script", "style", "noscript", "h2", "h3", "h4", "h5", "h6", "a"}
TOKEN_RE = re.compile(r"[a-zñ0-9]+", flags=re.UNICODE)


def normalizar(texto: str) -> str:
    """Pasa a minúsculas y elimina diacríticos, conservando la letra ñ."""
    texto = texto.lower().replace("ñ", "__enie__")
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caracter for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )
    return texto.replace("__enie__", "ñ")


def tokenizar(texto: str, stopwords: set[str]) -> list[str]:
    """Convierte un texto a tokens normalizados y descarta palabras vacías."""
    texto_normalizado = normalizar(texto)
    tokens = TOKEN_RE.findall(texto_normalizado)
    return [token for token in tokens if token not in stopwords and len(token) > 1]


def cargar_stopwords(ruta: Path) -> set[str]:
    if not ruta.exists():
        raise SystemExit(f"No se encontró el archivo de stopwords: {ruta}")
    palabras: set[str] = set()
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        palabra = linea.strip()
        if not palabra or palabra.startswith("#"):
            continue
        palabras.add(normalizar(palabra))
    return palabras


class ExtractorTextoArticulo(HTMLParser):
    """Extrae texto visible del bloque <article class=\"article\">.

    Excluye navegación, metadatos, enlaces relacionados y elementos decorativos.
    Incluye el título, el texto descriptivo y las etiquetas de palabras clave.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.textos: list[str] = []
        self.pila: list[tuple[str, bool, bool, bool]] = []
        self.dentro_articulo = False
        self.ignorado = False

    def handle_starttag(self, tag: str, attrs) -> None:
        atributos = {k.lower(): (v or "") for k, v in attrs}
        clases = set(atributos.get("class", "").lower().split())

        es_articulo = tag.lower() == "article" and "article" in clases
        dentro = self.dentro_articulo or es_articulo
        ignorar_heredado = self.ignorado
        ignorar = ignorar_heredado or bool(clases & IGNORED_CLASSES) or tag.lower() in IGNORED_TAGS

        if tag.lower() not in VOID_TAGS:
            self.pila.append((tag.lower(), ignorar, self.dentro_articulo, self.ignorado))
        self.dentro_articulo = dentro
        self.ignorado = ignorar

    def handle_startendtag(self, tag: str, attrs) -> None:
        if tag.lower() not in VOID_TAGS:
            self.handle_starttag(tag, attrs)
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for posicion in range(len(self.pila) - 1, -1, -1):
            if self.pila[posicion][0] == tag:
                _, _, estado_anterior, ignorado_anterior = self.pila[posicion]
                del self.pila[posicion:]
                self.dentro_articulo = estado_anterior
                self.ignorado = ignorado_anterior
                break

    def handle_data(self, data: str) -> None:
        if self.dentro_articulo and not self.ignorado:
            texto = " ".join(data.split())
            if texto:
                self.textos.append(texto)

    def resultado(self) -> str:
        return " ".join(self.textos)


def extraer_texto_html(ruta: Path) -> str:
    try:
        html = ruta.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"No existe el HTML del documento: {ruta}")
    except UnicodeDecodeError as exc:
        raise SystemExit(f"No se pudo leer como UTF-8 {ruta}: {exc}")

    parser = ExtractorTextoArticulo()
    try:
        parser.feed(html)
        parser.close()
    except Exception as exc:  # HTMLParser tolera HTML incompleto; informa errores inesperados.
        raise SystemExit(f"Error al procesar HTML {ruta}: {exc}")

    texto = parser.resultado()
    if not texto.strip():
        raise SystemExit(
            f"No se encontró texto dentro de <article class=\"article\"> en {ruta}."
        )
    return texto


def cargar_grafo(ruta: Path) -> list[dict]:
    if not ruta.exists():
        raise SystemExit(
            "No se encontró indices/grafo.json. Ejecuta primero:\n"
            "  python3 generar.py\n  python3 grafo.py"
        )
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"El archivo {ruta} no contiene JSON válido: {exc}")

    nodos = datos.get("nodos", [])
    if not nodos:
        raise SystemExit("El grafo no contiene nodos para indexar.")

    ids = [nodo.get("id") for nodo in nodos]
    if None in ids or len(ids) != len(set(ids)):
        raise SystemExit("El grafo contiene identificadores vacíos o duplicados.")
    return nodos


def construir_indice(
    nodos: list[dict],
    public_dir: Path,
    stopwords: set[str],
    stopwords_path: Path,
) -> tuple[dict, dict]:
    documentos: dict[str, dict] = {}
    indice: dict[str, dict[str, int]] = {}
    total_tokens = 0
    total_tokens_originales = 0

    for nodo in nodos:
        doc_id = nodo["id"]
        ruta_relativa = Path(nodo["ruta"])

        # Evita que una ruta registrada pueda salir del directorio public.
        ruta_html = (public_dir / ruta_relativa).resolve()
        raiz_publica = public_dir.resolve()
        if ruta_html != raiz_publica and raiz_publica not in ruta_html.parents:
            raise SystemExit(f"Ruta de documento fuera de public/: {nodo['ruta']}")

        texto = extraer_texto_html(ruta_html)
        tokens = tokenizar(texto, stopwords)
        frecuencias = Counter(tokens)

        if not frecuencias:
            raise SystemExit(
                f"El documento {doc_id} no produjo términos después del procesamiento."
            )

        for termino, frecuencia in frecuencias.items():
            indice.setdefault(termino, {})[doc_id] = frecuencia

        documentos[doc_id] = {
            "titulo": nodo.get("titulo", doc_id),
            "facultad_id": nodo.get("facultad_id", ""),
            "facultad": nodo.get("facultad", ""),
            "ruta": nodo["ruta"],
            "total_terminos": len(tokens),
            "terminos_unicos": len(frecuencias),
        }
        total_tokens += len(tokens)
        total_tokens_originales += len(TOKEN_RE.findall(normalizar(texto)))

    indice_invertido = {}
    for termino in sorted(indice):
        postings = dict(sorted(indice[termino].items()))
        indice_invertido[termino] = {
            "frecuencia_documental": len(postings),
            "postings": postings,
        }

    cantidad_documentos = len(documentos)
    vocabulario = len(indice_invertido)
    promedio = total_tokens / cantidad_documentos if cantidad_documentos else 0

    resultado = {
        "proyecto": "Mini buscador académico BUAP",
        "version_esquema": 1,
        "descripcion": (
            "Índice invertido obtenido del texto de los artículos HTML. "
            "Cada término contiene su frecuencia documental y las frecuencias "
            "del término en cada documento (postings)."
        ),
        "configuracion": {
            "normalizacion": "minúsculas, eliminación de acentos excepto ñ",
            "tokenizacion": "secuencias alfanuméricas en español",
            "eliminacion_stopwords": bool(stopwords),
            "archivo_stopwords": (str(stopwords_path.relative_to(ROOT)) if stopwords_path.is_relative_to(ROOT) else str(stopwords_path)),
            "cantidad_stopwords": len(stopwords),
            "stemming": False,
        },
        "estadisticas": {
            "total_documentos": cantidad_documentos,
            "total_tokens_sin_stopwords": total_tokens,
            "total_tokens_antes_stopwords": total_tokens_originales,
            "tokens_descartados": total_tokens_originales - total_tokens,
            "total_terminos_unicos": vocabulario,
            "promedio_terminos_por_documento": round(promedio, 3),
        },
        "documentos": documentos,
        "indice_invertido": indice_invertido,
    }

    # Archivo resumen separado para validaciones rápidas y reportes.
    resumen = {
        "total_documentos": cantidad_documentos,
        "total_tokens_sin_stopwords": total_tokens,
        "total_tokens_antes_stopwords": total_tokens_originales,
        "tokens_descartados": total_tokens_originales - total_tokens,
        "total_terminos_unicos": vocabulario,
        "promedio_terminos_por_documento": round(promedio, 3),
        "cantidad_stopwords": len(stopwords),
        "documentos_sin_terminos": [],
        "terminos_mas_frecuentes": sorted(
            [
                {
                    "termino": termino,
                    "frecuencia_total": sum(registro["postings"].values()),
                    "frecuencia_documental": registro["frecuencia_documental"],
                }
                for termino, registro in indice_invertido.items()
            ],
            key=lambda item: (-item["frecuencia_total"], item["termino"]),
        )[:20],
    }

    # Verifica las propiedades básicas del índice antes de guardarlo.
    suma_postings = 0
    ids_documentos = set(documentos)
    for termino, registro in indice_invertido.items():
        postings = registro["postings"]
        if registro["frecuencia_documental"] != len(postings):
            raise SystemExit(
                f"Frecuencia documental inconsistente para el término: {termino}"
            )
        if not set(postings).issubset(ids_documentos):
            raise SystemExit(
                f"El término {termino} contiene referencias a documentos inexistentes."
            )
        if any(not isinstance(tf, int) or tf <= 0 for tf in postings.values()):
            raise SystemExit(f"Frecuencia de término inválida para: {termino}")
        suma_postings += sum(postings.values())

    if suma_postings != total_tokens:
        raise SystemExit(
            "La suma de las frecuencias de los postings no coincide con "
            "el total de tokens indexados."
        )

    return resultado, resumen


def guardar_json(ruta: Path, datos: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Procesa los artículos HTML y genera un índice invertido."
    )
    parser.add_argument(
        "--grafo", type=Path, default=INDICES / "grafo.json",
        help="Ruta del inventario de artículos generado por grafo.py.",
    )
    parser.add_argument(
        "--public", type=Path, default=PUBLIC,
        help="Directorio que contiene los artículos HTML.",
    )
    parser.add_argument(
        "--stopwords", type=Path, default=STOPWORDS_DEFAULT,
        help="Archivo de palabras vacías en español.",
    )
    parser.add_argument(
        "--sin-stopwords", action="store_true",
        help="No elimina palabras vacías (opción útil para comparar resultados).",
    )
    args = parser.parse_args()

    stopwords_path = args.stopwords.resolve()
    stopwords = set() if args.sin_stopwords else cargar_stopwords(stopwords_path)
    nodos = cargar_grafo(args.grafo.resolve())

    resultado, resumen = construir_indice(
        nodos=nodos,
        public_dir=args.public.resolve(),
        stopwords=stopwords,
        stopwords_path=stopwords_path,
    )

    salida_indice = INDICES / "indice_invertido.json"
    salida_resumen = INDICES / "resumen_indexacion.json"
    guardar_json(salida_indice, resultado)
    guardar_json(salida_resumen, resumen)

    stats = resultado["estadisticas"]
    print("\nINDEXACIÓN COMPLETADA CORRECTAMENTE")
    print("----------------------------------")
    print(f"Documentos procesados : {stats['total_documentos']}")
    print(f"Tokens antes de stopwords: {stats['total_tokens_antes_stopwords']}")
    print(f"Tokens indexados      : {stats['total_tokens_sin_stopwords']}")
    print(f"Términos únicos       : {stats['total_terminos_unicos']}")
    print(f"Promedio por documento: {stats['promedio_terminos_por_documento']}")
    print(f"Tokens descartados    : {stats['tokens_descartados']}")
    print(f"Palabras vacías usadas: {len(stopwords)}")
    print(f"\nÍndice guardado en    : {salida_indice}")
    print(f"Resumen guardado en   : {salida_resumen}")
    print("\nEjemplo de términos indexados:")
    for elemento in resumen["terminos_mas_frecuentes"][:10]:
        print(
            f"  {elemento['termino']}: {elemento['frecuencia_total']} aparición(es), "
            f"en {elemento['frecuencia_documental']} documento(s)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
