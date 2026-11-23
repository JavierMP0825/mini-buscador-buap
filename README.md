# Mini buscador académico BUAP

Proyecto integrador de la materia **Recuperación de Información**. Implementa un corpus simulado de páginas HTML sobre 25 facultades, extracción de enlaces, un índice invertido, consultas OR/AND, ranking TF-IDF, PageRank y comparación de resultados.

> **Aviso:** los artículos son textos demostrativos creados para este proyecto. No son publicaciones oficiales ni representan contenido institucional de la BUAP.

## Estado actual — Fase 2, entrega 9

- **25 facultades** incluidas en el catálogo.
- **20 artículos por facultad**, para un total de **500 documentos**.
- **500 páginas HTML individuales**, más 25 índices de facultad y la página principal.
- Textos de entre **24 y 64 palabras** en el corpus actual; todos cumplen el límite máximo de 200 palabras.
- **500 nodos y 2,006 aristas** extraídas de los enlaces HTML.
- El grafo tiene una componente fuertemente conexa y no contiene nodos sin enlaces salientes.
- Índice invertido con **500 documentos** y **2,604 términos únicos**.
- PageRank calculado para los 500 artículos y convergencia alcanzada.
- Motor de consulta OR/AND, ranking TF-IDF, PageRank y ranking híbrido.
- Interfaz web interactiva con búsqueda, filtros por facultad, selección de ranking y paginación.
- API REST con Flask: `/api/health`, `/api/facultades` y `/api/search`.
- Integración preparada para Apache mediante proxy inverso hacia Flask.
- **78 pruebas de lógica e interfaz** pasan; 5 pruebas HTTP adicionales se habilitan al instalar Flask.

## Requisitos

- Python 3.9 o posterior.
- No se requieren paquetes externos para generar las páginas, extraer enlaces, indexar o ejecutar los algoritmos de recuperación. Se utiliza la biblioteca estándar de Python.
- La interfaz con búsquedas en vivo requiere Flask y Gunicorn; se instalan con `python3 -m pip install -r requirements.txt` dentro de un entorno virtual.
- Graphviz es opcional y solamente se necesita para convertir `indices/grafo.dot` en una imagen.

## Estructura principal

```text
mini-buscador-buap-entrega-1/
├── data/
│   ├── catalogo.json             # 25 facultades y 500 títulos
│   ├── articulos.json            # Contenido de los 500 documentos
│   └── stopwords_es.txt          # Palabras vacías en español
├── public/
│   ├── index.html                # Buscador web y catálogo de facultades
│   ├── css/estilos.css
│   ├── js/buscador.js            # Cliente JavaScript de la API
│   └── facultades/               # 25 directorios, 20 artículos por facultad
├── indices/
│   ├── grafo.json
│   ├── resumen_grafo.json
│   ├── grafo.dot
│   ├── indice_invertido.json
│   ├── resumen_indexacion.json
│   ├── pagerank.json
│   ├── resumen_pagerank.json
│   ├── resumen_tfidf.json
│   ├── resumen_corpus.json
│   └── comparacion_ejemplo_500.json
├── pruebas/
│   ├── test_buscador.py
│   ├── test_ranking.py
│   ├── test_pagerank.py
│   ├── test_comparador.py
│   ├── test_corpus_500.py
│   ├── test_servicio_busqueda.py
│   ├── test_web_assets.py
│   └── test_api.py
├── completar_corpus.py           # Construye los 460 artículos faltantes
├── resumir_corpus.py              # Genera estadísticas del corpus
├── generar.py                    # Genera los HTML desde los JSON
├── grafo.py                      # Extrae enlaces y genera el grafo
├── indexador.py                  # Procesa HTML y genera índice invertido
├── buscador.py                   # Consultas OR/AND y ranking
├── ranking.py                    # TF-IDF y similitud del coseno
├── pagerank.py                   # PageRank
├── comparador.py                 # Comparación y ranking híbrido
├── servicio_busqueda.py          # Capa de servicio consumida por Flask
├── app.py                        # API HTTP
├── wsgi.py                       # Punto de entrada WSGI
├── requirements.txt              # Flask y Gunicorn
├── deploy/                       # Ejemplo de VirtualHost Apache
└── README.md
```

## Generar o reconstruir el corpus

Desde la carpeta raíz del proyecto:

```bash
python3 completar_corpus.py
python3 generar.py
```

`completar_corpus.py` conserva los 40 artículos iniciales y crea los 460 restantes usando los títulos que ya existen en `data/catalogo.json`. También establece enlaces temáticos entre documentos. El script puede ejecutarse nuevamente sin duplicar artículos.

