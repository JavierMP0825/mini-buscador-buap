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

---

# Entrega 3 — Procesamiento de documentos e índice invertido

Esta entrega añade `indexador.py` y `data/stopwords_es.txt`. El indexador procesa el **contenido de los archivos HTML publicados**, no el texto del JSON de artículos. Utiliza `indices/grafo.json` como inventario de documentos y sus metadatos, por lo que primero deben generarse las páginas y el grafo.

## Ejecutar las tres etapas

Desde la carpeta raíz del proyecto:

```bash
python3 generar.py
python3 grafo.py
python3 indexador.py
```

El último comando genera:

```text
indices/
├── indice_invertido.json
└── resumen_indexacion.json
```

## Procesamiento de texto

Para cada artículo HTML, el programa:

1. Extrae el texto del bloque `<article class="article">`.
2. Incluye el título, el párrafo descriptivo y las etiquetas de palabras clave.
3. Excluye navegación, metadatos, botones/enlaces de regreso, títulos auxiliares y la sección de artículos relacionados, para no contaminar el contenido del documento.
4. Convierte el texto a minúsculas.
5. Elimina tildes de vocales (`administración` → `administracion`) y conserva la `ñ` (`año` sigue siendo `año`).
6. Tokeniza el texto en secuencias alfanuméricas.
7. Elimina palabras vacías usando `data/stopwords_es.txt`.

No se aplica stemming ni lematización en esta etapa. Por ejemplo, `construcción` y `construcciones` permanecen como términos distintos. Esto hace que el procesamiento sea sencillo y permite observar claramente cómo se construye el índice.

La lista de palabras vacías es editable. Se pueden agregar o retirar palabras según el comportamiento que se quiera evaluar.

## ¿Cómo se representa el índice invertido?

El archivo `indice_invertido.json` conserva metadatos de los documentos y, para cada término, almacena:

- `frecuencia_documental`: cantidad de documentos que contienen el término (DF).
- `postings`: identificador de cada documento y número de veces que aparece el término en él (TF).

Ejemplo ilustrativo de la estructura:

```json
{
  "indice_invertido": {
    "gestion": {
      "frecuencia_documental": 2,
      "postings": {
        "adm-02": 3,
        "adm-08": 1
      }
    }
  }
}
```

En el ejemplo, `gestion` aparece tres veces en `adm-02` y una vez en `adm-08`; por tanto, su frecuencia documental es 2. Estos valores son solamente ilustrativos: los valores reales se encuentran en el JSON generado.

Esta estructura será la entrada para implementar consultas y TF-IDF. El valor TF se obtiene de cada posting y el valor DF se obtiene de `frecuencia_documental`; el total de documentos `N` aparece en `estadisticas.total_documentos`.

## Opciones

Para crear un índice sin eliminar palabras vacías (útil para comparar el efecto del preprocesamiento):

```bash
python3 indexador.py --sin-stopwords
```

Para volver al índice normal, ejecuta otra vez:

```bash
python3 indexador.py
```

También se puede indicar otra lista de stopwords:

```bash
python3 indexador.py --stopwords data/stopwords_es.txt
```

## Validaciones automáticas

Antes de guardar el índice se comprueba que:

- Todos los artículos registrados en el grafo tengan un HTML legible.
- Todos los artículos produzcan al menos un término indexable.
- Las frecuencias documentales coincidan con la cantidad de postings.
- Todos los postings apunten a documentos existentes.
- Todas las frecuencias TF sean enteros positivos.
- La suma de todas las frecuencias TF coincida con el total de tokens indexados.

## Resultado de referencia con el corpus inicial

Al procesar los 40 artículos de Administración y Arquitectura, el índice de esta entrega produce:

| Indicador | Resultado |
|---|---:|
| Documentos procesados | 40 |
| Tokens antes de filtrar | 2,565 |
| Tokens indexados | 1,640 |
| Tokens descartados | 925 |
| Términos únicos | 783 |
| Promedio de términos por documento | 41 |
| Palabras vacías configuradas | 117 |

Estos valores corresponden a la versión actual del corpus y pueden cambiar si se modifica el contenido de los artículos o la lista de palabras vacías.

**Importante:** el índice debe regenerarse después de editar o agregar artículos. Cuando se incorporen más facultades, ejecuta nuevamente `generar.py`, `grafo.py` e `indexador.py`, en ese orden.

---

# Entrega 4 — Implementación de consultas sencillas

Esta entrega incorpora `buscador.py`, un programa de consola que recibe una consulta, procesa sus términos con las mismas reglas de `indexador.py` y recupera los documentos consultando directamente el índice invertido.

