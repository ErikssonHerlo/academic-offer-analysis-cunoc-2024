"""Indicadores y analisis exploratorio de la oferta academica 2024."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.config.settings import (
    FIGURES_DIR,
    PERIOD_LABELS,
    PERIOD_ORDER,
    PROCESSED_DATA_DIR,
    PROJECT_ROOT,
    REPORTS_DIR,
    RESULT_APPROVED,
    TABLES_DIR,
    YES_VALUE,
)
from src.data.utils import ensure_project_directories, safe_divide, save_table, write_text
from src.visualization.plots_eda import (
    plot_approval_distribution_by_semester,
    plot_assignments_by_period,
    plot_loss_vs_continuity,
    plot_offer_by_area_group_period,
    plot_offer_by_period,
    plot_offer_heatmap,
    plot_professional_critical_courses,
    plot_professional_loss_without_later_offer,
    plot_retake_flow_by_area_group,
    plot_risk_by_area,
    plot_top_definitive_loss,
)


COURSE_PERIOD_PATH = PROCESSED_DATA_DIR / "ds_resumen_curso_periodo_2024.csv"
CONTINUITY_PATH = PROCESSED_DATA_DIR / "ds_continuidad_oferta_2024.csv"
CLASSIFICATION_PATH = PROCESSED_DATA_DIR / "ds_modelo_clasificacion.csv"
STUDENT_RESULT_PATH = PROCESSED_DATA_DIR / "ds_estudiante_curso_resultado_2024.csv"

INDICATORS_DIR = TABLES_DIR / "indicators"
EDA_FIGURES_DIR = FIGURES_DIR / "eda"
EDA_REPORT_PATH = REPORTS_DIR / "resumen_indicadores.md"

TOP_COURSES_LIMIT = 10
LOW_CONTINUITY_THRESHOLD = 0.50
MIN_RESULTS_FOR_RATE_RANKING = 10
TOP_FLOW_COURSES_LIMIT = 12
COMMON_AREA_NAME = "Ciencias Basicas y Complementarias"
COMMON_AREA_GROUP = "Area comun"
PROFESSIONAL_AREA_GROUP = "Area profesional"
PERCENT_COLUMNS = (
    "tasa_ocupacion_cupo",
    "tasa_aprobacion_ordinaria",
    "tasa_perdida_ordinaria",
    "tasa_recuperacion",
    "tasa_aprobacion_recuperacion",
    "tasa_perdida_definitiva",
    "indice_dependencia_recuperacion",
    "indice_continuidad_oferta",
    "tasa_perdida_definitiva_2024",
    "tasa_recuperacion_2024",
    "tasa_ocupacion_promedio_2024",
)


@dataclass(frozen=True)
class FigureRecord:
    """Metadatos interpretativos de una figura EDA."""

    figura: str
    pregunta_analitica: str
    descripcion: str
    interpretacion: str
    conclusion: str
    ruta: Path


def _read_processed(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def _relative_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def _period_label(period: str) -> str:
    return PERIOD_LABELS.get(period, period)


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


def _course_label(df: pd.DataFrame) -> pd.Series:
    return df["codigo_curso"].astype(str) + " - " + df["nombre_curso"].astype(str)


def _sort_periods(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["periodo_academico"] = pd.Categorical(
        result["periodo_academico"],
        categories=list(PERIOD_ORDER),
        ordered=True,
    )
    return result.sort_values("periodo_academico").reset_index(drop=True)


def _coerce_numeric(df: pd.DataFrame, columns: tuple[str, ...] | list[str]) -> pd.DataFrame:
    result = df.copy()
    for column in columns:
        if column in result.columns:
            result[column] = pd.to_numeric(result[column], errors="coerce")
    return result


def _as_bool(series: pd.Series) -> pd.Series:
    normalized = series.astype(str).str.strip().str.lower()
    return normalized.isin({"true", "1", "si", "sí", "yes"})


def _add_area_group(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["grupo_area"] = result["area_academica"].where(
        result["area_academica"].eq(COMMON_AREA_NAME),
        PROFESSIONAL_AREA_GROUP,
    )
    result["grupo_area"] = result["grupo_area"].replace({COMMON_AREA_NAME: COMMON_AREA_GROUP})
    return result


def load_inputs() -> dict[str, pd.DataFrame]:
    course_period = _read_processed(COURSE_PERIOD_PATH)
    continuity = _read_processed(CONTINUITY_PATH)
    classification = _read_processed(CLASSIFICATION_PATH)
    student_result = _read_processed(STUDENT_RESULT_PATH)
    return {
        "course_period": prepare_course_period(course_period),
        "continuity": prepare_continuity(continuity),
        "classification": prepare_classification(classification),
        "student_result": prepare_student_result(student_result),
    }


def prepare_course_period(df: pd.DataFrame) -> pd.DataFrame:
    numeric_columns = [
        "orden_periodo",
        "semestre_pensum",
        "cantidad_cursos_dependientes",
        "secciones_abiertas",
        "cupo_total_ofertado",
        "estudiantes_asignados",
        "estudiantes_desasignados",
        "estudiantes_con_nota",
        "estudiantes_con_acta_ordinaria",
        "aprobados_ordinario",
        "reprobados_ordinario",
        "estudiantes_recuperacion",
        "aprobados_recuperacion",
        "perdida_definitiva",
        "nsp_total",
        "equivalencias_total",
        "estudiantes_sin_oportunidad_inmediata",
        "estudiantes_en_riesgo_retraso_curricular",
        *PERCENT_COLUMNS,
    ]
    result = _coerce_numeric(df, numeric_columns)
    return _sort_periods(_add_area_group(result))


def prepare_continuity(df: pd.DataFrame) -> pd.DataFrame:
    numeric_columns = [
        "semestre_pensum",
        "cantidad_cursos_dependientes",
        "cantidad_periodos_abierto",
        "total_estudiantes_asignados_2024",
        "total_estudiantes_con_nota_2024",
        "total_perdida_definitiva_2024",
        "total_recuperacion_2024",
        "estudiantes_sin_oportunidad_inmediata_2024",
        "estudiantes_en_riesgo_retraso_curricular_2024",
        *PERCENT_COLUMNS,
    ]
    result = _coerce_numeric(df, numeric_columns)
    for period in PERIOD_ORDER:
        column = f"abierto_{period}"
        result[column] = _as_bool(result[column])
    return _add_area_group(result).sort_values(["semestre_pensum", "codigo_curso"]).reset_index(drop=True)


def prepare_classification(df: pd.DataFrame) -> pd.DataFrame:
    numeric_columns = ["semestre_pensum", "cantidad_cursos_dependientes", "zona_ordinaria"]
    result = _coerce_numeric(df, numeric_columns)
    boolean_columns = [
        "necesito_recuperacion",
        "perdida_definitiva",
        "riesgo_retraso_potencial",
        "riesgo_retraso_potencial_amplio",
        "curso_abierto_periodo_siguiente",
        "curso_abierto_siguiente_periodo",
    ]
    for column in boolean_columns:
        result[column] = _as_bool(result[column])
    return _sort_periods(_add_area_group(result))


def prepare_student_result(df: pd.DataFrame) -> pd.DataFrame:
    numeric_columns = [
        "orden_periodo",
        "semestre_pensum",
        "cantidad_cursos_dependientes",
        "espera_minima_periodos_2024",
    ]
    result = _coerce_numeric(df, numeric_columns)
    boolean_columns = [
        "tiene_resultado_final",
        "perdida_definitiva",
        "es_desasignado",
        "curso_abierto_periodo_siguiente",
        "curso_abierto_en_periodo_posterior_2024",
        "riesgo_retraso_potencial",
        "riesgo_retraso_potencial_amplio",
    ]
    for column in boolean_columns:
        result[column] = _as_bool(result[column])
    return _sort_periods(_add_area_group(result))


def build_period_indicators(course_period: pd.DataFrame, continuity: pd.DataFrame) -> pd.DataFrame:
    grouped = course_period.groupby("periodo_academico", observed=False).agg(
        cursos_con_registro=("codigo_curso", "nunique"),
        secciones_abiertas=("secciones_abiertas", "sum"),
        cupo_total_ofertado=("cupo_total_ofertado", "sum"),
        estudiantes_asignados=("estudiantes_asignados", "sum"),
        estudiantes_desasignados=("estudiantes_desasignados", "sum"),
        estudiantes_con_nota=("estudiantes_con_nota", "sum"),
        estudiantes_con_acta_ordinaria=("estudiantes_con_acta_ordinaria", "sum"),
        aprobados_ordinario=("aprobados_ordinario", "sum"),
        reprobados_ordinario=("reprobados_ordinario", "sum"),
        estudiantes_recuperacion=("estudiantes_recuperacion", "sum"),
        aprobados_recuperacion=("aprobados_recuperacion", "sum"),
        perdida_definitiva=("perdida_definitiva", "sum"),
        nsp_total=("nsp_total", "sum"),
        equivalencias_total=("equivalencias_total", "sum"),
        estudiantes_sin_oportunidad_inmediata=("estudiantes_sin_oportunidad_inmediata", "sum"),
        estudiantes_en_riesgo_retraso_curricular=("estudiantes_en_riesgo_retraso_curricular", "sum"),
    )
    period_rows = []
    total_courses = len(continuity)
    for period in PERIOD_ORDER:
        offered = int(continuity[f"abierto_{period}"].sum())
        period_rows.append(
            {
                "periodo_academico": period,
                "descripcion_periodo": _period_label(period),
                "cursos_ofertados": offered,
                "cursos_no_ofertados": total_courses - offered,
            }
        )

    result = pd.DataFrame(period_rows).merge(grouped.reset_index(), on="periodo_academico", how="left").fillna(0)
    result["tasa_ocupacion_cupo"] = safe_divide(result["estudiantes_asignados"], result["cupo_total_ofertado"])
    result["tasa_aprobacion_ordinaria"] = safe_divide(
        result["aprobados_ordinario"], result["estudiantes_con_acta_ordinaria"]
    )
    result["tasa_recuperacion"] = safe_divide(
        result["estudiantes_recuperacion"], result["estudiantes_con_acta_ordinaria"]
    )
    result["tasa_aprobacion_recuperacion"] = safe_divide(
        result["aprobados_recuperacion"], result["estudiantes_recuperacion"]
    )
    result["tasa_perdida_definitiva"] = safe_divide(
        result["perdida_definitiva"], result["estudiantes_con_acta_ordinaria"]
    )
    return result


def build_offer_by_group_period(continuity: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for group_name, group_df in continuity.groupby("grupo_area", observed=False):
        total_courses = len(group_df)
        for period in PERIOD_ORDER:
            offered = int(group_df[f"abierto_{period}"].sum())
            rows.append(
                {
                    "grupo_area": group_name,
                    "periodo_academico": period,
                    "descripcion_periodo": _period_label(period),
                    "total_cursos_catalogo": total_courses,
                    "cursos_ofertados": offered,
                    "cursos_no_ofertados": total_courses - offered,
                    "porcentaje_cursos_ofertados": safe_divide(offered, total_courses),
                }
            )
    return _sort_periods(pd.DataFrame(rows)).sort_values(["periodo_academico", "grupo_area"]).reset_index(drop=True)


def build_area_indicators(course_period: pd.DataFrame, continuity: pd.DataFrame) -> pd.DataFrame:
    catalog = continuity.groupby(["grupo_area", "area_academica"], observed=False).agg(
        total_cursos_catalogo=("codigo_curso", "nunique"),
        cursos_con_oferta_2024=("cantidad_periodos_abierto", lambda values: int((values > 0).sum())),
        cursos_sin_oferta_2024=("cantidad_periodos_abierto", lambda values: int((values == 0).sum())),
        cursos_baja_continuidad=(
            "indice_continuidad_oferta",
            lambda values: int((values <= LOW_CONTINUITY_THRESHOLD).sum()),
        ),
        indice_continuidad_promedio=("indice_continuidad_oferta", "mean"),
    )
    results = course_period.groupby(["grupo_area", "area_academica"], observed=False).agg(
        cursos_con_resultado=("codigo_curso", "nunique"),
        estudiantes_con_acta_ordinaria=("estudiantes_con_acta_ordinaria", "sum"),
        perdida_definitiva=("perdida_definitiva", "sum"),
        estudiantes_recuperacion=("estudiantes_recuperacion", "sum"),
        estudiantes_en_riesgo_retraso_curricular=("estudiantes_en_riesgo_retraso_curricular", "sum"),
    )
    result = catalog.merge(results, left_index=True, right_index=True, how="left").reset_index().fillna(0)
    result["tasa_perdida_definitiva"] = safe_divide(
        result["perdida_definitiva"], result["estudiantes_con_acta_ordinaria"]
    )
    result["tasa_recuperacion"] = safe_divide(
        result["estudiantes_recuperacion"], result["estudiantes_con_acta_ordinaria"]
    )
    return result.sort_values(["grupo_area", "perdida_definitiva"], ascending=[True, False]).reset_index(drop=True)


def build_course_level_indicators(course_period: pd.DataFrame, continuity: pd.DataFrame) -> pd.DataFrame:
    results = course_period.groupby(
        ["codigo_curso", "nombre_curso", "semestre_pensum", "area_academica"],
        as_index=False,
    ).agg(
        estudiantes_con_acta_ordinaria=("estudiantes_con_acta_ordinaria", "sum"),
        perdida_definitiva=("perdida_definitiva", "sum"),
        estudiantes_recuperacion=("estudiantes_recuperacion", "sum"),
        aprobados_recuperacion=("aprobados_recuperacion", "sum"),
        estudiantes_en_riesgo_retraso_curricular=("estudiantes_en_riesgo_retraso_curricular", "sum"),
    )
    result = continuity.merge(results, on=["codigo_curso", "nombre_curso", "semestre_pensum", "area_academica"], how="left")
    for column in [
        "estudiantes_con_acta_ordinaria",
        "perdida_definitiva",
        "estudiantes_recuperacion",
        "aprobados_recuperacion",
        "estudiantes_en_riesgo_retraso_curricular",
    ]:
        result[column] = pd.to_numeric(result[column], errors="coerce").fillna(0)
    result["curso_etiqueta"] = _course_label(result)
    result["tasa_perdida_definitiva"] = safe_divide(
        result["perdida_definitiva"], result["estudiantes_con_acta_ordinaria"]
    )
    result["tasa_recuperacion"] = safe_divide(
        result["estudiantes_recuperacion"], result["estudiantes_con_acta_ordinaria"]
    )
    result["rank_criticidad_descriptiva"] = (
        result["tasa_perdida_definitiva"].fillna(0)
        * (1 - result["indice_continuidad_oferta"].fillna(0))
        * result["estudiantes_con_acta_ordinaria"].fillna(0)
    )
    return result.sort_values(["grupo_area", "semestre_pensum", "codigo_curso"]).reset_index(drop=True)


def build_top_courses(course_level: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    eligible_for_rate = course_level[course_level["estudiantes_con_acta_ordinaria"] >= MIN_RESULTS_FOR_RATE_RANKING].copy()
    professional = eligible_for_rate[eligible_for_rate["grupo_area"].eq(PROFESSIONAL_AREA_GROUP)].copy()
    common = course_level[course_level["grupo_area"].eq(COMMON_AREA_GROUP)].copy()

    top_loss = course_level.sort_values(
        ["perdida_definitiva", "tasa_perdida_definitiva"],
        ascending=[False, False],
    ).head(TOP_COURSES_LIMIT)
    top_recovery = course_level.sort_values(
        ["estudiantes_recuperacion", "tasa_recuperacion"],
        ascending=[False, False],
    ).head(TOP_COURSES_LIMIT)
    top_professional = professional.sort_values(
        ["tasa_perdida_definitiva", "rank_criticidad_descriptiva", "perdida_definitiva"],
        ascending=[False, False, False],
    ).head(TOP_COURSES_LIMIT)
    common_courses = common.sort_values(
        ["perdida_definitiva", "tasa_perdida_definitiva"],
        ascending=[False, False],
    )
    return (
        top_loss.reset_index(drop=True),
        top_recovery.reset_index(drop=True),
        top_professional.reset_index(drop=True),
        common_courses.reset_index(drop=True),
    )


def build_continuity_indicators(continuity: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    result = continuity.copy()
    result["curso_etiqueta"] = _course_label(result)
    result = result.sort_values(
        ["indice_continuidad_oferta", "estudiantes_en_riesgo_retraso_curricular_2024", "codigo_curso"],
        ascending=[True, False, True],
    )

    blocking_mask = result["curso_bloqueante"].eq(YES_VALUE) | (result["cantidad_cursos_dependientes"].fillna(0) > 0)
    low_continuity_mask = result["indice_continuidad_oferta"].fillna(0) <= LOW_CONTINUITY_THRESHOLD
    blocking_low = result[blocking_mask & low_continuity_mask].copy()
    blocking_low = blocking_low.sort_values(
        ["estudiantes_en_riesgo_retraso_curricular_2024", "total_perdida_definitiva_2024"],
        ascending=[False, False],
    )

    heatmap = result.sort_values(["semestre_pensum", "codigo_curso"]).reset_index(drop=True)
    return result.reset_index(drop=True), blocking_low.reset_index(drop=True), heatmap


def build_risk_indicators(classification: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    def aggregate(group_columns: list[str]) -> pd.DataFrame:
        grouped = classification.groupby(group_columns, observed=False).agg(
            registros_modelables=("riesgo_retraso_potencial", "size"),
            estudiantes_en_riesgo_retraso_curricular=("riesgo_retraso_potencial", "sum"),
            estudiantes_en_riesgo_retraso_amplio=("riesgo_retraso_potencial_amplio", "sum"),
            perdida_definitiva=("perdida_definitiva", "sum"),
            necesidad_recuperacion=("necesito_recuperacion", "sum"),
        ).reset_index()
        grouped["tasa_riesgo_retraso_curricular"] = safe_divide(
            grouped["estudiantes_en_riesgo_retraso_curricular"], grouped["registros_modelables"]
        )
        grouped["tasa_riesgo_retraso_amplio"] = safe_divide(
            grouped["estudiantes_en_riesgo_retraso_amplio"], grouped["registros_modelables"]
        )
        grouped["tasa_perdida_definitiva"] = safe_divide(
            grouped["perdida_definitiva"], grouped["registros_modelables"]
        )
        return grouped

    by_period = _sort_periods(aggregate(["periodo_academico"]))
    by_semester = aggregate(["semestre_pensum"]).sort_values("semestre_pensum").reset_index(drop=True)
    by_area = aggregate(["area_academica"]).sort_values(
        ["estudiantes_en_riesgo_retraso_curricular", "tasa_riesgo_retraso_curricular"],
        ascending=[False, False],
    ).reset_index(drop=True)
    return by_period, by_semester, by_area


def build_retake_events(student_result: pd.DataFrame) -> pd.DataFrame:
    """Construye eventos agregables de perdida con recursamiento posterior observable."""

    active_assignments = student_result[~student_result["es_desasignado"]].copy()
    losses = active_assignments[
        active_assignments["tiene_resultado_final"]
        & active_assignments["perdida_definitiva"]
        & active_assignments["orden_periodo"].lt(len(PERIOD_ORDER))
    ].copy()

    rows = []
    grouped = active_assignments.groupby(["estudiante_id_ofuscado", "codigo_curso"], observed=False)
    for loss in losses.itertuples(index=False):
        key = (getattr(loss, "estudiante_id_ofuscado"), getattr(loss, "codigo_curso"))
        student_course = grouped.get_group(key)
        later_records = student_course[student_course["orden_periodo"].gt(getattr(loss, "orden_periodo"))]
        later_records = later_records.sort_values("orden_periodo")

        has_later_retake = not later_records.empty
        later_with_result = later_records[later_records["tiene_resultado_final"]]
        has_later_result = not later_with_result.empty
        approved_later = bool(later_with_result["resultado_final"].eq(RESULT_APPROVED).any())
        first_later_period = str(later_records.iloc[0]["periodo_academico"]) if has_later_retake else ""

        rows.append(
            {
                "codigo_curso": getattr(loss, "codigo_curso"),
                "nombre_curso": getattr(loss, "nombre_curso"),
                "periodo_perdida": getattr(loss, "periodo_academico"),
                "semestre_pensum": getattr(loss, "semestre_pensum"),
                "area_academica": getattr(loss, "area_academica"),
                "grupo_area": getattr(loss, "grupo_area"),
                "curso_base": getattr(loss, "curso_base"),
                "curso_bloqueante": getattr(loss, "curso_bloqueante"),
                "cantidad_cursos_dependientes": getattr(loss, "cantidad_cursos_dependientes"),
                "nivel_bloqueo_curricular": getattr(loss, "nivel_bloqueo_curricular"),
                "curso_abierto_periodo_siguiente": getattr(loss, "curso_abierto_periodo_siguiente"),
                "curso_abierto_en_periodo_posterior_2024": getattr(
                    loss,
                    "curso_abierto_en_periodo_posterior_2024",
                ),
                "periodo_posterior_disponible_2024": getattr(loss, "periodo_posterior_disponible_2024"),
                "recursamiento_observable": has_later_retake,
                "recursamiento_con_resultado": has_later_result,
                "aprobacion_posterior_observable": approved_later,
                "primer_periodo_recursado_observable": first_later_period,
            }
        )
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result["curso_etiqueta"] = _course_label(result)
    return result


def _aggregate_retake_flow(events: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    grouped = events.groupby(group_columns, observed=False).agg(
        perdidas_definitivas=("codigo_curso", "size"),
        perdidas_con_oferta_posterior_2024=("curso_abierto_en_periodo_posterior_2024", "sum"),
        recursamientos_observables=("recursamiento_observable", "sum"),
        recursamientos_con_resultado=("recursamiento_con_resultado", "sum"),
        aprobaciones_posteriores=("aprobacion_posterior_observable", "sum"),
    ).reset_index()
    grouped["perdidas_sin_oferta_posterior_2024"] = (
        grouped["perdidas_definitivas"] - grouped["perdidas_con_oferta_posterior_2024"]
    )
    grouped["tasa_perdidas_con_oferta_posterior"] = safe_divide(
        grouped["perdidas_con_oferta_posterior_2024"], grouped["perdidas_definitivas"]
    )
    grouped["tasa_perdidas_sin_oferta_posterior"] = safe_divide(
        grouped["perdidas_sin_oferta_posterior_2024"], grouped["perdidas_definitivas"]
    )
    grouped["tasa_recursamiento_observable"] = safe_divide(
        grouped["recursamientos_observables"], grouped["perdidas_definitivas"]
    )
    grouped["tasa_aprobacion_al_recursar"] = safe_divide(
        grouped["aprobaciones_posteriores"], grouped["recursamientos_con_resultado"]
    )
    grouped["tasa_aprobacion_posterior_sobre_perdidas"] = safe_divide(
        grouped["aprobaciones_posteriores"], grouped["perdidas_definitivas"]
    )
    return grouped


def build_retake_indicators(
    student_result: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    events = build_retake_events(student_result)
    by_group = _aggregate_retake_flow(events, ["grupo_area"]).sort_values("grupo_area").reset_index(drop=True)
    by_area = _aggregate_retake_flow(events, ["grupo_area", "area_academica"]).sort_values(
        ["grupo_area", "perdidas_definitivas"],
        ascending=[True, False],
    ).reset_index(drop=True)
    by_course = _aggregate_retake_flow(
        events,
        [
            "grupo_area",
            "area_academica",
            "codigo_curso",
            "nombre_curso",
            "curso_etiqueta",
            "semestre_pensum",
            "curso_bloqueante",
            "cantidad_cursos_dependientes",
            "nivel_bloqueo_curricular",
        ],
    )
    by_course = by_course.sort_values(
        ["grupo_area", "perdidas_sin_oferta_posterior_2024", "perdidas_definitivas"],
        ascending=[True, False, False],
    ).reset_index(drop=True)

    common_flow = by_course[by_course["grupo_area"].eq(COMMON_AREA_GROUP)].copy()
    professional_flow = by_course[by_course["grupo_area"].eq(PROFESSIONAL_AREA_GROUP)].copy()
    professional_without_later_offer = professional_flow[
        professional_flow["perdidas_sin_oferta_posterior_2024"].gt(0)
    ].sort_values(
        ["perdidas_sin_oferta_posterior_2024", "tasa_perdidas_sin_oferta_posterior"],
        ascending=[False, False],
    ).head(TOP_FLOW_COURSES_LIMIT)

    return (
        by_group,
        by_area,
        common_flow.reset_index(drop=True),
        professional_flow.reset_index(drop=True),
        professional_without_later_offer.reset_index(drop=True),
    )


def save_indicator_tables(tables: dict[str, pd.DataFrame]) -> dict[str, Path]:
    saved_paths = {}
    for table_name, df in tables.items():
        path = INDICATORS_DIR / f"{table_name}.csv"
        save_table(df, path)
        saved_paths[table_name] = path
    return saved_paths


def build_figure_records(
    period_indicators: pd.DataFrame,
    offer_by_group_period: pd.DataFrame,
    top_loss: pd.DataFrame,
    top_professional: pd.DataFrame,
    retake_by_group: pd.DataFrame,
    professional_without_later_offer: pd.DataFrame,
    continuity: pd.DataFrame,
    blocking_low: pd.DataFrame,
    risk_by_area: pd.DataFrame,
) -> list[FigureRecord]:
    highest_offer = period_indicators.sort_values("cursos_ofertados", ascending=False).iloc[0]
    highest_assignments = period_indicators.sort_values("estudiantes_asignados", ascending=False).iloc[0]
    highest_loss = top_loss.iloc[0]
    highest_professional = top_professional.iloc[0]
    highest_retake = retake_by_group.sort_values("recursamientos_observables", ascending=False).iloc[0]
    highest_without_offer = professional_without_later_offer.iloc[0]
    highest_professional_offer = offer_by_group_period[
        offer_by_group_period["grupo_area"].eq(PROFESSIONAL_AREA_GROUP)
    ].sort_values("cursos_ofertados", ascending=False).iloc[0]
    pattern_counts = continuity["patron_oferta"].value_counts()
    most_common_pattern = pattern_counts.index[0] if not pattern_counts.empty else "sin dato"
    low_blocking_count = len(blocking_low)
    highest_risk_area = risk_by_area.iloc[0]

    return [
        FigureRecord(
            figura="05_cursos_ofertados_por_periodo.png",
            pregunta_analitica="Cuantos cursos fueron ofertados y no ofertados por periodo academico?",
            descripcion="Barras comparativas de cursos ofertados y no ofertados en S1, V1, S2 y V2.",
            interpretacion=(
                f"{_period_label(str(highest_offer['periodo_academico']))} concentra la mayor cantidad de cursos "
                f"ofertados, con {_format_number(highest_offer['cursos_ofertados'])} cursos."
            ),
            conclusion="La oferta observada es mas amplia en periodos semestrales que en escuelas de vacaciones.",
            ruta=EDA_FIGURES_DIR / "05_cursos_ofertados_por_periodo.png",
        ),
        FigureRecord(
            figura="05_asignaciones_por_periodo.png",
            pregunta_analitica="Como varia el volumen de asignaciones y estudiantes con nota por periodo?",
            descripcion="Barras comparativas de asignaciones registradas y estudiantes con nota por periodo.",
            interpretacion=(
                f"{_period_label(str(highest_assignments['periodo_academico']))} registra el mayor volumen, con "
                f"{_format_number(highest_assignments['estudiantes_asignados'])} asignaciones."
            ),
            conclusion="El volumen de actividad academica evaluada se concentra principalmente en periodos semestrales.",
            ruta=EDA_FIGURES_DIR / "05_asignaciones_por_periodo.png",
        ),
        FigureRecord(
            figura="05_top_perdida_definitiva.png",
            pregunta_analitica="Que cursos concentran mayor perdida definitiva observada?",
            descripcion="Barras horizontales con los cursos de mayor perdida definitiva agregada en 2024.",
            interpretacion=(
                f"El curso con mayor perdida definitiva observada es {highest_loss['curso_etiqueta']}, con "
                f"{_format_number(highest_loss['perdida_definitiva'])} registros."
            ),
            conclusion=(
                "El conteo absoluto identifica volumen de perdida, pero debe complementarse con tasa e indice "
                "de continuidad para comparar cursos masivos contra cursos de oferta menos frecuente."
            ),
            ruta=EDA_FIGURES_DIR / "05_top_perdida_definitiva.png",
        ),
        FigureRecord(
            figura="05_oferta_por_grupo_area_periodo.png",
            pregunta_analitica="Como se distribuye la oferta entre area comun y area profesional por periodo?",
            descripcion="Barras comparativas de cursos ofertados por grupo academico en cada periodo.",
            interpretacion=(
                f"En area profesional, {_period_label(str(highest_professional_offer['periodo_academico']))} "
                f"presenta el mayor numero de cursos ofertados, con "
                f"{_format_number(highest_professional_offer['cursos_ofertados'])} cursos."
            ),
            conclusion=(
                "La lectura por grupo academico evita interpretar los cursos no ofertados como una sola bolsa "
                "homogenea y permite separar area comun de cursos propios de la carrera."
            ),
            ruta=EDA_FIGURES_DIR / "05_oferta_por_grupo_area_periodo.png",
        ),
        FigureRecord(
            figura="05_cursos_profesionales_perdida_relativa.png",
            pregunta_analitica="Que cursos profesionales combinan mayor perdida relativa y menor continuidad?",
            descripcion=(
                "Barras horizontales de tasa de perdida definitiva en cursos profesionales con volumen minimo "
                "de registros evaluables."
            ),
            interpretacion=(
                f"El curso profesional con mayor tasa observada es {highest_professional['curso_etiqueta']}, "
                f"con {_format_percent(highest_professional['tasa_perdida_definitiva'])}, "
                f"n={_format_number(highest_professional['estudiantes_con_acta_ordinaria'])} e indice de "
                f"continuidad {_format_percent(highest_professional['indice_continuidad_oferta'])}."
            ),
            conclusion=(
                "Este ranking es mas adecuado para detectar vulnerabilidad academica en cursos profesionales "
                "que se ofertan pocas veces durante el anio."
            ),
            ruta=EDA_FIGURES_DIR / "05_cursos_profesionales_perdida_relativa.png",
        ),
        FigureRecord(
            figura="05_recursamiento_y_aprobacion_por_grupo.png",
            pregunta_analitica="Que flujo posterior se observa despues de una perdida definitiva por grupo academico?",
            descripcion=(
                "Barras de perdidas definitivas, recursamientos observables y aprobaciones posteriores para area "
                "comun y area profesional."
            ),
            interpretacion=(
                f"{highest_retake['grupo_area']} concentra "
                f"{_format_number(highest_retake['recursamientos_observables'])} recursamientos observables "
                "posteriores a una perdida definitiva dentro de 2024."
            ),
            conclusion=(
                "El recursamiento observable permite medir flujo academico posterior sin asumir que la oferta "
                "por si sola asegura aprobacion."
            ),
            ruta=EDA_FIGURES_DIR / "05_recursamiento_y_aprobacion_por_grupo.png",
        ),
        FigureRecord(
            figura="05_profesional_perdida_sin_oferta_posterior.png",
            pregunta_analitica="Que cursos profesionales acumulan perdidas sin oferta posterior observable?",
            descripcion="Barras de cursos profesionales con perdidas definitivas y sin oferta posterior durante 2024.",
            interpretacion=(
                f"El curso profesional con mayor conteo es {highest_without_offer['curso_etiqueta']}, con "
                f"{_format_number(highest_without_offer['perdidas_sin_oferta_posterior_2024'])} perdidas sin "
                "oferta posterior observable en 2024."
            ),
            conclusion=(
                "Estos cursos representan candidatos prioritarios para revisar continuidad de oferta, porque la "
                "perdida coincide con menor ventana observable de recursamiento."
            ),
            ruta=EDA_FIGURES_DIR / "05_profesional_perdida_sin_oferta_posterior.png",
        ),
        FigureRecord(
            figura="05_heatmap_oferta_curso_periodo.png",
            pregunta_analitica="Que patron de continuidad de oferta muestra cada curso durante 2024?",
            descripcion="Matriz curso-periodo donde cada celda indica si el curso fue ofertado en el periodo observado.",
            interpretacion=(
                f"El patron mas frecuente es `{most_common_pattern}`. Se identifican "
                f"{_format_number(low_blocking_count)} cursos bloqueantes o dependientes con continuidad baja."
            ),
            conclusion="La continuidad de oferta es heterogenea y requiere analizar cursos con dependencia curricular.",
            ruta=EDA_FIGURES_DIR / "05_heatmap_oferta_curso_periodo.png",
        ),
        FigureRecord(
            figura="05_distribucion_aprobacion_semestre.png",
            pregunta_analitica="Como se distribuye la tasa de aprobacion ordinaria por semestre del pensum?",
            descripcion="Diagrama de caja de tasas de aprobacion ordinaria agrupadas por semestre del pensum.",
            interpretacion="La dispersion por semestre permite observar variabilidad entre cursos dentro del mismo nivel curricular.",
            conclusion="La tasa de aprobacion debe interpretarse por curso y semestre, no solo como promedio general.",
            ruta=EDA_FIGURES_DIR / "05_distribucion_aprobacion_semestre.png",
        ),
        FigureRecord(
            figura="05_perdida_vs_continuidad.png",
            pregunta_analitica="Como se relacionan descriptivamente la perdida definitiva y la continuidad de oferta?",
            descripcion="Dispersion por curso entre indice de continuidad de oferta y tasa de perdida definitiva.",
            interpretacion=(
                "Los puntos combinan continuidad, perdida definitiva y cantidad de estudiantes en riesgo potencial "
                "curricular para ubicar cursos que merecen revision integrada."
            ),
            conclusion="La grafica apoya una lectura descriptiva conjunta, sin afirmar causalidad entre continuidad y perdida.",
            ruta=EDA_FIGURES_DIR / "05_perdida_vs_continuidad.png",
        ),
        FigureRecord(
            figura="05_riesgo_por_area.png",
            pregunta_analitica="En que areas academicas se concentra el riesgo de retraso academico potencial?",
            descripcion="Barras horizontales de estudiantes en riesgo potencial curricular por area academica.",
            interpretacion=(
                f"El area con mayor conteo observado es {highest_risk_area['area_academica']}, con "
                f"{_format_number(highest_risk_area['estudiantes_en_riesgo_retraso_curricular'])} registros."
            ),
            conclusion="El riesgo potencial se concentra de forma desigual entre areas y debe revisarse junto con cursos especificos.",
            ruta=EDA_FIGURES_DIR / "05_riesgo_por_area.png",
        ),
    ]


def generate_figures(
    period_indicators: pd.DataFrame,
    offer_by_group_period: pd.DataFrame,
    top_loss: pd.DataFrame,
    top_professional: pd.DataFrame,
    retake_by_group: pd.DataFrame,
    professional_without_later_offer: pd.DataFrame,
    course_period: pd.DataFrame,
    continuity: pd.DataFrame,
    heatmap: pd.DataFrame,
    risk_by_area: pd.DataFrame,
) -> None:
    plot_offer_by_period(period_indicators, EDA_FIGURES_DIR / "05_cursos_ofertados_por_periodo.png")
    plot_assignments_by_period(period_indicators, EDA_FIGURES_DIR / "05_asignaciones_por_periodo.png")
    plot_top_definitive_loss(top_loss, EDA_FIGURES_DIR / "05_top_perdida_definitiva.png")
    plot_offer_by_area_group_period(offer_by_group_period, EDA_FIGURES_DIR / "05_oferta_por_grupo_area_periodo.png")
    plot_professional_critical_courses(
        top_professional,
        EDA_FIGURES_DIR / "05_cursos_profesionales_perdida_relativa.png",
    )
    plot_retake_flow_by_area_group(
        retake_by_group,
        EDA_FIGURES_DIR / "05_recursamiento_y_aprobacion_por_grupo.png",
    )
    plot_professional_loss_without_later_offer(
        professional_without_later_offer,
        EDA_FIGURES_DIR / "05_profesional_perdida_sin_oferta_posterior.png",
    )
    plot_offer_heatmap(heatmap, EDA_FIGURES_DIR / "05_heatmap_oferta_curso_periodo.png")
    plot_approval_distribution_by_semester(course_period, EDA_FIGURES_DIR / "05_distribucion_aprobacion_semestre.png")
    plot_loss_vs_continuity(continuity, EDA_FIGURES_DIR / "05_perdida_vs_continuidad.png")
    plot_risk_by_area(risk_by_area, EDA_FIGURES_DIR / "05_riesgo_por_area.png")


def build_figure_catalog(records: list[FigureRecord]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "figura": record.figura,
                "pregunta_analitica": record.pregunta_analitica,
                "descripcion": record.descripcion,
                "interpretacion": record.interpretacion,
                "conclusion": record.conclusion,
                "ruta": _relative_path(record.ruta),
            }
            for record in records
        ]
    )


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


def _table_inventory(saved_tables: dict[str, Path]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"tabla": table_name, "ruta": _relative_path(path)}
            for table_name, path in sorted(saved_tables.items())
        ]
    )


def _period_report_table(period_indicators: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "periodo_academico",
        "cursos_ofertados",
        "cursos_no_ofertados",
        "estudiantes_asignados",
        "estudiantes_con_nota",
        "tasa_aprobacion_ordinaria",
        "tasa_recuperacion",
        "tasa_perdida_definitiva",
        "estudiantes_en_riesgo_retraso_curricular",
    ]
    table = period_indicators[columns].copy()
    for column in ["tasa_aprobacion_ordinaria", "tasa_recuperacion", "tasa_perdida_definitiva"]:
        table[column] = table[column].map(_format_percent)
    return table


def _area_report_table(area_indicators: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "grupo_area",
        "area_academica",
        "total_cursos_catalogo",
        "cursos_con_oferta_2024",
        "cursos_sin_oferta_2024",
        "cursos_baja_continuidad",
        "estudiantes_con_acta_ordinaria",
        "perdida_definitiva",
        "tasa_perdida_definitiva",
        "indice_continuidad_promedio",
    ]
    table = area_indicators[columns].copy()
    for column in ["tasa_perdida_definitiva", "indice_continuidad_promedio"]:
        table[column] = table[column].map(_format_percent)
    return table


def _professional_report_table(top_professional: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "curso_etiqueta",
        "estudiantes_con_acta_ordinaria",
        "perdida_definitiva",
        "tasa_perdida_definitiva",
        "indice_continuidad_oferta",
        "patron_oferta",
    ]
    table = top_professional[columns].copy()
    for column in ["tasa_perdida_definitiva", "indice_continuidad_oferta"]:
        table[column] = table[column].map(_format_percent)
    return table


def _retake_group_report_table(retake_by_group: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "grupo_area",
        "perdidas_definitivas",
        "perdidas_con_oferta_posterior_2024",
        "perdidas_sin_oferta_posterior_2024",
        "recursamientos_observables",
        "aprobaciones_posteriores",
        "tasa_recursamiento_observable",
        "tasa_aprobacion_al_recursar",
    ]
    table = retake_by_group[columns].copy()
    for column in ["tasa_recursamiento_observable", "tasa_aprobacion_al_recursar"]:
        table[column] = table[column].map(_format_percent)
    return table


def _professional_without_offer_report_table(professional_without_later_offer: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "curso_etiqueta",
        "perdidas_definitivas",
        "perdidas_sin_oferta_posterior_2024",
        "tasa_perdidas_sin_oferta_posterior",
        "recursamientos_observables",
        "aprobaciones_posteriores",
    ]
    table = professional_without_later_offer[columns].copy()
    table["tasa_perdidas_sin_oferta_posterior"] = table["tasa_perdidas_sin_oferta_posterior"].map(_format_percent)
    return table


def write_report(
    period_indicators: pd.DataFrame,
    area_indicators: pd.DataFrame,
    top_loss: pd.DataFrame,
    top_recovery: pd.DataFrame,
    top_professional: pd.DataFrame,
    retake_by_group: pd.DataFrame,
    professional_without_later_offer: pd.DataFrame,
    blocking_low: pd.DataFrame,
    figure_catalog: pd.DataFrame,
    saved_tables: dict[str, Path],
) -> None:
    top_loss_course = top_loss.iloc[0]
    top_recovery_course = top_recovery.iloc[0]
    top_professional_course = top_professional.iloc[0]
    highest_without_offer = professional_without_later_offer.iloc[0]
    blocking_count = len(blocking_low)
    tables_inventory = _table_inventory(saved_tables)

    figure_sections = []
    for _, row in figure_catalog.iterrows():
        figure_sections.append(
            f"""### {row['figura']}

