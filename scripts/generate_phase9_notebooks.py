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

La validacion inicial establece que el proyecto puede avanzar con una base
institucional consistente, pero tambien muestra donde debe ponerse atencion
antes de interpretar resultados. El catalogo de 90 cursos funciona como marco
para medir oferta observada, cursos no ofertados y continuidad; por eso la
calidad de ese catalogo es central para cualquier comparacion futura. En
contraste, los hallazgos de oferta academica duplicada y campos operativos
vacios no se tratan como errores menores: se documentan porque pueden afectar
conteos de secciones, cupos, cursos aperturados y lectura de continuidad.

Desde una perspectiva de toma de decisiones, esta fase permite separar dos
cosas: problemas que requieren correccion tecnica y valores especiales que
deben conservarse por significado academico. `NSP`, `EQ` y `desasignado` no
son ruido; representan situaciones distintas del avance estudiantil. Si se
eliminaran sin criterio, el analisis perderia capacidad para distinguir entre
no presentarse, aprobar por equivalencia, retirarse administrativamente o tener
un resultado evaluado.

## Conclusiones generales

El valor practico de esta validacion es que evita construir indicadores sobre
supuestos invisibles. Para planificacion academica futura, esto significa que
las decisiones deben apoyarse en datos trazables: cuantos cursos existen en el
catalogo, cuales se ofertaron, cuantos estudiantes aparecen con asignacion y
que tipo de resultado academico se observa. La calidad de datos no resuelve el
problema academico, pero define que tan confiable es la lectura posterior.

La conclusion general es que el repositorio cuenta con datos suficientes para
analizar oferta, asignaciones y resultados 2024, siempre que se mantenga una
lectura agregada, descriptiva y prudente. Esta base permite estudiar diferencias
entre cursos de area comun y cursos profesionales sin exponer casos
individuales ni convertir problemas de registro en afirmaciones academicas no
respaldadas."""
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

La fase de ETL aporta valor porque transforma registros institucionales en
unidades analiticas comparables. El dataset maestro conserva 2879 registros a
nivel estudiante-curso-periodo, mientras que el dataset de clasificacion queda
en 2726 registros al excluir desasignados y variables con fuga de informacion.
Esa separacion es importante: un estudiante desasignado forma parte del flujo
administrativo, pero no debe mezclarse con quien tuvo una evaluacion final
observable. Para decisiones futuras, esta distincion evita sobredimensionar o
distorsionar indicadores de perdida, recuperacion o riesgo.

Los targets tambien quedan definidos con alcance claro. `perdida_definitiva`
aparece en 827 registros modelables, equivalente a 30.34%, y significa que el
ultimo resultado observable no fue aprobado. `riesgo_retraso_potencial` aparece
en 411 registros, equivalente a 15.08%, y agrega continuidad de oferta y
condicion curricular. Esta diferencia ayuda a la toma de decisiones: no toda
perdida implica el mismo nivel de vulnerabilidad academica. Una perdida en un
curso con oferta frecuente no se comporta igual que una perdida en un curso
profesional de baja continuidad.

## Conclusiones generales

La conclusion general es que la base procesada permite analizar el problema con
mas precision que los archivos raw por separado. Para cursos de area comun, la
alta cantidad de registros puede elevar los conteos absolutos de perdida; para
cursos profesionales, la menor continuidad puede convertir una perdida en una
espera academica mas larga dentro de la ventana observada. Por eso el proyecto
no debe priorizar unicamente por volumen, sino por una combinacion de tasa,
continuidad, dependencia curricular y flujo posterior observable.

En terminos de comportamiento esperado, si un estudiante pierde un curso con
oferta posterior observable, tiene mayor posibilidad institucional de intentar
recursarlo dentro del mismo anio. Si pierde un curso sin oferta posterior
observable, especialmente profesional y bloqueante, el comportamiento esperado
es una interrupcion temporal del flujo curricular hasta la siguiente ventana de
oferta. Esta lectura sigue siendo potencial y descriptiva, pero es mucho mas
util para planificacion que un conteo aislado de perdidas."""
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

