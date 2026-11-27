"""Genera el reporte final en PDF a partir de los resultados exportados por los notebooks.

Uso (desde la raíz del proyecto, con el entorno activado):
    python reporte/generar_reporte.py

Requiere que los notebooks notebooks/hojas.ipynb y notebooks/cancer_mama.ipynb se hayan
ejecutado completos, ya que su última celda guarda las tablas y figuras en resultados/.
Todas las cifras del reporte se leen de esos archivos; ninguna se escribe a mano.
"""
import json
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

RAIZ = Path(__file__).resolve().parent.parent
RES_HOJAS = RAIZ / "resultados" / "hojas"
RES_CANCER = RAIZ / "resultados" / "cancer"
SALIDA = RAIZ / "reporte" / "reporte_final.pdf"

ANCHO_UTIL = letter[0] - 4.4 * cm


# ----------------------------------------------------------------------------
# Tipografía y estilos
# ----------------------------------------------------------------------------
def registrar_fuentes():
    """Usa Arial si está disponible (mejor soporte de acentos y símbolos); si no, Helvetica."""
    fuentes = Path("C:/Windows/Fonts")
    archivos = {
        "Texto": "arial.ttf",
        "Texto-Negrita": "arialbd.ttf",
        "Texto-Cursiva": "ariali.ttf",
        "Texto-NegritaCursiva": "arialbi.ttf",
    }
    if all((fuentes / a).exists() for a in archivos.values()):
        for nombre, archivo in archivos.items():
            pdfmetrics.registerFont(TTFont(nombre, str(fuentes / archivo)))
        pdfmetrics.registerFontFamily(
            "Texto", normal="Texto", bold="Texto-Negrita",
            italic="Texto-Cursiva", boldItalic="Texto-NegritaCursiva",
        )
        return "Texto", "Texto-Negrita", "Texto-Cursiva"
    return "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"


NORMAL, NEGRITA, CURSIVA = registrar_fuentes()
base = getSampleStyleSheet()

ESTILOS = {
    "titulo": ParagraphStyle("titulo", parent=base["Title"], fontName=NEGRITA, fontSize=22, leading=28,
                             alignment=TA_CENTER, spaceAfter=10),
    "subtitulo": ParagraphStyle("subtitulo", parent=base["Normal"], fontName=NORMAL, fontSize=13, leading=18,
                                alignment=TA_CENTER, textColor=colors.HexColor("#333333")),
    "portada": ParagraphStyle("portada", parent=base["Normal"], fontName=NORMAL, fontSize=11.5, leading=18,
                              alignment=TA_CENTER),
    "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName=NEGRITA, fontSize=15, leading=19,
                         spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#1F3A5F"), keepWithNext=1),
    "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName=NEGRITA, fontSize=12, leading=15,
                         spaceBefore=8, spaceAfter=4, textColor=colors.HexColor("#1F3A5F"), keepWithNext=1),
    "cuerpo": ParagraphStyle("cuerpo", parent=base["Normal"], fontName=NORMAL, fontSize=10, leading=14,
                             alignment=TA_JUSTIFY, spaceAfter=6),
    "vineta": ParagraphStyle("vineta", parent=base["Normal"], fontName=NORMAL, fontSize=10, leading=14,
                             alignment=TA_JUSTIFY, leftIndent=14, bulletIndent=4, spaceAfter=3),
    "pie": ParagraphStyle("pie", parent=base["Normal"], fontName=CURSIVA, fontSize=8.5, leading=11,
                          alignment=TA_CENTER, textColor=colors.HexColor("#444444"), spaceAfter=10),
    "celda": ParagraphStyle("celda", parent=base["Normal"], fontName=NORMAL, fontSize=8, leading=10),
    "celda_enc": ParagraphStyle("celda_enc", parent=base["Normal"], fontName=NEGRITA, fontSize=8, leading=10,
                                textColor=colors.white),
}


# ----------------------------------------------------------------------------
# Utilidades de formato
# ----------------------------------------------------------------------------
def p(texto, estilo="cuerpo"):
    return Paragraph(texto, ESTILOS[estilo])


def vinetas(elementos):
    return [Paragraph(e, ESTILOS["vineta"], bulletText="•") for e in elementos]


def f4(valor):
    return f"{valor:.4f}"


def pm(media, desv):
    return f"{media:.4f} ± {desv:.4f}"


def pct(valor):
    return f"{valor:.2f} %"


class Contador:
    def __init__(self):
        self.figura = 0
        self.tabla = 0

    def fig(self):
        self.figura += 1
        return self.figura

    def tab(self):
        self.tabla += 1
        return self.tabla


NUM = Contador()


def siguiente_tabla(desplazamiento=0):
    return NUM.tabla + 1 + desplazamiento


def ultima_figura():
    return NUM.figura


def figura(ruta, pie, ancho=ANCHO_UTIL):
    lector = ImageReader(str(ruta))
    ancho_px, alto_px = lector.getSize()
    alto = ancho * alto_px / ancho_px
    if alto > 19 * cm:
        alto = 19 * cm
        ancho = alto * ancho_px / alto_px
    return KeepTogether([
        Image(str(ruta), width=ancho, height=alto),
        p(f"<b>Figura {NUM.fig()}.</b> {pie}", "pie"),
    ])


def tabla(encabezado, filas, anchos, titulo):
    datos = [[Paragraph(str(c), ESTILOS["celda_enc"]) for c in encabezado]]
    datos += [[Paragraph(str(c), ESTILOS["celda"]) for c in fila] for fila in filas]
    t = Table(datos, colWidths=anchos, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3A5F")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF2F7")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B0B8C4")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return KeepTogether([p(f"<b>Tabla {NUM.tab()}.</b> {titulo}", "pie"), t, Spacer(1, 8)])


