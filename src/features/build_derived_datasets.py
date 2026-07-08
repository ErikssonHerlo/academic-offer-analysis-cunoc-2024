"""Construccion de datasets derivados para el analisis academico 2024."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.config.settings import (
    ASSIGNMENT_DROPPED,
    EVALUATION_EQUIVALENCE,
    EVALUATION_FIRST_RECOVERY,
    EVALUATION_ORDINARY,
    EVALUATION_SECOND_RECOVERY,
    PERIOD_ORDER,
    PROCESSED_DATA_DIR,
    PROJECT_ROOT,
    REPORTS_DIR,
    RESULT_APPROVED,
    RESULT_FAILED,
    RESULT_NSP,
    TABLES_DIR,
    YES_VALUE,
)
from src.data.utils import ensure_project_directories, safe_divide, save_table, write_text


INTERIM_DIR = Path("data/interim")
CONSOLIDATED_OFFER_PATH = PROCESSED_DATA_DIR / "04_oferta_academica_2024_consolidada.csv"

STUDENT_RESULT_PATH = PROCESSED_DATA_DIR / "ds_estudiante_curso_resultado_2024.csv"
COURSE_PERIOD_PATH = PROCESSED_DATA_DIR / "ds_resumen_curso_periodo_2024.csv"
CONTINUITY_PATH = PROCESSED_DATA_DIR / "ds_continuidad_oferta_2024.csv"
CLUSTERING_PATH = PROCESSED_DATA_DIR / "ds_cursos_criticos_clustering.csv"
CLASSIFICATION_PATH = PROCESSED_DATA_DIR / "ds_modelo_clasificacion.csv"
ASSOCIATION_PATH = PROCESSED_DATA_DIR / "ds_reglas_asociacion.csv"

DERIVED_SUMMARY_PATH = TABLES_DIR / "04_resumen_datasets_derivados.csv"
TARGET_DISTRIBUTION_PATH = TABLES_DIR / "04_distribucion_targets.csv"
DERIVED_REPORT_PATH = REPORTS_DIR / "datasets_derivados.md"

STUDENT_KEYS = ["estudiante_id_ofuscado", "codigo_curso", "periodo_academico", "seccion"]
OFFER_KEY_COLUMNS = ["periodo_academico", "codigo_curso", "seccion"]
COURSE_PERIOD_KEYS = ["periodo_academico", "codigo_curso"]
PERIOD_ORDER_MAP = {period: index + 1 for index, period in enumerate(PERIOD_ORDER)}
PERIOD_BY_ORDER = {index + 1: period for index, period in enumerate(PERIOD_ORDER)}


@dataclass(frozen=True)
class DerivedOutput:
    dataset: str
    path: Path
    rows: int
    columns: int
    conclusion: str


def _read_csv(path: Path | str) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _read_interim(filename: str) -> pd.DataFrame:
    return _read_csv(INTERIM_DIR / filename)


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _to_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin({"true", "si", "sí", "1", "yes"})


def _first_non_empty(series: pd.Series) -> str:
    values = [str(value).strip() for value in series.astype(str).tolist() if str(value).strip()]
    return values[0] if values else ""


def _relative_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def _period_next(period: str) -> str:
    order = PERIOD_ORDER_MAP.get(period)
    if order is None:
        return ""
    return PERIOD_BY_ORDER.get(order + 1, "")


def _ordered_periods_after(period: str) -> list[str]:
    order = PERIOD_ORDER_MAP.get(period)
    if order is None:
        return []
    return [PERIOD_BY_ORDER[index] for index in range(order + 1, len(PERIOD_ORDER) + 1)]


def load_inputs() -> dict[str, pd.DataFrame]:
    return {
        "catalogo": _read_interim("01_catalogo_cursos_2024_normalizado.csv"),
        "actas": _read_interim("02_actas_notas_2024_detalle_normalizado.csv"),
        "asignaciones": _read_interim("03_asignaciones_2024_normalizado.csv"),
        "oferta": _read_csv(CONSOLIDATED_OFFER_PATH),
        "prerrequisitos": _read_interim("05_malla_prerrequisitos_normalizado.csv"),
        "calendario": _read_interim("06_calendario_academico_2024_normalizado.csv"),
        "parametros": _read_interim("07_parametros_academicos_normalizado.csv"),
        "configuracion": _read_interim("08_configuracion_academica_cursos_normalizado.csv"),
        "inscritos": _read_interim("09_estudiantes_inscritos_2024_normalizado.csv"),
        "inscritos_anual": _read_interim("10_inscritos_sistemas_anual_normalizado.csv"),
    }


def get_passing_grade(parametros: pd.DataFrame) -> float:
    row = parametros[parametros["parametro"].eq("nota_minima_aprobacion")]
    if row.empty:
        return 61.0
    value = pd.to_numeric(row.iloc[0]["valor"], errors="coerce")
    return float(value) if pd.notna(value) else 61.0


def _opportunity_row(group: pd.DataFrame, opportunity: str) -> pd.Series | None:
    rows = group[group["oportunidad_evaluacion"].eq(opportunity)].sort_values("fecha_acta_dt")
    if rows.empty:
        return None
    return rows.iloc[-1]


def _approved(row: pd.Series | None, passing_grade: float) -> bool:
    if row is None:
        return False
    nota = pd.to_numeric(row.get("nota_total_num", ""), errors="coerce")
    return row.get("resultado") == RESULT_APPROVED or (pd.notna(nota) and nota >= passing_grade)


def _result_for_final_row(row: pd.Series | None) -> str:
    if row is None:
        return ""
    return str(row.get("resultado", ""))


def build_acta_outcomes(actas: pd.DataFrame, passing_grade: float) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for key_values, group in actas.groupby(STUDENT_KEYS, dropna=False):
        key = dict(zip(STUDENT_KEYS, key_values, strict=True))
        ordinary = _opportunity_row(group, EVALUATION_ORDINARY)
        first_recovery = _opportunity_row(group, EVALUATION_FIRST_RECOVERY)
        second_recovery = _opportunity_row(group, EVALUATION_SECOND_RECOVERY)
        equivalence = _opportunity_row(group, EVALUATION_EQUIVALENCE)

        has_ordinary = ordinary is not None
        has_first = first_recovery is not None
        has_second = second_recovery is not None
        has_equivalence = equivalence is not None
        has_nsp = bool(group["resultado"].eq(RESULT_NSP).any())

        approved_ordinary = _approved(ordinary, passing_grade)
        approved_recovery = (not approved_ordinary) and (
            _approved(first_recovery, passing_grade) or _approved(second_recovery, passing_grade)
        )

        final_row = ordinary
        if has_first:
            final_row = first_recovery
        if has_second:
            final_row = second_recovery
        if has_equivalence:
            final_row = equivalence

        final_result = _result_for_final_row(final_row)
        final_grade = pd.to_numeric(final_row.get("nota_total_num", ""), errors="coerce") if final_row is not None else np.nan
        final_approved = final_result == RESULT_APPROVED or (pd.notna(final_grade) and final_grade >= passing_grade)
        definitive_loss = bool(final_result and not final_approved)
        definitive_loss_without_nsp = bool(definitive_loss and not has_nsp)

        rows.append(
            {
                **key,
                "zona_ordinaria": ordinary.get("zona_num", "") if ordinary is not None else "",
                "nota_examen_ordinario": ordinary.get("nota_examen_num", "") if ordinary is not None else "",
                "nota_total_ordinario": ordinary.get("nota_total_num", "") if ordinary is not None else "",
                "resultado_ordinario": ordinary.get("resultado", "") if ordinary is not None else "",
                "tiene_ordinario": has_ordinary,
                "tiene_primera_recuperacion": has_first,
                "tiene_segunda_recuperacion": has_second,
                "tiene_equivalencia": has_equivalence,
                "tiene_nsp": has_nsp,
                "nota_total_final": final_grade if pd.notna(final_grade) else "",
                "resultado_final": final_result,
                "tiene_resultado_final": bool(final_result),
                "aprobo_ordinario": approved_ordinary,
                "necesito_recuperacion": has_first or has_second,
                "aprobo_por_recuperacion": approved_recovery,
                "perdida_definitiva": definitive_loss,
                "perdida_definitiva_sin_nsp": definitive_loss_without_nsp,
            }
        )

    return pd.DataFrame(rows)


def build_offer_section_features(oferta: pd.DataFrame) -> pd.DataFrame:
    result = oferta.copy()
    for column in ("cupo_ofertado", "estudiantes_asignados", "estudiantes_con_nota"):
        result[f"{column}_oferta"] = _to_numeric(result[column])
    result["tasa_ocupacion_cupo"] = safe_divide(
        result["estudiantes_asignados_oferta"],
        result["cupo_ofertado_oferta"],
    )
    return result[
        [
            "periodo_academico",
            "codigo_curso",
            "seccion",
            "curso_aperturado",
            "curso_cancelado",
            "cupo_ofertado_oferta",
            "estudiantes_asignados_oferta",
            "estudiantes_con_nota_oferta",
            "tasa_ocupacion_cupo",
            "jornada",
            "horario",
            "modalidad",
        ]
    ]


def _open_periods_by_course(oferta: pd.DataFrame) -> dict[str, set[str]]:
    active = oferta[
        oferta["curso_aperturado"].eq(YES_VALUE)
        & ~oferta["curso_cancelado"].eq(YES_VALUE)
    ]
    return active.groupby("codigo_curso")["periodo_academico"].apply(lambda values: set(values)).to_dict()


def add_continuity_and_risk(df: pd.DataFrame, oferta: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    open_periods = _open_periods_by_course(oferta)

    next_periods: list[str] = []
    opened_next: list[bool] = []
    opened_later: list[bool] = []
    first_later_periods: list[str] = []
    wait_periods: list[Any] = []

    for row in result.itertuples(index=False):
        period = getattr(row, "periodo_academico")
        code = getattr(row, "codigo_curso")
        available_periods = open_periods.get(code, set())
        next_period = _period_next(period)
        later_periods = _ordered_periods_after(period)
        first_later = next((candidate for candidate in later_periods if candidate in available_periods), "")

        next_periods.append(next_period)
        opened_next.append(bool(next_period and next_period in available_periods))
        opened_later.append(bool(first_later))
        first_later_periods.append(first_later)
        wait_periods.append(
            PERIOD_ORDER_MAP[first_later] - PERIOD_ORDER_MAP[period] if first_later else ""
        )

    result["periodo_siguiente_cronologico"] = next_periods
    result["curso_abierto_periodo_siguiente"] = opened_next
    result["curso_abierto_siguiente_periodo"] = opened_next
    result["curso_abierto_en_periodo_posterior_2024"] = opened_later
    result["periodo_posterior_disponible_2024"] = first_later_periods
    result["espera_minima_periodos_2024"] = wait_periods
    result["sin_oferta_posterior_2024"] = ~pd.Series(opened_later, index=result.index)

    dependent_count = _to_numeric(result["cantidad_cursos_dependientes"]).fillna(0)
    blocking_course = result["curso_bloqueante"].eq(YES_VALUE) | (dependent_count > 0)
    definitive_loss = result["perdida_definitiva"].fillna(False).astype(bool)
    no_immediate_offer = ~result["curso_abierto_periodo_siguiente"].fillna(False).astype(bool)

    result["riesgo_retraso_simple"] = definitive_loss & no_immediate_offer
    result["riesgo_retraso_potencial_amplio"] = result["riesgo_retraso_simple"]
    result["riesgo_retraso_curricular"] = result["riesgo_retraso_simple"] & blocking_course
    result["riesgo_retraso_potencial"] = result["riesgo_retraso_curricular"]
    return result


def build_student_course_result(inputs: dict[str, pd.DataFrame], passing_grade: float) -> pd.DataFrame:
    acta_outcomes = build_acta_outcomes(inputs["actas"], passing_grade)
    assignments = inputs["asignaciones"].copy()

    result = assignments.merge(acta_outcomes, on=STUDENT_KEYS, how="left")
    boolean_columns = [
        "tiene_ordinario",
        "tiene_primera_recuperacion",
        "tiene_segunda_recuperacion",
        "tiene_equivalencia",
        "tiene_nsp",
        "tiene_resultado_final",
        "aprobo_ordinario",
        "necesito_recuperacion",
        "aprobo_por_recuperacion",
        "perdida_definitiva",
        "perdida_definitiva_sin_nsp",
    ]
    for column in boolean_columns:
        result[column] = result[column].fillna(False).astype(bool)

    for column in ("zona_ordinaria", "nota_examen_ordinario", "nota_total_ordinario", "nota_total_final"):
        result[column] = _to_numeric(result[column])

    result["es_desasignado"] = _to_bool(result["es_desasignado"]) | result["estado_asignacion"].eq(ASSIGNMENT_DROPPED)

    catalog = inputs["catalogo"][["codigo_curso", "nombre_curso", "semestre_pensum"]]
    config = inputs["configuracion"][
        [
            "codigo_curso",
            "area_academica",
            "tipo_curso_configurado",
            "requiere_laboratorio",
            "componente_practico",
            "curso_obligatorio",
            "curso_base",
            "curso_bloqueante",
            "cantidad_cursos_dependientes",
            "nivel_bloqueo_curricular",
        ]
    ]
    calendar = inputs["calendario"][["periodo_academico", "orden_periodo"]]
    enrolled = inputs["inscritos"][["estudiante_id_ofuscado", "cohorte_ingreso"]]
    offer_features = build_offer_section_features(inputs["oferta"])

    result = result.merge(catalog, on="codigo_curso", how="left")
    result = result.merge(config, on="codigo_curso", how="left")
    result = result.merge(calendar, on="periodo_academico", how="left")
    result = result.merge(enrolled, on="estudiante_id_ofuscado", how="left")
    result = result.merge(offer_features, on=OFFER_KEY_COLUMNS, how="left")
    result = add_continuity_and_risk(result, inputs["oferta"])

    ordered_columns = [
        "estudiante_id_ofuscado",
        "codigo_curso",
        "nombre_curso",
        "periodo_academico",
        "orden_periodo",
        "seccion",
        "semestre_pensum",
        "area_academica",
        "tipo_curso_configurado",
        "requiere_laboratorio",
        "componente_practico",
        "curso_obligatorio",
        "curso_base",
        "curso_bloqueante",
        "cantidad_cursos_dependientes",
        "nivel_bloqueo_curricular",
        "cohorte_ingreso",
        "zona_ordinaria",
        "nota_examen_ordinario",
        "nota_total_ordinario",
        "resultado_ordinario",
        "tiene_ordinario",
        "tiene_primera_recuperacion",
        "tiene_segunda_recuperacion",
        "tiene_equivalencia",
        "tiene_nsp",
        "nota_total_final",
        "resultado_final",
        "tiene_resultado_final",
        "aprobo_ordinario",
        "necesito_recuperacion",
        "aprobo_por_recuperacion",
        "perdida_definitiva",
        "perdida_definitiva_sin_nsp",
        "estado_asignacion",
        "es_desasignado",
        "fecha_asignacion",
        "fecha_desasignacion",
        "cupo_ofertado_oferta",
        "estudiantes_asignados_oferta",
        "estudiantes_con_nota_oferta",
        "tasa_ocupacion_cupo",
        "curso_aperturado",
        "curso_cancelado",
        "jornada",
        "horario",
        "modalidad",
        "curso_abierto_periodo_siguiente",
        "curso_abierto_siguiente_periodo",
        "periodo_siguiente_cronologico",
        "curso_abierto_en_periodo_posterior_2024",
        "periodo_posterior_disponible_2024",
        "espera_minima_periodos_2024",
        "sin_oferta_posterior_2024",
        "riesgo_retraso_simple",
        "riesgo_retraso_curricular",
        "riesgo_retraso_potencial",
        "riesgo_retraso_potencial_amplio",
    ]
    return result[ordered_columns]


def _aggregate_offer_course_period(oferta: pd.DataFrame) -> pd.DataFrame:
    work = oferta.copy()
    for column in ("cupo_ofertado", "estudiantes_asignados", "estudiantes_con_nota"):
        work[column] = _to_numeric(work[column]).fillna(0)

    grouped = work.groupby(COURSE_PERIOD_KEYS, as_index=False).agg(
        curso_aperturado=("curso_aperturado", lambda values: YES_VALUE if (values == YES_VALUE).any() else "No"),
        curso_cancelado=("curso_cancelado", lambda values: YES_VALUE if (values == YES_VALUE).any() else "No"),
        secciones_abiertas=("seccion", "nunique"),
        cupo_total_ofertado=("cupo_ofertado", "sum"),
        estudiantes_asignados=("estudiantes_asignados", "sum"),
        estudiantes_con_nota=("estudiantes_con_nota", "sum"),
    )
    grouped["tasa_ocupacion_cupo"] = safe_divide(grouped["estudiantes_asignados"], grouped["cupo_total_ofertado"])
    return grouped


def _aggregate_student_course_period(student_result: pd.DataFrame) -> pd.DataFrame:
    eligible = student_result[student_result["tiene_resultado_final"]].copy()
    grouped = eligible.groupby(COURSE_PERIOD_KEYS, as_index=False).agg(
        estudiantes_con_acta_ordinaria=("tiene_ordinario", "sum"),
        aprobados_ordinario=("aprobo_ordinario", "sum"),
        reprobados_ordinario=("resultado_ordinario", lambda values: int((values == RESULT_FAILED).sum())),
        estudiantes_recuperacion=("necesito_recuperacion", "sum"),
        aprobados_recuperacion=("aprobo_por_recuperacion", "sum"),
        perdida_definitiva=("perdida_definitiva", "sum"),
        nsp_total=("tiene_nsp", "sum"),
        equivalencias_total=("tiene_equivalencia", "sum"),
        estudiantes_sin_oportunidad_inmediata=("riesgo_retraso_simple", "sum"),
        estudiantes_en_riesgo_retraso_curricular=("riesgo_retraso_curricular", "sum"),
        promedio_zona_ordinaria=("zona_ordinaria", "mean"),
        promedio_examen_ordinario=("nota_examen_ordinario", "mean"),
        promedio_nota_total_ordinario=("nota_total_ordinario", "mean"),
        estudiantes_con_resultado_final=("tiene_resultado_final", "sum"),
        total_aprobados_finales=("resultado_final", lambda values: int((values == RESULT_APPROVED).sum())),
        total_recuperacion_2024=("necesito_recuperacion", "sum"),
    )
    desasignados = student_result.groupby(COURSE_PERIOD_KEYS, as_index=False).agg(
        estudiantes_desasignados=("es_desasignado", "sum")
    )
    return grouped.merge(desasignados, on=COURSE_PERIOD_KEYS, how="outer").fillna(0)


def build_course_period_summary(inputs: dict[str, pd.DataFrame], student_result: pd.DataFrame) -> pd.DataFrame:
    offer_summary = _aggregate_offer_course_period(inputs["oferta"])
    student_summary = _aggregate_student_course_period(student_result)
    base = offer_summary.merge(student_summary, on=COURSE_PERIOD_KEYS, how="outer")

    catalog = inputs["catalogo"][["codigo_curso", "nombre_curso", "semestre_pensum"]]
    config = inputs["configuracion"][
        [
            "codigo_curso",
            "area_academica",
            "tipo_curso_configurado",
            "requiere_laboratorio",
            "curso_obligatorio",
            "curso_base",
            "curso_bloqueante",
            "cantidad_cursos_dependientes",
            "nivel_bloqueo_curricular",
        ]
    ]
    calendar = inputs["calendario"][["periodo_academico", "orden_periodo"]]

    base = base.merge(catalog, on="codigo_curso", how="left")
    base = base.merge(config, on="codigo_curso", how="left")
    base = base.merge(calendar, on="periodo_academico", how="left")

    for column in [
        "secciones_abiertas",
        "cupo_total_ofertado",
        "estudiantes_asignados",
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
        "estudiantes_con_resultado_final",
        "total_aprobados_finales",
        "total_recuperacion_2024",
        "estudiantes_desasignados",
    ]:
        base[column] = _to_numeric(base[column]).fillna(0)

    base["tasa_aprobacion_ordinaria"] = safe_divide(base["aprobados_ordinario"], base["estudiantes_con_acta_ordinaria"])
    base["tasa_perdida_ordinaria"] = safe_divide(base["reprobados_ordinario"], base["estudiantes_con_acta_ordinaria"])
    base["tasa_recuperacion"] = safe_divide(base["estudiantes_recuperacion"], base["estudiantes_con_acta_ordinaria"])
    base["tasa_aprobacion_recuperacion"] = safe_divide(base["aprobados_recuperacion"], base["estudiantes_recuperacion"])
    base["tasa_perdida_definitiva"] = safe_divide(base["perdida_definitiva"], base["estudiantes_con_resultado_final"])
    base["indice_dependencia_recuperacion"] = safe_divide(base["aprobados_recuperacion"], base["total_aprobados_finales"])

    continuity_probe = add_continuity_and_risk(
        base.assign(
            estudiante_id_ofuscado="",
            seccion="",
            perdida_definitiva=False,
        ),
        inputs["oferta"],
    )
    base["curso_abierto_periodo_siguiente"] = continuity_probe["curso_abierto_periodo_siguiente"]
    base["curso_abierto_en_periodo_posterior_2024"] = continuity_probe["curso_abierto_en_periodo_posterior_2024"]

    ordered_columns = [
        "periodo_academico",
        "orden_periodo",
        "codigo_curso",
        "nombre_curso",
        "semestre_pensum",
        "area_academica",
        "tipo_curso_configurado",
        "requiere_laboratorio",
        "curso_obligatorio",
        "curso_base",
        "curso_bloqueante",
        "cantidad_cursos_dependientes",
        "nivel_bloqueo_curricular",
        "curso_aperturado",
        "curso_cancelado",
        "secciones_abiertas",
        "cupo_total_ofertado",
        "estudiantes_asignados",
        "estudiantes_desasignados",
        "estudiantes_con_nota",
        "tasa_ocupacion_cupo",
        "estudiantes_con_acta_ordinaria",
        "aprobados_ordinario",
        "reprobados_ordinario",
        "estudiantes_recuperacion",
        "aprobados_recuperacion",
        "perdida_definitiva",
        "nsp_total",
        "equivalencias_total",
        "tasa_aprobacion_ordinaria",
        "tasa_perdida_ordinaria",
        "tasa_recuperacion",
        "tasa_aprobacion_recuperacion",
        "tasa_perdida_definitiva",
        "indice_dependencia_recuperacion",
        "promedio_zona_ordinaria",
        "promedio_examen_ordinario",
        "promedio_nota_total_ordinario",
        "curso_abierto_periodo_siguiente",
        "curso_abierto_en_periodo_posterior_2024",
        "estudiantes_sin_oportunidad_inmediata",
        "estudiantes_en_riesgo_retraso_curricular",
    ]
    return base[ordered_columns].sort_values(["orden_periodo", "codigo_curso"]).reset_index(drop=True)


def _offer_pattern(row: pd.Series) -> str:
    periods_open = [period for period in PERIOD_ORDER if row[f"abierto_{period}"]]
    count = len(periods_open)
    semester_open = {"S1", "S2"} & set(periods_open)
    vacation_open = {"V1", "V2"} & set(periods_open)

    if count == 0:
        return "sin_oferta_2024"
    if count >= 3:
        return "oferta_continua"
    if count == 1:
        return "oferta_vacaciones" if vacation_open and not semester_open else "oferta_unica"
    if set(periods_open) == {"S1", "S2"}:
        return "oferta_semestral"
    if vacation_open and not semester_open:
        return "oferta_vacaciones"
    if semester_open and vacation_open:
        return "oferta_mixta"
    return "oferta_irregular"


def build_continuity_dataset(inputs: dict[str, pd.DataFrame], course_period: pd.DataFrame) -> pd.DataFrame:
    catalog = inputs["catalogo"][["codigo_curso", "nombre_curso", "semestre_pensum"]]
    config = inputs["configuracion"][
        [
            "codigo_curso",
            "area_academica",
            "curso_base",
            "curso_bloqueante",
            "cantidad_cursos_dependientes",
            "nivel_bloqueo_curricular",
        ]
    ]
    base = catalog.merge(config, on="codigo_curso", how="left")

    active_offer = inputs["oferta"][
        inputs["oferta"]["curso_aperturado"].eq(YES_VALUE)
        & ~inputs["oferta"]["curso_cancelado"].eq(YES_VALUE)
    ]
    open_pivot = (
        active_offer.assign(abierto=True)
        .pivot_table(index="codigo_curso", columns="periodo_academico", values="abierto", aggfunc="any", fill_value=False)
        .reset_index()
    )
    for period in PERIOD_ORDER:
        if period not in open_pivot.columns:
            open_pivot[period] = False
    open_pivot = open_pivot.rename(columns={period: f"abierto_{period}" for period in PERIOD_ORDER})
    base = base.merge(open_pivot, on="codigo_curso", how="left")
    for period in PERIOD_ORDER:
        base[f"abierto_{period}"] = base[f"abierto_{period}"].fillna(False).astype(bool)

    base["cantidad_periodos_abierto"] = base[[f"abierto_{period}" for period in PERIOD_ORDER]].sum(axis=1)
    base["indice_continuidad_oferta"] = base["cantidad_periodos_abierto"] / len(PERIOD_ORDER)
    base["patron_oferta"] = base.apply(_offer_pattern, axis=1)

    summary = course_period.groupby("codigo_curso", as_index=False).agg(
        total_estudiantes_asignados_2024=("estudiantes_asignados", "sum"),
        total_estudiantes_con_nota_2024=("estudiantes_con_nota", "sum"),
        total_perdida_definitiva_2024=("perdida_definitiva", "sum"),
        total_recuperacion_2024=("estudiantes_recuperacion", "sum"),
        estudiantes_sin_oportunidad_inmediata_2024=("estudiantes_sin_oportunidad_inmediata", "sum"),
        estudiantes_en_riesgo_retraso_curricular_2024=("estudiantes_en_riesgo_retraso_curricular", "sum"),
        tasa_ocupacion_promedio_2024=("tasa_ocupacion_cupo", "mean"),
        estudiantes_con_resultado_final_2024=("estudiantes_con_acta_ordinaria", "sum"),
    )
    base = base.merge(summary, on="codigo_curso", how="left")
    numeric_columns = [
        "total_estudiantes_asignados_2024",
        "total_estudiantes_con_nota_2024",
        "total_perdida_definitiva_2024",
        "total_recuperacion_2024",
        "estudiantes_sin_oportunidad_inmediata_2024",
        "estudiantes_en_riesgo_retraso_curricular_2024",
        "estudiantes_con_resultado_final_2024",
    ]
    for column in numeric_columns:
        base[column] = _to_numeric(base[column]).fillna(0)
    base["tasa_perdida_definitiva_2024"] = safe_divide(
        base["total_perdida_definitiva_2024"], base["estudiantes_con_resultado_final_2024"]
    )
    base["tasa_recuperacion_2024"] = safe_divide(
        base["total_recuperacion_2024"], base["estudiantes_con_resultado_final_2024"]
    )
    ordered_columns = [
        "codigo_curso",
        "nombre_curso",
        "semestre_pensum",
        "area_academica",
        "curso_base",
        "curso_bloqueante",
        "cantidad_cursos_dependientes",
        "nivel_bloqueo_curricular",
        "abierto_S1",
        "abierto_V1",
        "abierto_S2",
        "abierto_V2",
        "cantidad_periodos_abierto",
        "indice_continuidad_oferta",
        "patron_oferta",
        "total_estudiantes_asignados_2024",
        "total_estudiantes_con_nota_2024",
        "total_perdida_definitiva_2024",
        "total_recuperacion_2024",
        "tasa_perdida_definitiva_2024",
        "tasa_recuperacion_2024",
        "estudiantes_sin_oportunidad_inmediata_2024",
        "estudiantes_en_riesgo_retraso_curricular_2024",
        "tasa_ocupacion_promedio_2024",
    ]
    return (
        base.drop(columns=["estudiantes_con_resultado_final_2024"])[ordered_columns]
        .sort_values("codigo_curso")
        .reset_index(drop=True)
    )


def build_clustering_dataset(continuity: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "codigo_curso",
        "nombre_curso",
        "area_academica",
        "curso_base",
        "curso_bloqueante",
        "nivel_bloqueo_curricular",
        "tasa_perdida_definitiva_2024",
        "tasa_recuperacion_2024",
        "indice_continuidad_oferta",
        "estudiantes_sin_oportunidad_inmediata_2024",
        "estudiantes_en_riesgo_retraso_curricular_2024",
        "cantidad_cursos_dependientes",
        "tasa_ocupacion_promedio_2024",
        "total_estudiantes_asignados_2024",
        "total_estudiantes_con_nota_2024",
    ]
    result = continuity[columns].copy()
    for column in [
        "tasa_perdida_definitiva_2024",
        "tasa_recuperacion_2024",
        "indice_continuidad_oferta",
        "estudiantes_sin_oportunidad_inmediata_2024",
        "estudiantes_en_riesgo_retraso_curricular_2024",
        "cantidad_cursos_dependientes",
        "tasa_ocupacion_promedio_2024",
        "total_estudiantes_asignados_2024",
        "total_estudiantes_con_nota_2024",
    ]:
        result[column] = _to_numeric(result[column]).fillna(0)
    return result


def build_classification_dataset(student_result: pd.DataFrame) -> pd.DataFrame:
    model = student_result[
        student_result["tiene_resultado_final"].fillna(False).astype(bool)
        & ~student_result["es_desasignado"].fillna(False).astype(bool)
    ].copy()
    columns = [
        "codigo_curso",
        "periodo_academico",
        "semestre_pensum",
        "area_academica",
        "tipo_curso_configurado",
        "requiere_laboratorio",
        "componente_practico",
        "curso_obligatorio",
        "curso_base",
        "cantidad_cursos_dependientes",
        "nivel_bloqueo_curricular",
        "cohorte_ingreso",
        "zona_ordinaria",
        "cupo_ofertado_oferta",
        "tasa_ocupacion_cupo",
        "curso_abierto_periodo_siguiente",
        "curso_abierto_siguiente_periodo",
        "necesito_recuperacion",
        "perdida_definitiva",
        "riesgo_retraso_potencial",
        "riesgo_retraso_potencial_amplio",
    ]
    return model[columns].reset_index(drop=True)


def _zone_item(value: Any) -> str:
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return "zona_sin_dato"
    if numeric < 40:
        return "zona_baja"
    if numeric <= 55:
        return "zona_media"
    return "zona_alta"


def _occupancy_item(value: Any) -> str:
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return "ocupacion_sin_dato"
    if numeric < 0.6:
        return "ocupacion_baja"
    if numeric <= 0.9:
        return "ocupacion_media"
    return "ocupacion_alta"


def _safe_item(prefix: str, value: Any) -> str:
    text = str(value).strip().lower()
    text = (
        text.replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
        .replace(",", "")
        .replace(".", "")
    )
    return f"{prefix}_{text}" if text else f"{prefix}_sin_dato"


def build_association_dataset(student_result: pd.DataFrame) -> pd.DataFrame:
    source = student_result[
        student_result["tiene_resultado_final"].fillna(False).astype(bool)
        & ~student_result["es_desasignado"].fillna(False).astype(bool)
    ].copy()
    item_sets: list[set[str]] = []
    for row in source.itertuples(index=False):
        items = {
            _zone_item(getattr(row, "zona_ordinaria")),
            _occupancy_item(getattr(row, "tasa_ocupacion_cupo")),
            _safe_item("periodo", getattr(row, "periodo_academico")),
            _safe_item("area", getattr(row, "area_academica")),
            _safe_item("semestre", getattr(row, "semestre_pensum")),
            _safe_item("bloqueo", getattr(row, "nivel_bloqueo_curricular")),
        }
        items.add("perdio" if getattr(row, "perdida_definitiva") else "aprobo")
        items.add("recuperacion" if getattr(row, "necesito_recuperacion") else "sin_recuperacion")
        items.add("no_abierto_siguiente" if not getattr(row, "curso_abierto_periodo_siguiente") else "abierto_siguiente")
        items.add("riesgo_retraso" if getattr(row, "riesgo_retraso_potencial") else "sin_riesgo_retraso")
        items.add("curso_base" if getattr(row, "curso_base") == YES_VALUE else "curso_no_base")
        items.add("curso_obligatorio" if getattr(row, "curso_obligatorio") == YES_VALUE else "curso_no_obligatorio")
        items.add("requiere_laboratorio" if getattr(row, "requiere_laboratorio") == YES_VALUE else "no_requiere_laboratorio")
        item_sets.append(items)

    all_items = sorted({item for items in item_sets for item in items})
    rows = []
    for index, items in enumerate(item_sets, start=1):
        rows.append(
            {
                "transaccion_id": f"TX-{index:05d}",
                **{item: item in items for item in all_items},
            }
        )
    return pd.DataFrame(rows)


def build_output_summary(outputs: list[DerivedOutput]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "dataset": output.dataset,
                "archivo": _relative_path(output.path),
                "filas": output.rows,
                "columnas": output.columns,
                "conclusion": output.conclusion,
            }
            for output in outputs
        ]
    )


def build_target_distribution(classification: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for target in [
        "necesito_recuperacion",
        "perdida_definitiva",
        "riesgo_retraso_potencial",
        "riesgo_retraso_potencial_amplio",
    ]:
        counts = classification[target].value_counts(dropna=False).to_dict()
        total = len(classification)
        for value, count in counts.items():
            rows.append(
                {
                    "target": target,
                    "valor": value,
                    "conteo": int(count),
                    "porcentaje": round((count / total) * 100, 2) if total else 0,
                }
            )
    return pd.DataFrame(rows)


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


def write_report(summary: pd.DataFrame, target_distribution: pd.DataFrame) -> None:
    content = f"""# Datasets derivados