El EDA muestra que el analisis academico debe combinar conteos, tasas,
continuidad y grupo academico. En 2024, S1 concentra 51 cursos ofertados y 1321
asignaciones, mientras que las escuelas de vacaciones muestran ventanas mucho
mas reducidas. Esto significa que la oportunidad de recursar no se distribuye
de forma homogenea durante el anio. La oferta semestral sostiene la mayor parte
del flujo academico; las vacaciones funcionan como una ventana adicional, pero
no equivalente.

La comparacion entre area comun y area profesional es el hallazgo estructural
mas importante. Area comun registra 1703 estudiantes con acta ordinaria y 497
perdidas definitivas, con tasa de perdida de 29.2% e indice de continuidad
promedio de 47.6%. El area profesional, por su parte, presenta areas con menor
continuidad promedio, como Ciencias de la Computacion con 23.4% y Desarrollo de
Software con 26.6%. Esto cambia la lectura: Matematica Basica 1 puede liderar
en conteo absoluto por volumen, pero cursos profesionales como Introduccion a la
Programacion y Computacion 1 combinan tasa alta, volumen relevante y menor
ventana de recursamiento que muchos cursos de area comun.

## Conclusiones generales

La continuidad de oferta aparece como un eje descriptivo central para entender
recursamiento y riesgo potencial. Despues de una perdida con ventana posterior,
el area comun muestra 333 recursamientos observables de 435 perdidas, equivalente
a 76.6%, y 203 aprobaciones posteriores. En area profesional se observan 85
recursamientos de 319 perdidas, equivalente a 26.6%, con 39 aprobaciones
posteriores. Esta brecha no prueba causalidad, pero si describe un flujo
academico distinto: cuando la oferta posterior es mas limitada, el estudiante
tiene menos oportunidades observables para reincorporarse al curso dentro del
mismo anio.

Para la toma de decisiones, el comportamiento esperado es claro a nivel
agregado: cursos de area comun con oferta mas frecuente tienden a sostener mas
recursamiento observable; cursos profesionales con oferta unica o baja
continuidad tienden a concentrar riesgo de espera academica cuando se pierden.
El proyecto no debe recomendar abrir cursos solo porque tienen perdidas, sino
priorizar aquellos donde coinciden perdida relativa alta, baja continuidad,
condicion bloqueante y bajo flujo posterior."""
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

La fase estadistica y de modelos confirma que varios patrones observados en el
EDA son consistentes con asociaciones medibles. No se observa evidencia
estadistica suficiente de asociacion global entre grupo academico y perdida
definitiva, pero si se observa asociacion entre grupo academico y riesgo de
retraso potencial, recursamiento observable, aprobacion posterior al recursar y
perdidas sin oferta posterior observable. Esta combinacion es importante para
decisiones futuras: el problema no parece estar solamente en perder cursos, sino
en que ocurre despues de perderlos segun continuidad y area academica.

Los modelos de clasificacion ayudan a ordenar senales, no a dictar decisiones.
Para `riesgo_retraso_potencial`, Random Forest obtiene F1 0.535 y recall 0.883,
lo que indica capacidad exploratoria para capturar casos positivos observados,
aunque con limitaciones de precision. Para `perdida_definitiva`, la regresion
logistica logra F1 0.504. Estos valores muestran que los patrones existen, pero
no son tan simples como para resolverlos con una sola variable. La decision
academica debe apoyarse en el conjunto: continuidad, curso, area, semestre,
zona previa disponible y condicion curricular.

## Conclusiones generales

El analisis modelado complementa el EDA al mostrar que el riesgo potencial esta
mas vinculado con el contexto academico posterior que con una lectura global de
perdida. Para un estudiante, la diferencia practica no es solo reprobar, sino
si el curso perdido aparece nuevamente en una ventana cercana y si ese curso
bloquea cursos posteriores. En area comun, la mayor continuidad observada puede
mantener abierto el flujo de recursamiento; en area profesional, la baja
frecuencia puede convertir una perdida en un cuello de botella temporal.

La regresion lineal agregada obtiene R2 0.216, MAE 0.039 y RMSE 0.054. Esto
aporta una lectura complementaria, pero tambien advierte que la perdida
definitiva no se explica completamente con variables agregadas de oferta y
estructura. Por tanto, el valor para la toma de decisiones esta en usar modelos
como sistema de priorizacion y contraste, no como mecanismo automatico. Las
acciones futuras deberian concentrarse en cursos donde coinciden senales
estadisticas, baja continuidad y afectacion curricular potencial."""
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
dependencia curricular, recursamiento observable y perfil de cluster. Por eso
Introduccion a la Programacion y Computacion 1 es relevante no solo por sus 62
perdidas definitivas, sino porque tambien presenta 43.1% de perdida definitiva,
50.0% de continuidad y 25 perdidas sin oferta posterior observable dentro de
2024. En un curso profesional inicial, ese patron puede afectar el ingreso del
estudiante al bloque de cursos posteriores de programacion.

