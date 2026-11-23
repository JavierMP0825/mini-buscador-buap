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

---

# Entrega 5 — Ranking textual con TF-IDF y similitud del coseno

Esta entrega incorpora `ranking.py` e integra el ranking textual con `buscador.py`. El sistema ya no se limita a recuperar documentos: por defecto calcula una puntuación de similitud y ordena los resultados de mayor a menor relevancia textual.

## Ejecutar una búsqueda ordenada por relevancia

Desde la raíz del proyecto:

```bash
python3 buscador.py "construcción sostenible"
python3 buscador.py "diseño arquitectónico" --modo AND
```

El ranking TF-IDF está activado por defecto. Cada resultado muestra su puntuación `Similitud TF-IDF`, entre 0 y 1, y su posición en la clasificación.

Para comparar contra la recuperación sin ranking de la entrega anterior:

```bash
python3 buscador.py "construcción sostenible" --ranking ninguno
```

También se puede generar una respuesta JSON para futuras integraciones:

```bash
python3 buscador.py "construcción sostenible" --json
```

En modo interactivo se puede cambiar de modo y activar/desactivar el ranking:

```text
:modo AND
:modo OR
:ranking tfidf
:ranking ninguno
:salir
```

## Fórmulas utilizadas

El ranking utiliza TF ponderada, IDF suavizada y similitud del coseno:

```text
TF_ponderada(t,d) = 1 + ln(tf(t,d))
IDF(t) = ln((N + 1) / (df(t) + 1)) + 1
TFIDF(t,d) = TF_ponderada(t,d) * IDF(t)
```

Donde:

- `tf(t,d)` es el número de veces que el término aparece en el documento.
- `df(t)` es el número de documentos que contienen el término.
- `N` es el número total de documentos del corpus.

Cada consulta se representa como un vector en el que cada término procesado aparece una vez. Los documentos se representan con los pesos TF-IDF de todo su vocabulario. Se calcula el coseno entre ambos vectores:

```text
coseno(q,d) = producto_punto(q,d) / (norma(q) * norma(d))
```

La norma del documento considera todos sus términos, no solamente las palabras de la consulta. El modelo precalcula los valores IDF y las normas de los documentos al iniciar el buscador, y los reutiliza durante las consultas de la sesión.

## Relación con la recuperación OR/AND

La recuperación y el ranking son dos etapas separadas:

1. `buscador.py` obtiene los documentos candidatos con OR o AND.
2. `ranking.py` calcula la similitud TF-IDF de esos candidatos y los ordena.

Por tanto, OR/AND sigue determinando qué documentos pueden aparecer. TF-IDF determina el orden en que se muestran. Los términos de consulta que no existen en el vocabulario se ignoran para el cálculo vectorial; en modo AND, un término desconocido continúa provocando cero resultados.

## Archivos incorporados

- `ranking.py`: construcción del modelo TF-IDF, cálculo de normas y ordenamiento por coseno.
- `pruebas/test_ranking.py`: pruebas de IDF, normas, puntuaciones, ordenamiento, modos OR/AND y casos sin resultados.

## Ejecutar las pruebas

```bash
python3 -m unittest discover -s pruebas -v
```

La suite conjunta incluye nueve pruebas de recuperación y diez pruebas de ranking (19 en total). No se requieren paquetes externos: el módulo usa bibliotecas estándar de Python.

## Ejemplo de validación con el corpus inicial

Con los 40 artículos de Administración y Arquitectura, la consulta `construcción sostenible` en modo OR recupera ocho documentos. El ranking coloca primero `Arquitectura sostenible` porque es el documento con mayor similitud coseno entre los candidatos de esa consulta. Los valores concretos dependen del contenido y del tamaño del corpus.

El corpus puede ampliarse a las 25 facultades y 500 artículos sin cambiar las fórmulas. Después de añadir los nuevos HTML, hay que volver a ejecutar `generar.py`, `grafo.py` e `indexador.py`; el ranking se recalcula automáticamente al iniciar `buscador.py`.

## Relación con PageRank

TF-IDF mide similitud textual, no importancia de enlaces. Un documento puede ser muy parecido a la consulta y tener pocas conexiones en el grafo. La etapa de PageRank se incorpora en la Entrega 6 y permite comparar ambos criterios.

---

# Entrega 6 — Cálculo de PageRank

Esta entrega incorpora `pagerank.py`, que calcula la importancia global de los artículos a partir de los enlaces dirigidos extraídos de los HTML. El cálculo utiliza `indices/grafo.json`, generado por `grafo.py`, y no depende de una consulta en particular.