def pie_de_pagina(canvas, doc):
    canvas.saveState()
    canvas.setFont(NORMAL, 8.5)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(2.2 * cm, 1.2 * cm, "Proyecto Final — Razonamiento con IA")
    canvas.drawRightString(letter[0] - 2.2 * cm, 1.2 * cm, f"Página {doc.page}")
    canvas.restoreState()


def lista_texto(elementos):
    elementos = list(elementos)
    if len(elementos) == 1:
        return elementos[0]
    return ", ".join(elementos[:-1]) + " y " + elementos[-1]


# ----------------------------------------------------------------------------
# Carga de resultados
# ----------------------------------------------------------------------------
def cargar():
    faltantes = [r for r in [RES_HOJAS / "resumen.json", RES_CANCER / "resumen.json"] if not r.exists()]
    if faltantes:
        raise FileNotFoundError(
            "No se encontraron los resultados exportados: "
            + ", ".join(str(f) for f in faltantes)
            + ". Ejecuta primero los dos notebooks completos."
        )

    h = {
        "resumen": json.loads((RES_HOJAS / "resumen.json").read_text(encoding="utf-8")),
        "distribucion": pd.read_csv(RES_HOJAS / "distribucion.csv", index_col=0),
        "estadisticas": pd.read_csv(RES_HOJAS / "estadisticas_por_clase.csv", header=[0, 1], index_col=0),
        "relacion": pd.read_csv(RES_HOJAS / "relacion_alto_ancho.csv", index_col=0),
        "metricas": pd.read_csv(RES_HOJAS / "metricas_supervisados.csv"),
        "configuraciones": pd.read_csv(RES_HOJAS / "configuraciones_finales.csv"),
        "errores": pd.read_csv(RES_HOJAS / "hojas_mal_clasificadas.csv", keep_default_na=False),
        "clustering": pd.read_csv(RES_HOJAS / "clustering.csv"),
    }
    c = {
        "resumen": json.loads((RES_CANCER / "resumen.json").read_text(encoding="utf-8")),
        "distribucion": pd.read_csv(RES_CANCER / "distribucion.csv", index_col=0),
        "separacion": pd.read_csv(RES_CANCER / "separacion_caracteristicas.csv", index_col=0),
        "metricas": pd.read_csv(RES_CANCER / "metricas_supervisados.csv"),
        "clustering": pd.read_csv(RES_CANCER / "clustering.csv"),
    }
    return h, c


# ----------------------------------------------------------------------------
# Secciones
# ----------------------------------------------------------------------------
def portada():
    return [
        Spacer(1, 5 * cm),
        p("Proyecto Final", "titulo"),
        p("Razonamiento con IA", "subtitulo"),
        Spacer(1, 0.6 * cm),
        p("Aprendizaje supervisado y no supervisado aplicado a un corpus de hojas "
          "y a la base de datos de cáncer de mama", "subtitulo"),
        Spacer(1, 3 * cm),
        p("<b>Integrantes del equipo:</b> [PENDIENTE]", "portada"),
        p("<b>Profesor:</b> [PENDIENTE]", "portada"),
        p("<b>Institución:</b> [PENDIENTE]", "portada"),
        p("<b>Fecha de entrega:</b> [PENDIENTE]", "portada"),
        PageBreak(),
    ]


def introduccion(h, c):
    return [
        p("1. Introducción", "h1"),
        p("El objetivo de este proyecto es aplicar de forma sistemática los algoritmos de aprendizaje "
          "supervisado y no supervisado vistos en el curso sobre dos conjuntos de datos: el corpus de hojas "
          "construido por el equipo y la base de datos de cáncer de mama (Breast Cancer Wisconsin, "
          "Diagnostic) disponible en scikit-learn. Se aplicaron dos métodos no supervisados (clustering "
          "jerárquico y K-means) y seis clasificadores (k-NN, Naive Bayes, SVM, árbol de decisión, Random "
          "Forest y Multilayer Perceptron)."),
        p("Para cada base se describen los datos, se buscan y justifican los hiperparámetros, se evalúan los "
          "modelos con validación cruzada estratificada anidada y se presentan las fronteras de decisión y los "
          "agrupamientos. El análisis completo, con el código, las tablas por fold y las interpretaciones de "
          "cada modelo, se encuentra en los notebooks <i>notebooks/hojas.ipynb</i> y "
          "<i>notebooks/cancer_mama.ipynb</i>; este reporte resume sus resultados principales."),
    ]