Tambien se observan cursos profesionales con 100% de perdidas sin oferta
posterior observable en la ventana 2024, como Lenguajes Formales, Matematica de
Computo 1, Logica de Sistemas y Sistemas de Bases de Datos 1. La interpretacion
no es que todos los estudiantes abandonen o que nunca puedan aprobar; el punto
es que, dentro del anio observado, la perdida no encontro una nueva oferta
posterior visible. Para planificacion, estos cursos merecen revision porque una
perdida puede traducirse en espera hasta la siguiente apertura.

## Conclusiones generales

La evidencia integrada apoya una hipotesis descriptiva para toma de decisiones:
ampliar o redistribuir ventanas de oferta puede mejorar el flujo observable de
recursamiento en cursos profesionales vulnerables, pero no garantiza aprobacion.
La comparacion con area comun es clave: cuando existen mas ventanas de oferta,
se observa mas recursamiento posterior; cuando la oferta profesional es unica o
limitada, la perdida tiende a convertirse en una espera academica dentro del
anio observado.

El comportamiento esperado para un estudiante que pierde un curso profesional
bloqueante de baja continuidad es distinto al de un estudiante que pierde un
curso de area comun con mayor oferta. En el primer caso, puede quedar limitado
para avanzar en cursos dependientes hasta que el curso vuelva a abrirse. En el
segundo, existe una mayor probabilidad observada de recursamiento cercano,
aunque eso no asegure aprobacion. Por eso, una decision academica futura podria
priorizar cursos profesionales donde coinciden cuatro senales: alta perdida
relativa, baja continuidad, dependencia curricular y bajo recursamiento
observable.