![{row['descripcion']}](../figures/eda/{row['figura']})

- Pregunta analitica: {row['pregunta_analitica']}
- Descripcion: {row['descripcion']}
- Interpretacion: {row['interpretacion']}
- Conclusion: {row['conclusion']}
- Ruta: `{row['ruta']}`
"""
        )

    content = f"""# Resumen de indicadores y EDA

## Objetivo

Describir la oferta academica observada, asignaciones, resultados registrados,
continuidad de oferta y riesgo de retraso academico potencial durante 2024.

El analisis es descriptivo. No afirma causalidad y no utiliza variables de
docencia, contratacion, presupuesto ni identificadores individuales en las
salidas publicas.

## Tablas generadas

{_markdown_table(tables_inventory)}

## Indicadores por periodo

{_markdown_table(_period_report_table(period_indicators))}

Los cursos no ofertados por periodo se calculan contra el catalogo completo de
90 cursos. Por eso, cuando S1 muestra 51 cursos ofertados y 39 no ofertados,
los 39 corresponden a cursos del catalogo que no aparecen como oferta activa
en ese periodo, no a cursos cancelados ni necesariamente a cursos que debian
abrirse obligatoriamente.

## Separacion por area comun y area profesional

{_markdown_table(_area_report_table(area_indicators))}