def datos_hojas(h):
    r = h["resumen"]
    dist = h["distribucion"]
    est = h["estadisticas"]
    rel = h["relacion"]
    clases = r["clases"]

    filas_dist = [[clase, int(dist.loc[clase, "Número de hojas"]), pct(dist.loc[clase, "Porcentaje (%)"])]
                  for clase in clases]

    filas_est = []
    for clase in clases:
        fila = [clase]
        for var in ["Alto (cm)", "Ancho (cm)"]:
            fila.append(f"{est.loc[clase, (var, 'Media')]:.2f} ± {est.loc[clase, (var, 'Desv. estándar')]:.2f}")
            fila.append(f"{est.loc[clase, (var, 'Mínimo')]:.1f} – {est.loc[clase, (var, 'Máximo')]:.1f}")
        fila.append(f"{rel.loc[clase, 'Correlación Alto-Ancho']:.2f}")
        filas_est.append(fila)

    ancho_max_ocozote = est.loc["Ocozote", ("Ancho (cm)", "Mínimo")]
    ancho_max_otras = max(est.loc["Limón", ("Ancho (cm)", "Máximo")], est.loc["Fresno", ("Ancho (cm)", "Máximo")])
    alto_max_limon = est.loc["Limón", ("Alto (cm)", "Máximo")]
    alto_min_fresno = est.loc["Fresno", ("Alto (cm)", "Mínimo")]

    texto_alto = (
        f"Limón llega hasta {alto_max_limon:.1f} cm y Fresno comienza en {alto_min_fresno:.1f} cm, por lo que ambas "
        f"clases solo coinciden en ese valor del alto"
        if alto_max_limon == alto_min_fresno else
        f"Limón llega hasta {alto_max_limon:.1f} cm y Fresno comienza en {alto_min_fresno:.1f} cm, por lo que ambas "
        f"clases quedan muy próximas en el alto"
    )

    contenido = [
        p("2. Conjuntos de datos", "h1"),
        p("2.1 Corpus de hojas", "h2"),
        p("El corpus fue construido por el equipo durante el curso. Las hojas fueron recolectadas a mano por un "
          "integrante del equipo a inicios de octubre, de tres tipos de árbol: <b>Limón</b>, <b>Ocozote</b> y "
          "<b>Fresno</b>. Cada hoja se fotografió junto a una regla, que sirvió como escala; la mayoría de las "
          "medidas se obtuvo a partir de las fotografías con ayuda de herramientas de inteligencia artificial "
          "(Gemini y ChatGPT), y unas pocas se midieron directamente con la regla. La etiqueta de cada hoja es "
          "el árbol del que se recolectó."),
        p(f"Cada hoja se representa con dos características numéricas: el <b>alto</b>, medido desde el inicio "
          f"de la hoja sin contar el pecíolo, y el <b>ancho</b>, ambos en centímetros y con un decimal. El "
          f"corpus contiene {r['n_muestras']} hojas en {len(clases)} clases balanceadas, sin valores faltantes "
          f"(Tablas {siguiente_tabla()} y {siguiente_tabla(1)}). La columna <i>ID hoja</i> es solo un identificador y no se usa como característica."),
        tabla(["Árbol", "Número de hojas", "Porcentaje"], filas_dist, [5 * cm, 4 * cm, 4 * cm],
              "Distribución de las hojas por clase."),
        tabla(["Árbol", "Alto: media ± desv.", "Alto: rango", "Ancho: media ± desv.", "Ancho: rango",
               "Correlación alto-ancho"],
              filas_est, [2.4 * cm, 3 * cm, 2.6 * cm, 3 * cm, 2.6 * cm, 3.6 * cm],
              "Estadísticas descriptivas por clase (cm)."),
        figura(RES_HOJAS / "figuras" / "dispersograma.png",
               "Dispersograma del corpus de hojas en el plano original Alto × Ancho.", ancho=12 * cm),
    ]
    contenido += [
        p(f"El dispersograma (Figura {ultima_figura()}) muestra que <b>Ocozote</b> se separa de las otras clases por el ancho: "
          f"su hoja más angosta mide {ancho_max_ocozote:.1f} cm, mientras que ninguna hoja de Limón o Fresno "
          f"supera {ancho_max_otras:.1f} cm. <b>Limón</b> y <b>Fresno</b> se traslapan en el ancho y se "
          f"distinguen por el alto: {texto_alto}. Dentro de cada clase el "
          f"alto y el ancho están fuertemente correlacionados, y Ocozote es la clase más dispersa. Como las dos "
          f"variables tienen escalas distintas, los métodos basados en distancias se aplicaron sobre las "
          f"variables estandarizadas."),
    ]
    return contenido


def datos_cancer(c):
    r = c["resumen"]
    dist = c["distribucion"]
    sep = c["separacion"]
    columna_sep = [col for col in sep.columns if col.startswith("Separación")][0]

    filas_dist = [[clase, int(dist.loc[clase, "Número de muestras"]), pct(dist.loc[clase, "Porcentaje (%)"])]
                  for clase in r["clases"]]
    filas_sep = [[nombre, f"{fila['Media maligno']:.3f}", f"{fila['Media benigno']:.3f}", f"{fila[columna_sep]:.3f}"]
                 for nombre, fila in sep.head(5).iterrows()]

    return [
        p("2.2 Base de datos de cáncer de mama", "h2"),
        p("Se utilizó el conjunto <b>Breast Cancer Wisconsin (Diagnostic)</b>, cargado con "
          "<i>load_breast_cancer()</i> de scikit-learn. Fue creado por W. H. Wolberg, W. N. Street y O. L. "
          "Mangasarian, de la Universidad de Wisconsin. Cada muestra corresponde a una imagen digitalizada de una "
          "aspiración con aguja fina de una masa en la mama, y sus características describen los núcleos "
          "celulares de la imagen. Las 10 medidas (radio, textura, perímetro, área, suavidad, compacidad, "
          "concavidad, puntos cóncavos, simetría y dimensión fractal) se resumen con su media, su error estándar y "
          f"su valor peor, para un total de {r['n_caracteristicas']} características. La etiqueta indica si el "
          "tumor es maligno (clase 0) o benigno (clase 1)."),
        tabla(["Diagnóstico", "Número de muestras", "Porcentaje"], filas_dist, [5 * cm, 4 * cm, 4 * cm],
              f"Distribución de las {r['n_muestras']} muestras por diagnóstico."),
        p(f"La base no tiene valores faltantes y presenta un desbalance moderado a favor de la clase benigna, por "
          f"lo que se usaron particiones estratificadas y métricas con promedio macro. Para comparar las "
          f"características en una misma escala se calculó la diferencia de medias entre diagnósticos dividida "
          f"entre la desviación estándar combinada (Tabla {NUM.tabla + 1}): las variables de concavidad y tamaño son las que más "
          f"separan los diagnósticos, siempre con valores mayores en los tumores malignos."),
        tabla(["Característica", "Media maligno", "Media benigno", "Separación"], filas_sep,
              [6 * cm, 3.2 * cm, 3.2 * cm, 3.2 * cm],
              "Las cinco características con mayor separación entre diagnósticos."),
        p(f"Muchas características son redundantes: el radio y el perímetro medios tienen una correlación de "
          f"{r['correlacion_radio_perimetro']:.3f}, y {r['pares_correlacion_mayor_08']} de los "
          f"{r['pares_correlacion_total']} pares de características tienen una correlación absoluta mayor a 0.8. "
          f"Como lo pide el enunciado, la visualización se hizo con PCA sobre las características "
          f"estandarizadas: la primera componente explica el {pct(r['varianza_pc1'])} de la varianza y la segunda "
          f"el {pct(r['varianza_pc2'])}, con un acumulado de {pct(r['varianza_pc1'] + r['varianza_pc2'])} "
          f"(Figura {NUM.figura + 1}). Los tumores benignos se concentran en la región de PC1 negativa y los malignos se extienden "
          f"hacia la derecha con mayor dispersión, con traslape en la zona central."),
        figura(RES_CANCER / "figuras" / "pca_por_clase.png",
               "Muestras de cáncer de mama proyectadas sobre las dos primeras componentes principales "
               "(solo para visualización).", ancho=12 * cm),
    ]