La conclusion final no es abrir todos los cursos ni asumir que mas oferta
resuelve por si sola el problema. La recomendacion analitica es construir una
priorizacion institucional basada en evidencia: identificar cursos profesionales
criticos, revisar su patron de oferta, evaluar si una ventana adicional es
factible y acompanarla con estrategias academicas que atiendan dificultad,
prerrequisitos y recuperacion. Esa es la forma en que el analisis aporta valor
sin convertir patrones observados en afirmaciones causales."""
        ),
    ]
    write_notebook("05_cursos_criticos_y_hallazgos.ipynb", cells)


def build_project_synthesis_notebook() -> None:
    period = read_csv("outputs/tables/indicators/05_indicadores_periodo.csv")
    area = read_csv("outputs/tables/indicators/05_indicadores_area.csv")
    retake = read_csv("outputs/tables/indicators/05_recursamiento_observable.csv")
    top_professional = read_csv("outputs/tables/indicators/05_cursos_profesionales_perdida_relativa.csv")
    without_offer = read_csv("outputs/tables/indicators/05_cursos_profesionales_sin_oportunidad_posterior.csv")
    tests = read_csv("outputs/tables/statistical_tests/06_resumen_pruebas_estadisticas.csv")
    model_metrics = read_csv("outputs/tables/models/07_metricas_modelos.csv")
    cluster_profile = read_csv("outputs/tables/clusters/08_perfil_clusters.csv")
    regression_metrics = read_csv("outputs/tables/regression/08_metricas_regresion.csv")
    eda_catalog = read_csv("outputs/tables/indicators/05_catalogo_figuras_eda.csv")
    model_catalog = read_csv("outputs/tables/models/07_catalogo_figuras_modelos.csv")
    cluster_catalog = read_csv("outputs/tables/clusters/08_catalogo_figuras_clustering.csv")
    regression_catalog = read_csv("outputs/tables/regression/08_catalogo_figuras_regresion.csv")

    period_summary = period[
        [
            "periodo_academico",
            "cursos_ofertados",
            "cursos_no_ofertados",
            "estudiantes_asignados",
            "estudiantes_con_nota",
            "perdida_definitiva",
            "tasa_perdida_definitiva",
            "estudiantes_en_riesgo_retraso_curricular",
        ]
    ].copy()
    period_summary["tasa_perdida_definitiva"] = period_summary["tasa_perdida_definitiva"].map(percent)

    area_summary = area[
        [
            "grupo_area",
            "area_academica",
            "total_cursos_catalogo",
            "indice_continuidad_promedio",
            "estudiantes_con_acta_ordinaria",
            "perdida_definitiva",
            "tasa_perdida_definitiva",
            "estudiantes_en_riesgo_retraso_curricular",
        ]
    ].copy()
    area_summary["indice_continuidad_promedio"] = area_summary["indice_continuidad_promedio"].map(percent)
    area_summary["tasa_perdida_definitiva"] = area_summary["tasa_perdida_definitiva"].map(percent)

    retake_summary = retake[
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
        retake_summary[column] = retake_summary[column].map(percent)

    priority_courses = top_professional[
        [
            "curso_etiqueta",
            "area_academica",
            "estudiantes_con_acta_ordinaria",
            "perdida_definitiva",
            "tasa_perdida_definitiva",
            "indice_continuidad_oferta",
            "cantidad_cursos_dependientes",
            "patron_oferta",
        ]
    ].head(10).copy()
    for column in ["tasa_perdida_definitiva", "indice_continuidad_oferta"]:
        priority_courses[column] = priority_courses[column].map(percent)

    no_later_offer = without_offer[
        [
            "curso_etiqueta",
            "perdidas_definitivas",
            "perdidas_sin_oferta_posterior_2024",
            "tasa_perdidas_sin_oferta_posterior",
            "recursamientos_observables",
            "aprobaciones_posteriores",
        ]
    ].head(10).copy()
    no_later_offer["tasa_perdidas_sin_oferta_posterior"] = no_later_offer[
        "tasa_perdidas_sin_oferta_posterior"
    ].map(percent)

    selected_tests = tests[
        tests["prueba"].isin(
            [
                "grupo_area_vs_perdida_definitiva",
                "grupo_area_vs_riesgo_retraso_potencial",
                "recursamiento_area_comun_vs_profesional",
                "aprobacion_al_recursar_area_comun_vs_profesional",
                "sin_oferta_posterior_area_comun_vs_profesional",
                "continuidad_area_comun_vs_profesional",
            ]
        )
    ][["prueba", "p_value", "conclusion"]].copy()
    selected_tests["p_value"] = selected_tests["p_value"].map(metric)

    best_models = []
    for _, group in model_metrics.groupby("target", observed=False):
        best = group.sort_values(["f1", "recall", "roc_auc"], ascending=False).iloc[0]
        best_models.append(
            {
                "target": best["target_descripcion"],
                "modelo_destacado": best["modelo_nombre"],
                "f1": metric(best["f1"]),
                "recall": metric(best["recall"]),
                "roc_auc": metric(best["roc_auc"]),
            }
        )
    best_models_table = pd.DataFrame(best_models)

    cluster_summary = cluster_profile[
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
        cluster_summary[column] = cluster_summary[column].map(percent)

    regression_summary = regression_metrics[["modelo_nombre", "n_total", "r2", "mae", "rmse"]].copy()
    for column in ["r2", "mae", "rmse"]:
        regression_summary[column] = regression_summary[column].map(metric)

    recommendation_table = pd.DataFrame(
        [
            {
                "prioridad": "Alta",
                "linea_de_accion": "Revisar continuidad de cursos profesionales criticos",
                "evidencia": "Area profesional tiene menor continuidad y 231 perdidas sin oferta posterior observable.",
                "uso_para_decision": "Evaluar ventanas adicionales o redistribucion de oferta en cursos bloqueantes.",
            },
            {
                "prioridad": "Alta",
                "linea_de_accion": "Priorizar cursos con perdida relativa alta y dependencia curricular",
                "evidencia": "IPC1 registra 62 perdidas, 43.1% de perdida definitiva y 25 perdidas sin oferta posterior.",
                "uso_para_decision": "Construir lista corta de cursos para seguimiento academico y planificacion de oferta.",
            },
            {
                "prioridad": "Media",
                "linea_de_accion": "Diferenciar estrategia de area comun y profesional",
                "evidencia": "Area comun observa 76.6% de recursamiento posterior; area profesional 26.6%.",
                "uso_para_decision": "Evitar una politica unica basada solo en conteos absolutos de perdida.",
            },
            {
                "prioridad": "Media",
                "linea_de_accion": "Acompanamiento academico junto con oferta",
                "evidencia": "Mas oferta no garantiza aprobacion; area profesional aprueba 45.9% entre quienes recursan.",
                "uso_para_decision": "Combinar apertura de ventanas con apoyo en cursos de alta dificultad.",
            },
            {
                "prioridad": "Media",
                "linea_de_accion": "Monitorear indicadores anualmente",
                "evidencia": "Los modelos son exploratorios y el R2 de regresion es 0.216.",
                "uso_para_decision": "Usar el pipeline como tablero anual de priorizacion, no como regla automatica.",
            },
        ]
    )

    synthesis_figures = pd.concat(
        [
            eda_catalog[
                eda_catalog["figura"].isin(
                    [
                        "05_oferta_por_grupo_area_periodo.png",
                        "05_recursamiento_y_aprobacion_por_grupo.png",
                        "05_cursos_profesionales_perdida_relativa.png",
                        "05_profesional_perdida_sin_oferta_posterior.png",
                    ]
                )
            ],
            model_catalog[model_catalog["figura"].isin(["07_metricas_modelos.png"])],
            cluster_catalog,
            regression_catalog,
        ],
        ignore_index=True,
    )

    cells = [
        md(
            """# Sintesis de hallazgos y recomendaciones

