"""Genera notebooks narrativos para Fase 9.

Los notebooks consumen outputs ya generados por el pipeline. No recalculan la
logica analitica de `src/`; funcionan como capa de lectura, interpretacion y
documentacion reproducible.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
TABLES_DIR = OUTPUTS_DIR / "tables"
FIGURES_DIR = OUTPUTS_DIR / "figures"

NOTEBOOK_METADATA = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    },
    "language_info": {
        "codemirror_mode": {"name": "ipython", "version": 3},
        "file_extension": ".py",
        "mimetype": "text/x-python",
        "name": "python",
        "nbconvert_exporter": "python",
        "pygments_lexer": "ipython3",
        "version": "3.12.3",
    },
}

SETUP_CODE = """from pathlib import Path
import pandas as pd

ROOT = Path.cwd()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent

OUTPUTS = ROOT / "outputs"
TABLES = OUTPUTS / "tables"
FIGURES = OUTPUTS / "figures"
REPORTS = OUTPUTS / "reports"

pd.set_option("display.max_columns", 80)
pd.set_option("display.max_colwidth", 120)
"""


def read_csv(relative_path: str) -> pd.DataFrame:
    return pd.read_csv(PROJECT_ROOT / relative_path)


def percent(value: Any) -> str:
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return "sin dato"
    return f"{numeric:.1%}"


def number(value: Any) -> str:
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return "sin dato"
    return f"{numeric:,.0f}".replace(",", " ")


def metric(value: Any) -> str:
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return "sin dato"
    return f"{numeric:.3f}"


def markdown_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    if max_rows is not None:
        df = df.head(max_rows)
    if df.empty:
        return "_Sin registros._"
    display = df.fillna("").astype(str)
    headers = list(display.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in display.iterrows():
        lines.append("| " + " | ".join(row[column].replace("|", "\\|") for column in headers) + " |")
    return "\n".join(lines)


def md(source: str) -> dict[str, Any]:
    return {"cell_type": "markdown", "metadata": {}, "source": source.strip() + "\n"}


def code(source: str) -> dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.strip() + "\n",
    }


def notebook(cells: list[dict[str, Any]]) -> dict[str, Any]:
    normalized_cells = []
    for index, cell in enumerate(cells, start=1):
        normalized = dict(cell)
        normalized["id"] = f"fase9-{index:03d}"
        normalized_cells.append(normalized)
    return {
        "cells": normalized_cells,
        "metadata": NOTEBOOK_METADATA,
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def write_notebook(filename: str, cells: list[dict[str, Any]]) -> None:
    NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)
    path = NOTEBOOKS_DIR / filename
    path.write_text(json.dumps(notebook(cells), ensure_ascii=False, indent=2), encoding="utf-8")


def figure_sections(catalog: pd.DataFrame) -> str:
    sections: list[str] = []
    for _, row in catalog.iterrows():
        figure_path = "../" + str(row["ruta"]).replace("\\", "/")
        sections.append(
            f"""### {row['figura']}

![{row['descripcion']}]({figure_path})

- Pregunta analitica: {row['pregunta_analitica']}
- Descripcion: {row['descripcion']}
- Interpretacion: {row['interpretacion']}
- Conclusion: {row['conclusion']}
- Ruta: `{row['ruta']}`
"""
        )
    return "\n".join(sections)


def build_quality_notebook() -> None:
    profile = read_csv("outputs/tables/01_dataset_profile.csv")
    findings = read_csv("outputs/tables/01_data_quality_findings.csv")
    dataset_summary = (
        profile.groupby("dataset", as_index=False)
        .agg(
            filas=("filas", "max"),
            columnas=("columna", "nunique"),
            valores_vacios=("valores_vacios", "sum"),
            porcentaje_vacios_maximo=("porcentaje_vacios", "max"),
        )
        .sort_values("dataset")
    )
    dataset_summary["porcentaje_vacios_maximo"] = dataset_summary["porcentaje_vacios_maximo"].map(
        lambda value: f"{value:.2f}%"
    )
    findings_display = findings[["severidad", "dataset", "regla", "columna", "hallazgo", "cantidad"]].copy()

    cells = [
        md(
            """# Validacion y calidad de datos