def metodologia():
    algoritmos = [
        ["Clustering jerárquico", "Estandarización", "Enlace, métrica de distancia y número de clústeres (2 a 6)",
         "Revela la estructura de agrupamiento sin suponer una forma de los grupos."],
        ["K-means", "Estandarización", "Número de clústeres (2 a 6); en hojas también inicialización y reinicios",
         "Agrupa alrededor de centroides; es eficiente y fácil de interpretar."],
        ["k-NN", "Estandarización en el pipeline", "Número de vecinos, distancia de Minkowski (p) y ponderación",
         "Clasificador local sin supuestos sobre la forma de las clases."],
        ["Naive Bayes (gaussiano)", "Estandarización en el pipeline", "var_smoothing",
         "Modelo probabilístico sencillo para variables continuas."],
        ["SVM", "Estandarización en el pipeline", "Kernel (lineal, RBF, polinomial, sigmoide), C, gamma y grado",
         "Maximiza el margen; con kernels puede formar fronteras no lineales."],
        ["Árbol de decisión", "Ninguno (umbrales)", "Criterio, profundidad máxima y mínimos de muestras por nodo",
         "Reglas interpretables sobre las variables originales."],
        ["Random Forest", "Ninguno (umbrales)", "Número de árboles, profundidad, características por división y criterio",
         "Promedia muchos árboles para reducir la varianza."],
        ["MLP", "Estandarización en el pipeline", "Capas ocultas y neuronas, activación, alpha y tasa de aprendizaje",
         "Red neuronal capaz de aprender fronteras no lineales."],
    ]
    return [
        PageBreak(),
        p("3. Metodología", "h1"),
        p("3.1 Algoritmos y búsqueda de hiperparámetros", "h2"),
        tabla(["Algoritmo", "Preprocesamiento", "Hiperparámetros explorados", "Justificación"], algoritmos,
              [3 * cm, 3 * cm, 5.4 * cm, 5.8 * cm], "Algoritmos aplicados a ambas bases de datos."),
        p("3.2 Evaluación", "h2"),
        *vinetas([
            "<b>Validación cruzada anidada.</b> La partición externa es <i>StratifiedKFold</i> de 10 folds con "
            "barajado y semilla fija, la misma para los seis clasificadores. Dentro de cada fold externo, "
            "<i>GridSearchCV</i> con 5 folds selecciona los hiperparámetros por F1 macro usando solo los datos de "
            "entrenamiento (en cáncer, el MLP usó <i>RandomizedSearchCV</i> con un número limitado de configuraciones "
            "aleatorias por fold). El escalado forma parte del <i>Pipeline</i>, por lo que no hay fuga de información.",
            "<b>Métricas.</b> Se reportan accuracy, precision, recall y F1 con promedio macro, y el MAE, como "
            "media ± desviación estándar de los 10 folds externos. La matriz de confusión se construye con las "
            "predicciones fuera de muestra. En hojas, el MAE depende de la codificación de las clases "
            "(Limón = 0, Fresno = 1, Ocozote = 2) y no tiene interpretación ordinal.",
            "<b>Configuración final.</b> Se repite la búsqueda con todos los datos para obtener el modelo final, "
            "que se usa para las fronteras de decisión. En cáncer, las configuraciones finales de Random Forest y MLP "
            "se tomaron de los resultados de la validación anidada (en el MLP, la configuración más frecuente entre "
            "los folds). En hojas, cuando varias configuraciones empataron en F1 "
            "se eligió la más sencilla según un criterio de desempate fijado antes de evaluar.",
            "<b>Clustering.</b> Los métodos se ajustaron con las características estandarizadas, sin usar las "
            "etiquetas, y la configuración se eligió por coeficiente de silueta. Después se compararon con las "
            "clases reales mediante tablas cruzadas, ARI y NMI. En hojas, todas las configuraciones se compararon "
            "con la silueta euclidiana; en cáncer, la silueta del clustering jerárquico se calculó con la métrica "
            "de cada configuración (coseno en la seleccionada), por lo que no está en la misma escala que la de "
            "K-means.",
            "<b>Visualización.</b> En hojas, todas las figuras usan el plano original Alto × Ancho y las fronteras "
            "corresponden exactamente a los modelos evaluados. En cáncer, las fronteras se dibujan con modelos "
            "adicionales entrenados solo con PC1 y PC2; no son la proyección de los modelos de 30 dimensiones.",
        ]),
    ]


