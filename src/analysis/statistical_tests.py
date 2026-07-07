"""Inferencia estadistica para asociaciones academicas observadas."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, kruskal, mannwhitneyu, spearmanr
from statsmodels.stats.proportion import proportion_confint, proportions_ztest

from src.analysis import eda
from src.config.settings import PROJECT_ROOT, REPORTS_DIR, TABLES_DIR
from src.data.utils import ensure_project_directories, safe_divide, save_table, write_text


STATISTICAL_TESTS_DIR = TABLES_DIR / "statistical_tests"
STATISTICAL_REPORT_PATH = REPORTS_DIR / "inferencia_estadistica.md"
ALPHA = 0.05
MIN_COURSE_RESULTS = 10
GROUP_ORDER = (eda.COMMON_AREA_GROUP, eda.PROFESSIONAL_AREA_GROUP)


@dataclass(frozen=True)
class ProportionSpec:
    """Especificacion para comparar dos proporciones."""

    nombre_prueba: str
    pregunta: str
    df: pd.DataFrame
    group_column: str
    outcome_column: str
    positive_label: str
    denominator_filter: str


def _relative_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def _p_value_text(p_value: float) -> str:
    if pd.isna(p_value):
        return "sin p-value"
    if p_value < 0.001:
        return "< 0.001"
    return f"{p_value:.4f}"


def _format_percent(value: Any) -> str:
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return "sin dato"
    return f"{numeric:.1%}"


def _format_number(value: Any) -> str:
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return "0"
    return f"{numeric:,.0f}".replace(",", " ")


def _neutral_conclusion(p_value: float, association_text: str) -> str:
    if pd.isna(p_value):
        return "No se pudo calcular la prueba con los datos disponibles."
    if p_value < ALPHA:
        return f"Se observa evidencia estadistica de asociacion entre {association_text}."
    return f"No se observa evidencia estadistica suficiente de asociacion entre {association_text}."


def _markdown_table(df: pd.DataFrame) -> str:
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


def _contingency_to_text(table: pd.DataFrame) -> str:
    parts = []
    for index, row in table.iterrows():
        values = ", ".join(f"{column}={int(value)}" for column, value in row.items())
        parts.append(f"{index}: {values}")
    return " | ".join(parts)


def _cramers_v(table: pd.DataFrame, chi2_statistic: float) -> float:
    total = table.to_numpy().sum()
    min_dimension = min(table.shape[0] - 1, table.shape[1] - 1)
    if total == 0 or min_dimension <= 0:
        return np.nan
    return float(np.sqrt(chi2_statistic / (total * min_dimension)))


def _binary_table(df: pd.DataFrame, row_column: str, outcome_column: str) -> pd.DataFrame:
    work = df[[row_column, outcome_column]].copy()
    work["_outcome_binario"] = np.where(work[outcome_column].astype(bool), "si", "no")
    table = pd.crosstab(work[row_column], work["_outcome_binario"])
    for value in ("no", "si"):
        if value not in table.columns:
            table[value] = 0
    return table.loc[:, ["no", "si"]]


def load_analysis_inputs() -> dict[str, pd.DataFrame]:
    inputs = eda.load_inputs()
    course_period = inputs["course_period"]
    continuity = inputs["continuity"]
    classification = inputs["classification"]
    student_result = inputs["student_result"]
    course_level = eda.build_course_level_indicators(course_period, continuity)
    retake_events = eda.build_retake_events(student_result)
    retake_by_group, retake_by_area, common_flow, professional_flow, professional_without_offer = (
        eda.build_retake_indicators(student_result)
    )
    retake_flow = pd.concat([common_flow, professional_flow], ignore_index=True)
    course_flow = course_level.merge(
        retake_flow[
            [
                "codigo_curso",
                "perdidas_definitivas",
                "perdidas_con_oferta_posterior_2024",
                "perdidas_sin_oferta_posterior_2024",
                "recursamientos_observables",
                "recursamientos_con_resultado",
                "aprobaciones_posteriores",
                "tasa_recursamiento_observable",
                "tasa_aprobacion_al_recursar",
                "tasa_aprobacion_posterior_sobre_perdidas",
            ]
        ],
        on="codigo_curso",
        how="left",
    )
    return {
        "classification": classification,
        "course_level": course_level,
        "course_flow": course_flow,
        "retake_events": retake_events,
        "retake_by_group": retake_by_group,
        "retake_by_area": retake_by_area,
        "professional_without_offer": professional_without_offer,
    }


def build_chi_square_tests(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    specs = [
        (
            "grupo_area_vs_perdida_definitiva",
            "Existe asociacion entre grupo academico y perdida definitiva?",
            inputs["classification"],
            "grupo_area",
            "perdida_definitiva",
            "grupo academico y perdida definitiva",
        ),
        (
            "grupo_area_vs_riesgo_retraso_potencial",
            "Existe asociacion entre grupo academico y riesgo de retraso potencial?",
            inputs["classification"],
            "grupo_area",
            "riesgo_retraso_potencial",
            "grupo academico y riesgo de retraso academico potencial",
        ),
        (
            "area_academica_vs_perdida_definitiva",
            "Existe asociacion entre area academica especifica y perdida definitiva?",
            inputs["classification"],
            "area_academica",
            "perdida_definitiva",
            "area academica especifica y perdida definitiva",
        ),
        (
            "grupo_area_vs_recursamiento_observable",
            "Existe asociacion entre grupo academico y recursamiento observable posterior?",
            inputs["retake_events"],
            "grupo_area",
            "recursamiento_observable",
            "grupo academico y recursamiento observable posterior",
        ),
        (
            "oferta_posterior_vs_recursamiento_observable",
            "Existe asociacion entre oferta posterior y recursamiento observable?",
            inputs["retake_events"],
            "curso_abierto_en_periodo_posterior_2024",
            "recursamiento_observable",
            "oferta posterior observable y recursamiento observable",
        ),
    ]

    rows = []
    for test_name, question, df, row_column, outcome_column, association_text in specs:
        table = _binary_table(df, row_column, outcome_column)
        can_calculate = bool(
            table.shape[0] >= 2
            and table.shape[1] >= 2
            and (table.sum(axis=0) > 0).all()
            and (table.sum(axis=1) > 0).all()
        )
        if can_calculate:
            chi2_statistic, p_value, degrees_freedom, expected = chi2_contingency(table)
            minimum_expected = float(np.min(expected))
            cramers_v = _cramers_v(table, float(chi2_statistic))
            conclusion = _neutral_conclusion(float(p_value), association_text)
        else:
            chi2_statistic = np.nan
            p_value = np.nan
            degrees_freedom = 0
            minimum_expected = np.nan
            cramers_v = np.nan
            conclusion = "No se pudo calcular chi-cuadrado porque la tabla no tiene variacion suficiente."
        rows.append(
            {
                "prueba": test_name,
                "pregunta": question,
                "variable_filas": row_column,
                "variable_columnas": outcome_column,
                "n": int(table.to_numpy().sum()),
                "chi2": round(float(chi2_statistic), 6) if not pd.isna(chi2_statistic) else np.nan,
                "grados_libertad": int(degrees_freedom),
                "p_value": float(p_value) if not pd.isna(p_value) else np.nan,
                "cramers_v": round(cramers_v, 6) if not pd.isna(cramers_v) else np.nan,
                "frecuencia_esperada_minima": round(minimum_expected, 6) if not pd.isna(minimum_expected) else np.nan,
                "tabla_observada": _contingency_to_text(table),
                "conclusion": conclusion,
            }
        )
    return pd.DataFrame(rows)


def _proportion_counts(df: pd.DataFrame, group_column: str, outcome_column: str) -> dict[str, tuple[int, int, float]]:
    result = {}
    for group in GROUP_ORDER:
        subset = df[df[group_column].eq(group)]
        total = len(subset)
        positives = int(subset[outcome_column].sum()) if total else 0
        result[group] = (positives, total, safe_divide(positives, total))
    return result


def build_proportion_tests(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    recursamiento_con_resultado = inputs["retake_events"][
        inputs["retake_events"]["recursamiento_con_resultado"]
    ].copy()
    specs = [
        ProportionSpec(
            "perdida_definitiva_area_comun_vs_profesional",
            "La proporcion de perdida definitiva difiere entre area comun y area profesional?",
            inputs["classification"],
            "grupo_area",
            "perdida_definitiva",
            "perdida definitiva",
            "registros modelables con resultado final",
        ),
        ProportionSpec(
            "riesgo_retraso_area_comun_vs_profesional",
            "La proporcion de riesgo de retraso potencial difiere entre grupos?",
            inputs["classification"],
            "grupo_area",
            "riesgo_retraso_potencial",
            "riesgo de retraso potencial",
            "registros modelables con resultado final",
        ),
        ProportionSpec(
            "recursamiento_area_comun_vs_profesional",
            "La proporcion de recursamiento observable difiere entre grupos?",
            inputs["retake_events"],
            "grupo_area",
            "recursamiento_observable",
            "recursamiento observable",
            "perdidas definitivas con ventana posterior observable en 2024",
        ),
        ProportionSpec(
            "aprobacion_al_recursar_area_comun_vs_profesional",
            "La proporcion de aprobacion posterior entre quienes recursaron difiere entre grupos?",
            recursamiento_con_resultado,
            "grupo_area",
            "aprobacion_posterior_observable",
            "aprobacion posterior al recursar",
            "recursamientos con resultado posterior observable",
        ),
        ProportionSpec(
            "sin_oferta_posterior_area_comun_vs_profesional",
            "La proporcion de perdidas sin oferta posterior difiere entre grupos?",
            inputs["retake_events"].assign(
                sin_oferta_posterior=~inputs["retake_events"]["curso_abierto_en_periodo_posterior_2024"]
            ),
            "grupo_area",
            "sin_oferta_posterior",
            "perdida sin oferta posterior observable",
            "perdidas definitivas con ventana posterior observable en 2024",
        ),
    ]

    rows = []
    for spec in specs:
        counts = _proportion_counts(spec.df, spec.group_column, spec.outcome_column)
        common_success, common_total, common_rate = counts[eda.COMMON_AREA_GROUP]
        professional_success, professional_total, professional_rate = counts[eda.PROFESSIONAL_AREA_GROUP]
        count = np.array([common_success, professional_success])
        nobs = np.array([common_total, professional_total])

        if np.any(nobs == 0):
            z_statistic = np.nan
            p_value = np.nan
        else:
            z_statistic, p_value = proportions_ztest(count, nobs)

        rows.append(
            {
                "prueba": spec.nombre_prueba,
                "pregunta": spec.pregunta,
                "evento": spec.positive_label,
                "denominador": spec.denominator_filter,
                "exitos_area_comun": common_success,
                "n_area_comun": common_total,
                "proporcion_area_comun": common_rate,
                "exitos_area_profesional": professional_success,
                "n_area_profesional": professional_total,
                "proporcion_area_profesional": professional_rate,
                "diferencia_area_profesional_menos_comun": professional_rate - common_rate,
                "z": float(z_statistic) if not pd.isna(z_statistic) else np.nan,
                "p_value": float(p_value) if not pd.isna(p_value) else np.nan,
                "conclusion": _neutral_conclusion(
                    float(p_value) if not pd.isna(p_value) else np.nan,
                    f"grupo academico y {spec.positive_label}",
                ),
            }
        )
    return pd.DataFrame(rows)


def _mann_whitney_row(
    df: pd.DataFrame,
    variable: str,
    test_name: str,
    question: str,
    association_text: str,
) -> dict[str, Any]:
    common_values = df[df["grupo_area"].eq(eda.COMMON_AREA_GROUP)][variable].dropna()
    professional_values = df[df["grupo_area"].eq(eda.PROFESSIONAL_AREA_GROUP)][variable].dropna()
    statistic, p_value = mannwhitneyu(common_values, professional_values, alternative="two-sided")
    effect_size = 1 - (2 * statistic / (len(common_values) * len(professional_values)))
    return {
        "prueba": test_name,
        "tipo_prueba": "Mann-Whitney U",
        "pregunta": question,
        "variable": variable,
        "grupo_a": eda.COMMON_AREA_GROUP,
        "n_grupo_a": len(common_values),
        "mediana_grupo_a": float(common_values.median()),
        "grupo_b": eda.PROFESSIONAL_AREA_GROUP,
        "n_grupo_b": len(professional_values),
        "mediana_grupo_b": float(professional_values.median()),
        "estadistico": float(statistic),
        "p_value": float(p_value),
        "tamano_efecto_rank_biserial": float(effect_size),
        "conclusion": _neutral_conclusion(float(p_value), association_text),
    }


def _kruskal_row(
    df: pd.DataFrame,
    variable: str,
    group_column: str,
    test_name: str,
    question: str,
    association_text: str,
) -> dict[str, Any]:
    groups = [group[variable].dropna() for _, group in df.groupby(group_column, observed=False)]
    labels = [str(label) for label, _ in df.groupby(group_column, observed=False)]
    valid_groups = [group for group in groups if len(group) > 0]
    statistic, p_value = kruskal(*valid_groups)
    total_n = sum(len(group) for group in valid_groups)
    k = len(valid_groups)
    epsilon_squared = (statistic - k + 1) / (total_n - k) if total_n > k else np.nan
    return {
        "prueba": test_name,
        "tipo_prueba": "Kruskal-Wallis",
        "pregunta": question,
        "variable": variable,
        "grupo": group_column,
        "niveles": "; ".join(labels),
        "n": total_n,
        "estadistico": float(statistic),
        "p_value": float(p_value),
        "epsilon_cuadrado": float(max(epsilon_squared, 0)) if not pd.isna(epsilon_squared) else np.nan,
        "conclusion": _neutral_conclusion(float(p_value), association_text),
    }


def build_nonparametric_tests(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    course_level = inputs["course_level"].copy()
    course_level = course_level[course_level["estudiantes_con_acta_ordinaria"] >= MIN_COURSE_RESULTS].copy()

    rows = [
        _mann_whitney_row(
            course_level,
            "indice_continuidad_oferta",
            "continuidad_area_comun_vs_profesional",
            "La continuidad de oferta difiere entre area comun y area profesional?",
            "grupo academico e indice de continuidad de oferta",
        ),
        _mann_whitney_row(
            course_level,
            "tasa_perdida_definitiva",
            "perdida_relativa_area_comun_vs_profesional",
            "La tasa de perdida definitiva por curso difiere entre grupos?",
            "grupo academico y tasa de perdida definitiva por curso",
        ),
        _mann_whitney_row(
            course_level,
            "rank_criticidad_descriptiva",
            "criticidad_descriptiva_area_comun_vs_profesional",
            "El indicador descriptivo de criticidad difiere entre grupos?",
            "grupo academico y criticidad descriptiva",
        ),
        _kruskal_row(
            course_level,
            "tasa_perdida_definitiva",
            "area_academica",
            "perdida_relativa_por_area_academica",
            "La tasa de perdida definitiva por curso difiere entre areas academicas?",
            "area academica y tasa de perdida definitiva por curso",
        ),
        _kruskal_row(
            course_level,
            "indice_continuidad_oferta",
            "area_academica",
            "continuidad_por_area_academica",
            "La continuidad de oferta difiere entre areas academicas?",
            "area academica e indice de continuidad de oferta",
        ),
    ]
    return pd.DataFrame(rows)


def build_spearman_correlations(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    course_flow = inputs["course_flow"].copy()
    course_flow = course_flow[course_flow["estudiantes_con_acta_ordinaria"] >= MIN_COURSE_RESULTS].copy()
    specs = [
        (
            "continuidad_vs_tasa_perdida",
            "indice_continuidad_oferta",
            "tasa_perdida_definitiva",
            "Se asocia la continuidad de oferta con la tasa de perdida definitiva?",
        ),
        (
            "continuidad_vs_recursamiento",
            "indice_continuidad_oferta",
            "tasa_recursamiento_observable",
            "Se asocia la continuidad de oferta con la tasa de recursamiento observable?",
        ),
        (
            "continuidad_vs_perdidas_sin_oferta_posterior",
            "indice_continuidad_oferta",
            "perdidas_sin_oferta_posterior_2024",
            "Se asocia la continuidad de oferta con perdidas sin oferta posterior?",
        ),
        (
            "dependencias_vs_riesgo_curricular",
            "cantidad_cursos_dependientes",
            "estudiantes_en_riesgo_retraso_curricular",
            "Se asocia la cantidad de cursos dependientes con riesgo curricular observado?",
        ),
    ]

    rows = []
    for test_name, x_column, y_column, question in specs:
        subset = course_flow[[x_column, y_column]].dropna()
        statistic, p_value = spearmanr(subset[x_column], subset[y_column])
        rows.append(
            {
                "prueba": test_name,
                "pregunta": question,
                "variable_x": x_column,
                "variable_y": y_column,
                "n": len(subset),
                "rho_spearman": float(statistic),
                "p_value": float(p_value),
                "conclusion": _neutral_conclusion(
                    float(p_value),
                    f"{x_column} y {y_column}",
                ),
            }
        )
    return pd.DataFrame(rows)


def _confidence_interval_row(
    indicator: str,
    group: str,
    successes: int,
    total: int,
    denominator: str,
) -> dict[str, Any]:
    if total == 0:
        lower, upper = np.nan, np.nan
        proportion = np.nan
    else:
        lower, upper = proportion_confint(successes, total, alpha=ALPHA, method="wilson")
        proportion = safe_divide(successes, total)
    return {
        "indicador": indicator,
        "grupo_area": group,
        "exitos": int(successes),
        "n": int(total),
        "proporcion": proportion,
        "ic_95_inferior": float(lower) if not pd.isna(lower) else np.nan,
        "ic_95_superior": float(upper) if not pd.isna(upper) else np.nan,
        "denominador": denominator,
    }


def build_confidence_intervals(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    classification = inputs["classification"]
    retake_events = inputs["retake_events"]
    retake_with_result = retake_events[retake_events["recursamiento_con_resultado"]]

    for group in GROUP_ORDER:
        classification_group = classification[classification["grupo_area"].eq(group)]
        retake_group = retake_events[retake_events["grupo_area"].eq(group)]
        retake_result_group = retake_with_result[retake_with_result["grupo_area"].eq(group)]

        rows.extend(
            [
                _confidence_interval_row(
                    "perdida_definitiva",
                    group,
                    int(classification_group["perdida_definitiva"].sum()),
                    len(classification_group),
                    "registros modelables con resultado final",
                ),
                _confidence_interval_row(
                    "riesgo_retraso_potencial",
                    group,
                    int(classification_group["riesgo_retraso_potencial"].sum()),
                    len(classification_group),
                    "registros modelables con resultado final",
                ),
                _confidence_interval_row(
                    "recursamiento_observable",
                    group,
                    int(retake_group["recursamiento_observable"].sum()),
                    len(retake_group),
                    "perdidas definitivas con ventana posterior observable en 2024",
                ),
                _confidence_interval_row(
                    "aprobacion_al_recursar",
                    group,
                    int(retake_result_group["aprobacion_posterior_observable"].sum()),
                    len(retake_result_group),
                    "recursamientos con resultado posterior observable",
                ),
            ]
        )
    return pd.DataFrame(rows)


def build_summary_table(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for table_name, df in tables.items():
        if "p_value" not in df.columns:
            continue
        for _, row in df.iterrows():
            rows.append(
                {
                    "fuente": table_name,
                    "prueba": row.get("prueba", ""),
                    "pregunta": row.get("pregunta", ""),
                    "p_value": row.get("p_value", np.nan),
                    "conclusion": row.get("conclusion", ""),
                }
            )
    return pd.DataFrame(rows)


def save_statistical_tables(tables: dict[str, pd.DataFrame]) -> dict[str, Path]:
    saved_paths = {}
    for name, df in tables.items():
        path = STATISTICAL_TESTS_DIR / f"{name}.csv"
        save_table(df, path)
        saved_paths[name] = path
    return saved_paths


def _report_table_inventory(saved_paths: dict[str, Path]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"tabla": name, "ruta": _relative_path(path)}
            for name, path in sorted(saved_paths.items())
        ]
    )


def _main_findings(summary: pd.DataFrame) -> pd.DataFrame:
    columns = ["prueba", "p_value", "conclusion"]
    result = summary[columns].copy()
    result["p_value"] = result["p_value"].map(_p_value_text)
    return result.head(12)


def _confidence_report(confidence_intervals: pd.DataFrame) -> pd.DataFrame:
    result = confidence_intervals.copy()
    for column in ["proporcion", "ic_95_inferior", "ic_95_superior"]:
        result[column] = result[column].map(_format_percent)
    return result


def write_report(
    saved_paths: dict[str, Path],
    summary: pd.DataFrame,
    proportion_tests: pd.DataFrame,
    confidence_intervals: pd.DataFrame,
) -> None:
    significant_count = int((summary["p_value"] < ALPHA).sum())
    total_tests = int(summary["p_value"].notna().sum())
    retake_test = proportion_tests[
        proportion_tests["prueba"].eq("recursamiento_area_comun_vs_profesional")
    ].iloc[0]

    content = f"""# Inferencia estadistica