## Objetivo

Revisar la estructura, completitud y hallazgos principales de los datasets raw
que alimentan el analisis academico 2024.

Este notebook es descriptivo. No expone registros individuales y no utiliza
variables de docencia como eje analitico."""
        ),
        code(SETUP_CODE),
        md(
            f"""## Resumen de datasets revisados

{markdown_table(dataset_summary)}

Interpretacion: los 10 datasets raw tienen estructura reconocible y fueron
perfilados antes de iniciar limpieza y construccion de variables. Los datasets
02, 03 y 09 se tratan como provistos por el Departamento de Computo.

Conclusion: el insumo base es suficiente para continuar con ETL, siempre que
los hallazgos de calidad se resuelvan o documenten antes de modelar."""
        ),
        code(
            """perfil = pd.read_csv(TABLES / "01_dataset_profile.csv")
resumen_datasets = (
    perfil.groupby("dataset", as_index=False)
    .agg(filas=("filas", "max"), columnas=("columna", "nunique"), valores_vacios=("valores_vacios", "sum"))
    .sort_values("dataset")
)
resumen_datasets"""
        ),
        md(
            f"""## Hallazgos de calidad

{markdown_table(findings_display)}

Interpretacion: los hallazgos mas relevantes se concentran en duplicados de
oferta academica y valores vacios de atributos operativos. Tambien se conservan
valores especiales como `NSP`, `EQ` y `desasignado`, porque tienen significado
academico o administrativo para fases posteriores.

Conclusion: la calidad inicial no bloquea el analisis, pero requiere decisiones
explicitas de limpieza y conservacion de valores especiales."""
        ),
        code(
            """hallazgos = pd.read_csv(TABLES / "01_data_quality_findings.csv")
hallazgos[["severidad", "dataset", "regla", "columna", "hallazgo", "cantidad"]]"""
        ),
        md(
            """## Hallazgos obtenidos

- Se confirma la existencia de los 10 datasets raw esperados.
- El catalogo contiene 90 cursos vigentes, que luego funcionan como base para
  medir oferta y cursos no ofertados por periodo.
- Los registros especiales se conservan para evitar perder informacion sobre
  equivalencias, no presentados y desasignaciones.
- La oferta academica presenta duplicados de llave que se resuelven en la fase
  de ETL, dejando trazabilidad de la decision.

## Conclusiones del notebook

La validacion inicial establece una base confiable para el analisis porque
identifica estructura, completitud y reglas de calidad antes de transformar los
datos. Los hallazgos no se ocultan: se documentan y se conectan con decisiones
posteriores de ETL.

## Conclusiones generales

El proyecto parte de datos institucionales suficientes para analizar oferta,
asignaciones y resultados de 2024. La lectura debe mantenerse descriptiva,
agregada y metodologicamente prudente, sin inferir causalidad ni exponer casos
individuales."""
        ),
    ]
    write_notebook("01_validacion_y_calidad_datos.ipynb", cells)


def build_etl_notebook() -> None:
    derived = read_csv("outputs/tables/04_resumen_datasets_derivados.csv")
    targets = read_csv("outputs/tables/04_distribucion_targets.csv")
    target_display = targets.copy()
    target_display["porcentaje"] = target_display["porcentaje"].map(lambda value: f"{value:.2f}%")

    cells = [
        md(
            """# ETL y datasets derivados

## Objetivo

Explicar como los datos raw se transforman en datasets analiticos para
indicadores, modelado, clustering, reglas de asociacion y regresion agregada.

La fase conserva trazabilidad: los desasignados permanecen en el dataset
maestro, pero se excluyen del dataset de clasificacion porque no representan un
resultado academico evaluado comparable."""
        ),
        code(SETUP_CODE),
        md(
            f"""## Datasets derivados generados

{markdown_table(derived)}

Interpretacion: cada dataset derivado tiene una unidad analitica distinta. Esto
evita mezclar niveles de analisis: estudiante-curso-periodo, curso-periodo,
curso anual, transaccion o registro modelable.

