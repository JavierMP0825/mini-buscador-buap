#!/usr/bin/env python3
"""API HTTP del mini buscador académico BUAP.

Producción local detrás de Apache:
    gunicorn --workers 2 --bind 127.0.0.1:5000 app:app

Prueba de desarrollo:
    python3 app.py
"""
from __future__ import annotations

import argparse
from typing import Any

from flask import Flask, jsonify, request

from buscador import ErrorConsulta
from comparador import ErrorComparacion
from pagerank import ErrorPageRank
from ranking import ErrorRanking
from servicio_busqueda import ErrorSolicitud, ServicioBusqueda


def create_app(servicio: ServicioBusqueda | None = None) -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024  # Las consultas solo requieren un JSON pequeño.
    motor = servicio or ServicioBusqueda()
    app.config["BUSCADOR_SERVICE"] = motor

    @app.get("/api/health")
    def health():
        return jsonify(motor.health())

    @app.get("/api/facultades")
    def facultades():
        return jsonify({"facultades": motor.listar_facultades()})

    @app.route("/api/search", methods=["GET", "POST"])
    def search():
        if request.method == "GET":
            parametros: dict[str, Any] = request.args.to_dict()
        else:
            datos = request.get_json(silent=True)
            if not isinstance(datos, dict):
                return jsonify({"error": "El cuerpo debe ser JSON válido y contener un objeto."}), 400
            parametros = datos
        try:
            resultado = motor.buscar(parametros)
        except (ErrorSolicitud, ErrorConsulta) as exc:
            return jsonify({"error": str(exc)}), 400
        except (ErrorRanking, ErrorPageRank, ErrorComparacion, RuntimeError) as exc:
            app.logger.exception("Error interno al ejecutar la búsqueda: %s", exc)
            return jsonify({"error": "El motor no pudo completar la búsqueda. Revise los índices y los registros del servidor."}), 500
        return jsonify(resultado)

    @app.errorhandler(413)
    def request_too_large(_error):
        return jsonify({"error": "La solicitud supera el tamaño permitido."}), 413

    @app.get("/api/")
    def api_index():
        return jsonify({
            "nombre": "BUAP Search API",
            "endpoints": ["/api/health", "/api/facultades", "/api/search"],
        })

    return app


app = create_app()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="API local para BUAP Search")
    parser.add_argument("--host", default="127.0.0.1", help="Interfaz de escucha (predeterminada: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="Puerto de Flask (predeterminado: 5000)")
    parser.add_argument("--debug", action="store_true", help="Activa depuración (solo desarrollo local)")
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, debug=args.debug)
