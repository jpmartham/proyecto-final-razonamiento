# HANDOFF — Corpus de hojas (Proyecto Final, Razonamiento con IA)

> Contexto para Claude Code. Léelo completo antes de escribir código.
> Las partes marcadas **[PENDIENTE]** las tiene que confirmar el alumno; no las inventes.

## 1. Objetivo

Crear `notebooks/hojas.ipynb`, que aplique **el mismo procedimiento** que `notebooks/cancer_mama.ipynb`
(con el mismo estilo de código, de markdown y de gráficas) al corpus `data/hojasRazonamiento.csv`.
El enunciado completo está en `docs/Proyecto_Final_Razonamiento_IA.pdf`.

## 2. Datos

- Columnas: `ID hoja`, `Árbol`, `Alto (cm)`, `Ancho (cm)`. Archivo en UTF-8 con acentos.
- Hay 150 hojas en **3 clases balanceadas** (Limón, Ocozote y Fresno, con 50 cada una) y no hay valores faltantes.
- **Características:** `Alto (cm)` y `Ancho (cm)`. **Etiqueta:** `Árbol`.
- `ID hoja` es un identificador. **No es una característica.**
- Fija el orden de las etiquetas explícitamente (por ejemplo `["Limón", "Fresno", "Ocozote"]`) y documéntalo,
  porque ese orden afecta al MAE (ver §4.4).

Estas son observaciones del análisis exploratorio previo. Deben verificarse en el notebook antes de interpretarse:

| Clase | Alto media ± desv. (cm) | Ancho media ± desv. (cm) |
|---|---|---|
| Limón | 6.02 ± 0.89 | 3.05 ± 0.45 |
| Fresno | 10.94 ± 1.85 | 3.45 ± 0.73 |
| Ocozote | 12.81 ± 2.75 | 12.10 ± 1.97 |

*Hipótesis:* Ocozote se separa por el ancho. Limón y Fresno se traslapan en el ancho y se separan sobre todo por el alto.

## 3. Lo que exige el enunciado para esta base (y en qué difiere de cáncer de mama)

| Aspecto | Cáncer de mama (referencia) | Hojas (lo que hay que hacer) |
|---|---|---|
| Visualización | PCA 2D | **Sin PCA.** Todo va en el plano original Alto × Ancho (cm). |
| Fronteras de decisión | Modelos extra entrenados con PC1 y PC2 | Se usan los modelos con las 2 variables originales. Como son las mismas variables de la evaluación, no hace falta entrenar un modelo aparte. |
| Clases | 2 | 3 (paletas, leyendas, matrices de 3×3) |
| Descripción de la base | Origen sklearn | Hay que explicar cómo se recolectaron las hojas, cómo se midieron y cómo se definieron las etiquetas. **[PENDIENTE §6]** |
| Ejes | PC1 y PC2 | `Alto (cm)` y `Ancho (cm)` |

Lo que se mantiene igual:
- `StratifiedKFold(10, shuffle=True, random_state=42)` como partición externa. Son las mismas particiones para los 6 clasificadores.
- CV interna de 5 folds con `GridSearchCV(scoring="f1_macro")`, es decir, validación cruzada anidada.
- El escalado va dentro del `Pipeline`. Las métricas son accuracy, precision, recall, F1 (macro) y MAE, con media y desviación estándar.
- La matriz de confusión se arma con las predicciones fuera de muestra.
- Clustering jerárquico (enlace × métrica × k = 2..6) y K-means (k = 2..6, `n_init=20`), seleccionados por silueta.
  Después se comparan contra las etiquetas reales (tabla cruzada, ARI, NMI) sin usarlas para entrenar.
- La estructura por modelo, en este orden: markdown de introducción → búsqueda → tabla por fold → resumen → matriz → configuración final → gráfica → interpretación.

## 4. Adaptaciones obligatorias (bugs que aparecerían si solo se copia el notebook)

1. **Validaciones fijas:** `if X.shape != (569, 30)` debe cambiar a `(150, 2)`, con su mensaje de error.
2. **Paletas y colores fijos de 2 clases:** `["royalblue", "darkorange"]`, `{"malignant": ..., "benign": ...}`,
   el `ListedColormap` de 2 colores y los `zip([0, 1], ...)`. Hay que generalizarlos a 3 clases y a k clústeres.
   Usa la misma paleta para la misma clase en todas las figuras.
3. **Tabla comparativa escrita a mano** (celda 81 del notebook de referencia): ahí las métricas están tecleadas.
   En hojas, construye la tabla a partir de los DataFrames `resumen_*` para que sea reproducible.
   *Nota:* esto también es un riesgo en el notebook de cáncer. Conviene corregirlo allá.
4. **MAE con 3 clases nominales:** el enunciado lo exige, así que repórtalo. Agrega una nota de que depende del orden en que se codifican las etiquetas
   (confundir clase 0 con 2 cuenta doble) y de que no tiene interpretación ordinal en este problema.
5. **Mallas para las fronteras:** se construyen en cm sobre `Alto` y `Ancho`. El `Pipeline` ya incluye el escalado, así que la malla
   no se escala a mano.
6. **Clustering:** ajústalo sobre las 2 variables **estandarizadas**, porque Alto y Ancho tienen rangos distintos. Grafica los clústeres en cm
   y dilo explícitamente en el markdown. Si la silueta favorece k = 2 sobre k = 3, repórtalo y discútelo; no fuerces k = 3.
7. **Cifras en el markdown:** las interpretaciones deben citar los valores que salgan en las celdas, nunca los de cáncer.

## 5. Secciones que el enunciado pide y el notebook de cáncer no tiene

Hay que verificarlo, porque el notebook de referencia empieza directamente con la carga de datos:
- Descripción de la base: origen, cómo se obtuvo, variables, número de instancias, número de clases y distribución por clase.
- Estadísticas descriptivas por clase (media, desviación estándar, mínimo y máximo), con tabla e interpretación.
- Gráficas exploratorias: dispersograma por clase y, por ejemplo, histogramas o boxplots por variable.
- Ranking de los 6 clasificadores por F1 macro y comparación de clustering por silueta (§7 del enunciado).

## 6. Preguntas abiertas para el alumno

1. ¿Cómo se recolectaron las hojas (lugar, fechas, quién las tomó)? ¿Cómo se midieron alto y ancho
   (regla, foto + software, punto de medición)? Fueron recolectadas a mano, se midieron con software la mayoria, solo unas pocas con regla y a mano. Desde el inicio de la hoja sin contar el palito. 
2. ¿Se debe agregar también la sección de descripción y EDA al notebook de cáncer? Si lo pide el documento de instrucciones si.
3. ¿El reporte PDF se escribe aparte, o el notebook es la base del reporte? Se escribe basado en el notebook pero es un reporte de este mismo. 

## 7. Orden de trabajo para Claude Code

1. Leer este archivo, el PDF y `notebooks/cancer_mama.ipynb` completo. Responder §6 si sigue pendiente.
2. Proponer el índice de secciones de `hojas.ipynb` en modo Plan.
3. Escribir las secciones **una por una**: descripción y EDA → jerárquico → K-means → k-NN → Naive Bayes → SVM → árbol de decisión →
   Random Forest → MLP → comparativa y ranking. Ejecutar y revisar cada una antes de seguir, con un commit por sección.
4. Al final, ejecutar el notebook completo desde cero (con `nbconvert --execute`) para comprobar que es reproducible.
