# CUNOC Academic Offer Analysis 2024

Repositorio para el análisis de datos institucionales sobre la oferta académica del CUNOC durante el año 2024, desarrollado como parte de una tesis de maestría en análisis de datos.

## Objetivo del proyecto

Analizar la oferta académica, asignaciones y resultados registrados en actas de la carrera de Ingeniería en Ciencias y Sistemas del CUNOC durante el año 2024, con el fin de identificar patrones relacionados con pérdida de cursos, recuperación, continuidad de oferta y riesgo de retraso académico potencial.

El análisis se centra exclusivamente en datos institucionales académicos. No se trabajará con información presupuestaria, horas docentes, contratación, encuestas ni datos personales identificables.

## Alcance del análisis

El proyecto debe analizar:

* Oferta académica por período académico.
* Cursos aperturados y no aperturados en S1, V1, S2 y V2.
* Asignaciones por estudiante, curso, sección y período.
* Resultados registrados en actas.
* Pérdida ordinaria, recuperación y pérdida definitiva.
* Continuidad de oferta entre períodos.
* Cursos que funcionan como prerrequisito de otros cursos.
* Riesgo de retraso académico potencial cuando un estudiante pierde un curso que no se oferta en el período inmediato posterior.
* Cursos críticos por pérdida, recuperación, baja continuidad y bloqueo curricular.

## Restricciones metodológicas

No implementar análisis relacionados con:

* Presupuesto ordinario o extraordinario.
* Montos financieros.
* Horas docentes.
* Contratación docente.
* Evaluación individual de docentes.
* Encuestas a estudiantes.
* Datos personales identificables.
* Causalidad directa entre presupuesto y resultados académicos.
* Dashboards como entregable obligatorio.

El enfoque debe ser neutral, académico y basado en evidencia descriptiva, estadística y de minería de datos.

## Codificación de períodos académicos

Utilizar de forma consistente la siguiente codificación:

* `S1`: Primer semestre 2024.
* `V1`: Vaqueras junio 2024.
* `S2`: Segundo semestre 2024.
* `V2`: Vaqueras diciembre 2024.

El orden cronológico debe ser:

1. `S1`
2. `V1`
3. `S2`
4. `V2`

## Arquitectura del repositorio

```text
cunoc-academic-offer-analysis-2024/
│
├── README.md
├── INSTRUCTIONS.md
├── instructions-codex.md
├── requirements.txt
├── .gitignore
│
├── data/
│   ├── raw/
│   │   ├── 01_catalogo_cursos_2024.csv
│   │   ├── 02_actas_notas_2024_detalle.csv
│   │   ├── 03_asignaciones_2024.csv
│   │   ├── 04_oferta_academica_2024.csv
│   │   ├── 05_malla_prerrequisitos.csv
│   │   ├── 06_calendario_academico_2024.csv
│   │   ├── 07_parametros_academicos.csv
│   │   ├── 08_configuracion_academica_cursos.csv
│   │   ├── 09_estudiantes_inscritos_2024.csv
│   │   └── 10_inscritos_sistemas_anual.csv
│   │
│   ├── interim/
│   │   └── archivos intermedios generados durante el ETL
│   │
│   └── processed/
│       ├── ds_estudiante_curso_resultado_2024.csv
│       ├── ds_resumen_curso_periodo_2024.csv
│       ├── ds_continuidad_oferta_2024.csv
│       ├── ds_cursos_criticos_clustering.csv
│       ├── ds_modelo_clasificacion.csv
│       └── ds_reglas_asociacion.csv
│
├── notebooks/
│   ├── 01_validacion_y_calidad_datos.ipynb
│   ├── 02_etl_y_datasets_derivados.ipynb
│   ├── 03_eda_indicadores_academicos.ipynb
│   ├── 04_analisis_estadistico_y_modelos.ipynb
│   └── 05_cursos_criticos_y_hallazgos.ipynb
│
├── src/
│   ├── config/
│   │   └── settings.py
│   │
│   ├── data/
│   │   ├── load_data.py
│   │   ├── validate_data.py
│   │   └── clean_data.py
│   │
│   ├── features/
│   │   ├── build_indicators.py
│   │   ├── build_targets.py
│   │   └── build_derived_datasets.py
│   │
│   ├── analysis/
│   │   ├── eda.py
│   │   ├── statistical_tests.py
│   │   └── academic_continuity.py
│   │
│   ├── models/
│   │   ├── logistic_regression.py
│   │   ├── decision_tree.py
│   │   ├── random_forest.py
│   │   ├── clustering.py
│   │   ├── association_rules.py
│   │   └── linear_regression.py
│   │
│   └── visualization/
│       ├── plots_eda.py
│       ├── plots_models.py
│       └── plots_clusters.py
│
├── outputs/
│   ├── figures/
│   │   ├── eda/
│   │   ├── models/
│   │   └── clusters/
│   │
│   ├── tables/
│   │   ├── indicators/
│   │   ├── statistical_tests/
│   │   └── models/
│   │
│   └── reports/
│       ├── resumen_indicadores.md
│       ├── resultados_modelos.md
│       └── hallazgos_generales.md
│
└── docs/
    ├── diccionario_datos.md
    ├── metodologia.md
    ├── decisiones_etl.md
    └── limitaciones.md
```