## Objetivo

Construir las unidades analiticas principales para indicadores, continuidad,
modelos, clustering y reglas de asociacion.

## Archivos generados

{_markdown_table(summary)}

## Distribucion de targets de modelado

{_markdown_table(target_distribution)}

## Definicion e interpretacion de targets

Los targets se derivan de registros academicos observados en actas y de la
continuidad de oferta disponible para 2024. No deben interpretarse como causas,
sino como etiquetas operativas para describir resultados y riesgos potenciales
bajo los datos registrados.

| target | valor verdadero cuando | interpretacion | advertencia metodologica |
| --- | --- | --- | --- |
| `necesito_recuperacion` | El estudiante tiene registro de primera o segunda recuperacion para el curso. | El curso no fue aprobado directamente en ordinario y requirio una oportunidad posterior registrada. | No mide por si solo si la recuperacion fue aprobada o perdida; para eso se usa `aprobo_por_recuperacion` o `perdida_definitiva`. |
| `perdida_definitiva` | El ultimo resultado observable del curso no fue aprobado. La ultima oportunidad se toma en este orden de prioridad: equivalencia, segunda recuperacion, primera recuperacion u ordinario. | Representa que, con las oportunidades registradas en acta, el estudiante no cerro el curso como aprobado. Puede incluir perdida en ordinario sin recuperacion registrada, perdida despues de recuperacion o un ultimo resultado especial no aprobado como `NSP`. | No significa necesariamente que el estudiante no tuvo acceso a recuperacion. Indica el resultado final observado en los datos disponibles. Para separar sensibilidad por inasistencia existe `perdida_definitiva_sin_nsp` en el dataset maestro. |
| `riesgo_retraso_potencial` | Existe `perdida_definitiva`, el curso no se oferta en el periodo inmediato posterior y el curso cumple condicion bloqueante curricular. | Identifica casos donde la perdida de un curso bloqueante coincide con ausencia de oferta inmediata posterior, lo que puede generar retraso academico potencial. | Es un indicador potencial, no una prueba causal ni una medicion individual definitiva de retraso. |
| `riesgo_retraso_potencial_amplio` | Existe `perdida_definitiva` y el curso no se oferta en el periodo inmediato posterior, sin exigir condicion bloqueante. | Version mas amplia del riesgo, util para sensibilidad y comparacion con el target curricular estricto. | Puede incluir cursos con menor impacto curricular directo; por eso se reporta separado del target principal. |

