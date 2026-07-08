# Academic Offer Analysis CUNOC 2024

Proyecto técnico de análisis de datos sobre oferta académica, continuidad curricular y riesgo de retraso académico potencial en estudiantes de Ingeniería en Ciencias y Sistemas del Centro Universitario de Occidente durante 2024.

**Autor:** Eriksson José Hernández López  
**Asesor:** Mtro. Ing. Edwin Estuardo Zapeta Gómez

## Propósito

Este repositorio documenta y reproduce un flujo de análisis descriptivo, estadístico y de minería de datos aplicado a oferta académica, asignaciones y resultados registrados en actas durante 2024. El objetivo es construir una base técnica y documental que permita identificar patrones de continuidad de oferta, pérdida definitiva, recursamiento observable y riesgo de retraso académico potencial.

El análisis no mide presupuesto, montos financieros, contratación, horas docentes, evaluación individual de docentes, encuestas ni datos personales identificables. Los resultados deben interpretarse como hallazgos observados en los registros disponibles, no como afirmaciones causales.

## Lectura rápida: notebooks y reportes

Si solo se desea revisar el análisis sin ejecutar el proyecto completo, los notebooks son la entrada recomendada:

1. [`notebooks/01_validacion_y_calidad_datos.ipynb`](notebooks/01_validacion_y_calidad_datos.ipynb): validación inicial, estructura y calidad de datos.
2. [`notebooks/02_etl_y_datasets_derivados.ipynb`](notebooks/02_etl_y_datasets_derivados.ipynb): limpieza, normalización y construcción de datasets derivados.
3. [`notebooks/03_eda_indicadores_academicos.ipynb`](notebooks/03_eda_indicadores_academicos.ipynb): indicadores, exploración y visualizaciones académicas.
4. [`notebooks/04_analisis_estadistico_y_modelos.ipynb`](notebooks/04_analisis_estadistico_y_modelos.ipynb): inferencia estadística exploratoria y modelos de clasificación.
5. [`notebooks/05_cursos_criticos_y_hallazgos.ipynb`](notebooks/05_cursos_criticos_y_hallazgos.ipynb): clustering, reglas de asociación, regresión agregada y cursos críticos.
6. [`notebooks/06_sintesis_hallazgos_y_recomendaciones.ipynb`](notebooks/06_sintesis_hallazgos_y_recomendaciones.ipynb): síntesis ejecutiva, conclusiones y recomendaciones.

Reportes técnicos generados:

- [`outputs/reports/data_quality_report.md`](outputs/reports/data_quality_report.md)
- [`outputs/reports/datasets_derivados.md`](outputs/reports/datasets_derivados.md)
- [`outputs/reports/resumen_indicadores.md`](outputs/reports/resumen_indicadores.md)
- [`outputs/reports/inferencia_estadistica.md`](outputs/reports/inferencia_estadistica.md)
- [`outputs/reports/resultados_modelos.md`](outputs/reports/resultados_modelos.md)
- [`outputs/reports/clustering_cursos.md`](outputs/reports/clustering_cursos.md)
- [`outputs/reports/reglas_asociacion.md`](outputs/reports/reglas_asociacion.md)
- [`outputs/reports/regresion_lineal.md`](outputs/reports/regresion_lineal.md)

Manuscritos derivados del análisis:

- [`manuscripts/scientific_article.md`](manuscripts/scientific_article.md): ubicación del artículo científico y documentos asociados.
- [`manuscripts/tesis/README.md`](manuscripts/tesis/README.md): ubicación del informe de tesis y trazabilidad del manuscrito.

## Estructura del repositorio

```text
.
├── data/
│   ├── raw/          # datasets de entrada
│   ├── interim/      # datasets normalizados intermedios
│   └── processed/    # datasets analíticos finales
├── docs/             # metodología, decisiones, diccionario y documentación técnica
├── manuscripts/      # artículo científico, tesis y reportes de revisión externos
├── notebooks/        # notebooks narrativos del análisis
├── outputs/
│   ├── figures/      # figuras generadas
│   ├── reports/      # reportes en Markdown
│   └── tables/       # tablas de indicadores, modelos y pruebas
├── scripts/          # generadores auxiliares
├── src/              # código fuente del pipeline analítico
├── requirements.txt
└── run_all.py        # ejecución completa reproducible
```

## Datasets utilizados

Los datasets de entrada se encuentran en [`data/raw/`](data/raw/). El diccionario completo de variables está en [`docs/diccionario_datos.md`](docs/diccionario_datos.md) y la descripción metodológica de datasets está en [`docs/dataset_descriptions.md`](docs/dataset_descriptions.md).