`generar.py` valida que haya 25 facultades, 20 títulos por facultad, 500 artículos con identificadores únicos, textos de máximo 200 palabras y enlaces relacionados válidos. Después publica los HTML dentro de `public/`.

## Reconstruir grafo, índice y PageRank

Cuando se modifiquen contenidos o enlaces, ejecutar en este orden:

```bash
python3 generar.py
python3 grafo.py
python3 indexador.py
python3 pagerank.py
python3 resumir_corpus.py
```

- `grafo.py` lee las etiquetas de enlace de los archivos HTML. Cada artículo constituye un nodo y los enlaces a otros artículos forman aristas dirigidas. Los enlaces a índices de facultad se validan, pero no se cuentan como nodos del grafo.
- `indexador.py` extrae el título, cuerpo y palabras clave del HTML; normaliza mayúsculas y acentos, tokeniza, elimina stopwords y conserva frecuencias TF/DF en el índice invertido.
- `pagerank.py` calcula la importancia global de cada artículo a partir del grafo y guarda las puntuaciones en `indices/pagerank.json`.

### Diseño de los enlaces

Cada artículo enlaza con documentos de su propia facultad y con artículos de otras áreas afines. Se conserva un ciclo interno entre los 20 artículos de cada facultad y se añaden puentes entre facultades para que todo el corpus sea alcanzable en ambas direcciones. Los enlaces se extraen de los HTML reales: el archivo `grafo.json` no se construye directamente desde la lista de relaciones del JSON.

## Realizar búsquedas

El modo predeterminado es OR y el ranking predeterminado es TF-IDF:

```bash
python3 buscador.py "inteligencia artificial"
python3 buscador.py "derechos humanos" --modo AND
python3 buscador.py "salud bucal" --ranking pagerank
python3 buscador.py "salud bucal" --ranking hibrido
python3 buscador.py "salud bucal" --ranking ninguno
```

Los modos de recuperación son:

- `OR`: recupera documentos que contienen al menos uno de los términos.
- `AND`: recupera documentos que contienen todos los términos.

Los métodos de ordenamiento disponibles son `tfidf`, `pagerank`, `hibrido` y `ninguno`.

Para modificar el peso de TF-IDF en el ranking híbrido:

```bash
python3 buscador.py "salud bucal" --ranking hibrido --peso-tfidf 0.6
```

También existe un modo interactivo:

```bash
python3 buscador.py
```

Comandos interactivos: `:modo OR`, `:modo AND`, `:ranking tfidf`, `:ranking pagerank`, `:ranking hibrido`, `:ranking ninguno` y `:salir`.

## Comparar los algoritmos

```bash
python3 comparador.py "derechos humanos" --modo OR --top 5
python3 comparador.py "biología molecular" --top 10 --peso-tfidf 0.7
```

El comparador muestra las posiciones y puntuaciones de TF-IDF, PageRank y el ranking híbrido, además de coincidencia top-k e índice Jaccard. El resultado se guarda en `indices/comparacion.json`, salvo que se utilice `--sin-guardar`.

El ranking híbrido utiliza:

\[
Score(d)=\alpha\,TFIDF(d)+(1-\alpha)\,PR_{norm}(d)
\]

PageRank se normaliza entre los documentos recuperados por la consulta antes de combinarlo con TF-IDF. Los candidatos siguen dependiendo del modo OR/AND; PageRank no incorpora documentos que no fueron recuperados por la consulta.

## Validar el proyecto

Ejecutar todas las pruebas:

```bash
python3 -m unittest discover -s pruebas -v
```

Las pruebas verifican los algoritmos, la integridad del corpus completo, la capa de servicio de búsqueda, la paginación, los filtros y los recursos web. El archivo `pruebas/test_api.py` contiene cinco pruebas HTTP que se omiten automáticamente cuando Flask no está instalado; después de instalar `requirements.txt` se ejecutan junto con las demás.

## Entregable 9: interfaz web y API Flask

La portada `public/index.html` es generada por `generar.py` e incluye una interfaz web para:

- Enviar consultas al motor de recuperación.
- Elegir recuperación OR o AND.
- Ordenar por TF-IDF, PageRank, ranking híbrido o identificador.
- Ajustar el peso de TF-IDF en el ranking híbrido.
- Filtrar por cualquiera de las 25 facultades.
- Navegar los resultados mediante paginación y abrir el HTML original.

