# Mini buscador académico BUAP — Entrega 1

Este repositorio contiene la primera entrega del proyecto integrador de Recuperación de Información.

## Alcance de esta entrega

- Catálogo de **25 facultades**.
- **20 títulos por facultad**: 500 temas en total.
- **40 artículos HTML generados**: 20 de Administración y 20 de Arquitectura.
- Cada artículo generado incluye identificador, texto, palabras clave y enlaces relacionados.
- La muestra inicial tiene un ciclo de enlaces entre los 40 documentos, además de enlaces temáticos, para que el futuro extractor pueda construir un grafo conectado.

Los textos son demostrativos, elaborados para el proyecto. No son publicaciones oficiales de la BUAP.

## Requisitos

- Python 3.9 o posterior.
- No se requieren paquetes externos para generar las páginas: se utiliza únicamente la biblioteca estándar de Python.

## Estructura

```text
mini-buscador-buap-entrega-1/
├── data/
│   ├── catalogo.json       # 25 facultades y 500 títulos
│   └── articulos.json      # Contenido completo de los primeros 40 artículos
├── public/
│   ├── index.html          # Página principal
│   ├── css/estilos.css
│   └── facultades/
│       ├── administracion/
│       └── arquitectura/
├── generar.py              # Valida datos y genera HTML
└── README.md
```

## Generar las páginas

Desde la raíz del proyecto:

```bash
python3 generar.py
```

El programa valida que:

- existan 25 facultades y 20 títulos en cada una;
- los identificadores de los artículos no estén duplicados;
- ningún texto generado supere 200 palabras;
- todos los enlaces relacionados del lote inicial apunten a artículos existentes.

Después crea o actualiza el contenido de `public/`.

## Probar localmente antes de publicarlo en Apache

```bash
python3 -m http.server 8000 --directory public
```

Abre `http://127.0.0.1:8000` en el mismo equipo. Para detener el servidor, usa `Ctrl+C`.

## Abrirlo desde otro dispositivo de la red

Cuando se copie el contenido de `public/` al DocumentRoot que se configure en Apache, se podrá acceder mediante la IP del equipo servidor y el puerto de Apache, por ejemplo:

```text
http://IP_DEL_SERVIDOR:8080
```

La configuración definitiva de Apache, Flask y la API de búsqueda corresponde a una entrega posterior. En esta primera entrega las páginas son estáticas y se pueden navegar sin Flask.

## Cómo agregar las siguientes facultades

1. Añadir los 20 objetos de artículo correspondientes a la facultad en `data/articulos.json`.
2. Respetar los identificadores del catálogo (`facultad-01` a `facultad-20`).
3. Mantener cada texto en 200 palabras o menos.
4. Agregar identificadores existentes en `relacionados`.
5. Ejecutar `python3 generar.py`.

El catálogo completo de títulos ya está definido en `data/catalogo.json`; no es necesario cambiar el generador para incorporar más facultades.