## Ejecutar PageRank

Desde la raíz del proyecto, después de haber construido el grafo:

```bash
python3 pagerank.py
```

El programa utiliza estos parámetros predeterminados:

| Parámetro | Valor | Descripción |
|---|---:|---|
| Amortiguamiento (`d`) | 0.85 | Probabilidad de continuar siguiendo enlaces. |
| Iteraciones máximas | 100 | Límite de actualizaciones del vector PageRank. |
| Tolerancia | 1e-10 | Umbral de convergencia usando la suma de diferencias absolutas. |
| Inicialización | 1/N | Todos los artículos comienzan con la misma puntuación. |

Puedes cambiar los parámetros al ejecutar el programa:

```bash
python3 pagerank.py --amortiguamiento 0.85 --iteraciones 200 --tolerancia 1e-12
```

Para mostrar los diez primeros artículos:

```bash
python3 pagerank.py --limite 10
```

Para mostrar todos:

```bash
python3 pagerank.py --limite 0
```

## Fórmula implementada

En cada iteración se calcula:

\[
PR_{k+1}(v)=\frac{1-d}{N}+d\left(\sum_{u\in M(v)}\frac{PR_k(u)}{L(u)}+\frac{D_k}{N}\right)
\]

Donde:

- `PR(v)` es la importancia del nodo destino `v`.
- `N` es el número total de artículos.
- `d` es el factor de amortiguamiento.
- `M(v)` es el conjunto de documentos que enlazan a `v`.
- `L(u)` es el número de enlaces salientes del nodo `u`.
- `D_k` es la suma de PageRank de los nodos colgantes en la iteración `k`.

Un nodo colgante es un artículo sin enlaces salientes. Para evitar que su puntuación desaparezca del sistema, el programa distribuye uniformemente su masa entre todos los nodos. Esta implementación también funciona con grafos desconectados, con nodos colgantes y con un grafo vacío.

El algoritmo termina cuando la suma de las diferencias absolutas entre las puntuaciones de dos iteraciones consecutivas es menor que la tolerancia, o cuando alcanza el máximo de iteraciones.

## Archivos generados

```text
indices/
├── pagerank.json
└── resumen_pagerank.json
```

- `pagerank.json`: contiene los parámetros usados, estadísticas, puntuación de cada artículo y ranking ordenado de mayor a menor.
- `resumen_pagerank.json`: contiene indicadores de convergencia, suma de puntuaciones, nodos colgantes y los diez artículos principales.

La suma de todas las puntuaciones PageRank debe ser aproximadamente 1. La magnitud individual de cada puntuación representa una fracción de la importancia total del grafo; no es un porcentaje de relevancia textual.

## Integración con las consultas

El buscador ahora permite tres formas de presentar los documentos recuperados:

```bash
# Orden textual (predeterminado)
python3 buscador.py "construcción sostenible" --ranking tfidf

# Orden según importancia global de enlaces
python3 buscador.py "construcción sostenible" --ranking pagerank

# Sin ranking, por identificador
python3 buscador.py "construcción sostenible" --ranking ninguno
```

Antes de usar `--ranking pagerank`, ejecuta `python3 pagerank.py` para generar `indices/pagerank.json`.

En los tres casos, OR/AND sigue determinando qué documentos se recuperan. La diferencia es cómo se ordena ese conjunto:

- **TF-IDF:** ordena según la similitud textual con la consulta.
- **PageRank:** ordena según la importancia global del documento en el grafo, independientemente de las palabras buscadas.
- **Ninguno:** mantiene el orden estable por ID.

En el modo interactivo puedes cambiar el método durante la sesión:

```text
:modo AND
:modo OR
:ranking tfidf
:ranking pagerank
:ranking ninguno
:salir
```

La salida PageRank muestra el valor global del artículo y su posición entre los documentos que coincidieron con la consulta. El ranking completo, independiente de las consultas, se obtiene ejecutando `python3 pagerank.py`.

## Resultado de referencia con los 40 artículos

Con el grafo de Administración y Arquitectura de esta entrega, el programa produjo:

| Indicador | Resultado |
|---|---:|
| Nodos | 40 |
| Aristas | 99 |
| Factor de amortiguamiento | 0.85 |
| Iteraciones realizadas | 80 |
| Convergencia | Sí |
| Diferencia final | 8.8991e-11 |
| Suma de puntuaciones | 1.000000000000 |
| Nodos colgantes | 0 |