| Dataset | Descripción | Procedencia |
| --- | --- | --- |
| `01_catalogo_cursos_2024.csv` | Catálogo de cursos del pensum analizado. | Generado por el estudiante a partir de datos oficiales del portal de Ingeniería CUNOC y la CICS App. |
| `02_actas_notas_2024_detalle.csv` | Resultados registrados en actas durante 2024. | Provisto por el Departamento de Cómputo. |
| `03_asignaciones_2024.csv` | Asignaciones estudiantiles por curso, período y sección. | Provisto por el Departamento de Cómputo. |
| `04_oferta_academica_2024.csv` | Oferta académica observada por curso, período y sección. | Generado por el estudiante a partir de datos oficiales del portal de Ingeniería CUNOC y la CICS App. |
| `05_malla_prerrequisitos.csv` | Relaciones de prerrequisitos y correquisitos. | Generado por el estudiante a partir de datos oficiales del portal de Ingeniería CUNOC y la CICS App. |
| `06_calendario_academico_2024.csv` | Períodos académicos considerados en 2024. | Generado por el estudiante a partir de datos oficiales del portal de Ingeniería CUNOC y la CICS App. |
| `07_parametros_academicos.csv` | Parámetros de evaluación y estados académicos. | Generado por el estudiante a partir de datos oficiales del portal de Ingeniería CUNOC y la CICS App. |
| `08_configuracion_academica_cursos.csv` | Configuración curricular y académica de cursos. | Generado por el estudiante a partir de datos oficiales del portal de Ingeniería CUNOC y la CICS App. |
| `09_estudiantes_inscritos_2024.csv` | Padrón ofuscado de estudiantes inscritos en 2024. | Provisto por el Departamento de Cómputo. |
| `10_inscritos_sistemas_anual.csv` | Serie anual agregada de estudiantes inscritos. | Generado por el estudiante a partir de datos oficiales del portal de Ingeniería CUNOC y la CICS App. |

## Entorno recomendado

El flujo fue validado con Python 3.12.3.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip check
```

Si el entorno virtual ya existe, se puede usar directamente:

```bash
.venv/bin/pip install -r requirements.txt
.venv/bin/pip check
```

## Reproducción por módulos

Estos comandos permiten ejecutar fases específicas del análisis:

```bash
.venv/bin/python -m src.data.validate_data
.venv/bin/python -m src.data.clean_data
.venv/bin/python -m src.features.build_derived_datasets
.venv/bin/python -m src.analysis.eda
.venv/bin/python -m src.analysis.statistical_tests
.venv/bin/python -m src.models.logistic_regression
.venv/bin/python -m src.models.decision_tree
.venv/bin/python -m src.models.random_forest
.venv/bin/python -m src.models.clustering
.venv/bin/python -m src.models.association_rules
.venv/bin/python -m src.models.linear_regression
```

## Reproducción completa

Para validar el código y regenerar los outputs principales:

```bash
.venv/bin/python -m compileall -q src scripts run_all.py
.venv/bin/python run_all.py
```

El script [`run_all.py`](run_all.py) ejecuta el flujo completo: validación de datos, limpieza, construcción de datasets derivados, EDA, pruebas estadísticas, modelos de clasificación, clustering, reglas de asociación y regresión lineal agregada.

Validación registrada: el flujo completo fue ejecutado exitosamente el 8 de julio de 2026 con Python 3.12.3 y sin conflictos de dependencias reportados por `pip check`.

## Outputs generados

Principales datasets procesados:

- `data/processed/04_oferta_academica_2024_consolidada.csv`
- `data/processed/ds_estudiante_curso_resultado_2024.csv`
- `data/processed/ds_resumen_curso_periodo_2024.csv`
- `data/processed/ds_continuidad_oferta_2024.csv`
- `data/processed/ds_cursos_criticos_clustering.csv`
- `data/processed/ds_modelo_clasificacion.csv`
- `data/processed/ds_reglas_asociacion.csv`

Principales carpetas de resultados:

- `outputs/tables/indicators/`
- `outputs/tables/statistical_tests/`
- `outputs/tables/models/`
- `outputs/figures/eda/`
- `outputs/figures/models/`
- `outputs/figures/clusters/`
- `outputs/reports/`

## Restricciones de uso

- No usar la columna `docente` como variable analítica, de modelado ni de reporte.
- No publicar identificadores individuales de estudiantes.
- No interpretar los modelos como evidencia causal.
- No extender el análisis hacia presupuesto, contratación, horas docentes, encuestas o evaluación individual de docentes.
- Mantener la bifurcación analítica entre área común y área profesional cuando el indicador lo requiera.

## Conclusión

Este repositorio ofrece una ruta reproducible para estudiar la oferta académica y su relación observada con continuidad curricular, recursamiento y riesgo de retraso académico potencial. Los notebooks y reportes permiten revisar los hallazgos sin ejecutar el pipeline, mientras que `run_all.py` permite regenerar el flujo técnico completo desde los datos disponibles.
