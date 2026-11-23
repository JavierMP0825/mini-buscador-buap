#!/usr/bin/env python3
"""Completa el corpus demostrativo BUAP hasta 500 artículos.

Conserva los 40 artículos de la primera muestra y crea los 460 restantes
usando los títulos del catálogo. Todo el contenido generado es simulado.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CATALOGO_PATH = ROOT / "data" / "catalogo.json"
ARTICULOS_PATH = ROOT / "data" / "articulos.json"
FUENTE = (
    "Contenido demostrativo elaborado para el proyecto académico; "
    "no es una publicación oficial de la BUAP."
)

# Cada resumen aporta una explicación temática propia para cada uno de los
# 460 artículos que faltaban. El generador agrega una breve contextualización.
RESUMENES = {
"art": [
"Estudia cómo los elementos visuales —punto, línea, plano, forma, textura y espacio— organizan una composición y orientan la lectura de una imagen.",
"Examina las relaciones entre tono, saturación, temperatura y contraste, así como la manera en que las combinaciones cromáticas producen jerarquía y significado.",
"Revisa las manifestaciones artísticas de las civilizaciones antiguas y su relación con la religión, el poder, la vida cotidiana y los materiales disponibles.",
"Analiza la producción visual medieval, sus símbolos religiosos, la función de los talleres y los cambios estilísticos entre los periodos románico y gótico.",
"Aborda las transformaciones artísticas desde el Renacimiento hasta las vanguardias, considerando la perspectiva, el naturalismo, la experimentación formal y los cambios sociales.",
"Estudia prácticas artísticas recientes que cuestionan convenciones, incorporan nuevos medios y dialogan con asuntos como identidad, memoria, territorio y tecnología.",
"Presenta el dibujo como herramienta de observación y representación mediante proporción, volumen, gesto, encuadre, perspectiva y valoración tonal.",
"Describe procedimientos pictóricos como acuarela, óleo, acrílico y técnicas mixtas, atendiendo a soportes, pigmentos, capas, secado y conservación básica.",
"Examina procesos de modelado, talla, ensamblaje y vaciado, además de las propiedades de materiales como barro, madera, metal, piedra y materiales reciclados.",
"Explica la producción de imágenes impresas mediante matrices, entintado y transferencia, distinguiendo procedimientos en relieve, hueco, plano y técnicas experimentales.",
"Analiza la fotografía como práctica artística a partir de luz, exposición, óptica, encuadre, profundidad de campo y decisiones expresivas del autor.",
"Estudia la distribución de formas, pesos, ritmos, contrastes y espacios dentro de una imagen para construir equilibrio, movimiento y jerarquía visual.",
"Explora cómo una obra produce experiencias sensibles e interpretaciones, relacionando forma, contexto, percepción, juicio estético y experiencia del espectador.",
"Describe la selección, investigación, interpretación y organización de obras para construir un discurso expositivo comprensible y contextualizado para distintos públicos.",
"Aborda la planeación de proyectos culturales, la gestión de recursos, la mediación con públicos y la evaluación del impacto de actividades artísticas.",
"Examina intervenciones artísticas en espacios compartidos y su diálogo con comunidad, memoria local, paisaje, participación y apropiación del entorno.",
"Estudia acciones en vivo que utilizan cuerpo, tiempo, espacio y presencia como materiales expresivos, así como el registro y documentación de la obra.",
"Revisa prácticas creativas con herramientas digitales, imagen generada por computadora, medios interactivos y procesos de producción híbrida.",
"Presenta métodos para interpretar obras, argumentar valoraciones y situar la producción artística en su contexto histórico, social y cultural.",
"Analiza factores físicos, químicos y ambientales que influyen en el deterioro de obras, junto con criterios de documentación, prevención y conservación responsable.",
],
"arpa": [
"Estudia la relación entre imagen, sonido, movimiento, encuadre y montaje para construir mensajes audiovisuales comprensibles y expresivos.",
"Analiza la organización de una historia cinematográfica mediante estructura dramática, conflicto, personajes, punto de vista, tiempo y espacio narrativo.",
"Presenta el guion como documento de trabajo que organiza acciones, diálogos, escenas, personajes y descripciones para orientar la realización audiovisual.",
"Examina las decisiones creativas y técnicas de dirección, desde la interpretación de un guion hasta la coordinación de actores, cámara, arte y sonido.",
"Describe la planeación de una obra audiovisual mediante presupuesto, calendario, equipo técnico, permisos, locaciones, logística y control de recursos.",
"Analiza el uso de iluminación, lentes, exposición, composición y movimiento de cámara para construir atmósferas y continuidad visual en una película.",
"Explica cómo la selección y unión de planos construye ritmo, continuidad, espacio y sentido, considerando montaje narrativo y herramientas de edición digital.",
"Estudia la captura, diseño y mezcla de diálogos, ambientes, efectos y música para crear una perspectiva sonora coherente con las imágenes.",
"Revisa la creación de movimiento cuadro por cuadro mediante dibujo, secuencias, temporización, ciclos y principios básicos de animación.",
"Describe la construcción de objetos y personajes tridimensionales mediante modelado, topología, materiales, iluminación y movimiento digital.",
"Analiza silueta, proporción, personalidad, vestuario y expresividad para diseñar personajes que respondan a las necesidades de una historia.",
"Presenta bocetos, referencias y propuestas visuales para definir escenarios, objetos, atmósferas y estilo antes de la producción final.",
"Examina técnicas digitales para integrar imágenes, generar entornos, componer capas y crear efectos que amplían o modifican la toma original.",
"Estudia el registro de acontecimientos reales mediante investigación, entrevistas, observación, archivo y decisiones narrativas que distinguen al documental.",
"Explica la producción de una pieza breve desde la idea y el guion hasta el rodaje, la edición, la mezcla y la exhibición.",
"Analiza obras que experimentan con estructura, duración, soporte, montaje y lenguaje visual para explorar formas alternativas de narración cinematográfica.",
"Aborda la integración de texto, imagen, audio, video y elementos interactivos en productos digitales dirigidos a plataformas y públicos diversos.",
"Describe las tareas de edición, corrección de color, composición, mezcla y exportación que preparan los materiales para su entrega y distribución.",
"Examina ventanas de exhibición, festivales, distribución comercial, plataformas digitales y estrategias para acercar películas a sus públicos.",
"Presenta principios de autoría, licenciamiento, contratos y uso de materiales de terceros para proteger y gestionar obras audiovisuales.",
],
"cap": [
"Analiza sistemas agrícolas que buscan conservar recursos, diversificar cultivos y mantener la productividad mediante prácticas adaptadas al clima y al territorio.",
"Estudia la composición, estructura, textura, origen y propiedades del suelo para interpretar su aptitud agrícola y orientar su manejo.",
"Describe prácticas para reducir erosión, pérdida de materia orgánica y compactación mediante cobertura vegetal, terrazas y manejo de pendientes.",
"Examina la captación, conducción, distribución y aplicación del agua en cultivos, comparando métodos de riego y criterios de eficiencia.",
"Relaciona precipitación, infiltración, escurrimiento, evapotranspiración y disponibilidad hídrica para planear el uso del agua en sistemas productivos.",
"Estudia la interacción entre suelo, agua, vegetación y actividades humanas dentro de una cuenca, así como estrategias de conservación y aprovechamiento.",
"Revisa el establecimiento y manejo de maíz, frijol y otros granos básicos, desde la preparación del terreno hasta la cosecha y almacenamiento.",
"Aborda la producción de hortalizas considerando clima, variedades, almácigos, nutrición, manejo fitosanitario, cosecha y calidad comercial.",
"Analiza el establecimiento de huertos frutales, selección de variedades, poda, polinización, manejo del suelo y conservación de la cosecha.",
"Explica el reconocimiento de enfermedades vegetales, sus agentes causales, síntomas, ciclos de infección y alternativas de manejo integrado.",
"Estudia insectos asociados a cultivos, su identificación, ciclos biológicos, daños y papel como plagas, polinizadores o controladores naturales.",
"Describe la disponibilidad de nutrientes, el diagnóstico de deficiencias y la fertilización equilibrada según cultivo, suelo y etapa de desarrollo.",
"Examina la producción bajo estructuras protegidas, donde se regulan temperatura, humedad, ventilación, radiación y suministro de agua.",
"Analiza el uso de tractores, implementos y equipos para preparar suelo, sembrar, aplicar insumos y cosechar con criterios de seguridad y eficiencia.",
"Presenta componentes del sistema bovino, manejo de alimentación, reproducción, sanidad, alojamiento y registros para evaluar productividad y bienestar.",
"Estudia instalaciones, alimentación, reproducción, bioseguridad y manejo de cerdos en distintas etapas de crecimiento y producción.",
"Describe prácticas de alojamiento, nutrición, sanidad y manejo de aves para producción de carne y huevo, con atención a bioseguridad.",
"Examina la selección y evaluación de características heredables para mejorar poblaciones animales, considerando diversidad genética y objetivos productivos.",
"Analiza condiciones de alojamiento, alimentación, manejo, salud y comportamiento que influyen en el bienestar de animales de producción.",
"Aborda canales de comercialización, costos, calidad, almacenamiento y transporte para conectar unidades productivas con mercados y consumidores.",
],
"bio": [
"Estudia la organización de células procariotas y eucariotas, sus organelos, membranas y procesos que mantienen las funciones vitales.",
"Analiza cómo se almacena, transmite y expresa la información hereditaria, incluyendo genes, cromosomas, variación y patrones de herencia.",
"Examina microorganismos como bacterias y arqueas, su estructura, metabolismo, reproducción y participación en procesos ambientales y biotecnológicos.",
"Describe la diversidad de plantas, sus estructuras, tejidos, ciclos de vida, clasificación y adaptaciones a diferentes ambientes.",
"Estudia la diversidad animal mediante anatomía comparada, clasificación, comportamiento, evolución y relaciones con los ecosistemas.",
"Analiza las relaciones entre organismos y ambiente, incluyendo flujo de energía, ciclos de nutrientes, poblaciones, comunidades y ecosistemas.",
"Explica la variedad de genes, especies y ecosistemas, así como los métodos utilizados para describirla, monitorearla y conservarla.",
"Revisa los mecanismos de cambio en poblaciones a través de selección natural, deriva genética, mutación, flujo génico y especiación.",
"Estudia la estructura y función de moléculas biológicas, la replicación del ADN, la transcripción, la traducción y la regulación génica.",
"Analiza sistemas fisiológicos de animales, como circulación, respiración, digestión, excreción y regulación interna.",
"Describe procesos de nutrición, transporte, fotosíntesis, respiración y respuesta al ambiente en plantas.",
"Examina estrategias para proteger poblaciones y hábitats, evaluar amenazas y diseñar acciones de manejo basadas en evidencia.",
"Estudia características físicas, químicas y biológicas de ríos, lagos, humedales y otros ambientes acuáticos continentales.",
"Analiza la diversidad de insectos, su anatomía, metamorfosis, comportamiento y funciones ecológicas como polinización y descomposición.",
"Describe hongos microscópicos y macroscópicos, sus estructuras, reproducción, clasificación y funciones en los ecosistemas.",
"Estudia organismos parásitos, sus ciclos de vida, hospederos, relaciones biológicas y métodos de identificación en muestras.",
"Examina el uso de células, enzimas y organismos para desarrollar procesos y productos en agricultura, salud, industria y ambiente.",
"Integra herramientas computacionales para almacenar, comparar y analizar secuencias, estructuras moleculares y datos biológicos.",
"Analiza efectos del cambio climático sobre distribución de especies, fenología, conectividad de hábitats y funcionamiento de ecosistemas.",
"Presenta objetivos y herramientas de conservación dentro de áreas protegidas, incluyendo zonificación, monitoreo, participación y evaluación del manejo.",
],
"cc": [
"Estudia variables, tipos, expresiones, estructuras de control y funciones para construir programas claros, verificables y mantenibles.",
"Analiza colecciones como listas, pilas, colas, árboles y grafos, junto con sus operaciones, costos y aplicaciones en programas.",
"Compara métodos de ordenamiento como burbuja, inserción, mezcla y rápido, considerando complejidad, estabilidad y uso de memoria.",
"Describe tablas, claves, relaciones y restricciones para organizar información y realizar consultas mediante lenguaje SQL.",
"Examina la estructura cliente-servidor, interfaces, servicios, persistencia y protocolos que intervienen en aplicaciones web.",
"Estudia procesos, memoria, archivos, planificación y administración de dispositivos que permiten ejecutar programas en una computadora.",
"Analiza protocolos, direccionamiento, enrutamiento y medios de transmisión que permiten intercambiar datos entre equipos.",
"Presenta principios de confidencialidad, integridad y disponibilidad, junto con amenazas, controles y prácticas de protección de sistemas.",
"Estudia técnicas para proteger información mediante cifrado, funciones hash, firmas digitales y gestión de claves.",
"Examina métodos computacionales para reconocer patrones, representar conocimiento y resolver tareas que requieren percepción o razonamiento.",
"Analiza modelos que aprenden a partir de datos, etapas de entrenamiento, validación, evaluación y generalización.",
"Estudia técnicas para tokenizar, representar, clasificar y generar texto mediante modelos lingüísticos y métodos estadísticos.",
"Describe procesos para rastrear, representar, indexar y recuperar documentos relevantes a partir de consultas de usuarios.",
"Examina métodos para descubrir patrones, agrupaciones y asociaciones en grandes conjuntos de datos con fines exploratorios.",
"Integra estadística, programación y visualización para limpiar, explorar, modelar y comunicar información obtenida de datos.",
"Analiza recursos computacionales remotos, virtualización, almacenamiento, redes y servicios que se ofrecen bajo demanda.",
"Estudia sistemas formados por componentes conectados que coordinan tareas, comparten datos y mantienen disponibilidad.",
"Examina objetos físicos conectados, sensores, actuadores y protocolos que permiten recopilar datos e intercambiar información.",
"Describe la integración de programación, sensores, actuadores y control para construir máquinas que perciben y ejecutan acciones.",
"Presenta requisitos, arquitectura, diseño, pruebas, mantenimiento y gestión de cambios durante el ciclo de vida del software.",
],
"com": [
"Presenta modelos que explican la producción, circulación e interpretación de mensajes, desde enfoques interpersonales hasta perspectivas sociales y culturales.",
"Analiza la interacción cara a cara, la escucha, la retroalimentación, los contextos y las señales verbales y no verbales.",
"Estudia los flujos de información, canales formales e informales, clima laboral y coordinación entre integrantes de una organización.",
"Explica la búsqueda, verificación, jerarquización y presentación de hechos de interés público con claridad, contexto y atribución de fuentes.",
"Aborda técnicas de investigación periodística como revisión documental, entrevistas, contraste de fuentes y análisis de datos para asuntos complejos.",
"Describe criterios de precisión, estructura, coherencia, atribución y edición que permiten redactar notas, crónicas y reportajes informativos.",
"Examina el alcance y funcionamiento de prensa, radio, televisión y otros medios masivos, así como sus efectos en la agenda pública.",
"Analiza la comunicación en plataformas digitales, formatos multimedia, participación de usuarios, métricas y circulación de contenidos en línea.",
"Estudia cómo las plataformas sociales influyen en vínculos, identidad, conversación pública, comunidades y circulación de información.",
"Presenta las etapas de producción radiofónica, desde el guion y la conducción hasta la grabación, edición y transmisión de programas.",
"Describe la planeación de contenidos televisivos, lenguaje de cámara, iluminación, sonido, realización en estudio y transmisión.",
"Analiza mensajes, actores, estrategias y medios empleados en la comunicación política, así como su relación con ciudadanía y poder.",
"Examina la creación de mensajes comerciales, públicos objetivo, propuestas de valor, medios, creatividad y evaluación de campañas.",
"Estudia estrategias para construir relaciones de confianza entre organizaciones y públicos mediante información, diálogo y gestión de reputación.",
"Analiza percepciones y actitudes colectivas, métodos de medición, encuestas, sondeos y límites de interpretación de sus resultados.",
"Presenta herramientas para evaluar fuentes, identificar sesgos, reconocer desinformación y comprender cómo se producen los mensajes mediáticos.",
"Aborda responsabilidades, verificación, independencia, privacidad, conflictos de interés y protección de fuentes en el ejercicio periodístico.",
"Explica estrategias para comunicar hallazgos científicos con lenguaje accesible, contexto, visualización y diálogo con públicos no especializados.",
"Estudia la fotografía como registro informativo mediante selección del instante, composición, contexto, pie de foto y criterios de veracidad.",
"Examina cómo se construyen significados mediante palabras, imágenes, contextos, géneros discursivos y relaciones de poder.",
],
"ele": [
"Estudia tensión, corriente, resistencia y potencia en redes eléctricas, así como leyes y métodos para analizar circuitos de corriente directa y alterna.",
"Analiza circuitos con resistencias, capacitores, inductores y dispositivos activos para comprender amplificación, filtrado y acondicionamiento de señales.",
"Describe diodos, transistores y otros semiconductores a partir de sus propiedades eléctricas, curvas características y aplicaciones en dispositivos electrónicos.",
"Examina señales continuas y circuitos con amplificadores operacionales, filtros y osciladores para acondicionar y procesar información analógica.",
"Presenta sistemas que representan información mediante niveles lógicos, compuertas, álgebra booleana, contadores y circuitos secuenciales.",
"Estudia dispositivos programables que ejecutan instrucciones, leen entradas y controlan salidas en sistemas electrónicos de propósito específico.",
"Analiza la integración de hardware y software en dispositivos que realizan funciones concretas con restricciones de tiempo, energía y memoria.",
"Describe la medición de variables físicas y eléctricas, la calibración de instrumentos, la incertidumbre y el acondicionamiento de señales.",
"Examina dispositivos que detectan magnitudes del entorno y actuadores que producen cambios físicos, junto con sus interfaces y calibración.",
"Estudia la representación y transformación de señales mediante análisis temporal y frecuencial, filtrado, muestreo y procesamiento digital.",
"Presenta sistemas para transmitir información por medios guiados e inalámbricos, considerando modulación, ancho de banda, ruido y protocolos.",
"Analiza la radiación electromagnética, parámetros de antenas, patrones de radiación, impedancia y efectos de propagación.",
"Explica modelos de sistemas dinámicos y estrategias de retroalimentación para regular variables como posición, velocidad, temperatura o nivel.",
"Estudia la integración de sensores, motores, electrónica de potencia y control para construir plataformas robóticas capaces de interactuar con su entorno.",
"Describe el diseño de placas de circuito impreso, distribución de componentes, pistas, planos de tierra y criterios de fabricación.",
"Analiza la conversión y regulación de energía eléctrica mediante transformadores, rectificadores, reguladores y fuentes conmutadas.",
"Examina dispositivos y convertidores que controlan la transferencia de energía, variando tensión, corriente y frecuencia para distintas cargas.",
"Presenta la integración de sensores, controladores y actuadores para supervisar máquinas y coordinar operaciones industriales.",
"Estudia la captura, digitalización, almacenamiento y transmisión de mediciones provenientes de sensores y equipos de experimentación.",
"Aborda diagnóstico de fallas, mantenimiento preventivo, documentación técnica y seguridad al intervenir equipos electrónicos.",
],
"cfm": [
"Estudia vectores, matrices, espacios vectoriales, transformaciones lineales y sistemas de ecuaciones como herramientas para modelar problemas científicos.",
"Analiza límites, continuidad y derivadas para describir tasas de cambio, aproximaciones locales y comportamiento de funciones.",
"Examina antiderivadas, integrales definidas y técnicas de integración para calcular áreas, acumulaciones y magnitudes físicas.",
"Presenta ecuaciones que relacionan funciones con sus derivadas y métodos para modelar crecimiento, movimiento, difusión y otros procesos.",
"Estudia propiedades de funciones, sucesiones, series, continuidad y convergencia con razonamiento riguroso y demostraciones matemáticas.",
"Introduce modelos de incertidumbre mediante eventos, variables aleatorias, distribuciones y reglas para calcular probabilidades.",
"Analiza estimación, pruebas de hipótesis, distribuciones muestrales y propiedades de estimadores para extraer conclusiones a partir de datos.",
"Estudia estructuras finitas, lógica, conjuntos, relaciones, combinatoria y grafos, con aplicaciones en computación y ciencias de la información.",
"Examina propiedades de los enteros, divisibilidad, congruencias, números primos y resultados fundamentales de la aritmética.",
"Describe coordenadas, rectas, cónicas, distancias y transformaciones para representar relaciones geométricas mediante ecuaciones.",
"Analiza continuidad, abiertos, cerrados, compacidad y conectividad para estudiar propiedades que se conservan bajo transformaciones continuas.",
"Presenta principios de movimiento, equilibrio, trabajo y energía para describir fenómenos macroscópicos mediante modelos físicos.",
"Estudia el movimiento y las fuerzas que actúan sobre cuerpos, considerando leyes de Newton, conservación y sistemas de referencia.",
"Analiza campos eléctricos y magnéticos, potencial, inducción y ondas electromagnéticas mediante modelos matemáticos y experimentales.",
"Examina calor, temperatura, trabajo, energía interna y entropía para describir transformaciones y equilibrio de sistemas físicos.",
"Introduce estados cuánticos, operadores, medición y evolución de sistemas microscópicos para explicar fenómenos que no describe la física clásica.",
"Estudia la propagación de la luz, reflexión, refracción, interferencia, difracción y formación de imágenes mediante sistemas ópticos.",
"Analiza propiedades eléctricas, magnéticas y térmicas de sólidos a partir de estructura cristalina, bandas de energía y defectos.",
"Describe métodos numéricos para aproximar soluciones de ecuaciones, integración, interpolación y sistemas lineales con análisis de error.",
"Integra ecuaciones, datos y principios científicos para construir modelos que representen sistemas, exploren escenarios y apoyen decisiones.",
],
"cps": [
"Examina conceptos de poder, autoridad, legitimidad, representación y justicia utilizados para interpretar instituciones y conflictos políticos.",
"Estudia la organización del Estado, la distribución de competencias, las formas de gobierno y la relación entre instituciones y ciudadanía.",
"Compara regímenes, sistemas de partidos, reglas electorales y estructuras institucionales para explicar diferencias entre países.",
"Analiza división de poderes, representación, rendición de cuentas, participación y mecanismos de control en los sistemas democráticos.",
"Describe el ciclo de las políticas públicas: definición de problemas, diseño, implementación, seguimiento y evaluación de intervenciones.",
"Examina estructuras, procedimientos y capacidades de las instituciones públicas para prestar servicios y administrar recursos colectivos.",
"Estudia relaciones entre Estados y actores internacionales, cooperación, conflicto, diplomacia y organismos multilaterales.",
"Presenta principios, instrumentos e instituciones para reconocer, proteger y promover derechos fundamentales en distintos contextos.",
"Analiza mecanismos de intervención ciudadana, deliberación, organización comunitaria y vigilancia de decisiones públicas.",
"Examina formas de acción colectiva, identidad, movilización, repertorios de protesta y transformaciones sociales impulsadas por grupos organizados.",
"Estudia la relación entre estructuras sociales, grupos, clases, identidades y procesos de poder en la vida política.",
"Analiza la formación de opiniones, percepciones y actitudes públicas, así como métodos para observar su evolución.",
"Describe reglas para elegir representantes, convertir votos en cargos y organizar la competencia política en distintos sistemas.",
"Examina la organización, ideología, financiamiento y funciones de los partidos en la representación y competencia democrática.",
"Analiza instituciones, prevención, participación comunitaria y políticas orientadas a la convivencia y la protección de la población.",
"Estudia coordinación entre gobierno, sociedad y organizaciones para atender problemas colectivos y construir acuerdos.",
"Presenta herramientas para interpretar acontecimientos políticos recientes mediante contexto histórico, actores, intereses y evidencia verificable.",
"Describe diseños de investigación, muestreo, entrevistas, encuestas y análisis cualitativo o cuantitativo de fenómenos sociales.",
"Examina diferencias en ingreso, oportunidades, recursos y condiciones de vida, considerando factores históricos e institucionales.",
"Analiza estrategias, mensajes, medios y opinión pública durante campañas, debates y procesos de deliberación política.",
],
"quim": [
"Describe protones, neutrones y electrones, niveles de energía y modelos que explican la organización y propiedades de los átomos.",
"Organiza los elementos según número atómico y configuración electrónica, permitiendo interpretar tendencias periódicas y semejanzas químicas.",
"Estudia cómo se unen los átomos mediante enlaces iónicos, covalentes y metálicos, relacionando estructura con propiedades de las sustancias.",
"Presenta relaciones cuantitativas entre reactivos y productos mediante ecuaciones balanceadas, mol, masa molar y reactivo limitante.",
"Analiza mezclas homogéneas, unidades de concentración, solubilidad y factores que afectan la preparación de soluciones.",
"Estudia sistemas reversibles, constantes de equilibrio y perturbaciones que modifican la composición de una mezcla química.",
"Examina la velocidad de reacción, mecanismos, energía de activación y factores como temperatura, concentración y catalizadores.",
"Describe compuestos basados en carbono, estructura molecular, isomería y transformaciones características de las principales familias orgánicas.",
"Analiza grupos como alcoholes, aldehídos, cetonas, ácidos y aminas, relacionando estructura, nomenclatura y reactividad.",
"Estudia compuestos de elementos distintos al carbono, sus estructuras, propiedades, nomenclatura y reacciones representativas.",
"Presenta métodos para separar, identificar y cuantificar componentes de muestras mediante análisis volumétrico, gravimétrico e instrumental.",
"Examina la interacción entre radiación y materia para identificar sustancias y estudiar estructura molecular mediante espectros.",
"Analiza contaminantes, reacciones y ciclos químicos en aire, agua y suelo, así como métodos de monitoreo y mitigación.",
"Estudia biomoléculas, enzimas, rutas metabólicas y transformaciones químicas que permiten el funcionamiento de los seres vivos.",
"Describe la síntesis, estructura, propiedades y usos de macromoléculas, incluidos plásticos, elastómeros y materiales funcionales.",
"Examina procesos electroquímicos y ambientales que degradan metales, junto con factores que aceleran o inhiben la corrosión.",
"Presenta identificación de riesgos, manejo de reactivos, equipo de protección, almacenamiento y respuesta ante incidentes en laboratorio.",
"Analiza operaciones y reacciones químicas a escala industrial, control de calidad, consumo de energía y gestión de residuos.",
"Estudia características del agua y procesos físicos, químicos y biológicos para remover contaminantes y mejorar su calidad.",
"Explora materiales y sistemas a escala nanométrica, métodos de síntesis, caracterización y aplicaciones potenciales en química.",
],
"cont": [
"Presenta conceptos de activo, pasivo, capital, ingresos y gastos para registrar operaciones y comunicar la situación de una entidad.",
"Analiza informes contables que resumen situación financiera, desempeño y movimientos de efectivo para distintos usuarios.",
"Describe la estructura de activos, pasivos y capital en una fecha determinada y su utilidad para evaluar la posición financiera.",
"Examina ingresos, costos y gastos de un periodo para determinar resultados y apoyar el análisis del desempeño operativo.",
"Estudia la identificación, acumulación y asignación de costos a productos, servicios o procesos mediante distintos sistemas.",
"Presenta la planeación cuantitativa de ingresos, gastos, inversiones y recursos para orientar operaciones y evaluar desviaciones.",
"Describe procedimientos para obtener evidencia, evaluar registros y emitir conclusiones sobre información financiera.",
"Analiza políticas y procedimientos para proteger activos, mejorar confiabilidad de registros y reducir riesgos operativos.",
"Estudia criterios de registro y determinación de contribuciones conforme al marco fiscal aplicable a personas y organizaciones.",
"Examina responsabilidades de contribuyentes, declaraciones, plazos, comprobación y documentación de operaciones fiscales.",
"Analiza materiales, mano de obra y costos indirectos que intervienen en la fabricación, así como su control y asignación.",
"Explica cómo la información contable apoya presupuestos, decisiones internas, evaluación de áreas y planeación de operaciones.",
"Estudia decisiones de inversión y financiamiento, estructura de capital, costo de recursos y creación de valor en empresas.",
"Presenta razones financieras, tendencias y comparaciones para interpretar liquidez, solvencia, actividad y rentabilidad.",
"Analiza entradas y salidas de efectivo por operación, inversión y financiamiento para evaluar liquidez y capacidad de pago.",
"Describe normas y criterios de reconocimiento, valuación, presentación y revelación de información financiera.",
"Examina el registro, emisión, almacenamiento y consulta digital de comprobantes y registros contables.",
"Estudia prácticas de dirección, supervisión, transparencia y rendición de cuentas en organizaciones y sociedades.",
"Analiza incertidumbre en inversiones y operaciones mediante identificación, medición, seguimiento y estrategias de respuesta.",
"Presenta principios de integridad, objetividad, confidencialidad e independencia que orientan el trabajo contable.",
],
"cf": [
"Estudia huesos, articulaciones y músculos en relación con movimientos, posturas y adaptaciones que ocurren durante la actividad física.",
"Analiza respuestas cardiovasculares, respiratorias, musculares y metabólicas ante el esfuerzo, así como adaptaciones al entrenamiento.",
"Aplica principios de mecánica al movimiento humano para estudiar fuerzas, equilibrio, velocidad, aceleración y técnica deportiva.",
"Describe métodos para desarrollar capacidades físicas y habilidades técnicas mediante cargas, ejercicios, recuperación y seguimiento.",
"Examina la organización de ciclos, sesiones, objetivos, cargas y evaluaciones para estructurar procesos de entrenamiento.",
"Estudia principios de desarrollo de fuerza muscular y resistencia cardiorrespiratoria mediante métodos progresivos y controlados.",
"Analiza capacidades de reacción, desplazamiento, amplitud articular y coordinación, así como métodos para evaluarlas y entrenarlas.",
"Presenta necesidades de energía y nutrientes relacionadas con práctica física, composición corporal, recuperación y hábitos alimentarios.",
"Examina motivación, concentración, ansiedad, cohesión y autorregulación en contextos de actividad física y competencia.",
"Estudia cómo se adquieren, coordinan y perfeccionan movimientos mediante práctica, retroalimentación, percepción y desarrollo neuromotor.",
"Aborda objetivos pedagógicos, desarrollo motor, inclusión y evaluación de actividades físicas en contextos escolares.",
"Analiza la relación entre movimiento cotidiano, condición física y bienestar, considerando prevención y hábitos saludables.",
"Estudia adaptaciones de actividades, reglas, espacios y materiales para facilitar la participación de personas con distintas capacidades.",
"Describe pruebas y protocolos para estimar resistencia, fuerza, flexibilidad, velocidad y composición corporal.",
"Examina factores de riesgo, calentamiento, técnica, carga y medidas de prevención en la práctica deportiva.",
"Presenta principios generales de recuperación funcional, movilidad, progresión de ejercicios y colaboración con profesionales de salud.",
"Analiza planeación, administración de recursos, organización de eventos y evaluación de programas deportivos.",
"Estudia actividades recreativas y uso del tiempo libre como espacios de convivencia, participación y desarrollo comunitario.",
"Examina planificación, especialización, seguimiento y preparación integral de deportistas en contextos de alto rendimiento.",
"Describe funciones del agua, reposición de líquidos, electrolitos y estrategias de recuperación después del esfuerzo físico.",
],
"der": [
"Estudia conceptos, instituciones y principios que permiten comprender el orden jurídico, las normas y las relaciones reguladas por el derecho.",
"Analiza los procedimientos y criterios mediante los cuales se crean, reconocen e interpretan normas jurídicas dentro de un sistema.",
"Examina la organización del poder público, la supremacía constitucional, los derechos y los mecanismos de control del Estado.",
"Presenta principios e instrumentos nacionales e internacionales para reconocer, proteger y garantizar derechos fundamentales.",
"Estudia personalidad, capacidad, domicilio, estado civil y atributos jurídicos de las personas en el ámbito civil.",
"Analiza acuerdos entre partes, requisitos de validez, obligaciones, interpretación y consecuencias jurídicas de los contratos civiles.",
"Examina las relaciones jurídicas familiares, sus instituciones, derechos, deberes y mecanismos de protección previstos por la ley.",
"Estudia conductas tipificadas, elementos del delito, responsabilidad y consecuencias jurídicas desde una perspectiva normativa.",
"Describe etapas, sujetos, actos y garantías del procedimiento penal, incluyendo investigación, juicio y medios de impugnación.",
"Analiza actos de comercio, comerciantes, títulos de crédito y reglas que regulan las actividades mercantiles.",
"Estudia formas de organización empresarial, constitución, administración, responsabilidad de socios y funcionamiento de sociedades mercantiles.",
"Examina relaciones entre trabajadores y empleadores, condiciones laborales, derechos, obligaciones y mecanismos de solución de controversias.",
"Presenta la organización y actuación de las autoridades administrativas, sus facultades y los medios de defensa de las personas.",
"Analiza principios, obligaciones y procedimientos que regulan la relación entre autoridades fiscales y contribuyentes.",
"Estudia tratados, costumbre, principios y sujetos que intervienen en las relaciones jurídicas entre Estados y organizaciones internacionales.",
"Examina relaciones privadas con elementos extranjeros, jurisdicción, ley aplicable y reconocimiento de decisiones.",
"Describe reglas y etapas para resolver controversias, ofrecer pruebas, ejercer defensas y obtener resoluciones jurisdiccionales.",
"Presenta técnicas para construir argumentos jurídicos, interpretar normas, valorar razones y justificar conclusiones.",
"Analiza negociación, mediación, conciliación y otros mecanismos para atender controversias mediante diálogo y acuerdos.",
"Estudia deberes de honestidad, independencia, confidencialidad y responsabilidad en el ejercicio de las profesiones jurídicas.",
],
"eco": [
"Introduce la asignación de recursos escasos, los incentivos, los mercados y la interacción entre hogares, empresas y sector público.",
"Analiza decisiones de consumidores y empresas en mercados específicos mediante preferencias, costos, producción y formación de precios.",
"Estudia variables agregadas como producción, empleo, precios, consumo e inversión para comprender el funcionamiento de una economía.",
"Examina cómo interactúan compradores y vendedores, cómo se determina un precio y qué efectos producen cambios en las condiciones del mercado.",
"Describe la respuesta de cantidades demandadas u ofrecidas ante variaciones en precios, ingresos y otros factores.",
"Analiza preferencias, restricciones presupuestarias y decisiones de compra para explicar patrones de consumo.",
"Estudia tecnología, costos, productividad y decisiones de producción para comprender la oferta de bienes y servicios.",
"Compara competencia perfecta, monopolio, oligopolio y competencia monopolística, observando sus efectos en precios y bienestar.",
"Analiza aumentos sostenidos de la capacidad productiva mediante capital, trabajo, tecnología, productividad e instituciones.",
"Examina variaciones del nivel general de precios y cambios en el empleo, sus indicadores y posibles causas macroeconómicas.",
"Estudia decisiones de bancos centrales sobre tasas de interés, liquidez y dinero, así como sus canales de transmisión.",
"Analiza ingresos, gasto, deuda e impuestos públicos y sus efectos sobre demanda agregada, distribución y actividad económica.",
"Examina intercambios entre países, especialización, tipo de cambio, aranceles y efectos de la integración económica.",
"Describe operaciones de exportación e importación, logística, documentación, financiamiento y reglas del comercio internacional.",
"Analiza diferencias territoriales en producción, empleo e infraestructura y políticas para impulsar capacidades locales.",
"Estudia la provisión de bienes públicos, externalidades, redistribución y criterios económicos para la intervención gubernamental.",
"Examina empleo, salarios, productividad, negociación y participación laboral en distintos sectores y grupos de población.",
"Integra costos ambientales, recursos naturales y externalidades en el análisis de producción, consumo y políticas públicas.",
"Presenta modelos estadísticos para estimar relaciones entre variables económicas y contrastar hipótesis con datos.",
"Analiza cómo se distribuyen ingresos y oportunidades, así como indicadores y políticas relacionadas con pobreza y desigualdad.",
],
"enf": [
"Presenta bases científicas, éticas y humanísticas del cuidado, así como responsabilidades y funciones del personal de enfermería.",
"Describe la valoración, diagnóstico, planeación, ejecución y evaluación de cuidados individualizados mediante un proceso sistemático.",
"Repasa sistemas y funciones del cuerpo humano necesarios para observar necesidades, respuestas y cambios en el estado de salud.",
"Explica técnicas de medición de temperatura, pulso, respiración y presión arterial, así como registro e interpretación básica.",
"Analiza prácticas de higiene, identificación, comunicación, prevención de riesgos y verificación para reducir incidentes durante la atención.",
"Presenta principios generales sobre medicamentos, vías de administración, cálculos, efectos, interacciones y vigilancia del paciente.",
"Estudia cambios asociados al envejecimiento y necesidades de cuidado, autonomía, movilidad, nutrición y apoyo social de personas mayores.",
"Aborda necesidades de salud en infancia, crecimiento, desarrollo, prevención, vigilancia y acompañamiento de niñas, niños y familias.",
"Examina cuidados durante embarazo, parto, puerperio y primeros momentos de vida, con enfoque de atención respetuosa y segura.",
"Analiza necesidades colectivas, diagnóstico comunitario, participación social y acciones de promoción y prevención en el primer nivel de atención.",
"Presenta estrategias educativas y comunitarias para fortalecer hábitos saludables, autocuidado y decisiones informadas.",
"Estudia higiene de manos, precauciones, limpieza, desinfección, esterilización y vigilancia de infecciones asociadas a la atención.",
"Describe seguimiento y educación para personas con padecimientos prolongados, considerando adherencia, autocuidado y continuidad de atención.",
"Presenta principios de evaluación inicial, activación de servicios de emergencia y medidas básicas de apoyo mientras llega personal especializado.",
"Analiza comunicación terapéutica, observación, acompañamiento y cuidado integral de personas con necesidades de salud mental.",
"Estudia requerimientos nutricionales, valoración de ingesta, dietas indicadas y apoyo durante la alimentación en distintos contextos clínicos.",
"Describe vigilancia, confort, movilidad, heridas y continuidad del cuidado antes y después de procedimientos quirúrgicos.",
"Examina autonomía, confidencialidad, consentimiento, justicia y responsabilidad en decisiones relacionadas con el cuidado de la salud.",
"Presenta preguntas de investigación, diseños, búsqueda bibliográfica, recolección de datos y lectura crítica de evidencia en enfermería.",
"Analiza planeación de personal, calidad, coordinación, indicadores y uso responsable de recursos en servicios de enfermería.",
],
"est": [
"Estudia huesos, músculos, vasos y nervios de la región craneofacial, relacionando su anatomía con funciones y procedimientos odontológicos.",
"Describe tejidos de la cavidad oral, su organización microscópica, desarrollo y cambios asociados con condiciones fisiológicas y patológicas.",
"Analiza microorganismos de la boca, biopelículas, equilibrio microbiano y factores que influyen en la salud de los tejidos orales.",
"Explica la desmineralización de tejidos dentales, factores de riesgo, evolución de lesiones y medidas preventivas basadas en evidencia.",
"Estudia procesos inflamatorios que afectan los tejidos de soporte dental, sus factores asociados y estrategias generales de prevención.",
"Presenta hábitos de higiene, uso de fluoruros, alimentación y educación para conservar dientes y tejidos de la cavidad oral.",
"Examina la historia clínica, exploración, identificación de hallazgos y formulación de hipótesis para orientar la atención odontológica.",
"Describe principios de imagen radiográfica, proyecciones, calidad de imagen, protección radiológica y reconocimiento de estructuras.",
"Analiza composición, propiedades físicas, manipulación y aplicaciones de materiales utilizados en restauración y rehabilitación dental.",
"Estudia procedimientos para tratar lesiones y restaurar forma y función dental mediante materiales y técnicas operatorias.",
"Presenta principios para diagnosticar y tratar alteraciones de la pulpa y tejidos periapicales mediante procedimientos endodónticos.",
"Analiza crecimiento craneofacial, posición dental y relaciones oclusales, así como recursos para planear tratamientos ortodóncicos.",
"Describe opciones para reemplazar dientes y tejidos perdidos mediante prótesis fijas, removibles y otros dispositivos restauradores.",
"Examina fundamentos de procedimientos quirúrgicos orales, evaluación preoperatoria, asepsia y cuidados posteriores.",
"Estudia desarrollo oral infantil, prevención, manejo de conducta y atención adaptada a las necesidades de niñas y niños.",
"Analiza determinantes sociales, vigilancia epidemiológica, prevención y programas orientados a mejorar la salud bucal colectiva.",
"Presenta relaciones entre dientes, músculos y articulaciones durante el cierre mandibular, la masticación y otras funciones.",
"Describe principios de integración de implantes, planificación protésica, evaluación de tejidos y mantenimiento a largo plazo.",
"Examina barreras de protección, esterilización, manejo de instrumental, residuos y prevención de riesgos en el consultorio.",
"Integra diagnóstico, restauración, prótesis y seguimiento para recuperar función, estética y estabilidad del sistema oral.",
],
"fil": [
"Recorre problemas y corrientes filosóficas de distintas épocas, relacionando autores, argumentos y contextos históricos.",
"Estudia conceptos, proposiciones, inferencias y falacias para evaluar la validez y solidez de razonamientos.",
"Analiza preguntas sobre acción, deber, virtud, responsabilidad y criterios para justificar decisiones morales.",
"Examina el origen, alcance, justificación y límites del conocimiento, incluyendo problemas de verdad, evidencia y creencia.",
"Estudia preguntas sobre existencia, identidad, causalidad, tiempo y categorías fundamentales para comprender la realidad.",
"Analiza conceptos de justicia, libertad, autoridad, igualdad y legitimidad en la organización de la vida colectiva.",
"Examina métodos, explicaciones, modelos y criterios de demarcación utilizados para comprender la práctica científica.",
"Presenta obras, géneros y movimientos de distintas tradiciones literarias para interpretar sus formas y contextos.",
"Estudia autores, obras y corrientes de México, considerando contextos históricos, culturales, lingüísticos y sociales.",
"Analiza recursos métricos, ritmo, voz, imagen y figuras retóricas en distintas formas de creación poética.",
"Examina estructura narrativa, personajes, tiempo, espacio, voz y recursos expresivos en cuentos y novelas.",
"Presenta conceptos y enfoques para estudiar géneros, formas, recursos y procesos de producción literaria.",
"Describe métodos de interpretación y valoración de textos mediante análisis formal, histórico, cultural y comparativo.",
"Estudia sistemas lingüísticos, niveles de análisis, variación, adquisición y relación entre lengua, sociedad y cognición.",
"Analiza categorías gramaticales, estructura de oraciones, concordancia, funciones sintácticas y usos del español.",
"Examina cambios fonéticos, léxicos, morfosintácticos y semánticos que han configurado las variedades del español.",
"Estudia la interpretación de textos y acciones considerando contexto, intención, tradición y horizonte del lector.",
"Analiza recursos del discurso, organización de argumentos, figuras y estrategias para informar, persuadir y expresar ideas.",
"Revisa corrientes intelectuales de América Latina y su relación con historia, cultura, identidad, política y pensamiento social.",
"Presenta métodos de investigación documental, formulación de problemas, análisis de fuentes y escritura académica en humanidades.",
],
"ing": [
"Analiza cuerpos en equilibrio y movimiento mediante fuerzas, momentos, diagramas de cuerpo libre y leyes fundamentales de la mecánica.",
"Estudia la respuesta de materiales y elementos estructurales ante cargas, deformaciones, esfuerzos y condiciones de apoyo.",
"Examina tensión, deformación, propiedades mecánicas y criterios para evaluar el comportamiento de componentes sometidos a carga.",
"Presenta principios de energía, trabajo, propiedades termodinámicas y ciclos utilizados para analizar máquinas y sistemas térmicos.",
"Estudia el comportamiento de líquidos y gases en reposo y movimiento, incluyendo presión, continuidad, pérdidas y flujo en conductos.",
"Analiza conducción, convección y radiación para comprender el intercambio térmico en equipos, edificios y procesos industriales.",
"Describe circuitos y dispositivos eléctricos utilizados en medición, control, alimentación y funcionamiento de sistemas de ingeniería.",
"Estudia normas de representación, geometría, vistas, tolerancias y herramientas CAD para comunicar diseños técnicos.",
"Examina procesos de fundición, conformado, maquinado, unión y fabricación aditiva, considerando materiales y parámetros de operación.",
"Analiza estructura, propiedades, selección y comportamiento de metales, cerámicos, polímeros y materiales compuestos.",
"Presenta métodos para diseñar, mejorar y controlar sistemas de producción, calidad, logística y servicios.",
"Estudia modelos matemáticos para asignar recursos, programar operaciones, optimizar rutas y apoyar decisiones complejas.",
"Describe alcance, cronograma, costos, riesgos y coordinación de recursos en proyectos técnicos de ingeniería.",
"Analiza especificaciones, muestreo, medición y herramientas estadísticas para verificar procesos y mejorar productos.",
"Examina identificación de peligros, evaluación de riesgos, medidas preventivas y cultura de seguridad en instalaciones industriales.",
"Presenta estrategias de inspección, lubricación, reparación y mantenimiento predictivo para conservar equipos y reducir paros.",
"Estudia criterios de diseño, mecanismos, transmisión de potencia, materiales y análisis de movimiento en máquinas.",
"Analiza tecnologías solar, eólica, hidráulica y otras fuentes renovables, considerando conversión, almacenamiento e integración.",
"Describe planeación y diseño de obras, infraestructura, servicios y sistemas civiles mediante criterios técnicos y normativos.",
"Examina uso eficiente de recursos, prevención de contaminación, cumplimiento ambiental y evaluación de impactos en proyectos.",
],
"iq": [
"Presenta balances de entradas, salidas y acumulación para cuantificar componentes en equipos y procesos sin reacción química.",
"Analiza la conservación y transformación de energía en corrientes, equipos y procesos industriales mediante balances térmicos.",
"Estudia propiedades de sustancias, equilibrio de fases y relaciones entre presión, temperatura y composición en sistemas químicos.",
"Examina transporte de cantidad de movimiento, energía y materia mediante modelos de flujo y gradientes en medios continuos.",
"Describe operaciones físicas de separación y acondicionamiento como filtración, evaporación, secado, mezclado y transferencia.",
"Analiza difusión y transferencia de componentes entre fases, incluyendo coeficientes, equilibrio y diseño de equipos.",
"Estudia mecanismos de conducción, convección y radiación para calcular requerimientos y dimensionar intercambiadores de calor.",
"Presenta modelos de velocidad de reacción, equilibrio, selección de reactor y variables que afectan la conversión.",
"Examina la selección y conexión de operaciones, balances, equipos y restricciones para definir procesos de transformación.",
"Analiza sensores, controladores, válvulas y estrategias de regulación para mantener variables de proceso en condiciones deseadas.",
"Describe el uso de modelos computacionales para simular balances, equipos, propiedades y condiciones de operación.",
"Estudia la separación de mezclas por diferencias de volatilidad, equilibrio vapor-líquido y configuración de columnas.",
"Examina la separación de componentes mediante contacto entre fases, solubilidad y diferencias de concentración.",
"Analiza transformación de hidrocarburos y materias primas en combustibles y productos químicos, considerando catalizadores y seguridad.",
"Presenta procesos que emplean células, enzimas y microorganismos para producir compuestos de interés industrial.",
"Estudia tratamientos físicos, químicos y biológicos para reducir contaminantes en corrientes residuales antes de su descarga o reúso.",
"Analiza riesgos de reactividad, presión, temperatura y sustancias peligrosas, junto con barreras y sistemas de protección.",
"Examina tecnologías para prevenir emisiones, aprovechar recursos y reducir impactos ambientales en procesos industriales.",
"Describe la relación entre composición, estructura y propiedades de polímeros, además de métodos de procesamiento y caracterización.",
"Integra balances, equipos, restricciones y costos para encontrar condiciones de operación eficientes en instalaciones industriales.",
],
"len": [
"Estudia la aplicación de conocimientos lingüísticos a problemas de enseñanza, traducción, evaluación y comunicación en contextos reales.",
"Analiza procesos cognitivos, sociales y lingüísticos que intervienen cuando una persona aprende una lengua adicional.",
"Presenta enfoques, métodos y recursos para enseñar idiomas considerando objetivos, perfiles de estudiantes y contextos de aprendizaje.",
"Describe la formulación de objetivos, secuencias, actividades y evaluaciones para organizar cursos de lenguas.",
"Examina instrumentos y criterios para valorar comprensión, producción, interacción y mediación en distintas lenguas.",
"Estudia los sonidos del habla, su producción, percepción y organización dentro de sistemas lingüísticos.",
"Analiza la estructura interna de palabras y oraciones, así como reglas y patrones que organizan la expresión lingüística.",
"Examina significados, relaciones entre expresiones, contexto, intención comunicativa e interpretación de enunciados.",
"Presenta principios y procedimientos para trasladar textos entre lenguas, atendiendo a sentido, registro y destinatario.",
"Describe la traducción de textos técnicos, jurídicos, científicos o especializados mediante terminología y documentación temática.",
"Estudia la interpretación oral por segmentos, toma de notas, memoria y reformulación entre lenguas.",
"Analiza la interpretación en tiempo real, escucha activa, anticipación, coordinación y uso de cabinas y equipos.",
"Examina la relación entre prácticas lingüísticas, identidades, tradiciones y contextos socioculturales.",
"Estudia la interacción entre personas de distintos contextos culturales y estrategias para comprender diferencias comunicativas.",
"Presenta recursos para leer, escribir, argumentar y participar en contextos universitarios mediante inglés académico.",
"Describe principios de enseñanza del francés como lengua extranjera, secuenciación didáctica y desarrollo de competencias.",
"Analiza enfoques para enseñar español, gramática, comprensión, producción oral y escrita a distintos públicos.",
"Examina criterios pedagógicos, lingüísticos y visuales para elaborar libros, actividades, audios y recursos de aprendizaje.",
"Presenta plataformas, aplicaciones, corpus y herramientas digitales que apoyan la práctica y evaluación de idiomas.",
"Describe diseños, instrumentos y análisis de datos para estudiar procesos de enseñanza y aprendizaje de lenguas.",
],
"med": [
"Estudia órganos, tejidos y sistemas del cuerpo humano mediante relaciones anatómicas y estructuras relevantes para la práctica médica.",
"Analiza funciones de órganos y sistemas, mecanismos de regulación y respuestas del organismo ante cambios internos y externos.",
"Describe la organización microscópica de tejidos y órganos, relacionando su estructura con funciones y características celulares.",
"Estudia biomoléculas, enzimas y rutas metabólicas que explican procesos químicos de las células y su relación con la salud.",
"Analiza microorganismos asociados con procesos infecciosos, métodos de identificación y principios de prevención y control.",
"Examina mecanismos de defensa innata y adaptativa, células inmunitarias, anticuerpos y respuestas frente a agentes extraños.",
"Presenta principios generales de acción, absorción, distribución, metabolismo y eliminación de medicamentos, así como sus efectos.",
"Estudia alteraciones estructurales y funcionales de células, tejidos y órganos que ayudan a comprender los procesos de enfermedad.",
"Describe la entrevista clínica, exploración física y organización de signos y síntomas para orientar el razonamiento diagnóstico.",
"Analiza acciones para reducir riesgos, detectar factores asociados y promover medidas de protección en individuos y comunidades.",
"Estudia la distribución de eventos de salud en poblaciones, sus determinantes y métodos para investigar brotes y tendencias.",
"Examina condiciones sociales, ambientales y organizativas que influyen en salud colectiva, prevención y acceso a servicios.",
"Presenta principios de valoración y atención integral de personas adultas con problemas de salud de distintos sistemas.",
"Analiza crecimiento, desarrollo, prevención y atención de problemas frecuentes durante la infancia y adolescencia.",
"Estudia procesos fisiológicos y atención de salud durante etapas reproductivas, embarazo, parto y puerperio.",
"Describe principios de evaluación, preparación, procedimientos y cuidados perioperatorios en distintas intervenciones quirúrgicas.",
"Analiza estructura y función del sistema nervioso, exploración neurológica y principales síndromes que afectan su funcionamiento.",
"Estudia estructura y funcionamiento cardiovascular, factores de riesgo y métodos generales de evaluación clínica.",
"Examina técnicas de imagen como radiografía, ultrasonido, tomografía y resonancia para apoyar la observación de estructuras internas.",
"Presenta principios de autonomía, consentimiento, confidencialidad, integridad científica y responsabilidad en la práctica clínica.",
],
"vet": [
"Estudia huesos, músculos, órganos y sistemas de distintas especies domésticas para comprender su estructura y función.",
"Analiza funciones orgánicas, regulación fisiológica y adaptaciones de animales a distintas condiciones ambientales y productivas.",
"Examina bacterias, virus y hongos relevantes en medicina veterinaria, así como métodos de identificación y prevención.",
"Estudia parásitos internos y externos, ciclos biológicos, hospedadores y medidas generales de control en animales.",
"Describe cambios estructurales y funcionales asociados a enfermedades, mediante observación, necropsia y análisis de muestras.",
"Presenta principios generales de uso de medicamentos veterinarios, dosificación, vías de administración, efectos y vigilancia.",
"Analiza vacunación, bioseguridad, vigilancia sanitaria y manejo preventivo para mantener la salud de poblaciones animales.",
"Examina valoración clínica, historia, exploración y atención integral de perros y gatos en diferentes etapas de vida.",
"Estudia manejo, nutrición, reproducción y problemas de salud frecuentes en caballos, considerando su actividad y entorno.",
"Describe sistemas de producción bovina, alimentación, reproducción, manejo sanitario, registros y bienestar del ganado.",
"Analiza alojamiento, nutrición, reproducción, bioseguridad y manejo de cerdos en unidades de producción.",
"Examina sistemas de crianza de aves, alimentación, manejo ambiental, sanidad y control de calidad de productos.",
"Estudia requerimientos nutricionales, formulación de raciones, digestibilidad y evaluación de alimentos para distintas especies.",
"Presenta anatomía y fisiología reproductiva, manejo del ciclo, gestación, parto y técnicas de reproducción asistida.",
"Analiza indicadores físicos y conductuales, alojamiento, manejo y condiciones que favorecen el bienestar animal.",
"Examina enfermedades compartidas entre animales y personas, inocuidad, vigilancia y coordinación desde el enfoque de Una Salud.",
"Estudia agentes, vías de transmisión, reservorios y prevención de enfermedades zoonóticas en poblaciones humanas y animales.",
"Describe principios de evaluación, preparación, asepsia, técnicas quirúrgicas generales y seguimiento posoperatorio en animales.",
"Analiza identificación, conservación, manejo y rehabilitación de fauna silvestre con atención a hábitats y normativa.",
"Estudia higiene, procesamiento, inspección y control de productos de origen animal para proteger la salud pública.",
],
"psi": [
"Presenta conceptos, métodos y principales perspectivas teóricas que explican la conducta, los procesos mentales y la experiencia humana.",
"Analiza cambios físicos, cognitivos, emocionales y sociales a lo largo de la vida, considerando etapas y contextos.",
"Estudia cómo grupos, normas, actitudes, identidad y relaciones influyen en la conducta de las personas.",
"Examina procesos de aprendizaje, desarrollo, evaluación e inclusión en contextos educativos y comunitarios.",
"Presenta modelos de comprensión de la conducta y recursos generales de evaluación e intervención en contextos clínicos.",
"Analiza patrones de pensamiento, emoción y conducta relacionados con malestar psicológico, desde enfoques descriptivos y contextuales.",
"Estudia la relación entre cerebro, cognición, emoción y conducta mediante evaluación de funciones como memoria, lenguaje y atención.",
"Examina percepción, atención, memoria, lenguaje, pensamiento y resolución de problemas como procesos que organizan la experiencia.",
"Analiza relaciones entre estímulos, respuestas, consecuencias y procesos de aprendizaje en distintos contextos.",
"Compara teorías que explican rasgos, diferencias individuales, motivaciones y patrones relativamente estables de comportamiento.",
"Presenta fundamentos de medición psicológica, confiabilidad, validez, escalas y construcción de instrumentos.",
"Describe entrevistas, observación y pruebas estandarizadas como fuentes de información para integrar hipótesis de evaluación.",
"Estudia conducta en organizaciones, clima laboral, liderazgo, selección, capacitación y bienestar en el trabajo.",
"Analiza necesidades colectivas, participación, redes de apoyo y acciones orientadas al bienestar de comunidades.",
"Examina diseño, implementación y seguimiento de estrategias de acompañamiento psicológico según objetivos y contexto.",
"Estudia factores individuales, sociales y ambientales relacionados con bienestar emocional, prevención y acceso a apoyos.",
"Presenta diseños experimentales, variables, control, observación y análisis de datos para estudiar fenómenos psicológicos.",
"Describe métodos cualitativos y cuantitativos, ética, muestreo y análisis para producir conocimiento psicológico.",
"Analiza capacidades, relaciones y condiciones que favorecen el desarrollo personal, social y comunitario.",
"Examina confidencialidad, consentimiento, competencia, límites profesionales y responsabilidad en el trabajo psicológico.",
],
}

CIERRES = {
    "art": "En proyectos de creación, la bitácora y el análisis de referentes ayudan a explicar decisiones formales y conceptuales.",
    "arpa": "La preproducción, el registro técnico y la revisión colectiva permiten organizar cada etapa de realización.",
    "cap": "La observación de parcelas, los registros de producción y las condiciones locales orientan la evaluación de prácticas.",
    "bio": "La observación, el trabajo de laboratorio y el registro de datos permiten contrastar explicaciones sobre los organismos.",
    "cc": "La abstracción, las pruebas y la documentación ayudan a diseñar soluciones computacionales verificables.",
    "com": "El análisis de audiencias, fuentes y contextos permite evaluar cómo circulan y se interpretan los mensajes.",
    "ele": "La medición, el diseño experimental y las pruebas de funcionamiento permiten evaluar el comportamiento del sistema.",
    "cfm": "El razonamiento lógico, la modelación y la comparación con evidencia permiten evaluar los resultados.",
    "cps": "El análisis de casos, documentos y datos permite situar los fenómenos en su contexto institucional y social.",
    "quim": "La observación experimental, el control de variables y el registro de resultados ayudan a interpretar los procesos.",
    "cont": "La documentación y trazabilidad de operaciones permiten sustentar informes y decisiones financieras.",
    "cf": "La observación del movimiento, la evaluación de capacidades y el seguimiento de cargas orientan la práctica física.",
    "der": "La interpretación de normas, hechos y precedentes requiere argumentación clara y revisión del marco jurídico aplicable.",
    "eco": "El uso de indicadores y modelos permite comparar escenarios y explicar cambios en la actividad económica.",
    "enf": "La valoración integral, el registro y la comunicación entre profesionales ayudan a mantener continuidad en el cuidado.",
    "est": "La valoración clínica, el diagnóstico y la documentación del caso orientan la planeación del tratamiento odontológico.",
    "fil": "La lectura crítica y la reconstrucción de argumentos permiten comparar perspectivas y justificar interpretaciones.",
    "ing": "El modelado, la medición y la verificación permiten comprobar que las soluciones respondan a requisitos técnicos.",
    "iq": "Los balances, la experimentación y la simulación ayudan a evaluar la eficiencia y seguridad del proceso.",
    "len": "El análisis de corpus, la práctica comunicativa y la retroalimentación permiten evaluar el aprendizaje de lenguas.",
    "med": "El razonamiento clínico combina antecedentes, exploración y evidencia; este material tiene finalidad educativa.",
    "vet": "La observación clínica, los registros productivos y la bioseguridad son elementos centrales del manejo responsable.",
    "psi": "La evaluación contextual y la interpretación ética de la información son esenciales para el trabajo psicológico.",
}

# Ciclo de facultades con conexiones disciplinares plausibles. Cada facultad
# forma un ciclo interno de 20 documentos; el artículo 20 enlaza también con
# el artículo 01 de la siguiente facultad. Esto garantiza conectividad fuerte.
CICLO_FACULTADES = [
    "adm", "cont", "eco", "cps", "der", "len", "fil", "art", "arpa",
    "com", "cc", "ele", "cfm", "quim", "iq", "ing", "arq", "bio",
    "cap", "vet", "med", "enf", "est", "cf", "psi",
]

VINCULOS_TEMATICOS = {
    "adm": ["cont", "eco", "cps"], "arq": ["ing", "art", "bio"],
    "art": ["arpa", "fil", "arq"], "arpa": ["com", "art", "cc"],
    "cap": ["bio", "vet", "eco"], "bio": ["med", "cap", "quim"],
    "cc": ["ele", "com", "cfm"], "com": ["cps", "arpa", "cc"],
    "ele": ["cc", "ing", "cfm"], "cfm": ["quim", "ing", "ele"],
    "cps": ["der", "com", "eco"], "quim": ["iq", "bio", "med"],
    "cont": ["adm", "eco", "der"], "cf": ["med", "psi", "enf"],
    "der": ["cps", "cont", "len"], "eco": ["cont", "cps", "adm"],
    "enf": ["med", "est", "cf"], "est": ["med", "enf", "bio"],
    "fil": ["len", "art", "cps"], "ing": ["ele", "arq", "iq"],
    "iq": ["quim", "ing", "bio"], "len": ["fil", "com", "der"],
    "med": ["enf", "est", "bio", "vet"], "vet": ["bio", "med", "cap"],
    "psi": ["enf", "cf", "adm"],
}

STOP = set("de la el los las y en un una unos unas para por con del al sobre entre desde como o que se su sus a e u".split())


def palabras(texto: str) -> set[str]:
    return {x for x in re.findall(r"[a-záéíóúüñ]+", texto.lower()) if x not in STOP and len(x) > 2}


def main() -> None:
    catalogo = json.loads(CATALOGO_PATH.read_text(encoding="utf-8"))
    datos = json.loads(ARTICULOS_PATH.read_text(encoding="utf-8"))
    facultades = catalogo["facultades"]
    existente = {a["id"]: a for a in datos["articulos"]}

    # Crear los 460 artículos que aún no estaban redactados.
    nuevos = 0
    for fac in facultades:
        fid = fac["id"]
        if fid in ("adm", "arq"):
            continue
        resumenes = RESUMENES.get(fid)
        if resumenes is None or len(resumenes) != 20:
            raise ValueError(f"Faltan 20 resúmenes para {fid}.")
        for tema, resumen in zip(fac["articulos"], resumenes):
            aid = tema["id"]
            contenido = f"{resumen} {CIERRES[fid]}"
            if aid in existente:
                # Los primeros 40 artículos se conservan; los artículos de la
                # ampliación se regeneran de forma determinista.
                existente[aid]["contenido"] = contenido
                existente[aid]["palabras_clave"] = list(dict.fromkeys(
                    list(existente[aid].get("palabras_clave", []))
                    + list(tema.get("palabras_clave", []))
                ))
                continue
            existente[aid] = {
                "id": aid,
                "facultad_id": fid,
                "titulo": tema["titulo"],
                "contenido": contenido,
                "palabras_clave": list(tema.get("palabras_clave", [])),
                "relacionados": [],
                "fuente": FUENTE,
            }
            nuevos += 1

    # Mantener el orden del catálogo, que será el orden canónico del corpus.
    articulos = []
    por_id = {}
    for fac in facultades:
        for tema in fac["articulos"]:
            aid = tema["id"]
            if aid not in existente:
                raise ValueError(f"No existe contenido para {aid}.")
            a = existente[aid]
            a["facultad_id"] = fac["id"]
            a["titulo"] = tema["titulo"]
            # Conservar palabras clave previas y agregar las del catálogo sin duplicar.
            palabras_clave = list(dict.fromkeys(
                list(a.get("palabras_clave", [])) + list(tema.get("palabras_clave", []))
            ))
            a["palabras_clave"] = palabras_clave
            a["fuente"] = a.get("fuente") or FUENTE
            por_id[aid] = a
            articulos.append(a)

    # Relaciones: siguiente artículo de la misma facultad, dos saltos internos
    # y enlaces a los artículos temáticamente más próximos de facultades afines.
    fac_por_id = {f["id"]: f for f in facultades}
    articulos_por_fac = {
        fid: [tema["id"] for tema in fac["articulos"]]
        for fid, fac in fac_por_id.items()
    }
    firma = {
        a["id"]: palabras(a["titulo"] + " " + a["contenido"] + " " + " ".join(a["palabras_clave"]))
        for a in articulos
    }
    siguiente_fac = {
        CICLO_FACULTADES[i]: CICLO_FACULTADES[(i + 1) % len(CICLO_FACULTADES)]
        for i in range(len(CICLO_FACULTADES))
    }
    # Para cada enlace entre facultades del ciclo global, elegir el par de
    # artículos con mayor solapamiento léxico. Así el puente es temático y no
    # envía automáticamente todos los enlaces al artículo 01.
    puentes_globales = {}
    for fid, otro_fid in siguiente_fac.items():
        pares = [
            (len(firma[origen] & firma[destino]), origen, destino)
            for origen in articulos_por_fac[fid]
            for destino in articulos_por_fac[otro_fid]
        ]
        _, origen, destino = max(pares)
        puentes_globales[origen] = destino

    for fac in facultades:
        fid = fac["id"]
        ids = articulos_por_fac[fid]
        vecinos = VINCULOS_TEMATICOS.get(fid, [])
        for i, aid in enumerate(ids):
            destinos = []
            # Ciclo interno: todos los artículos de la facultad son alcanzables.
            destinos.append(ids[(i + 1) % len(ids)])
            # Segundo enlace interno, para diversificar el grafo.
            destinos.append(ids[(i + 5) % len(ids)])

            # Un enlace a cada una de hasta dos facultades afines, escogiendo
            # el artículo con mayor solapamiento léxico del título y contenido.
            for otro_fid in vecinos[:2]:
                candidatos = articulos_por_fac[otro_fid]
                origen_terms = firma[aid]
                mejor = max(
                    candidatos,
                    key=lambda cid: (len(origen_terms & firma[cid]), cid)
                )
                destinos.append(mejor)

            # Puente léxicamente más cercano al siguiente bloque de facultad.
            # Los ciclos internos permiten que todos los nodos alcancen estos
            # puentes y que, a través del ciclo global, el grafo sea fuertemente conexo.
            if aid in puentes_globales:
                destinos.append(puentes_globales[aid])

            a = por_id[aid]
            a["relacionados"] = list(dict.fromkeys(d for d in destinos if d != aid))

    # Actualizar estados del catálogo para reflejar que ya existe contenido.
    for fac in facultades:
        for tema in fac["articulos"]:
            tema["estado"] = "generado"

    catalogo["proyecto"]["entrega"] = 8
    catalogo["proyecto"]["articulos_html_generados_inicialmente"] = 40
    catalogo["proyecto"]["articulos_html_generados"] = 500
    catalogo["proyecto"]["fase_actual"] = "Fase 2: corpus completo"
    catalogo["proyecto"]["descripcion"] = (
        "Corpus demostrativo completo de 500 documentos HTML relacionados "
        "con 25 facultades para una práctica de Recuperación de Información."
    )

    datos["articulos"] = articulos
    CATALOGO_PATH.write_text(json.dumps(catalogo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ARTICULOS_PATH.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Resumen de control previo a generar HTML.
    total = len(articulos)
    max_palabras = max(len(re.findall(r"\b\w+\b", a["contenido"], flags=re.UNICODE)) for a in articulos)
    min_palabras = min(len(re.findall(r"\b\w+\b", a["contenido"], flags=re.UNICODE)) for a in articulos)
    print(f"Artículos nuevos creados: {nuevos}")
    print(f"Total de artículos: {total}")
    print(f"Facultades: {len(facultades)}")
    print(f"Artículos por facultad: {min(len(x) for x in articulos_por_fac.values())}–{max(len(x) for x in articulos_por_fac.values())}")
    print(f"Palabras por contenido: mínimo {min_palabras}; máximo {max_palabras}")


if __name__ == "__main__":
    main()