El JavaScript consume la API en el mismo origen, bajo `/api/`. No se requiere configurar CORS cuando Apache sirve el frontend y reenvía esas rutas al backend.

### Endpoints

| Método | Ruta | Función |
|---|---|---|
| GET | `/api/health` | Estado de la API y estadísticas del corpus. |
| GET | `/api/facultades` | Catálogo para el filtro de facultades. |
| GET o POST | `/api/search` | Recupera, ordena, filtra y pagina documentos. |

Ejemplo POST:

```bash
curl -X POST http://127.0.0.1:5000/api/search \
  -H 'Content-Type: application/json' \
  -d '{"q":"inteligencia artificial","modo":"OR","ranking":"tfidf","facultad":"all","pagina":1,"por_pagina":10}'
```

### Instalar dependencias Python

Se recomienda utilizar un entorno virtual dentro del Distrobox Debian:

```bash
cd ~/proyectos/mini-buscador-buap-entrega-1
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

### Iniciar la API

Para el servidor de aplicación detrás de Apache:

```bash
gunicorn --workers 2 --bind 127.0.0.1:5000 app:app
```

La API escucha únicamente en `127.0.0.1:5000`; Apache es el punto de entrada desde otros dispositivos. Para una prueba local de desarrollo también se puede ejecutar `python3 app.py`, que utiliza el mismo host y puerto de forma predeterminada. No actives `--debug` para un despliegue normal.

Comprobar el backend desde otra terminal del mismo Distrobox:

```bash
curl http://127.0.0.1:5000/api/health
```

### Publicar los archivos estáticos en Apache

Esta guía conserva el puerto 8080 que ya se utilizó en el laboratorio. Desde la raíz del proyecto:

```bash
sudo mkdir -p /var/www/html/mini-buscador-buap/public
sudo cp -a public/. /var/www/html/mini-buscador-buap/public/
sudo a2enmod proxy proxy_http
```

Revisa `deploy/apache-mini-buscador.conf`. Si el VirtualHost de ejemplo coincide con tu configuración, cópialo y habilítalo:

```bash
sudo cp deploy/apache-mini-buscador.conf /etc/apache2/sites-available/mini-buscador.conf
sudo a2ensite mini-buscador.conf
sudo apache2ctl configtest
sudo apachectl -k graceful
```

El VirtualHost de ejemplo espera que Apache escuche en `*:8080`. Como tu Distrobox ya tenía Apache en ese puerto, conserva la directiva `Listen 8080` existente y evita duplicarla. Si ya tienes un VirtualHost activo en ese mismo puerto, puedes integrar en él las directivas `DocumentRoot`, `<Directory>`, `ProxyPass` y `ProxyPassReverse` del archivo de ejemplo en lugar de habilitar un segundo sitio. Si el sitio predeterminado captura las solicitudes, deshabilítalo solamente si no lo necesitas para otros proyectos.

Verifica que Apache puede llegar al backend:

```bash
curl http://127.0.0.1:8080/api/health
```

Después abre desde el propio equipo `http://127.0.0.1:8080` y desde otro dispositivo conectado a la misma red `http://IP_DE_BAZZITE:8080`. Para que funcione desde la red, Apache debe escuchar en una interfaz accesible y el firewall del anfitrión debe permitir TCP/8080.

**Importante:** el código y los recursos estáticos de este proyecto viven en la carpeta del proyecto; Apache sirve una copia de `public/` en `/var/www/html/mini-buscador-buap/public`. Cada vez que regeneres o modifiques el frontend, vuelve a copiar los archivos públicos. Flask debe seguir ejecutándose para que las búsquedas funcionen.

## Resultados de referencia del corpus de 500 documentos

| Indicador | Resultado |
|---|---:|
| Artículos HTML | 500 |
| Facultades | 25 |
| Artículos por facultad | 20 |
| Nodos del grafo | 500 |
| Aristas del grafo | 2,006 |
| Componentes fuertemente conexas | 1 |
| Nodos sin enlaces salientes | 0 |
| Tokens indexados | 12,847 |
| Términos únicos | 2,604 |
| Iteraciones PageRank | 86 |
| Suma de PageRank | 1.0 |
| Pruebas de servicio, algoritmos e interfaz | 78 correctas |
| Pruebas HTTP Flask | 5 (requieren instalar Flask) |

Los resultados de los algoritmos pueden cambiar si se modifica el contenido, las palabras clave o los enlaces. `resumir_corpus.py` genera `indices/resumen_corpus.json` con el conteo de artículos, páginas, palabras y estadísticas de los módulos.