## Proposito del notebook

Este notebook presenta la sintesis ejecutiva del proyecto `Academic Offer
Analysis CUNOC 2024`. Integra calidad de datos, ETL, indicadores, inferencia,
modelos, clustering, reglas de asociacion y regresion lineal agregada.

Su objetivo no es repetir el procedimiento tecnico, sino responder que se
aprendio, que cursos y patrones merecen atencion, como se interpreta la
diferencia entre area comun y area profesional, y que decisiones futuras puede
informar el analisis.

El enfoque es descriptivo y exploratorio. No se afirma causalidad y no se
presentan diagnosticos individuales."""
        ),
        code(SETUP_CODE),
        md(
            """## Resumen ejecutivo

El proyecto muestra que la perdida academica no debe interpretarse solo como
conteo de estudiantes que no aprobaron. El hallazgo mas importante es que el
riesgo academico potencial depende de la combinacion entre perdida, continuidad
de oferta, area academica y condicion curricular del curso.

Los cursos de area comun suelen tener mas volumen y mayor continuidad. Por eso
aparecen con conteos altos de perdida, pero tambien ofrecen mas ventanas
observables de recursamiento. Los cursos profesionales, en cambio, pueden tener
menor cantidad de registros, pero una perdida en ellos puede ser mas sensible
cuando el curso es bloqueante y no vuelve a ofertarse dentro del mismo anio.