## Tratamiento de desasignados

Los registros con `estado_asignacion=desasignado` se conservan en
`ds_estudiante_curso_resultado_2024.csv` porque forman parte de la trazabilidad
de asignaciones y permiten comparar asignacion inicial contra participacion
evaluada. Sin embargo, se excluyen de `ds_modelo_clasificacion.csv` porque no
representan un resultado academico evaluado comparable en acta.

Incluir desasignados en modelos de perdida, recuperacion o riesgo potencial
mezclaria procesos administrativos previos al cierre del curso con resultados
academicos observados. Tambien obligaria a asignar etiquetas no observadas a
casos que no completaron la trayectoria evaluable del curso.

## Decisiones metodologicas

- `ds_estudiante_curso_resultado_2024.csv` parte de asignaciones para conservar desasignados y cruza resultados de actas cuando existen.
- Los registros desasignados se conservan en el dataset maestro, pero se excluyen de `ds_modelo_clasificacion.csv`.
- `resultado_final` se toma de la ultima oportunidad registrada bajo prioridad academica: equivalencia, segunda recuperacion, primera recuperacion u ordinario.
- `perdida_definitiva` indica que el ultimo resultado observable no fue aprobado; no distingue por si sola entre ausencia de recuperacion registrada y perdida posterior a recuperacion.
- `riesgo_retraso_potencial` requiere perdida definitiva, ausencia de oferta inmediata posterior y condicion bloqueante del curso.
- `riesgo_retraso_potencial_amplio` requiere perdida definitiva y ausencia de oferta inmediata posterior.
- Los datasets de modelado no incluyen `docente`, `nota_examen_ordinario`, `nota_total_ordinario`, `nota_total_final` ni `resultado_final` como predictores.