## Datasets de entrada

Los archivos base se almacenan en `data/raw/`.

### 01_catalogo_cursos_2024.csv

Catálogo oficial de cursos de Ingeniería en Ciencias y Sistemas.

Uso principal:

* Identificar cursos.
* Relacionar códigos de curso con nombres.
* Asociar cursos con semestre del pensum.
* Enriquecer actas, asignaciones y oferta académica.

Campos esperados:

* `codigo_curso`
* `nombre_curso`
* `semestre_pensum`
* `pensum`
* `tipo_curso`
* `creditos`
* `estado_curso`

### 02_actas_notas_2024_detalle.csv

Dataset principal de resultados académicos.

Uso principal:

* Calcular aprobación ordinaria.
* Calcular pérdida ordinaria.
* Identificar estudiantes en recuperación.
* Calcular pérdida definitiva.
* Identificar NSP, equivalencias y otros resultados especiales.

Campos esperados:

* `estudiante_id_ofuscado`
* `codigo_curso`
* `periodo_academico`
* `fecha_acta`
* `oportunidad_evaluacion`
* `seccion`
* `zona`
* `nota_examen`
* `nota_total`
* `resultado`
* `numero_acta`
* `estado_acta`

Consideraciones:

* Los casos `NSP` deben conservarse.
* Las equivalencias deben tratarse como registros aprobados cuando `resultado=Aprobado`.
* Si `oportunidad_evaluacion=Equivalencia`, no debe mezclarse con ordinario o recuperación para métricas de rendimiento por examen.
* Las actas pueden registrarse entre 1 y 5 días después de la evaluación correspondiente.

### 03_asignaciones_2024.csv

Dataset de asignaciones por estudiante, curso, período y sección.

Uso principal:

* Comparar estudiantes asignados contra estudiantes con acta.
* Identificar desasignaciones.
* Calcular asignados por curso, sección y período.
* Validar cupos y ocupación.

Campos esperados:

* `estudiante_id_ofuscado`
* `codigo_curso`
* `periodo_academico`
* `seccion`
* `fecha_asignacion`
* `estado_asignacion`
* `fecha_desasignacion`

Consideraciones:

* Los registros con `estado_asignacion=desasignado` deben conservarse.
* No eliminar desasignados durante la carga inicial.
* Crear indicadores separados para asignados activos, desasignados y estudiantes con nota.

### 04_oferta_academica_2024.csv

Dataset de oferta académica por curso, sección y período.

Uso principal:

* Identificar cursos aperturados.
* Calcular continuidad de oferta.
* Calcular cupos ofertados.
* Calcular tasa de ocupación.
* Identificar si un curso perdido tuvo oferta en el siguiente período.

Campos esperados:

* `periodo_academico`
* `codigo_curso`
* `seccion`
* `curso_aperturado`
* `curso_cancelado`
* `cupo_ofertado`
* `estudiantes_asignados`
* `estudiantes_con_nota`
* `jornada`
* `horario`
* `modalidad`
* `fecha_inicio`
* `fecha_fin`