Conclusion: la arquitectura de datos permite analizar el problema desde varios
angulos sin duplicar reglas de negocio en notebooks."""
        ),
        code(
            """datasets_derivados = pd.read_csv(TABLES / "04_resumen_datasets_derivados.csv")
datasets_derivados"""
        ),
        md(
            f"""## Distribucion de targets

{markdown_table(target_display)}

Interpretacion: `perdida_definitiva` representa que el ultimo resultado
observable no fue aprobado; no significa necesariamente ausencia de recuperacion.
Los targets de riesgo combinan perdida observada con continuidad de oferta y
condicion curricular, por lo que deben leerse como riesgo potencial.

Conclusion: las clases positivas no tienen la misma prevalencia. Por eso las
fases de modelado usan metricas como precision, recall, F1 y ROC-AUC, no solo
accuracy."""
        ),
        code(
            """targets = pd.read_csv(TABLES / "04_distribucion_targets.csv")
targets"""
        ),
        md(
            """## Decisiones metodologicas relevantes

- El dataset maestro parte de asignaciones para conservar desasignaciones y
  cruzar resultados de actas cuando existen.
- Los desasignados se preservan para trazabilidad, pero se excluyen del dataset
  de clasificacion.
- La columna de docencia no se utiliza como variable analitica ni de modelado.
- Las variables con fuga de informacion, como notas finales y resultado final,
  se excluyen de los predictores.
- Los datasets 02, 03 y 09 se describen como provistos por el Departamento de
  Computo.

## Hallazgos obtenidos

- Se generaron seis datasets procesados principales para cubrir indicadores,
  clasificacion, clustering y reglas de asociacion.
- El dataset de clasificacion queda con 2726 registros modelables.
- La perdida definitiva observada aparece en 827 registros modelables, que
  equivalen a 30.34% del dataset de clasificacion.
- El riesgo de retraso academico potencial aparece en 411 registros, equivalente
  a 15.08%.

## Conclusiones del notebook

La fase de ETL convierte archivos institucionales en datasets analiticos con
unidades claras y decisiones explicitas. Esto reduce ambiguedad al interpretar
indicadores, pruebas estadisticas y modelos.

## Conclusiones generales

El proyecto cuenta con una base procesada reproducible. Las variables objetivo
son utiles para priorizar patrones academicos, pero no deben interpretarse como
diagnosticos individuales ni como evidencia causal."""
        ),
    ]
    write_notebook("02_etl_y_datasets_derivados.ipynb", cells)


def build_eda_notebook() -> None:
    period = read_csv("outputs/tables/indicators/05_indicadores_periodo.csv")
    area = read_csv("outputs/tables/indicators/05_indicadores_area.csv")
    retake = read_csv("outputs/tables/indicators/05_recursamiento_observable.csv")
    top_professional = read_csv("outputs/tables/indicators/05_cursos_profesionales_perdida_relativa.csv")
    catalog = read_csv("outputs/tables/indicators/05_catalogo_figuras_eda.csv")

    period_display = period[
        [
            "periodo_academico",
            "cursos_ofertados",
            "cursos_no_ofertados",
            "estudiantes_asignados",
            "estudiantes_con_nota",
            "tasa_perdida_definitiva",
            "estudiantes_en_riesgo_retraso_curricular",
        ]
    ].copy()
    period_display["tasa_perdida_definitiva"] = period_display["tasa_perdida_definitiva"].map(percent)

    area_display = area[
        [
            "grupo_area",
            "area_academica",
            "total_cursos_catalogo",
            "estudiantes_con_acta_ordinaria",
            "perdida_definitiva",
            "tasa_perdida_definitiva",
            "indice_continuidad_promedio",
        ]
    ].copy()
    area_display["tasa_perdida_definitiva"] = area_display["tasa_perdida_definitiva"].map(percent)
    area_display["indice_continuidad_promedio"] = area_display["indice_continuidad_promedio"].map(percent)

    retake_display = retake[
        [
            "grupo_area",
            "perdidas_definitivas",
            "perdidas_con_oferta_posterior_2024",
            "perdidas_sin_oferta_posterior_2024",
            "recursamientos_observables",
            "aprobaciones_posteriores",
            "tasa_recursamiento_observable",
            "tasa_aprobacion_al_recursar",
        ]
    ].copy()
    for column in ["tasa_recursamiento_observable", "tasa_aprobacion_al_recursar"]:
        retake_display[column] = retake_display[column].map(percent)

    top_display = top_professional[
        [
            "curso_etiqueta",
            "estudiantes_con_acta_ordinaria",
            "perdida_definitiva",
            "tasa_perdida_definitiva",
            "indice_continuidad_oferta",
            "patron_oferta",
        ]
    ].copy()
    top_display["tasa_perdida_definitiva"] = top_display["tasa_perdida_definitiva"].map(percent)
    top_display["indice_continuidad_oferta"] = top_display["indice_continuidad_oferta"].map(percent)

    cells = [
        md(
            """# EDA e indicadores academicos