La lectura integrada sugiere una linea de decision: priorizar cursos
profesionales donde coinciden perdida relativa alta, baja continuidad, condicion
bloqueante y bajo recursamiento observable. Esta priorizacion no implica abrir
todos los cursos ni asumir que mas oferta garantiza aprobacion; implica usar
evidencia para decidir donde revisar oferta, acompanamiento y flujo curricular."""
        ),
        md(
            f"""## Evidencia por periodo

{markdown_table(period_summary)}

Interpretacion: los semestres concentran la mayor parte de la oferta y la
actividad academica. S1 registra 51 cursos ofertados y 1321 asignaciones; S2
registra 48 cursos y 1107 asignaciones. Las escuelas de vacaciones tienen una
oferta mucho menor, por lo que funcionan como ventanas complementarias de
recursamiento, no como sustituto equivalente de la oferta semestral.

Conclusion: la planificacion academica debe considerar que el calendario no
ofrece oportunidades homogeneas. Cuando un curso profesional se pierde en una
ventana sin oferta posterior cercana, el estudiante puede enfrentar espera
academica aunque el curso tenga pocos registros absolutos."""
        ),
        md(
            f"""## Comparacion entre area comun y area profesional

{markdown_table(area_summary)}

Interpretacion: area comun concentra 1703 estudiantes con acta ordinaria y 497
perdidas definitivas, con tasa de perdida de 29.2% e indice de continuidad
promedio de 47.6%. En area profesional, Desarrollo de Software muestra 38.9% de
perdida definitiva e indice de continuidad de 26.6%; Ciencias de la Computacion
tiene 31.5% de perdida e indice de continuidad de 23.4%.

Conclusion: el area comun puede dominar rankings por volumen, pero el area
profesional concentra vulnerabilidad por menor continuidad. Para toma de
decisiones, la comparacion correcta no es solo "que curso pierde mas", sino
"que curso combina perdida, baja continuidad y bloqueo curricular"."""
        ),
        md(
            f"""## Flujo posterior observable

{markdown_table(retake_summary)}

Interpretacion: despues de una perdida definitiva con ventana posterior dentro
de 2024, area comun registra 333 recursamientos observables de 435 perdidas,
equivalente a 76.6%. Area profesional registra 85 recursamientos de 319
perdidas, equivalente a 26.6%. Tambien se observa menor aprobacion posterior en
area profesional entre quienes recursan: 45.9% frente a 61.0% en area comun.

Conclusion: el estudiante que pierde un curso profesional de baja continuidad
tiene menos oportunidades observables de reincorporarse al mismo curso dentro
del anio. Esto no prueba causalidad, pero si describe una diferencia relevante
para planificacion academica."""
        ),
        md(
            f"""## Cursos profesionales prioritarios

{markdown_table(priority_courses)}

Interpretacion: Introduccion a la Programacion y Computacion 1 concentra 62
perdidas definitivas, una tasa de perdida de 43.1%, continuidad de 50.0% y
cuatro cursos dependientes. Otros cursos como Bases de Datos 1, Estructura de
Datos, Sistemas Operativos 1 y Lenguajes Formales combinan perdida relativa alta
con continuidad de 25.0%.

Conclusion: estos cursos deben revisarse como candidatos prioritarios porque
pueden afectar la progresion profesional del estudiante. La prioridad no se
deriva solo de la dificultad, sino de la relacion entre perdida, continuidad y
dependencia curricular."""
        ),
        md(
            f"""## Perdidas sin oferta posterior observable