### 05_malla_prerrequisitos.csv

Dataset construido con base en el pensum oficial.

Uso principal:

* Identificar prerrequisitos.
* Calcular cantidad de cursos dependientes.
* Identificar cursos bloqueantes.
* Medir riesgo curricular cuando un curso perdido no se abre posteriormente.

Campos esperados:

* `codigo_curso`
* `nombre_curso`
* `codigo_prerrequisito`
* `nombre_prerrequisito`
* `tipo_requisito`
* `es_obligatorio`
* `semestre_curso`
* `semestre_prerrequisito`

Consideraciones:

* Los requisitos por créditos deben conservarse como `tipo_requisito=creditos`.
* Los requisitos por créditos pueden tener `codigo_prerrequisito` vacío.
* La relación de prerrequisitos debe usarse para calcular cursos dependientes directos.

### 06_calendario_academico_2024.csv

Dataset de configuración temporal.

Uso principal:

* Ordenar períodos.
* Calcular siguiente período académico.
* Calcular espera mínima en períodos.
* Calcular espera aproximada en meses.

Campos esperados:

* `periodo_academico`
* `descripcion_periodo`
* `orden_periodo`
* `fecha_inicio_clases`
* `fecha_fin_clases`
* `fecha_examen_final`
* `fecha_primera_recuperacion`
* `fecha_segunda_recuperacion`

Consideraciones:

* Las fechas pueden estar como rangos ISO en formato `YYYY-MM-DD/YYYY-MM-DD`.
* Para S2 puede no existir segunda recuperación dentro del calendario 2024.

### 07_parametros_academicos.csv

Dataset de reglas académicas.

Uso principal:

* Definir nota mínima de aprobación.
* Validar zona, examen y nota total.
* Calcular resultados derivados de forma consistente.

Parámetros esperados:

* `nota_minima_aprobacion`
* `zona_maxima`
* `examen_maximo`
* `nota_total_maxima`

Valores esperados:

* Nota mínima de aprobación: `61`
* Zona máxima: `70`
* Examen máximo: `30`
* Nota total máxima: `100`

### 08_configuracion_academica_cursos.csv

Dataset de configuración académica del curso.

Uso principal:

* Clasificar cursos por área.
* Identificar obligatoriedad.
* Identificar cursos base.
* Identificar cursos con laboratorio o componente práctico.
* Clasificar nivel de bloqueo curricular.

Campos esperados:

* `codigo_curso`
* `nombre_curso`
* `area_academica`
* `tipo_curso_configurado`
* `requiere_laboratorio`
* `componente_practico`
* `curso_obligatorio`
* `curso_base`
* `curso_bloqueante`
* `cantidad_cursos_dependientes`
* `nivel_bloqueo_curricular`
* `observaciones`

### 09_estudiantes_inscritos_2024.csv

Dataset del universo de estudiantes inscritos en 2024.

Uso principal:

* Definir población base.
* Validar estudiantes presentes en asignaciones y actas.
* Calcular cobertura de asignaciones respecto al universo inscrito.

Campos esperados:

* `estudiante_id_ofuscado`
* `periodo_inscripcion`
* `cohorte_ingreso`

Consideraciones:

* Todos los registros corresponden a estudiantes inscritos en Ciencias y Sistemas durante 2024.
* No debe contener carné ni datos personales directos.
* El identificador ofuscado debe coincidir con asignaciones y actas.

### 10_inscritos_sistemas_anual.csv

Dataset agregado de estudiantes inscritos por año.

Uso principal:

* Contextualizar la evolución de matrícula.
* Generar gráfico histórico simple de estudiantes inscritos.
* Mostrar crecimiento o variación anual.

Campos esperados:

* `anio`
* `total_inscritos`

## Flujo técnico del proyecto

El proyecto debe implementarse como un pipeline reproducible:

```text
Carga de datos raw
    ↓
Validación de estructura y calidad
    ↓
Limpieza y normalización
    ↓
Construcción de datasets derivados
    ↓
Cálculo de indicadores académicos
    ↓
Análisis exploratorio de datos
    ↓
Pruebas estadísticas
    ↓
Modelos de minería de datos
    ↓
Generación de tablas, gráficos y reportes
```