Para evitar que cursos masivos de area comun dominen toda la lectura, la Fase 5
separa `Area comun` de `Area profesional`. El conteo absoluto sigue siendo util
para medir volumen, pero los cursos profesionales se revisan tambien por tasa
de perdida e indice de continuidad de oferta.

## Cursos profesionales con mayor perdida relativa

{_markdown_table(_professional_report_table(top_professional))}

## Fase 5.1: Flujo posterior y recursamiento observable

{_markdown_table(_retake_group_report_table(retake_by_group))}

Esta seccion usa identificadores ofuscados solo de forma interna para observar
si, despues de perder definitivamente un curso en S1, V1 o S2, el mismo
estudiante vuelve a aparecer en el mismo curso en un periodo posterior de 2024.
Las salidas son agregadas y no exponen registros individuales.

La ventana de observacion excluye perdidas en V2 porque no existe un periodo
posterior dentro de 2024 para medir recursamiento. Por eso, estos indicadores
deben leerse como flujo posterior observable en el anio, no como trayectoria
academica completa.

### Cursos profesionales con perdida y sin oferta posterior observable

{_markdown_table(_professional_without_offer_report_table(professional_without_later_offer))}

Estos cursos ayudan a contrastar la hipotesis descriptiva del proyecto: una
mayor continuidad de oferta no garantiza aprobacion, pero puede ampliar la
ventana observable para recursar y cerrar cursos profesionales. La evidencia
tambien puede refutar parcialmente la hipotesis si existe oferta posterior y,
aun asi, se observa bajo recursamiento o baja aprobacion posterior.