## Objetivo

Evaluar asociaciones observadas entre area academica, continuidad de oferta,
perdida definitiva, recursamiento observable y riesgo de retraso academico
potencial.

Las pruebas de esta fase no demuestran causalidad. Su funcion es aportar
evidencia estadistica sobre patrones observados en los datasets procesados y
orientar las fases posteriores de modelado y sintesis.

## Tablas generadas

{_markdown_table(_report_table_inventory(saved_paths))}

## Resumen de pruebas

{_markdown_table(_main_findings(summary))}

En total se calcularon {_format_number(total_tests)} pruebas con p-value
interpretable. De ellas, {_format_number(significant_count)} presentan p-value
menor que {_format_percent(ALPHA)}, lo que se reporta como evidencia
estadistica de asociacion observada bajo el alcance del proyecto.

## Intervalos de confianza

{_markdown_table(_confidence_report(confidence_intervals))}

## Lectura vinculada con Fase 5.1

La comparacion de recursamiento observable entre area comun y area profesional
usa como denominador las perdidas definitivas con ventana posterior observable
en 2024. La proporcion estimada para area comun fue
{_format_percent(retake_test['proporcion_area_comun'])}; para area profesional
fue {_format_percent(retake_test['proporcion_area_profesional'])}.

Esta diferencia no debe interpretarse como causalidad. Es evidencia compatible
con la lectura descriptiva de Fase 5.1: la continuidad de oferta puede ampliar
la ventana observable de recursamiento, pero no garantiza aprobacion posterior.