## Validaciones iniciales

Implementar validaciones automáticas para:

* Existencia de todos los archivos esperados.
* Columnas requeridas por dataset.
* Codificación válida de `periodo_academico`.
* Códigos de curso consistentes entre datasets.
* Identificadores ofuscados consistentes entre actas, asignaciones e inscritos.
* Duplicados exactos.
* Valores nulos en campos críticos.
* Rangos válidos de zona, examen y nota total.
* Fechas válidas o rangos ISO válidos.
* Estados académicos esperados.
* Oportunidades de evaluación esperadas.

Generar un reporte en:

```text
outputs/reports/data_quality_report.md
```

## Limpieza y normalización

Implementar reglas de limpieza para:

* Normalizar nombres de columnas a `snake_case`.
* Estandarizar `periodo_academico` a `S1`, `V1`, `S2`, `V2`.
* Normalizar códigos de curso como texto.
* Normalizar secciones como texto.
* Convertir fechas a formato datetime cuando sea posible.
* Conservar rangos de fechas cuando el valor represente un rango ISO.
* Convertir zona, examen y nota total a numérico cuando aplique.
* Preservar valores especiales como `EQ`, `NSP` y `desasignado`.
* No eliminar registros especiales sin documentarlos.
* Guardar bitácora de transformaciones.

Documentar decisiones de limpieza en:

```text
docs/decisiones_etl.md
```

## Datasets derivados a generar

### ds_estudiante_curso_resultado_2024.csv

Unidad de análisis:

```text
estudiante + curso + periodo
```

Debe incluir:

* estudiante ofuscado.
* curso.
* nombre del curso.
* período.
* sección.
* semestre del pensum.
* área académica.
* zona ordinaria.
* nota examen ordinario.
* nota total ordinaria.
* indicador de aprobación ordinaria.
* indicador de necesidad de recuperación.
* indicador de aprobación por recuperación.
* indicador de pérdida definitiva.
* indicador NSP.
* indicador equivalencia.
* curso abierto en el siguiente período.
* siguiente período disponible.
* espera mínima en períodos.
* espera mínima aproximada en meses.
* cantidad de cursos dependientes.
* nivel de bloqueo curricular.
* riesgo de retraso potencial.

Definir:

```text
riesgo_retraso_potencial = 1
```

cuando:

```text
perdida_definitiva = 1
curso_abierto_siguiente_periodo = 0
curso_bloqueante = 1
```

También crear una versión alternativa más amplia:

```text
riesgo_retraso_potencial_amplio = 1
```

cuando:

```text
perdida_definitiva = 1
curso_abierto_siguiente_periodo = 0
```

### ds_resumen_curso_periodo_2024.csv

Unidad de análisis:

```text
curso + periodo
```

Debe incluir:

* código de curso.
* nombre del curso.
* período.
* semestre del pensum.
* área académica.
* curso aperturado.
* número de secciones abiertas.
* cupo total ofertado.
* estudiantes asignados.
* estudiantes desasignados.
* estudiantes con nota.
* tasa de ocupación.
* tasa de aprobación ordinaria.
* tasa de pérdida ordinaria.
* tasa de recuperación.
* tasa de aprobación por recuperación.
* tasa de pérdida definitiva.
* índice de dependencia de recuperación.
* estudiantes con pérdida definitiva.
* estudiantes sin oportunidad inmediata.
* curso abierto en siguiente período.
* cantidad de cursos dependientes.
* nivel de bloqueo curricular.

### ds_continuidad_oferta_2024.csv

Unidad de análisis:

```text
curso consolidado 2024
```

Debe incluir:

* código de curso.
* nombre del curso.
* abierto en S1.
* abierto en V1.
* abierto en S2.
* abierto en V2.
* cantidad de períodos abierto.
* índice de continuidad de oferta.
* patrón de oferta.
* total estudiantes asignados 2024.
* total estudiantes con nota 2024.
* total estudiantes con pérdida definitiva 2024.
* tasa de pérdida definitiva 2024.
* tasa de recuperación 2024.
* estudiantes sin oportunidad inmediata 2024.
* cantidad de cursos dependientes.
* nivel de bloqueo curricular.