{markdown_table(no_later_offer)}

Interpretacion: varios cursos profesionales muestran 100.0% de perdidas sin
oferta posterior observable dentro de 2024. Esto significa que, en la ventana
analizada, la perdida no tuvo una nueva oportunidad de cursarse posteriormente.
No significa que el estudiante no pueda aprobar en otro anio, sino que el flujo
2024 queda interrumpido para ese curso.

Conclusion: estos cursos son criticos para revisar continuidad porque una
perdida puede convertirse en espera academica. La decision futura podria ser
evaluar si existe espacio para una ventana adicional, una seccion estrategica o
acompanamiento academico antes de la siguiente apertura."""
        ),
        md(
            f"""## Evidencia estadistica y modelos

### Pruebas seleccionadas

{markdown_table(selected_tests)}

### Modelos destacados por target

{markdown_table(best_models_table)}

### Regresion lineal agregada

{markdown_table(regression_summary)}

Interpretacion: las pruebas no muestran evidencia suficiente de asociacion
global entre grupo academico y perdida definitiva, pero si muestran asociacion
con riesgo potencial, recursamiento observable, aprobacion posterior al recursar
y perdida sin oferta posterior. Los modelos ayudan a ordenar senales:
Random Forest destaca en targets de riesgo, mientras que la regresion lineal
agregada muestra capacidad explicativa parcial con R2 0.216.

Conclusion: la evidencia cuantitativa refuerza que la prioridad no debe
centrarse solo en perder cursos. Debe centrarse en que ocurre despues de la
perdida y en que cursos generan mayor vulnerabilidad curricular por baja
continuidad."""
        ),
        md(
            f"""## Perfil de cursos criticos por clustering

{markdown_table(cluster_summary)}

Interpretacion: el clustering identifica un perfil de alta perdida y baja
continuidad profesional con 21 cursos, 90.5% de cursos de area profesional y
154 registros en riesgo potencial curricular. Este perfil resume cursos donde
la perdida se combina con menor continuidad y condicion curricular sensible.

Conclusion: el clustering no crea categorias definitivas, pero ayuda a
priorizar perfiles. Para toma de decisiones, ese cluster puede funcionar como
lista inicial para revisar oferta, dependencia curricular y acompanamiento."""
        ),
        md("## Figuras ejecutivas e interpretacion\n\n" + figure_sections(synthesis_figures)),
        md(
            f"""## Recomendaciones para toma de decisiones

{markdown_table(recommendation_table)}

Estas recomendaciones son descriptivas. No proponen una solucion unica ni
atribuyen causalidad. Su funcion es convertir los hallazgos en preguntas
operativas para planificacion academica."""
        ),
        md(
            """## Lectura del efecto esperado en estudiantes

Desde la perspectiva del estudiante, el efecto esperado no se limita a aprobar
o perder un curso. El punto critico es la continuidad del flujo curricular
despues de una perdida.

En cursos de area comun, la mayor continuidad observada permite mas
recursamiento dentro del mismo anio. Esto no garantiza aprobacion, pero reduce
la probabilidad de que la perdida se convierta inmediatamente en espera
curricular prolongada. En cursos profesionales de baja continuidad, el
estudiante puede quedar temporalmente detenido porque el curso perdido no se
oferta nuevamente en la ventana observada y puede ser prerrequisito o base para
cursos posteriores.

El comportamiento esperado, por tanto, es distinto por grupo. En area comun se
espera mas flujo de recursamiento; en area profesional se espera mayor
vulnerabilidad ante perdida si el curso es bloqueante y tiene oferta limitada.
Esta diferencia justifica que las decisiones futuras no traten todos los cursos
con la misma regla."""
        ),
        md(
            """## Analisis critico