## Objetivo

Describir oferta, asignaciones, resultados, continuidad y flujo posterior
observable durante 2024.

El analisis separa `Area comun` y `Area profesional` cuando la comparacion lo
requiere, porque los cursos de area comun suelen tener mayor volumen y mayor
continuidad de oferta."""
        ),
        code(SETUP_CODE),
        md(
            f"""## Indicadores por periodo

{markdown_table(period_display)}

Interpretacion: los periodos semestrales concentran mayor oferta y volumen de
asignaciones. Las escuelas de vacaciones tienen menor numero de cursos
ofertados y, por tanto, deben interpretarse como ventanas complementarias.

Conclusion: la oferta observada no es uniforme durante el anio; esa diferencia
es clave para leer perdida, recursamiento y riesgo potencial."""
        ),
        code(
            """indicadores_periodo = pd.read_csv(TABLES / "indicators" / "05_indicadores_periodo.csv")
indicadores_periodo"""
        ),
        md(
            f"""## Comparacion por area

{markdown_table(area_display)}

Interpretacion: el area comun concentra mayor volumen de registros, mientras
que las areas profesionales muestran menor continuidad promedio y deben
analizarse con tasas y no solo con conteos absolutos.

Conclusion: comparar Matematica Basica 1 con cursos profesionales solo por
conteo puede distorsionar la lectura. Para cursos profesionales importan tambien
la tasa de perdida y la continuidad de oferta."""
        ),
        md(
            f"""## Recursamiento observable

{markdown_table(retake_display)}

Interpretacion: despues de una perdida definitiva con ventana posterior en
2024, el area comun muestra mayor recursamiento observable que el area
profesional. La aprobacion posterior tambien se reporta solo de forma agregada.

Conclusion: mayor continuidad no asegura aprobacion, pero si puede ampliar la
ventana observable para volver a cursar."""
        ),
        md(
            f"""## Cursos profesionales con mayor perdida relativa

{markdown_table(top_display, max_rows=10)}

Interpretacion: este ranking usa tasa de perdida y continuidad, no solo volumen.
Por eso resalta cursos profesionales vulnerables aunque no tengan tantos
registros como cursos masivos de area comun.

Conclusion: los cursos profesionales con oferta unica o baja continuidad deben
priorizarse en la lectura de riesgo academico potencial."""
        ),
        md("## Figuras generadas e interpretacion\n\n" + figure_sections(catalog)),
        code(
            """catalogo_figuras = pd.read_csv(TABLES / "indicators" / "05_catalogo_figuras_eda.csv")
catalogo_figuras[["figura", "pregunta_analitica", "ruta"]]"""
        ),
        md(
            """## Hallazgos obtenidos

- S1 concentra 51 cursos ofertados y 1321 asignaciones.
- Los cursos no ofertados se calculan contra el catalogo completo de 90 cursos;
  no equivalen automaticamente a cursos cancelados.
- Area comun presenta mayor volumen, pero area profesional muestra menor
  continuidad promedio en varias areas.
- En cursos profesionales, Introduccion a la Programacion y Computacion 1
  aparece como curso relevante por tasa, volumen y continuidad observada.