Definir patrones de oferta sugeridos:

* `oferta_continua`: abierto en dos o más períodos principales o con refuerzo en vacaciones.
* `oferta_anual`: abierto solo una vez en el año.
* `oferta_vacaciones`: abierto únicamente en V1 o V2.
* `oferta_irregular`: combinaciones no clasificadas.
* `sin_oferta_2024`: no abierto en ningún período, si aplica.

### ds_cursos_criticos_clustering.csv

Unidad de análisis:

```text
curso consolidado 2024
```

Debe incluir variables numéricas limpias para clustering:

* tasa de pérdida definitiva.
* tasa de recuperación.
* índice de dependencia de recuperación.
* índice de continuidad de oferta.
* estudiantes sin oportunidad inmediata.
* cantidad de cursos dependientes.
* tasa de ocupación promedio.
* total estudiantes asignados.
* total estudiantes con nota.

### ds_modelo_clasificacion.csv

Unidad de análisis:

```text
estudiante + curso + periodo
```

Targets:

* `necesito_recuperacion`
* `perdida_definitiva`
* `riesgo_retraso_potencial`
* `riesgo_retraso_potencial_amplio`

Variables predictoras:

* zona ordinaria.
* período académico.
* curso.
* semestre del pensum.
* área académica.
* tasa de ocupación.
* curso abierto en siguiente período.
* cantidad de cursos dependientes.
* nivel de bloqueo curricular.
* curso base.
* curso obligatorio.
* requiere laboratorio.
* componente práctico.

No usar como predictor principal la nota de examen ni la nota total cuando el target sea aprobación, pérdida o recuperación, porque generaría fuga de información.

### ds_reglas_asociacion.csv

Unidad de análisis:

```text
transacciones académicas categorizadas
```

Transformar variables a categorías tipo item:

* `zona_baja`, `zona_media`, `zona_alta`.
* `semestre_1`, `semestre_2`, etc.
* `area_programacion`, `area_matematica`, etc.
* `perdio`, `aprobo`, `recuperacion`.
* `no_abierto_siguiente`.
* `abierto_siguiente`.
* `bloqueo_bajo`, `bloqueo_medio`, `bloqueo_alto`.
* `ocupacion_baja`, `ocupacion_media`, `ocupacion_alta`.
* `riesgo_retraso`.
* `curso_base`.
* `curso_obligatorio`.

## Indicadores académicos

Calcular como mínimo:

### Indicadores de actas

* Tasa de aprobación ordinaria.
* Tasa de pérdida ordinaria.
* Tasa de recuperación.
* Tasa de aprobación por recuperación.
* Tasa de pérdida definitiva.
* Índice de dependencia de recuperación.
* Total de estudiantes con NSP.
* Total de equivalencias aprobadas.

### Indicadores de asignación

* Total de estudiantes asignados.
* Total de estudiantes desasignados.
* Total de estudiantes con nota.
* Diferencia entre asignados y estudiantes con nota.

### Indicadores de oferta

* Cursos abiertos por período.
* Secciones abiertas por período.
* Cupo ofertado por curso y período.
* Tasa de ocupación de cupo.
* Índice de continuidad de oferta.
* Cursos abiertos en S1 pero no en S2.
* Cursos abiertos en S2 pero no en S1.
* Cursos abiertos solo una vez en el año.

### Indicadores de continuidad académica

* Estudiantes que perdieron un curso.
* Estudiantes que perdieron un curso no abierto en el siguiente período.
* Estudiantes que perdieron un curso bloqueante no abierto en el siguiente período.
* Cursos con alta pérdida y baja continuidad.
* Cursos con alta cantidad de dependientes y baja continuidad.

## Análisis Exploratorio de Datos

Generar análisis y gráficos para:

* Matrícula anual 2022-2024.
* Estudiantes inscritos 2024 por cohorte de ingreso.
* Cursos ofertados por período.
* Secciones ofertadas por período.
* Cupo total ofertado por período.
* Top 10 cursos con más estudiantes asignados.
* Top 10 cursos con mayor pérdida definitiva.
* Top 10 cursos con mayor tasa de recuperación.
* Top 10 cursos con mayor cantidad de estudiantes sin oportunidad inmediata.
* Heatmap de cursos vs períodos según apertura.
* Heatmap de cursos vs períodos según tasa de pérdida.
* Distribución de zona por curso.
* Distribución de nota de examen por curso.
* Comparación de resultados por período.