def tabla_metricas_hojas(m):
    m = m.sort_values(["ranking_f1", "modelo"])
    filas = [[int(f["ranking_f1"]), f["modelo"], pm(f["f1_macro_promedio"], f["f1_macro_desv"]),
              pm(f["accuracy_promedio"], f["accuracy_desv"]), pm(f["precision_macro_promedio"], f["precision_macro_desv"]),
              pm(f["recall_macro_promedio"], f["recall_macro_desv"]), pm(f["mae_promedio"], f["mae_desv"]),
              int(f["errores_fuera_de_muestra"])]
             for _, f in m.iterrows()]
    return filas


def resultados_hojas(h):
    r = h["resumen"]
    m = h["metricas"]
    cl = h["clustering"].set_index("Método")
    jer, km = r["jerarquico"], r["kmeans"]
    errores = h["errores"]
    modelos = list(m["modelo"])
    mejores = m[m["ranking_f1"] == m["ranking_f1"].min()]
    peores = m[m["ranking_f1"] == m["ranking_f1"].max()]
    hojas_todos = errores[errores[modelos].ne("").all(axis=1)]
    clase_nunca = [cl_ for cl_ in r["clases"] if cl_ not in set(errores["Árbol"])]

    filas_cl = [[metodo, fila["Configuración"], int(fila["Clústeres"]), fila["Tamaños"], f4(fila["Silueta"]),
                 f4(fila["ARI"]), f4(fila["NMI"])] for metodo, fila in cl.iterrows()]

    filas_err = []
    for _, f in errores.iterrows():
        fallaron = [mod for mod in modelos if f[mod] != ""]
        filas_err.append([int(f["ID hoja"]), f["Árbol"], f"{f['Alto (cm)']:.1f} × {f['Ancho (cm)']:.1f}",
                          f[fallaron[0]], ", ".join(fallaron)])

    filas_conf = [[f["Modelo"], f["Configuración final"].replace("_", " "), int(f["Configuraciones empatadas"])]
                  for _, f in h["configuraciones"].iterrows()]

    texto_hoja_todos = ""
    if len(hojas_todos):
        hoja = hojas_todos.iloc[0]
        texto_hoja_todos = (
            f" La hoja {int(hoja['ID hoja'])} ({hoja['Árbol']}, {hoja['Alto (cm)']:.1f} × {hoja['Ancho (cm)']:.1f} cm) "
            f"fue mal clasificada por los seis modelos: con estas dos medidas es prácticamente indistinguible de una "
            f"hoja de {hoja[modelos[0]]}."
        )

    contenido = [
        PageBreak(),
        p("4. Resultados: corpus de hojas", "h1"),
        p("4.1 Métodos no supervisados", "h2"),
        tabla(["Método", "Configuración", "k", "Tamaños", "Silueta", "ARI", "NMI"], filas_cl,
              [3 * cm, 3.8 * cm, 0.8 * cm, 3.4 * cm, 1.9 * cm, 1.9 * cm, 1.9 * cm],
              "Configuración final de los métodos de clustering (silueta euclidiana sobre las variables estandarizadas)."),
        figura(RES_HOJAS / "figuras" / "clustering.png",
               "Clases reales y agrupamientos obtenidos, graficados en centímetros. Los modelos se ajustaron con las "
               "variables estandarizadas."),
        p(f"La silueta no favoreció 3 clústeres en ninguno de los dos métodos: con k = 3 fue de {f4(jer['silueta_k3'])} "
          f"en el jerárquico y de {f4(km['silueta_k3'])} en K-means, menor que la de las configuraciones elegidas "
          f"({jer['linkage']} + {jer['metrica']} con k = {jer['k']}, y K-means con k = {km['k']}). Ambos métodos "
          f"separan primero las hojas anchas (Ocozote) de las angostas, dividen a Ocozote, la clase más dispersa, en "
          f"grupos de distinto tamaño, y agrupan con Limón algunas hojas cortas de Fresno. Sus siluetas son "
          f"prácticamente iguales ({f4(jer['silueta'])} y {f4(km['silueta'])}), pero el jerárquico tiene mayor "
          f"correspondencia con los árboles reales (ARI de {f4(jer['ari'])} frente a {f4(km['ari'])}), porque divide "
          f"a Ocozote en menos grupos."),
        p("4.2 Clasificadores", "h2"),
        tabla(["#", "Modelo", "F1 macro", "Accuracy", "Precision macro", "Recall macro", "MAE", "Errores"],
              tabla_metricas_hojas(m),
              [0.7 * cm, 2.6 * cm, 2.45 * cm, 2.45 * cm, 2.45 * cm, 2.45 * cm, 2.45 * cm, 1.4 * cm],
              f"Métricas de validación cruzada anidada en hojas (media ± desviación estándar de 10 folds; errores de "
              f"{r['n_muestras']} hojas). Los empates comparten posición."),
        tabla(["Modelo", "Configuración final", "Configuraciones empatadas"], filas_conf,
              [3.2 * cm, 10.6 * cm, 3.4 * cm],
              "Configuración final de cada clasificador y número de configuraciones que empataron en F1 macro."),
        figura(RES_HOJAS / "figuras" / "matrices_confusion.png",
               "Matrices de confusión de los seis clasificadores en hojas.", ancho=14 * cm),
        tabla(["ID hoja", "Árbol real", "Alto × Ancho (cm)", "Clase predicha", "Modelos que fallaron"], filas_err,
              [1.6 * cm, 2.2 * cm, 3 * cm, 2.6 * cm, 7.8 * cm],
              "Hojas mal clasificadas por al menos un modelo (predicciones fuera de muestra)."),
        p(f"{lista_texto(mejores['modelo'])} comparten el primer lugar con un F1 macro de "
          f"{f4(mejores['f1_macro_promedio'].iloc[0])}, y {lista_texto(peores['modelo'])} el último con "
          f"{f4(peores['f1_macro_promedio'].iloc[0])}. Entre los seis modelos solo {len(errores)} hojas fueron mal "
          f"clasificadas alguna vez, todas en la frontera entre Limón y Fresno, y ninguna hoja de "
          f"{lista_texto(clase_nunca)} tuvo errores.{texto_hoja_todos} Las diferencias entre modelos son de una o "
          f"dos hojas, menores que la variación entre folds, por lo que el ranking no permite afirmar que un modelo "
          f"sea superior a otro con este tamaño de muestra."),
        figura(RES_HOJAS / "figuras" / "fronteras.png",
               "Fronteras de decisión de los modelos finales en el plano Alto × Ancho. Los círculos negros marcan las "
               "hojas mal clasificadas en la validación cruzada anidada."),
    ]
    contenido += [
        p(f"Las fronteras (Figura {ultima_figura()}) coinciden en lo esencial: Ocozote se separa por el ancho y Limón y Fresno por el "
          "alto. Cada modelo muestra su sesgo en la frontera entre Limón y Fresno: Naive Bayes genera regiones "
          "elípticas alineadas con los ejes porque supone independencia entre el alto y el ancho, aunque dentro de "
          "Limón están muy correlacionados; el árbol de decisión usa un único umbral vertical sobre el alto, que "
          "cambia según las hojas de entrenamiento; Random Forest estabiliza ese umbral al promediar árboles; y "
          "SVM lineal y MLP separan con rectas diagonales que combinan ambas variables, mientras que k-NN forma "
          "una frontera irregular. En las zonas sin hojas, cada modelo extrapola de forma distinta y la validación "
          "cruzada no permite decidir cuál es correcta."),
    ]
    return contenido