En esta etapa se implementa **recuperación**, no ranking: los resultados se muestran en orden estable por identificador. La clasificación por relevancia TF-IDF y PageRank se incorpora en las siguientes etapas.

## Preparar o actualizar el índice

Si los HTML, el grafo y el índice ya están generados, no necesitas repetir este paso. Si modificaste los artículos, regenera todos los archivos en este orden:

```bash
python3 generar.py
python3 grafo.py
python3 indexador.py
```

## Consultas desde la terminal

Desde la raíz del proyecto, realiza una consulta entre comillas:

```bash
python3 buscador.py "administración"
```

También puedes buscar varios términos:

```bash
python3 buscador.py "diseño arquitectónico"
```

El buscador presenta el identificador, título, facultad, ruta HTML, términos coincidentes y frecuencia de cada término en el documento.

## Modos de búsqueda

El programa incluye dos operadores:

- **OR (predeterminado):** recupera documentos que contienen al menos uno de los términos de la consulta. Equivale a la unión de los conjuntos de postings.
- **AND:** recupera únicamente documentos que contienen todos los términos procesados. Equivale a la intersección de los conjuntos de postings.

Ejemplos:

```bash
# Al menos uno de los términos
python3 buscador.py "construcción sostenible" --modo OR

# Todos los términos deben aparecer en el mismo documento
python3 buscador.py "diseño arquitectónico" --modo AND
```

Si un término no existe en el vocabulario, OR todavía puede devolver documentos que contengan los otros términos. En modo AND, si falta cualquiera de los términos, la consulta no devuelve documentos.

## Modo interactivo

También puedes iniciar el buscador sin argumentos:

```bash
python3 buscador.py
```

Escribe consultas y cambia el operador durante la sesión:

```text
[OR] Buscar> administración
[OR] Buscar> :modo AND
[AND] Buscar> diseño arquitectónico
[AND] Buscar> :modo OR
[OR] Buscar> :salir
```

Comandos disponibles:

- `:modo AND`: exige que todos los términos estén presentes.
- `:modo OR`: acepta documentos que contengan al menos uno de los términos.
- `:salir`: termina el programa.

## Salida JSON y opciones

Para imprimir la respuesta estructurada como JSON:

```bash
python3 buscador.py "diseño arquitectónico" --modo AND --json
```

Esta salida será útil cuando conectemos el motor con Flask y la interfaz web.

Otras opciones:

```bash
# Mostrar hasta 5 resultados
python3 buscador.py "construcción" --limite 5

# Mostrar todos los resultados
python3 buscador.py "construcción" --limite 0

# Usar otro archivo de índice
python3 buscador.py "administración" --indice indices/indice_invertido.json
```

## Procesamiento de las consultas

La consulta utiliza la misma función de tokenización y normalización que los documentos:

1. Convierte las palabras a minúsculas.
2. Elimina las tildes de las vocales y conserva la `ñ`.
3. Separa el texto en tokens.
4. Elimina las palabras vacías si el índice se construyó con stopwords.
5. Elimina términos repetidos en una misma consulta.
6. Busca cada término en `indice_invertido` y recupera los identificadores de sus postings.
7. Combina los conjuntos usando OR o AND.

Por consistencia, el buscador detecta en la configuración del índice si se utilizaron stopwords. Así aplica el mismo preprocesamiento que se utilizó al indexar.

## Pruebas automáticas

El proyecto incluye pruebas unitarias con `unittest`, sin instalar paquetes adicionales:

```bash
python3 -m unittest discover -s pruebas -v
```

Las pruebas comprueban los modos OR y AND, normalización de acentos, términos desconocidos, consultas vacías, consultas formadas únicamente por stopwords, términos repetidos y operadores no válidos.

## Ejemplo de resultado de referencia

Con el corpus de prueba de 40 artículos:

```bash
python3 buscador.py "diseño arquitectónico" --modo AND
```

La consulta recupera el documento `arq-01`, titulado **Fundamentos del diseño arquitectónico**, de la Facultad de Arquitectura. El resultado coincide con ambos términos.

Los resultados se muestran por identificador, no por frecuencia ni relevancia. Aunque se presentan las frecuencias de los términos para inspección, todavía no se calcula una puntuación. Esto permite diferenciar la recuperación básica del ranking textual que se implementará posteriormente.

## Archivos añadidos en esta entrega

```text
buscador.py                 # Motor de consultas OR / AND
pruebas/
└── test_buscador.py        # Pruebas unitarias del motor de consultas
```