Guardar figuras en:

```text
outputs/figures/eda/
```

Guardar tablas en:

```text
outputs/tables/indicators/
```

## Estadística inferencial

Implementar pruebas cuando los datos lo permitan:

* Chi-cuadrado para asociación entre período y resultado.
* Prueba de proporciones para comparar tasas de pérdida entre períodos.
* Mann-Whitney para comparar distribuciones de notas entre dos grupos.
* Kruskal-Wallis para comparar notas entre más de dos períodos o áreas.
* Spearman para correlación entre tasa de ocupación y tasa de pérdida.
* Intervalos de confianza para tasas principales.

Guardar resultados en:

```text
outputs/tables/statistical_tests/
```

Generar reporte:

```text
outputs/reports/inferencia_estadistica.md
```

## Modelos de clasificación

Implementar tres modelos:

1. Regresión logística.
2. Árbol de decisión.
3. Random Forest.

Targets principales:

* `necesito_recuperacion`
* `perdida_definitiva`
* `riesgo_retraso_potencial`
* `riesgo_retraso_potencial_amplio`

Requisitos:

* Separar train/test.
* Usar validación cruzada cuando sea viable.
* Codificar variables categóricas con OneHotEncoder.
* Escalar variables numéricas para regresión logística.
* Evitar fuga de información.
* Manejar clases desbalanceadas con `class_weight='balanced'` cuando aplique.
* Reportar matriz de confusión.
* Reportar accuracy, precision, recall, F1 y ROC-AUC cuando aplique.
* Guardar importancia de variables para Random Forest.
* Guardar coeficientes interpretables para regresión logística.
* Exportar árbol de decisión como imagen.

Guardar resultados en:

```text
outputs/tables/models/
outputs/figures/models/
outputs/reports/resultados_modelos.md
```

## Clustering de cursos críticos

Implementar clustering sobre `ds_cursos_criticos_clustering.csv`.

Requisitos:

* Escalar variables numéricas.
* Evaluar K entre 2 y 6.
* Usar elbow method.
* Usar silhouette score.
* Seleccionar K justificadamente.
* Generar tabla final con curso, cluster e interpretación.
* Generar gráfico 2D con PCA para visualizar clusters.
* Describir cada cluster de forma académica.

Interpretaciones esperadas:

* Cursos estables.
* Cursos con pérdida alta pero oferta continua.
* Cursos con baja continuidad pero baja pérdida.
* Cursos críticos por pérdida, baja continuidad y bloqueo curricular.

Guardar resultados en:

```text
outputs/tables/models/clustering_cursos.csv
outputs/figures/clusters/
outputs/reports/clustering_cursos.md
```

## Reglas de asociación

Implementar Apriori o FP-Growth sobre `ds_reglas_asociacion.csv`.

Requisitos:

* Generar matriz transaccional.
* Probar diferentes valores de soporte mínimo.
* Calcular soporte, confianza y lift.
* Filtrar reglas con consecuentes relevantes:

  * `riesgo_retraso`
  * `perdio`
  * `recuperacion`
  * `no_abierto_siguiente`
* Ordenar reglas por lift y confianza.
* Eliminar reglas redundantes u obvias si no aportan interpretación.
* Guardar reglas finales en CSV.

Guardar resultados en:

```text
outputs/tables/models/reglas_asociacion.csv
outputs/reports/reglas_asociacion.md
```

## Regresión lineal múltiple

Implementar a nivel agregado curso + período usando `ds_resumen_curso_periodo_2024.csv`.

Variables dependientes posibles:

* tasa de pérdida definitiva.
* tasa de recuperación.
* estudiantes sin oportunidad inmediata.
* tasa de aprobación ordinaria.

Predictores posibles:

* cupo total ofertado.
* estudiantes asignados.
* tasa de ocupación.
* secciones abiertas.
* curso abierto en siguiente período.
* cantidad de cursos dependientes.
* semestre del pensum.
* período académico.