## Hallazgos descriptivos principales

- El curso con mayor perdida definitiva observada es `{top_loss_course['curso_etiqueta']}` con {_format_number(top_loss_course['perdida_definitiva'])} registros.
- El curso con mayor necesidad de recuperacion observada es `{top_recovery_course['curso_etiqueta']}` con {_format_number(top_recovery_course['estudiantes_recuperacion'])} registros.
- El curso profesional con mayor perdida relativa observada, usando al menos {_format_number(MIN_RESULTS_FOR_RATE_RANKING)} registros evaluables, es `{top_professional_course['curso_etiqueta']}` con {_format_percent(top_professional_course['tasa_perdida_definitiva'])} e indice de continuidad {_format_percent(top_professional_course['indice_continuidad_oferta'])}.
- El curso profesional con mayor perdida sin oferta posterior observable es `{highest_without_offer['curso_etiqueta']}` con {_format_number(highest_without_offer['perdidas_sin_oferta_posterior_2024'])} registros dentro de la ventana S1-V1-S2.
- Se identifican {_format_number(blocking_count)} cursos bloqueantes o con dependencias directas con continuidad de oferta igual o menor a {_format_percent(LOW_CONTINUITY_THRESHOLD)}.
- Los indicadores de riesgo se interpretan como riesgo academico potencial bajo la oferta observada y los resultados registrados; no prueban causalidad.

