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


---

# Entrega 2 — Extracción de enlaces y construcción del grafo

Esta segunda entrega incorpora `grafo.py`, que construye el grafo **leyendo las etiquetas `<a href="...">` de los archivos HTML generados**. No utiliza el campo `relacionados` del JSON para crear las aristas; ese campo se utiliza solamente como dato de origen al generar las páginas HTML.

## Qué representa el grafo

- Cada artículo HTML es un nodo (por ejemplo, `adm-01` o `arq-07`).
- Cada enlace desde un artículo A hacia otro artículo B es una arista dirigida `A -> B`.
- Los enlaces hacia páginas de inicio o índices de facultad se comprueban, pero no se agregan como nodos del grafo de artículos.
- Los enlaces externos tampoco se agregan al grafo.

## Construir el grafo

Ejecuta los comandos desde la carpeta raíz del proyecto:

```bash
python3 generar.py
python3 grafo.py
```

`generar.py` debe ejecutarse primero para asegurarse de que los HTML corresponden a los datos JSON actuales. Después, `grafo.py` lee todos los artículos y genera:

```text
indices/
├── grafo.json
├── resumen_grafo.json
└── grafo.dot
```

### Contenido de los resultados

- `grafo.json`: metadatos de los documentos y lista de adyacencia. Es el archivo que consumirá posteriormente PageRank.
- `resumen_grafo.json`: número de nodos y aristas, grados de entrada y salida, nodos sin enlaces y componentes conexas.
- `grafo.dot`: representación del grafo en formato Graphviz, útil para crear una imagen.

## Resultado esperado con los 40 artículos de prueba

La ejecución de esta entrega sobre los artículos de Administración y Arquitectura genera:

| Indicador | Resultado |
|---|---:|
| Nodos (artículos) | 40 |
| Aristas (enlaces entre artículos) | 99 |
| Enlaces a índices/páginas no consideradas nodos | 160 |
| Componentes débilmente conexas | 1 |
| Componentes fuertemente conexas | 1 |
| Nodos sin enlaces salientes | 0 |
| Grado de salida promedio | 2.475 |

El grafo de prueba es fuertemente conexo: desde cualquier artículo se puede llegar a cualquier otro siguiendo la dirección de los enlaces. Esto es una propiedad útil para las pruebas, pero PageRank también puede ejecutarse con grafos que no sean fuertemente conexos, siempre que se manejen los nodos colgantes.

Los valores anteriores corresponden al corpus inicial de 40 artículos; cambiarán cuando se agreguen las demás facultades.

## Visualizar el grafo (opcional)

El archivo `.dot` puede convertirse a PNG usando Graphviz. En Debian:

```bash
sudo apt update
sudo apt install graphviz

dot -Tpng indices/grafo.dot -o indices/grafo.png
```

Después abre `indices/grafo.png` con un visor de imágenes. Graphviz es opcional: ni la extracción ni los JSON requieren instalarlo.

## Comprobaciones que realiza `grafo.py`

1. Verifica que exista el HTML correspondiente a cada artículo registrado en `articulos.json`.
2. Lee los enlaces reales de cada HTML.
3. Comprueba que los enlaces locales apunten a archivos existentes y permanezcan dentro de `public/`.
4. Convierte a aristas únicamente los enlaces cuyo destino sea otro artículo del corpus.
5. Evita aristas duplicadas entre el mismo par de artículos.
6. Calcula componentes débiles y fuertes para comprobar la conectividad.

Si encuentra un enlace local roto o un archivo de artículo faltante, termina con un error y señala el problema para que se corrija antes de continuar.

## Incorporar más facultades

Cuando se añadan los artículos de otra facultad:

1. Añadir sus objetos en `data/articulos.json`, usando los IDs definidos en `data/catalogo.json`.
2. Confirmar que los destinos del campo `relacionados` existan dentro del corpus generado en esa etapa.
3. Ejecutar `python3 generar.py` para actualizar las páginas HTML.
4. Ejecutar `python3 grafo.py` para reconstruir el grafo desde los HTML.

No edites manualmente `indices/grafo.json`: siempre debe regenerarse a partir de las páginas HTML para que el grafo represente los enlaces publicados realmente.