- El flujo posterior observable muestra diferencias fuertes entre area comun y
  area profesional.

## Conclusiones del notebook

El EDA muestra que la lectura academica debe combinar conteos, tasas,
continuidad y grupo academico. Los cursos de area comun y area profesional no
deben analizarse como si tuvieran la misma frecuencia de oferta ni el mismo
volumen de registros.

## Conclusiones generales

La continuidad de oferta aparece como un eje descriptivo central para entender
recursamiento y riesgo potencial. Aun asi, el analisis no demuestra causalidad:
describe patrones observados que orientan preguntas para planificacion
academica."""
        ),
    ]
    write_notebook("03_eda_indicadores_academicos.ipynb", cells)


def build_stats_models_notebook() -> None:
    tests = read_csv("outputs/tables/statistical_tests/06_resumen_pruebas_estadisticas.csv")
    metrics_df = read_csv("outputs/tables/models/07_metricas_modelos.csv")
    model_catalog = read_csv("outputs/tables/models/07_catalogo_figuras_modelos.csv")
    regression_metrics = read_csv("outputs/tables/regression/08_metricas_regresion.csv")
    regression_coefficients = read_csv("outputs/tables/regression/08_coeficientes_regresion.csv")
    regression_catalog = read_csv("outputs/tables/regression/08_catalogo_figuras_regresion.csv")

    tests_display = tests[["prueba", "p_value", "conclusion"]].head(12).copy()
    tests_display["p_value"] = tests_display["p_value"].map(metric)

    best_models = []
    for target, group in metrics_df.groupby("target", observed=False):
        best = group.sort_values(["f1", "recall", "roc_auc"], ascending=False).iloc[0]
        best_models.append(
            {
                "target": best["target_descripcion"],
                "modelo_mejor_f1": best["modelo_nombre"],
                "f1": metric(best["f1"]),
                "recall": metric(best["recall"]),
                "roc_auc": metric(best["roc_auc"]),
            }
        )
    best_display = pd.DataFrame(best_models)

    regression_display = regression_metrics[["modelo_nombre", "n_total", "n_test", "r2", "mae", "rmse"]].copy()
    for column in ["r2", "mae", "rmse"]:
        regression_display[column] = regression_display[column].map(metric)

    coeff_display = regression_coefficients[["variable", "variable_transformada", "coeficiente"]].head(10).copy()
    coeff_display["coeficiente"] = coeff_display["coeficiente"].map(metric)
    combined_catalog = pd.concat([model_catalog, regression_catalog], ignore_index=True)

    cells = [
        md(
            """# Analisis estadistico y modelos

## Objetivo

Reunir la inferencia estadistica exploratoria, los modelos de clasificacion y
la regresion lineal agregada.

Todas las lecturas son descriptivas o asociativas. No se interpretan como
causalidad ni como diagnostico individual."""
        ),
        code(SETUP_CODE),
        md(
            f"""## Resumen de pruebas estadisticas

{markdown_table(tests_display)}

Interpretacion: varias pruebas muestran asociacion observada entre grupo
academico, continuidad, recursamiento y riesgo potencial. No se observa
evidencia suficiente de asociacion global entre grupo academico y perdida
definitiva en la prueba principal.

Conclusion: la inferencia respalda diferencias observadas en continuidad y
flujo posterior, pero no convierte esas diferencias en explicaciones causales."""
        ),
        code(
            """pruebas = pd.read_csv(TABLES / "statistical_tests" / "06_resumen_pruebas_estadisticas.csv")
pruebas.head(12)"""
        ),
        md(
            f"""## Modelos destacados por target

{markdown_table(best_display)}

Interpretacion: los mejores modelos por F1 varian segun target. Esto indica que
ningun algoritmo debe tratarse como solucion unica; cada target tiene
prevalencia y dificultad distinta.

Conclusion: los modelos sirven para comparar patrones predictivos exploratorios
y orientar variables relevantes, no para tomar decisiones individuales."""
        ),
        code(
            """metricas_modelos = pd.read_csv(TABLES / "models" / "07_metricas_modelos.csv")