def parametros_texto(parametros):
    partes = []
    for nombre, valor in parametros.items():
        if nombre == "metric":
            continue
        if isinstance(valor, float) and (abs(valor) < 1e-3 or abs(valor) >= 1e4) and valor != 0:
            valor = f"{valor:.0e}"
        elif isinstance(valor, float):
            valor = f"{valor:.4g}"
        partes.append(f"{nombre.replace('_', ' ')}={valor}")
    return ", ".join(partes)


def resultados_cancer(c):
    r = c["resumen"]
    m = c["metricas"].sort_values("f1_macro", ascending=False).reset_index(drop=True)
    cl = c["clustering"]
    jer, km = r["jerarquico"], r["kmeans"]
    matrices = r["matrices_confusion"]

    filas = []
    for i, f in m.iterrows():
        matriz = matrices[f["modelo"]]
        no_detectados = matriz[0][1]
        filas.append([i + 1, f["modelo"], pm(f["f1_macro"], f["f1_std"]), pm(f["accuracy"], f["accuracy_std"]),
                      pm(f["precision_macro"], f["precision_std"]), pm(f["recall_macro"], f["recall_std"]),
                      pm(f["mae"], f["mae_std"]), no_detectados])

    filas_conf = [[nombre, parametros_texto(param)] for nombre, param in r["parametros_finales"].items()]

    filas_cl = [[f["Método"], f["Configuración final"], f4(f["Coeficiente de silueta"]), f4(f["ARI"]), f4(f["NMI"])]
                for _, f in cl.iterrows()]

    mejor, peor = m.iloc[0], m.iloc[-1]
    total_malignos = r["conteo_por_clase"]["malignant"]

    # ¿En todos los modelos predominan los malignos clasificados como benignos?
    predomina_fn = all(matriz[0][1] > matriz[1][0] for matriz in matrices.values())
    recall_menor = bool((m["recall_macro"] < m["precision_macro"]).all())
    texto_errores = (
        "En todos los modelos el error más frecuente fue clasificar tumores malignos como benignos, el error más "
        "delicado en una aplicación médica"
        + (", lo que explica que el recall macro sea menor que la precisión macro." if recall_menor else ".")
        if predomina_fn else
        "Los modelos difieren en el tipo de error predominante; los tumores malignos clasificados como benignos son "
        "el error más delicado en una aplicación médica."
    )

    return [
        PageBreak(),
        p("5. Resultados: cáncer de mama", "h1"),
        p("5.1 Métodos no supervisados", "h2"),
        tabla(["Método", "Configuración final", "Silueta", "ARI", "NMI"], filas_cl,
              [3.6 * cm, 6.4 * cm, 2.4 * cm, 2.4 * cm, 2.4 * cm],
              "Configuración final de los métodos de clustering en cáncer de mama (30 características estandarizadas). "
              "La silueta del clustering jerárquico se calculó con su propia métrica (coseno)."),
        figura(RES_CANCER / "figuras" / "clustering_pca.png",
               "Diagnósticos reales y agrupamientos representados en el plano PCA. Los modelos se ajustaron con las 30 "
               "características estandarizadas; PCA solo se usa para graficar."),
        p(f"{'Ambos métodos seleccionaron ' + str(jer['k']) + ' grupos. ' if jer['k'] == km['k'] else ''}El clustering jerárquico ({jer['linkage']} + "
          f"{jer['metrica']}) obtuvo un ARI de {f4(jer['ari'])} y un NMI de {f4(jer['nmi'])}, y K-means un ARI de "
          f"{f4(km['ari'])} y un NMI de {f4(km['nmi'])}: los dos encontraron grupos muy relacionados con el "
          f"diagnóstico sin usar las etiquetas. Las siluetas ({f4(jer['silueta'])} y {f4(km['silueta'])}) se "
          f"calcularon con métricas distintas, por lo que no deben compararse directamente."),
        p("5.2 Clasificadores", "h2"),
        tabla(["#", "Modelo", "F1 macro", "Accuracy", "Precision macro", "Recall macro", "MAE", "Malignos no detectados"],
              filas, [0.6 * cm, 2.7 * cm, 2.4 * cm, 2.4 * cm, 2.4 * cm, 2.4 * cm, 2.4 * cm, 1.9 * cm],
              f"Métricas de validación cruzada anidada en cáncer de mama con las 30 características (media ± desviación "
              f"estándar de 10 folds). La última columna cuenta los tumores malignos (de {total_malignos}) clasificados "
              f"como benignos."),
        tabla(["Modelo", "Configuración final"], filas_conf, [3.6 * cm, 13.6 * cm],
              "Configuración final de cada clasificador en cáncer de mama."),
        figura(RES_CANCER / "figuras" / "matrices_confusion.png",
               "Matrices de confusión de los seis clasificadores en cáncer de mama.", ancho=14 * cm),
        p(f"{mejor['modelo']} obtuvo el mejor desempeño, con un F1 macro de {pm(mejor['f1_macro'], mejor['f1_std'])}, "
          f"y {peor['modelo']} el más bajo, con {pm(peor['f1_macro'], peor['f1_std'])}. {texto_errores}"),
        figura(RES_CANCER / "figuras" / "fronteras_pca.png",
               "Fronteras de decisión de modelos adicionales entrenados solo con PC1 y PC2. Sirven para comparar "
               "visualmente los algoritmos, pero no son la proyección de los modelos evaluados con 30 características."),
        p("En el plano PCA, todos los modelos separan los tumores benignos (izquierda) de los malignos (derecha), con "
          "errores en la zona central de traslape. Las formas reflejan cada algoritmo: el árbol de decisión y Random "
          "Forest forman fronteras escalonadas paralelas a los ejes, Naive Bayes una curva que encierra a la clase "
          "benigna, SVM una curva suave, el MLP una frontera casi recta y k-NN un borde irregular. Como estas dos componentes solo "
          "conservan parte de la varianza, las fronteras no explican por completo el desempeño de los modelos de 30 "
          "dimensiones."),
    ]