Los primeros artículos del ranking global son:

| Posición | ID | Artículo | PageRank |
|---:|---|---|---:|
| 1 | arq-18 | Administración de proyectos de construcción | 0.0773071981 |
| 2 | adm-11 | Gestión de proyectos | 0.0682203383 |
| 3 | arq-16 | Paisaje urbano | 0.0505162909 |
| 4 | arq-17 | Costos y presupuestos de obra | 0.0501015013 |
| 5 | arq-12 | Planeación urbana | 0.0414379293 |

Estos valores corresponden al grafo actual de 40 documentos. Cambiarán al incorporar las otras 23 facultades y sus enlaces.

## Pruebas automáticas

La suite completa se ejecuta con:

```bash
python3 -m unittest discover -s pruebas -v
```

Las pruebas específicas de PageRank comprueban ciclos, cadenas, nodos colgantes, grafo vacío, convergencia, validación de parámetros, destinos inválidos, exportación JSON y ordenamiento de resultados recuperados.

En la Entrega 6, la suite conjunta contenía 35 pruebas: 9 de consultas, 10 de TF-IDF y 16 de PageRank e integración.

## Archivos incorporados

- `pagerank.py`: cálculo iterativo, validación, exportación de puntuaciones y clasificación global.
- `pruebas/test_pagerank.py`: pruebas unitarias del algoritmo y su integración con el buscador.
- `indices/pagerank.json`: puntuaciones y ranking calculados con el grafo actual.
- `indices/resumen_pagerank.json`: estadísticas y convergencia.

**Importante:** cuando se agreguen o modifiquen enlaces o artículos, reconstruye el grafo y vuelve a calcular PageRank:

```bash
python3 generar.py
python3 grafo.py
python3 indexador.py
python3 pagerank.py
```


---

# Entrega 7 — Comparación de resultados TF-IDF y PageRank

Esta entrega cierra los siete objetivos principales del motor de recuperación. Añade `comparador.py`, que utiliza el mismo conjunto de documentos recuperados por OR/AND para calcular y comparar tres ordenamientos:

- **TF-IDF:** similitud textual entre la consulta y cada documento.
- **PageRank:** importancia global de cada documento según los enlaces entrantes del grafo.
- **Híbrido:** combinación ponderada de la similitud textual y la importancia estructural.

## Preparación

Antes de comparar, deben existir los siguientes archivos, generados en las entregas anteriores:

```text
indices/indice_invertido.json
indices/pagerank.json
```

Si se modificaron los artículos o sus enlaces, reconstruye todos los índices y PageRank:

```bash
python3 generar.py
python3 grafo.py
python3 indexador.py
python3 pagerank.py
```

## Ejecutar la comparación

Ejemplo con la muestra inicial:

```bash
python3 comparador.py "construcción sostenible"
```

El programa recupera documentos mediante OR y compara los primeros cinco resultados de forma predeterminada. También genera `indices/comparacion.json`.

Para comparar los primeros diez:

```bash
python3 comparador.py "construcción sostenible" --modo OR --top 10
```

Para exigir que los documentos contengan todos los términos:

```bash
python3 comparador.py "diseño arquitectónico" --modo AND --top 5
```

Para cambiar el peso textual del ranking híbrido:

```bash
python3 comparador.py "construcción sostenible" --peso-tfidf 0.6
```

El peso de PageRank siempre es el complemento: si TF-IDF pesa 0.6, PageRank pesa 0.4. El parámetro debe estar entre 0 y 1.

Opciones adicionales:

```bash
# Guardar el reporte JSON en otra ruta
python3 comparador.py "arquitectura sostenible" --salida indices/reporte_arquitectura.json

# Mostrar el reporte completo como JSON en la terminal
python3 comparador.py "arquitectura sostenible" --json

# No crear ningún archivo de salida
python3 comparador.py "arquitectura sostenible" --sin-guardar
```

## Fórmula del ranking híbrido

TF-IDF ya produce una similitud coseno entre 0 y 1. PageRank tiene otra escala (sus puntuaciones globales suman 1), por lo que primero se normaliza mediante min-max entre los documentos recuperados por la consulta:

\[
PR_{norm}(d)=\frac{PR(d)-PR_{min}}{PR_{max}-PR_{min}}
\]

Si todos los candidatos tienen el mismo PageRank, el componente normalizado se establece en cero para todos, ya que PageRank no permite distinguirlos en ese conjunto.