metricas_modelos"""
        ),
        md(
            f"""## Regresion lineal agregada

{markdown_table(regression_display)}

### Coeficientes destacados

{markdown_table(coeff_display)}

Interpretacion: la regresion trabaja a nivel curso-periodo y estima la tasa de
perdida definitiva con variables agregadas de oferta, volumen, area y
continuidad. El R2 de prueba es moderado-bajo, por lo que el modelo debe leerse
como complemento descriptivo.

Conclusion: la regresion aporta una lectura de asociacion agregada, pero no
sustituye el analisis por curso ni prueba mecanismos causales."""
        ),
        md("## Figuras generadas e interpretacion\n\n" + figure_sections(combined_catalog)),
        md(
            """## Hallazgos obtenidos

- Se observa asociacion entre grupo academico y riesgo de retraso academico
  potencial.
- Se observa asociacion entre grupo academico y recursamiento observable.
- Los modelos de clasificacion logran mejores lecturas cuando se revisa F1,
  recall y ROC-AUC en conjunto.
- Random Forest obtiene el mayor F1 observado para los targets de riesgo, pero
  las importancias se interpretan solo como orientacion exploratoria.
- La regresion lineal agregada tiene R2 de prueba 0.216, por lo que resume parte
  del patron, pero no todo el comportamiento observado.

## Conclusiones del notebook

La fase estadistica y de modelos confirma que existen patrones observados
coherentes entre continuidad, grupo academico, recursamiento y riesgo potencial.
La evidencia es util para priorizar cursos y preguntas, no para afirmar causas.

## Conclusiones generales

El analisis modelado complementa el EDA: ayuda a ordenar senales, medir
asociaciones y comparar algoritmos. La interpretacion final debe permanecer
agregada, academica y prudente."""
        ),
    ]
    write_notebook("04_analisis_estadistico_y_modelos.ipynb", cells)


def build_critical_courses_notebook() -> None:
    top_professional = read_csv("outputs/tables/indicators/05_cursos_profesionales_perdida_relativa.csv")
    without_offer = read_csv("outputs/tables/indicators/05_cursos_profesionales_sin_oportunidad_posterior.csv")
    cluster_profile = read_csv("outputs/tables/clusters/08_perfil_clusters.csv")
    cluster_catalog = read_csv("outputs/tables/clusters/08_catalogo_figuras_clustering.csv")
    rules = read_csv("outputs/tables/association_rules/08_reglas_asociacion.csv")

    top_display = top_professional[
        [
            "curso_etiqueta",
            "estudiantes_con_acta_ordinaria",
            "perdida_definitiva",
            "tasa_perdida_definitiva",
            "indice_continuidad_oferta",
            "patron_oferta",
        ]
    ].head(10).copy()
    for column in ["tasa_perdida_definitiva", "indice_continuidad_oferta"]:
        top_display[column] = top_display[column].map(percent)

    without_display = without_offer[
        [
            "curso_etiqueta",
            "perdidas_definitivas",
            "perdidas_sin_oferta_posterior_2024",
            "tasa_perdidas_sin_oferta_posterior",
            "recursamientos_observables",
            "aprobaciones_posteriores",
        ]
    ].head(12).copy()
    without_display["tasa_perdidas_sin_oferta_posterior"] = without_display[
        "tasa_perdidas_sin_oferta_posterior"
    ].map(percent)

    cluster_display = cluster_profile[
        [
            "cluster",
            "etiqueta_descriptiva",
            "cursos",
            "tasa_perdida_definitiva_2024_media",
            "indice_continuidad_oferta_media",
            "proporcion_area_profesional",
            "estudiantes_en_riesgo_retraso_curricular_2024",
        ]
    ].copy()
    for column in [
        "tasa_perdida_definitiva_2024_media",
        "indice_continuidad_oferta_media",
        "proporcion_area_profesional",
    ]:
        cluster_display[column] = cluster_display[column].map(percent)

    rules_display = rules[["antecedente", "consecuente", "soporte", "confianza", "lift"]].head(12).copy()
    for column in ["soporte", "confianza", "lift"]:
        rules_display[column] = rules_display[column].map(metric)

    cells = [
        md(
            """# Cursos criticos y hallazgos integrados