Requisitos:

* Verificar multicolinealidad con VIF cuando sea posible.
* Reportar R² ajustado, MAE y RMSE.
* Graficar observado vs predicho.
* Graficar residuos.
* Interpretar resultados como asociaciones, no causalidad.

Guardar resultados en:

```text
outputs/tables/models/regresion_lineal.csv
outputs/figures/models/
outputs/reports/regresion_lineal.md
```

## Reportes finales

Generar los siguientes reportes en Markdown:

```text
outputs/reports/data_quality_report.md
outputs/reports/resumen_indicadores.md
outputs/reports/inferencia_estadistica.md
outputs/reports/resultados_modelos.md
outputs/reports/clustering_cursos.md
outputs/reports/reglas_asociacion.md
outputs/reports/regresion_lineal.md
outputs/reports/hallazgos_generales.md
```

El reporte `hallazgos_generales.md` debe ser neutral y académico. Debe evitar afirmar causalidad presupuestaria directa.

Usar redacciones como:

* “Se identificó una relación entre la continuidad de oferta y el riesgo de retraso académico potencial.”
* “Los cursos con alta pérdida y sin oferta inmediata posterior representan casos de atención para la planificación académica.”
* “Los resultados permiten documentar patrones académicos observados durante 2024.”

Evitar redacciones como:

* “El presupuesto causó pérdida de cursos.”
* “La falta de docentes provocó retraso.”
* “La universidad afectó directamente a los estudiantes.”
* “Se demuestra causalidad presupuestaria.”

## Privacidad y seguridad

No subir datos reales a repositorios públicos.

Agregar al `.gitignore`:

```gitignore
data/raw/
data/interim/
data/processed/
outputs/
*.csv
*.xlsx
*.xls
*.parquet
.env
__pycache__/
.ipynb_checkpoints/
```

No imprimir identificadores ofuscados en reportes finales.

No generar tablas con registros individuales de estudiantes.

Todos los resultados públicos deben estar agregados por curso, período, área o cluster.

## Stack técnico recomendado

Usar Python.

Dependencias sugeridas:

```text
pandas
numpy
scipy
statsmodels
scikit-learn
mlxtend
matplotlib
openpyxl
jupyter
python-dotenv
```

Evitar dependencias innecesarias.

## Comandos sugeridos

Crear entorno virtual:

```bash
python -m venv .venv
```

Activar entorno:

```bash
source .venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Ejecutar pipeline principal:

```bash
python -m src.data.validate_data
python -m src.features.build_derived_datasets
python -m src.analysis.eda
python -m src.analysis.statistical_tests
python -m src.models.logistic_regression
python -m src.models.decision_tree
python -m src.models.random_forest
python -m src.models.clustering
python -m src.models.association_rules
python -m src.models.linear_regression
```

## Criterios de aceptación

El proyecto estará correctamente implementado cuando:

* Los 10 datasets raw puedan cargarse sin errores.
* Exista un reporte de calidad de datos.
* Se generen todos los datasets derivados en `data/processed/`.
* Se calculen indicadores académicos por curso y período.
* Se generen gráficos EDA principales.
* Se ejecuten pruebas estadísticas básicas.
* Se entrenen modelos de clasificación sin fuga de información.
* Se genere clustering de cursos críticos.
* Se generen reglas de asociación.
* Se ejecute regresión lineal a nivel curso-período.
* Todos los resultados se guarden en `outputs/`.
* Los reportes finales estén redactados de forma neutral.
* No se expongan datos individuales de estudiantes.
* No se realicen afirmaciones causales sobre presupuesto, contratación u horas docentes.

## Resultado esperado

El proyecto debe producir una base documental cuantitativa que permita analizar la oferta académica observada durante 2024, identificar cursos críticos y evidenciar casos donde la pérdida de un curso, combinada con la falta de oferta inmediata posterior y su papel como prerrequisito, representa un riesgo de retraso académico potencial para el estudiante.

La interpretación final debe mantenerse dentro del alcance de los datos disponibles: oferta académica, asignaciones, actas, continuidad de cursos y configuración curricular.