La puntuación híbrida es:

\[
Score_{hibrido}(d)=\alpha\,TFIDF(d)+(1-\alpha)\,PR_{norm}(d)
\]

Con el valor predeterminado \(\alpha=0.7\), el 70 % corresponde a relevancia textual y el 30 % a importancia estructural. Estos pesos son parámetros experimentales; se pueden modificar para observar cómo cambia la clasificación.

## Métricas para comparar resultados

El reporte presenta las posiciones de cada documento en los tres métodos y calcula coincidencias entre los conjuntos de los primeros \(k\) resultados:

\[
Coincidencia@k=\frac{|A_k\cap B_k|}{k_{evaluado}}\times100
\]

También calcula el índice Jaccard:

\[
J(A_k,B_k)=\frac{|A_k\cap B_k|}{|A_k\cup B_k|}
\]

Donde \(A_k\) y \(B_k\) son los conjuntos de documentos que ocupan los primeros puestos en cada método. La coincidencia mide qué documentos aparecen en ambos grupos; la tabla de posiciones permite observar si aparecen en el mismo orden.

Si la consulta recupera menos documentos que el valor de `--top`, el programa muestra una advertencia: al incluir todos los candidatos, los conjuntos pueden coincidir al 100 % aunque el orden sea diferente. Para estudiar la muestra actual de 40 documentos, reduce `--top` a 3 o 5 cuando sea necesario. Con el corpus completo de 500 documentos, puede ser útil evaluar top 10.

## Usar el ranking híbrido desde buscador.py

El buscador también acepta el nuevo método:

```bash
python3 buscador.py "construcción sostenible" --ranking hibrido
```

Para cambiar la proporción:

```bash
python3 buscador.py "construcción sostenible" --ranking hibrido --peso-tfidf 0.6
```

En modo interactivo se puede cambiar con:

```text
:ranking tfidf
:ranking pagerank
:ranking hibrido
:ranking ninguno
:modo AND
:modo OR
:salir
```

## Archivos incorporados

```text
comparador.py
pruebas/test_comparador.py
indices/comparacion.json       # se genera al ejecutar comparador.py
```

## Pruebas automáticas

Ejecuta toda la suite:

```bash
python3 -m unittest discover -s pruebas -v
```

Las pruebas verifican la normalización de PageRank, los pesos extremos (0 y 1), la fórmula híbrida, la conservación de los documentos candidatos, los cálculos de coincidencia, las consultas sin resultados, las advertencias para conjuntos pequeños y la validación de parámetros. La suite final contiene 51 pruebas: 9 de recuperación, 10 de TF-IDF, 16 de PageRank y 16 de comparación.

## Ejemplo obtenido con los 40 artículos iniciales

Consulta: `construcción sostenible`, recuperación OR, top 5, peso TF-IDF 0.7 y PageRank 0.3.

| Documento | Puesto TF-IDF | Puesto PageRank | Puesto híbrido |
|---|---:|---:|---:|
| Administración de proyectos de construcción | 3 | 1 | 1 |
| Gestión de proyectos | 5 | 2 | 2 |
| Arquitectura sostenible | 1 | 6 | 3 |
| Costos y presupuestos de obra | 8 | 3 | 4 |
| Modelado de información de edificios (BIM) | 7 | 4 | 5 |

En esta ejecución, TF-IDF y PageRank comparten 2 de sus primeros 5 documentos (40 %); TF-IDF y el híbrido comparten 3 (60 %); PageRank y el híbrido comparten 4 (80 %). Estos resultados corresponden únicamente a la muestra actual de 40 documentos y pueden cambiar al ampliar el corpus a 500.

## Estado de los siete objetivos académicos

1. Crear o seleccionar un conjunto de documentos HTML: **completado con 40 artículos de prueba y catálogo de 500 títulos**.
2. Extraer enlaces y construir el grafo: **completado**.
3. Procesar documentos e implementar un índice invertido: **completado**.
4. Implementar consultas sencillas: **completado con OR y AND**.
5. Calcular un ranking textual: **completado con TF-IDF y similitud del coseno**.
6. Calcular PageRank: **completado**.
7. Comparar resultados: **completado con comparación top-k, Jaccard y ranking híbrido**.

La expansión de los 40 artículos de prueba a los 500 artículos del catálogo y la integración del motor con la interfaz web/API siguen siendo tareas de desarrollo posteriores; no deben confundirse con la finalización de estos siete algoritmos.