## Objetivo

Integrar rankings de cursos profesionales, flujo posterior observable,
clustering de cursos criticos y reglas de asociacion.

Este notebook prioriza cursos y perfiles desde una lectura descriptiva. No
presenta categorias definitivas ni afirmaciones causales."""
        ),
        code(SETUP_CODE),
        md(
            f"""## Cursos profesionales con mayor perdida relativa

{markdown_table(top_display)}

Interpretacion: estos cursos combinan perdida relativa alta con informacion de
continuidad. El ranking evita que los cursos masivos de area comun oculten
vulnerabilidades propias del area profesional.

Conclusion: la priorizacion debe revisar tasa, volumen y continuidad de forma
conjunta."""
        ),
        md(
            f"""## Cursos profesionales con perdida y sin oferta posterior observable

{markdown_table(without_display)}

Interpretacion: estos cursos acumulan perdidas definitivas en ventanas donde no
se observa oferta posterior dentro de 2024. Esto reduce la oportunidad
observable de recursamiento en el mismo anio.

Conclusion: estos cursos son candidatos fuertes para discutir continuidad de
oferta, especialmente cuando ademas tienen dependencia curricular."""
        ),
        md(
            f"""## Perfil de clusters

{markdown_table(cluster_display)}

Interpretacion: el clustering agrupa cursos por perfiles de perdida,
recuperacion, continuidad, volumen y bloqueo curricular. El cluster de alta
perdida y baja continuidad profesional concentra cursos con senales academicas
relevantes.

Conclusion: los clusters ayudan a ordenar cursos criticos, pero no reemplazan
la revision academica por curso."""
        ),
        md("## Figuras de clustering e interpretacion\n\n" + figure_sections(cluster_catalog)),
        md(
            f"""## Reglas de asociacion principales

{markdown_table(rules_display)}

Interpretacion: las reglas muestran coocurrencias frecuentes entre condiciones
academicas. Por ejemplo, ciertas areas o combinaciones curriculares aparecen
junto con ausencia de oferta posterior observada.

Conclusion: las reglas no explican por que ocurre un patron; sirven para
identificar combinaciones que merecen revision."""
        ),
        code(
            """reglas = pd.read_csv(TABLES / "association_rules" / "08_reglas_asociacion.csv")
reglas.head(12)"""
        ),
        md(
            """## Hallazgos obtenidos

- Introduccion a la Programacion y Computacion 1 aparece como curso profesional
  relevante por volumen, tasa de perdida y flujo posterior.
- Cursos como Lenguajes Formales, Matematica de Computo 1, Logica de Sistemas y
  Sistemas de Bases de Datos 1 aparecen con perdidas sin oferta posterior
  observable dentro de 2024.
- El clustering identifica un perfil de alta perdida y baja continuidad
  profesional con 21 cursos.
- Las reglas de asociacion refuerzan la lectura de coocurrencias con ausencia
  de oferta posterior, especialmente en condiciones curriculares especificas.

## Conclusiones del notebook

Los cursos criticos no deben definirse solo por el mayor conteo absoluto de
perdidas. La lectura mas util combina tasa, continuidad, area academica,
dependencia curricular, recursamiento observable y perfil de cluster.

## Conclusiones generales

La evidencia integrada apoya una hipotesis descriptiva: ampliar ventanas de
oferta puede favorecer el flujo observable de recursamiento, especialmente en
cursos profesionales. Sin embargo, mas oferta no garantiza aprobacion; por eso
las decisiones deben considerar acompanamiento academico, dificultad del curso y
continuidad curricular, siempre sin afirmar causalidad."""
        ),
    ]
    write_notebook("05_cursos_criticos_y_hallazgos.ipynb", cells)


def main() -> None:
    build_quality_notebook()
    build_etl_notebook()
    build_eda_notebook()
    build_stats_models_notebook()
    build_critical_courses_notebook()
    print("Notebooks de Fase 9 generados.")


if __name__ == "__main__":
    main()
