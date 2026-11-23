#!/usr/bin/env python3
"""Realiza consultas sencillas sobre el índice invertido del corpus BUAP.

Uso:
    python3 buscador.py "gestion financiera"
    python3 buscador.py "diseño arquitectónico" --modo AND
    python3 buscador.py "administracion" --modo OR --json
    python3 buscador.py                 # modo interactivo

Los resultados se recuperan desde el índice invertido y, por defecto, se
ordenan mediante TF-IDF y similitud del coseno. El argumento --ranking ninguno
permite conservar el orden estable por identificador para comparar.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from indexador import cargar_stopwords, tokenizar
from ranking import aplicar_ranking_tfidf, construir_modelo_tfidf, ErrorRanking

ROOT = Path(__file__).resolve().parent
INDICE_DEFAULT = ROOT / "indices" / "indice_invertido.json"
STOPWORDS_DEFAULT = ROOT / "data" / "stopwords_es.txt"


class ErrorConsulta(ValueError):
    """Error controlado al procesar una consulta."""


def cargar_indice(ruta: Path) -> dict[str, Any]:
    """Carga el índice invertido y valida los campos indispensables."""
    if not ruta.exists():
        raise SystemExit(
            f"No se encontró el índice: {ruta}\n"
            "Genera primero los archivos con:\n"
            "  python3 generar.py\n  python3 grafo.py\n  python3 indexador.py"
        )

    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"El índice no contiene JSON válido: {exc}")

    requeridos = {"configuracion", "estadisticas", "documentos", "indice_invertido"}
    faltantes = requeridos - datos.keys()
    if faltantes:
        raise SystemExit(
            "El archivo no tiene el formato de índice esperado. "
            f"Faltan campos: {', '.join(sorted(faltantes))}"
        )

    if not isinstance(datos["documentos"], dict) or not isinstance(datos["indice_invertido"], dict):
        raise SystemExit("El índice tiene una estructura inválida en documentos o indice_invertido.")

    return datos


def preparar_terminos_consulta(
    consulta: str,
    stopwords: set[str],
) -> list[str]:
    """Aplica a la consulta el mismo procesamiento usado para indexar."""
    if not consulta or not consulta.strip():
        raise ErrorConsulta("Escribe una consulta con al menos una palabra.")

    terminos = tokenizar(consulta, stopwords)
    # Una consulta como "de la y" puede quedar vacía después del filtrado.
    if not terminos:
        raise ErrorConsulta(
            "La consulta no contiene términos útiles después de eliminar "
            "las palabras vacías. Prueba con palabras más específicas."
        )

    # Repetir una palabra en la consulta no debe cambiar la recuperación.
    return list(dict.fromkeys(terminos))


def buscar(
    consulta: str,
    indice: dict[str, Any],
    stopwords: set[str] | None = None,
    modo: str = "OR",
) -> dict[str, Any]:
    """Recupera documentos mediante unión (OR) o intersección (AND).

    OR: devuelve documentos que contienen al menos uno de los términos.
    AND: devuelve documentos que contienen todos los términos procesados.

    No calcula puntuaciones ni aplica ranking; el orden por ID solo hace que
    la salida sea reproducible durante las pruebas.
    """
    modo = modo.upper()
    if modo not in {"OR", "AND"}:
        raise ErrorConsulta("El modo debe ser OR o AND.")

    terminos = preparar_terminos_consulta(consulta, stopwords or set())
    indice_terminos = indice["indice_invertido"]
    documentos = indice["documentos"]

    terminos_encontrados = [t for t in terminos if t in indice_terminos]
    terminos_no_encontrados = [t for t in terminos if t not in indice_terminos]

    conjuntos = [
        set(indice_terminos[t].get("postings", {}).keys())
        for t in terminos_encontrados
    ]

    if not conjuntos:
        ids_resultado: set[str] = set()
    elif modo == "AND":
        # Si uno de los términos no aparece en el vocabulario, no hay
        # documentos que contengan todos los términos de la consulta.
        if terminos_no_encontrados:
            ids_resultado = set()
        else:
            ids_resultado = set.intersection(*conjuntos)
    else:
        ids_resultado = set.union(*conjuntos)

    resultados: list[dict[str, Any]] = []
    for doc_id in sorted(ids_resultado):
        metadatos = documentos.get(doc_id)
        if not metadatos:
            # Un posting sin metadatos indica un índice inconsistente.
            continue

        frecuencias: dict[str, int] = {}
        for termino in terminos_encontrados:
            frecuencia = indice_terminos[termino].get("postings", {}).get(doc_id)
            if frecuencia is not None:
                frecuencias[termino] = int(frecuencia)

        resultados.append({
            "id": doc_id,
            "titulo": metadatos.get("titulo", doc_id),
            "facultad": metadatos.get("facultad", ""),
            "facultad_id": metadatos.get("facultad_id", ""),
            "ruta": metadatos.get("ruta", ""),
            "terminos_coincidentes": list(frecuencias.keys()),
            "frecuencias": frecuencias,
        })

    return {
        "consulta_original": consulta,
        "modo": modo,
        "terminos_procesados": terminos,
        "terminos_en_indice": terminos_encontrados,
        "terminos_no_encontrados": terminos_no_encontrados,
        "total_resultados": len(resultados),
        "resultados": resultados,
        "nota": (
            "Recuperación sin ranking: los resultados se muestran por ID. "
            "Puedes activar TF-IDF con --ranking tfidf (opción predeterminada)."
        ),
    }


def cargar_stopwords_para_indice(indice: dict[str, Any], ruta: Path) -> set[str]:
    """Usa las mismas stopwords que se configuraron al crear el índice."""
    usa_stopwords = bool(indice["configuracion"].get("eliminacion_stopwords", True))
    if not usa_stopwords:
        return set()
    return cargar_stopwords(ruta)


def imprimir_resultados(respuesta: dict[str, Any], limite: int | None = None) -> None:
    print(f"\nConsulta: {respuesta['consulta_original']}")
    print(f"Modo: {respuesta['modo']}")
    print("Términos procesados: " + ", ".join(respuesta["terminos_procesados"]))

    if respuesta["terminos_no_encontrados"]:
        print(
            "Términos sin coincidencias en el índice: "
            + ", ".join(respuesta["terminos_no_encontrados"])
        )

    total = respuesta["total_resultados"]
    print(f"Documentos recuperados: {total}")
    if respuesta.get("ranking"):
        print(f"Ordenamiento: {respuesta['ranking']}")

    resultados = respuesta["resultados"]
    mostrar = resultados if limite is None else resultados[:limite]

    if not mostrar:
        print("No se encontraron documentos para esta consulta.")
        return

    print("\n" + "=" * 78)
    for numero, doc in enumerate(mostrar, start=1):
        print(f"{numero}. [{doc['id']}] {doc['titulo']}")
        print(f"   Facultad: {doc['facultad']}")
        if "score_tfidf" in doc:
            print(f"   Similitud TF-IDF: {doc['score_tfidf']:.6f} (posición {doc['posicion_tfidf']})")
        print(f"   Ruta: public/{doc['ruta']}")
        print("   Términos coincidentes: " + ", ".join(doc["terminos_coincidentes"]))
        frecuencias = ", ".join(
            f"{termino}={frecuencia}"
            for termino, frecuencia in doc["frecuencias"].items()
        )
        print(f"   Frecuencias en el documento: {frecuencias}")
        print("-" * 78)

    if limite is not None and total > limite:
        print(f"Se muestran {limite} de {total} resultados. Usa --limite para cambiarlo.")

    if respuesta.get("nota"):
        print("\nNota: " + respuesta["nota"])


def modo_interactivo(
    indice: dict[str, Any], stopwords: set[str], modelo_tfidf: dict[str, Any] | None, ranking_activo: bool
) -> int:
    print("BUAP Search — Consola de consultas")
    print("Escribe una consulta; usa :modo AND, :modo OR, :ranking tfidf, :ranking ninguno o :salir.\n")
    modo = "OR"

    while True:
        try:
            consulta = input(f"[{modo}] Buscar> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSaliendo del buscador.")
            return 0

        if not consulta:
            continue
        if consulta.lower() in {":salir", ":q", "salir", "exit"}:
            print("Saliendo del buscador.")
            return 0
        if consulta.lower().startswith(":ranking"):
            partes = consulta.split()
            if len(partes) == 2 and partes[1].lower() in {"tfidf", "ninguno"}:
                ranking_activo = partes[1].lower() == "tfidf"
                if ranking_activo and modelo_tfidf is None:
                    modelo_tfidf = construir_modelo_tfidf(indice)
                estado = "TF-IDF activado" if ranking_activo else "Ranking desactivado"
                print(estado + ".")
            else:
                print("Uso: :ranking tfidf   o   :ranking ninguno")
            continue
        if consulta.lower().startswith(":modo"):
            partes = consulta.split()
            if len(partes) == 2 and partes[1].upper() in {"AND", "OR"}:
                modo = partes[1].upper()
                print(f"Modo cambiado a {modo}.")
            else:
                print("Uso: :modo AND   o   :modo OR")
            continue

        try:
            respuesta = buscar(consulta, indice, stopwords, modo)
            if ranking_activo:
                respuesta = aplicar_ranking_tfidf(respuesta, indice, modelo_tfidf)
        except (ErrorConsulta, ErrorRanking) as exc:
            print(f"Consulta no válida: {exc}")
            continue
        imprimir_resultados(respuesta)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Busca documentos del corpus BUAP y los ordena con TF-IDF."
    )
    parser.add_argument(
        "consulta", nargs="?", help="Texto que se desea buscar. Sin consulta inicia el modo interactivo."
    )
    parser.add_argument(
        "--modo", choices=["OR", "AND", "or", "and"], default="OR",
        help="OR: al menos un término; AND: todos los términos (predeterminado: OR)."
    )
    parser.add_argument(
        "--ranking", choices=["tfidf", "ninguno"], default="tfidf",
        help="Ordena por TF-IDF (predeterminado) o conserva el orden por ID.",
    )
    parser.add_argument(
        "--indice", type=Path, default=INDICE_DEFAULT,
        help="Ruta del archivo JSON del índice invertido."
    )
    parser.add_argument(
        "--stopwords", type=Path, default=STOPWORDS_DEFAULT,
        help="Ruta del archivo de palabras vacías usado al indexar."
    )
    parser.add_argument(
        "--limite", type=int, default=20,
        help="Máximo de resultados mostrados en consola (0 muestra todos)."
    )
    parser.add_argument(
        "--json", action="store_true", dest="salida_json",
        help="Imprime la respuesta completa como JSON, útil para integraciones posteriores."
    )
    args = parser.parse_args()

    if args.limite < 0:
        parser.error("--limite no puede ser negativo.")

    indice = cargar_indice(args.indice)
    stopwords = cargar_stopwords_para_indice(indice, args.stopwords)

    modelo_tfidf = construir_modelo_tfidf(indice) if args.ranking == "tfidf" else None

    if args.consulta is None:
        if args.salida_json:
            parser.error("--json requiere proporcionar una consulta.")
        return modo_interactivo(indice, stopwords, modelo_tfidf, args.ranking == "tfidf")

    try:
        respuesta = buscar(args.consulta, indice, stopwords, args.modo)
        if args.ranking == "tfidf":
            respuesta = aplicar_ranking_tfidf(respuesta, indice, modelo_tfidf)
    except (ErrorConsulta, ErrorRanking) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if args.salida_json:
        print(json.dumps(respuesta, ensure_ascii=False, indent=2))
    else:
        imprimir_resultados(respuesta, limite=None if args.limite == 0 else args.limite)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