## Conclusion

La Fase 4 deja construidos los datasets derivados necesarios para iniciar EDA,
indicadores, inferencia y modelos. Los targets presentan distribuciones
verificables y se separa el dataset maestro del dataset de modelado para evitar
mezclar desasignados o variables con fuga de informacion.
"""
    write_text(DERIVED_REPORT_PATH, content)


def save_derived_outputs(
    student_result: pd.DataFrame,
    course_period: pd.DataFrame,
    continuity: pd.DataFrame,
    clustering: pd.DataFrame,
    classification: pd.DataFrame,
    association: pd.DataFrame,
) -> list[DerivedOutput]:
    datasets = [
        (
            "ds_estudiante_curso_resultado_2024",
            STUDENT_RESULT_PATH,
            student_result,
            "Unidad estudiante-curso-periodo construida desde asignaciones y actas.",
        ),
        (
            "ds_resumen_curso_periodo_2024",
            COURSE_PERIOD_PATH,
            course_period,
            "Unidad curso-periodo lista para indicadores y regresion agregada.",
        ),
        (
            "ds_continuidad_oferta_2024",
            CONTINUITY_PATH,
            continuity,
            "Unidad curso anual lista para analizar continuidad de oferta.",
        ),
        (
            "ds_cursos_criticos_clustering",
            CLUSTERING_PATH,
            clustering,
            "Dataset numerico y contextual preparado para clustering.",
        ),
        (
            "ds_modelo_clasificacion",
            CLASSIFICATION_PATH,
            classification,
            "Dataset de modelado sin desasignados ni variables prohibidas por fuga.",
        ),
        (
            "ds_reglas_asociacion",
            ASSOCIATION_PATH,
            association,
            "Matriz transaccional codificada para reglas de asociacion.",
        ),
    ]

    outputs = []
    for dataset_name, path, df, conclusion in datasets:
        save_table(df, path)
        outputs.append(DerivedOutput(dataset_name, path, len(df), len(df.columns), conclusion))
    return outputs


def main() -> None:
    ensure_project_directories()
    inputs = load_inputs()
    passing_grade = get_passing_grade(inputs["parametros"])

    student_result = build_student_course_result(inputs, passing_grade)
    course_period = build_course_period_summary(inputs, student_result)
    continuity = build_continuity_dataset(inputs, course_period)
    clustering = build_clustering_dataset(continuity)
    classification = build_classification_dataset(student_result)
    association = build_association_dataset(student_result)

    outputs = save_derived_outputs(
        student_result,
        course_period,
        continuity,
        clustering,
        classification,
        association,
    )
    summary = build_output_summary(outputs)
    target_distribution = build_target_distribution(classification)
    save_table(summary, DERIVED_SUMMARY_PATH)
    save_table(target_distribution, TARGET_DISTRIBUTION_PATH)
    write_report(summary, target_distribution)

    print("Construccion de datasets derivados completada.")
    print(f"Resumen: {DERIVED_SUMMARY_PATH}")
    print(f"Distribucion de targets: {TARGET_DISTRIBUTION_PATH}")
    print(f"Reporte: {DERIVED_REPORT_PATH}")


if __name__ == "__main__":
    main()