def comparacion(h, c):
    mh = h["metricas"].set_index("modelo")
    mc = c["metricas"].set_index("modelo")
    equivalencias = {"Naive Bayes": "Gaussian Naive Bayes"}

    filas = []
    for modelo in mh.sort_values(["ranking_f1"]).index:
        modelo_c = equivalencias.get(modelo, modelo)
        filas.append([modelo, int(mh.loc[modelo, "ranking_f1"]), pm(mh.loc[modelo, "f1_macro_promedio"], mh.loc[modelo, "f1_macro_desv"]),
                      int((mc["f1_macro"].round(4) > round(mc.loc[modelo_c, "f1_macro"], 4)).sum() + 1),
                      pm(mc.loc[modelo_c, "f1_macro"], mc.loc[modelo_c, "f1_std"])])

    rh = h["resumen"]
    rc = c["resumen"]
    rango_h = (mh["f1_macro_promedio"].min(), mh["f1_macro_promedio"].max())
    rango_c = (mc["f1_macro"].min(), mc["f1_macro"].max())
    ultimos_h = set(mh[mh["ranking_f1"] == mh["ranking_f1"].max()].index)
    ultimos_c = {m for m, _ in mc["f1_macro"].nsmallest(2).items()}
    ultimos_c = {"Naive Bayes" if m == "Gaussian Naive Bayes" else m for m in ultimos_c}

    texto_ultimos = (
        f"En ambas bases, {lista_texto(sorted(ultimos_h))} ocuparon los últimos lugares."
        if ultimos_h == ultimos_c else
        f"Los últimos lugares fueron {lista_texto(sorted(ultimos_h))} en hojas y {lista_texto(sorted(ultimos_c))} en cáncer."
    )

    return [
        PageBreak(),
        p("6. Análisis comparativo y ranking", "h1"),
        p("6.1 Ranking por F1-score macro", "h2"),
        tabla(["Modelo", "Posición en hojas", "F1 macro en hojas", "Posición en cáncer", "F1 macro en cáncer"], filas,
              [3.6 * cm, 2.6 * cm, 3.9 * cm, 2.6 * cm, 3.9 * cm],
              "Ranking de los seis clasificadores por F1 macro promedio en cada base (validación cruzada anidada)."),
        p(f"En hojas, el F1 macro va de {f4(rango_h[0])} a {f4(rango_h[1])}; en cáncer de mama, de {f4(rango_c[0])} a "
          f"{f4(rango_c[1])}. {texto_ultimos} En los métodos no supervisados, el clustering jerárquico y K-means "
          f"obtuvieron en hojas siluetas casi iguales ({f4(rh['jerarquico']['silueta'])} y "
          f"{f4(rh['kmeans']['silueta'])}), mientras que en cáncer sus siluetas ({f4(rc['jerarquico']['silueta'])} y "
          f"{f4(rc['kmeans']['silueta'])}) se calcularon con métricas distintas y no son comparables."),
        p("6.2 Discusión de resultados", "h2"),
        *vinetas([
            "<b>Geometría y solapamiento.</b> El corpus de hojas es casi separable con dos variables: Ocozote se "
            "separa por completo y todos los errores ocurren en la estrecha zona donde Limón y Fresno coinciden en el "
            "alto. En cáncer de mama, los diagnósticos se traslapan en una región más amplia, lo que explica F1 más "
            "bajos y más variables entre modelos.",
            "<b>Ruido.</b> En hojas, las medidas tienen una resolución de 0.1 cm y en su mayoría se obtuvieron de "
            "fotografías con herramientas de inteligencia artificial; en la frontera entre Limón y Fresno, unos "
            "milímetros bastan para cambiar la predicción.",
            "<b>Escalado.</b> En ambas bases, los modelos basados en distancias o pesos se entrenaron con variables "
            "estandarizadas dentro del pipeline. En cáncer, las escalas difieren en varios órdenes de magnitud, por lo "
            "que el escalado es indispensable para k-NN, SVM y MLP.",
            "<b>Complejidad.</b> Los modelos más complejos no superaron a los sencillos: en hojas, SVM lineal y k-NN "
            "empataron con el MLP con un costo mucho menor, y en cáncer SVM superó al MLP. Naive Bayes quedó entre los "
            "últimos en ambas bases porque su supuesto de independencia no se cumple: el alto y el ancho están "
            "correlacionados dentro de cada árbol, y en cáncer muchas características son casi redundantes.",
            "<b>Sensibilidad a hiperparámetros.</b> En hojas, muchas configuraciones empataron en todos los modelos, "
            "lo que muestra que el resultado depende poco de los hiperparámetros cuando las clases están bien "
            "separadas.",
            "<b>Dimensionalidad.</b> En hojas, las fronteras graficadas son exactamente las de los modelos evaluados y "
            "permiten identificar las hojas concretas que causan los errores. En cáncer, PCA solo conserva parte de la "
            "varianza: sus gráficas muestran tendencias, pero no demuestran que las clases sean separables o no en "
            "las 30 dimensiones, y las fronteras 2D no representan a los modelos evaluados.",
        ]),
    ]