## Figuras generadas e interpretacion

{"".join(figure_sections)}

## Conclusion

La Fase 5 y su extension 5.1 dejan indicadores y graficas para describir la
actividad academica de 2024 desde cuatro perspectivas: oferta por periodo,
resultados academicos registrados, continuidad curricular y flujo posterior
observable despues de una perdida. Los hallazgos permiten priorizar cursos y
areas para analisis estadistico y modelado posterior, manteniendo una lectura
descriptiva y sin exponer registros individuales.
"""
    write_text(EDA_REPORT_PATH, content)


def main() -> None:
    ensure_project_directories()
    inputs = load_inputs()
    course_period = inputs["course_period"]
    continuity_source = inputs["continuity"]
    classification = inputs["classification"]
    student_result = inputs["student_result"]

    period_indicators = build_period_indicators(course_period, continuity_source)
    offer_by_group_period = build_offer_by_group_period(continuity_source)
    area_indicators = build_area_indicators(course_period, continuity_source)
    course_level = build_course_level_indicators(course_period, continuity_source)
    top_loss, top_recovery, top_professional, common_courses = build_top_courses(course_level)
    continuity, blocking_low, heatmap = build_continuity_indicators(continuity_source)
    risk_by_period, risk_by_semester, risk_by_area = build_risk_indicators(classification)
    (
        retake_by_group,
        retake_by_area,
        common_retake_flow,
        professional_retake_flow,
        professional_without_later_offer,
    ) = build_retake_indicators(student_result)

    records = build_figure_records(
        period_indicators,
        offer_by_group_period,
        top_loss,
        top_professional,
        retake_by_group,
        professional_without_later_offer,
        continuity,
        blocking_low,
        risk_by_area,
    )
    generate_figures(
        period_indicators,
        offer_by_group_period,
        top_loss,
        top_professional,
        retake_by_group,
        professional_without_later_offer,
        course_period,
        continuity,
        heatmap,
        risk_by_area,
    )
    figure_catalog = build_figure_catalog(records)

    tables = {
        "05_indicadores_periodo": period_indicators,
        "05_oferta_por_grupo_area_periodo": offer_by_group_period,
        "05_indicadores_area": area_indicators,
        "05_indicadores_curso": course_level,
        "05_cursos_area_comun": common_courses,
        "05_cursos_profesionales_perdida_relativa": top_professional,
        "05_recursamiento_observable": retake_by_group,
        "05_recursamiento_por_area": retake_by_area,
        "05_flujo_area_comun_posterior": common_retake_flow,
        "05_flujo_profesional_posterior": professional_retake_flow,
        "05_cursos_profesionales_sin_oportunidad_posterior": professional_without_later_offer,
        "05_top_perdida_definitiva": top_loss,
        "05_top_necesidad_recuperacion": top_recovery,
        "05_continuidad_curso": continuity,
        "05_cursos_bloqueantes_baja_continuidad": blocking_low,
        "05_riesgo_por_periodo": risk_by_period,
        "05_riesgo_por_semestre": risk_by_semester,
        "05_riesgo_por_area": risk_by_area,
        "05_catalogo_figuras_eda": figure_catalog,
    }
    saved_tables = save_indicator_tables(tables)
    write_report(
        period_indicators,
        area_indicators,
        top_loss,
        top_recovery,
        top_professional,
        retake_by_group,
        professional_without_later_offer,
        blocking_low,
        figure_catalog,
        saved_tables,
    )

    print("Analisis exploratorio e indicadores completados.")
    print(f"Tablas: {INDICATORS_DIR}")
    print(f"Figuras: {EDA_FIGURES_DIR}")
    print(f"Reporte: {EDA_REPORT_PATH}")


if __name__ == "__main__":
    main()