El proyecto aporta evidencia suficiente para construir una priorizacion
academica, pero tambien muestra limites importantes. La perdida definitiva por
si sola no explica todo el problema; tampoco la continuidad de oferta por si
sola garantiza aprobacion. Un curso puede ofertarse nuevamente y aun asi tener
bajo recursamiento o baja aprobacion posterior. Por eso, cualquier decision
debe combinar oferta con apoyo academico, revision de prerrequisitos y lectura
de dificultad propia del curso.

Tambien debe evitarse una lectura simplista de rankings. Los cursos de area
comun pueden aparecer arriba por volumen, mientras que cursos profesionales
pueden ser mas sensibles por continuidad y bloqueo curricular. La decision mas
defendible no es atender solamente el curso con mas perdidas, sino identificar
la interseccion entre tasa alta, baja continuidad, volumen suficiente y
afectacion curricular potencial.

Finalmente, el analisis trabaja con 2024. Esto permite describir el flujo
observable dentro del anio, pero no reconstruye trayectorias academicas
completas. Por eso las conclusiones deben verse como insumo de planificacion y
no como sentencia definitiva sobre estudiantes, cursos o resultados futuros."""
        ),
        md(
            """## Conclusiones del notebook

La sintesis del proyecto muestra que el principal valor analitico esta en
pasar de conteos aislados a criterios de priorizacion. El analisis permite
distinguir cursos con mucha perdida por volumen, cursos con alta perdida
relativa, cursos con baja continuidad y cursos que pueden bloquear el avance
curricular. Esa combinacion es la que aporta valor para decisiones futuras.

La comparacion entre area comun y area profesional sostiene la lectura central:
area comun concentra mas volumen y mas recursamiento observable; area
profesional presenta menor continuidad y, cuando un curso se pierde, puede
generar mayor espera dentro de la ventana 2024. Esta diferencia no prueba
causalidad, pero si es suficientemente consistente para orientar revision de
oferta y seguimiento academico.

El caso de cursos profesionales iniciales y bloqueantes es especialmente
relevante. Introduccion a la Programacion y Computacion 1, Bases de Datos 1,
Estructura de Datos, Sistemas Operativos 1 y Lenguajes Formales aparecen como
cursos donde conviene revisar no solo resultados, sino tambien continuidad,
dependencias y oportunidades reales de recursamiento.

## Conclusiones generales

El proyecto concluye que una estrategia de planificacion academica basada en
evidencia deberia priorizar cursos profesionales donde coinciden cuatro
senales: perdida relativa alta, baja continuidad de oferta, condicion
bloqueante o dependiente y bajo recursamiento observable. Esa priorizacion
puede ayudar a decidir donde evaluar ventanas adicionales, secciones
estrategicas o acompanamiento academico focalizado.

Mas oferta no debe interpretarse como solucion automatica. La evidencia muestra
que ampliar oportunidades puede favorecer el flujo observable de recursamiento,
pero la aprobacion posterior depende tambien de dificultad, preparacion,
prerrequisitos y apoyo academico. Por tanto, la decision futura mas robusta no
es simplemente abrir mas cursos, sino abrir o redistribuir oferta donde el
riesgo curricular sea mayor y acompanarla con acciones academicas.

La conclusion final es que el analisis aporta un marco de decision: usar datos
para identificar cursos vulnerables, diferenciar area comun de area
profesional, medir continuidad y evaluar el flujo posterior despues de la
perdida. Este marco permite discutir decisiones academicas con evidencia,
manteniendo una lectura descriptiva, agregada y metodologicamente prudente."""
        ),
    ]
    write_notebook("06_sintesis_hallazgos_y_recomendaciones.ipynb", cells)


def main() -> None:
    build_quality_notebook()
    build_etl_notebook()
    build_eda_notebook()
    build_stats_models_notebook()
    build_critical_courses_notebook()
    build_project_synthesis_notebook()
    print("Notebooks de Fase 9 generados.")


if __name__ == "__main__":
    main()