def conclusiones():
    return [
        p("7. Conclusiones", "h1"),
        *vinetas([
            "<b>Enfoques supervisados.</b> Los seis clasificadores alcanzaron un desempeño alto en ambas bases. Las "
            "diferencias entre ellos fueron pequeñas, sobre todo en hojas, donde fueron de una o dos hojas y menores "
            "que la variación entre folds. La validación cruzada anidada permitió estimar el desempeño sin el sesgo de "
            "la búsqueda de hiperparámetros.",
            "<b>Enfoques no supervisados.</b> El clustering encontró estructuras relacionadas con las clases reales "
            "sin usar las etiquetas, pero no las recuperó exactamente: en hojas, la silueta no favoreció tres grupos, "
            "porque Ocozote es muy disperso y Limón y Fresno son contiguos.",
            "<b>Características de cada conjunto.</b> En hojas, el ancho separa a Ocozote y el alto separa a Limón de "
            "Fresno. En cáncer de mama, las variables de tamaño y concavidad del núcleo son las más informativas, y "
            "muchas de las 30 características son redundantes.",
            "<b>Limitaciones.</b> El corpus de hojas es pequeño, sus medidas tienen una resolución limitada y dos "
            "características no bastan para algunas hojas de Limón y Fresno. En cáncer, las visualizaciones con PCA "
            "son aproximaciones. El MAE no tiene interpretación ordinal en ninguno de los dos problemas.",
            "<b>Recomendaciones.</b> Para problemas similares conviene empezar por modelos sencillos y bien escalados "
            "(SVM o k-NN), evaluar con validación cruzada anidada, definir de antemano un criterio para resolver "
            "empates y, cuando dos clases se confunden, agregar características informativas o medir con mayor "
            "precisión antes que aumentar la complejidad del modelo.",
        ]),
        p("Referencias", "h1"),
        *vinetas([
            "W. N. Street, W. H. Wolberg y O. L. Mangasarian. Nuclear feature extraction for breast tumor diagnosis. "
            "IS&amp;T/SPIE International Symposium on Electronic Imaging: Science and Technology, vol. 1905, pp. 861-870, 1993.",
            "F. Pedregosa et al. Scikit-learn: Machine Learning in Python. Journal of Machine Learning Research, 12, "
            "pp. 2825-2830, 2011.",
        ]),
    ]


def main():
    h, c = cargar()
    documento = SimpleDocTemplate(
        str(SALIDA), pagesize=letter,
        leftMargin=2.2 * cm, rightMargin=2.2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
        title="Proyecto Final — Razonamiento con IA",
        subject="Aprendizaje supervisado y no supervisado: corpus de hojas y cáncer de mama",
    )
    contenido = (
        portada()
        + introduccion(h, c)
        + datos_hojas(h)
        + datos_cancer(c)
        + metodologia()
        + resultados_hojas(h)
        + resultados_cancer(c)
        + comparacion(h, c)
        + conclusiones()
    )
    documento.build(contenido, onLaterPages=pie_de_pagina)
    print("Reporte generado:", SALIDA)


if __name__ == "__main__":
    main()