## Limitaciones

- Los p-values se reportan sin correccion por comparaciones multiples; deben
  interpretarse como evidencia exploratoria dentro de esta fase.
- Las pruebas trabajan con registros observados en 2024; no reconstruyen la
  trayectoria academica completa de cada estudiante.
- Los indicadores de recursamiento posterior excluyen perdidas en `V2`, porque
  no existe un periodo posterior dentro de 2024 para observar el flujo.
- La prueba entre oferta posterior observable y recursamiento observable esta
  estructuralmente vinculada con la definicion del indicador; se usa como
  validacion del flujo observado, no como prueba causal independiente.
- Las pruebas por curso usan agregados y pueden verse afectadas por tamanos de
  muestra pequenos.
- No se utiliza `docente`, presupuesto, contratacion, horas docentes ni datos
  personales identificables.
- Los resultados deben leerse como asociaciones observadas, no como mecanismos
  causales demostrados.

## Conclusion

La Fase 6 aporta evidencia estadistica para contrastar los patrones descriptivos
de Fase 5 y Fase 5.1. En particular, permite evaluar si las diferencias entre
area comun y area profesional, continuidad de oferta, perdida definitiva,
recursamiento observable y riesgo potencial son consistentes con asociaciones
observadas en los datos. Estos resultados quedan listos para alimentar modelos
explicativos y analisis de cursos criticos sin afirmar causalidad.
"""
    write_text(STATISTICAL_REPORT_PATH, content)


def main() -> None:
    ensure_project_directories()
    STATISTICAL_TESTS_DIR.mkdir(parents=True, exist_ok=True)

    inputs = load_analysis_inputs()
    chi_square_tests = build_chi_square_tests(inputs)
    proportion_tests = build_proportion_tests(inputs)
    nonparametric_tests = build_nonparametric_tests(inputs)
    spearman_correlations = build_spearman_correlations(inputs)
    confidence_intervals = build_confidence_intervals(inputs)

    preliminary_tables = {
        "06_chi_square_tests": chi_square_tests,
        "06_proportion_tests": proportion_tests,
        "06_nonparametric_tests": nonparametric_tests,
        "06_spearman_correlations": spearman_correlations,
    }
    summary = build_summary_table(preliminary_tables)

    tables = {
        **preliminary_tables,
        "06_confidence_intervals": confidence_intervals,
        "06_resumen_pruebas_estadisticas": summary,
    }
    saved_paths = save_statistical_tables(tables)
    write_report(saved_paths, summary, proportion_tests, confidence_intervals)

    print("Inferencia estadistica completada.")
    print(f"Tablas: {STATISTICAL_TESTS_DIR}")
    print(f"Reporte: {STATISTICAL_REPORT_PATH}")


if __name__ == "__main__":
    main()
