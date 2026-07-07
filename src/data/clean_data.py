"""Limpieza, normalizacion y consolidacion inicial de datasets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.config.settings import (
    ASSIGNMENT_DROPPED,
    DATASET_SPECS,
    DOCS_DIR,
    INTERIM_DATA_DIR,
    NO_VALUE,
    PROCESSED_DATA_DIR,
    PROJECT_ROOT,
    RESULT_NSP,
    SPECIAL_EQ_VALUE,
    TABLES_DIR,
    YES_VALUE,
)
from src.data.load_data import load_all_raw_datasets
from src.data.utils import (
    clean_text_series,
    ensure_project_directories,
    parse_date_or_range_end,
    parse_date_or_range_start,
    parse_numeric,
    save_table,
    write_text,
)


OFFER_KEY_COLUMNS = ["periodo_academico", "codigo_curso", "seccion"]
OFFER_DUPLICATES_PATH = TABLES_DIR / "02_oferta_duplicados_resueltos.csv"
CONSOLIDATED_OFFER_PATH = PROCESSED_DATA_DIR / "04_oferta_academica_2024_consolidada.csv"
ETL_DECISIONS_PATH = DOCS_DIR / "decisiones_etl.md"


@dataclass(frozen=True)
class EtlSummary:
    """Resumen de ejecucion de la fase ETL."""

    dataset: str
    archivo_salida: str
    filas_entrada: int
    filas_salida: int
    columnas_salida: int
    observacion: str


def _non_empty_values(series: pd.Series) -> list[str]:
    return [str(value) for value in clean_text_series(series).dropna().tolist()]


def _unique_non_empty(series: pd.Series) -> list[str]:
    values = _non_empty_values(series)
    return list(dict.fromkeys(values))


def _join_unique(series: pd.Series, separator: str = "; ") -> str:
    return separator.join(_unique_non_empty(series))


def _first_non_empty(series: pd.Series) -> str:
    values = _unique_non_empty(series)
    return values[0] if values else ""


def _si_if_any(series: pd.Series) -> str:
    values = {value.lower() for value in _unique_non_empty(series)}
    return YES_VALUE if YES_VALUE.lower() in values else NO_VALUE


def _max_numeric_as_text(series: pd.Series) -> str:
    numeric = parse_numeric(series)
    if numeric.notna().any():
        value = numeric.max()
        if float(value).is_integer():
            return str(int(value))
        return str(float(value))
    return _first_non_empty(series)


def _date_min_or_single(series: pd.Series) -> str:
    values = _unique_non_empty(series)
    if len(values) <= 1:
        return values[0] if values else ""
    parsed = pd.Series([parse_date_or_range_start(value) for value in values]).dropna()
    if parsed.empty:
        return _join_unique(series)
    return parsed.min().strftime("%Y-%m-%d")


def _date_max_or_single(series: pd.Series) -> str:
    values = _unique_non_empty(series)
    if len(values) <= 1:
        return values[0] if values else ""
    parsed = pd.Series([parse_date_or_range_end(value) for value in values]).dropna()
    if parsed.empty:
        return _join_unique(series)
    return parsed.max().strftime("%Y-%m-%d")


def _normalize_course_code(series: pd.Series) -> pd.Series:
    cleaned = clean_text_series(series)
    return cleaned.str.replace(r"\.0$", "", regex=True)


def _format_date_series(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce")
    return parsed.dt.strftime("%Y-%m-%d")


def normalize_base_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia espacios, codigos y etiquetas comunes sin eliminar registros."""

    result = df.copy()
    for column in result.columns:
        result[column] = clean_text_series(result[column])

    for column in ("codigo_curso", "codigo_prerrequisito"):
        if column in result.columns:
            result[column] = _normalize_course_code(result[column])

    for column in ("periodo_academico", "periodo_inscripcion", "seccion"):
        if column in result.columns:
            result[column] = clean_text_series(result[column]).str.upper()

    return result


def add_dataset_specific_columns(dataset_name: str, df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columnas auxiliares utiles para validacion y fases posteriores."""

    result = df.copy()

    if dataset_name == "actas_notas":
        result["fecha_acta_dt"] = _format_date_series(result["fecha_acta"])
        result["zona_num"] = parse_numeric(result["zona"])
        result["nota_examen_num"] = parse_numeric(result["nota_examen"], special_values={RESULT_NSP})
        result["nota_total_num"] = parse_numeric(result["nota_total"])
        result["es_equivalencia"] = result["nota_total"].eq(SPECIAL_EQ_VALUE)
        result["es_nsp"] = result["resultado"].eq(RESULT_NSP)

    if dataset_name == "asignaciones":
        result["fecha_asignacion_dt"] = _format_date_series(result["fecha_asignacion"])
        result["fecha_desasignacion_dt"] = _format_date_series(result["fecha_desasignacion"])
        result["es_desasignado"] = result["estado_asignacion"].eq(ASSIGNMENT_DROPPED)

    if dataset_name == "oferta_academica":
        result["fecha_inicio_dt"] = _format_date_series(result["fecha_inicio"])
        result["fecha_fin_inicio_dt"] = pd.Series(
            [parse_date_or_range_start(value) for value in result["fecha_fin"]]
        ).dt.strftime("%Y-%m-%d")
        result["fecha_fin_fin_dt"] = pd.Series(
            [parse_date_or_range_end(value) for value in result["fecha_fin"]]
        ).dt.strftime("%Y-%m-%d")
        for column in ("cupo_ofertado", "estudiantes_asignados", "estudiantes_con_nota"):
            result[f"{column}_num"] = parse_numeric(result[column])

    if dataset_name == "calendario_academico":
        for column in (
            "fecha_inicio_clases",
            "fecha_fin_clases",
            "fecha_examen_final",
            "fecha_primera_recuperacion",
            "fecha_segunda_recuperacion",
        ):
            result[f"{column}_inicio_dt"] = pd.Series(
                [parse_date_or_range_start(value) for value in result[column]]
            ).dt.strftime("%Y-%m-%d")
            result[f"{column}_fin_dt"] = pd.Series(
                [parse_date_or_range_end(value) for value in result[column]]
            ).dt.strftime("%Y-%m-%d")

    return result


def normalize_all_datasets(datasets: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Normaliza los datasets raw para guardarlos en data/interim."""

    normalized: dict[str, pd.DataFrame] = {}
    for dataset_name, df in datasets.items():
        base = normalize_base_dataframe(df)
        normalized[dataset_name] = add_dataset_specific_columns(dataset_name, base)
    return normalized


def save_interim_datasets(normalized: dict[str, pd.DataFrame]) -> list[EtlSummary]:
    summaries: list[EtlSummary] = []
    for dataset_name, df in normalized.items():
        filename = DATASET_SPECS[dataset_name].filename.replace(".csv", "_normalizado.csv")
        path = INTERIM_DATA_DIR / filename
        save_table(df, path)
        summaries.append(
            EtlSummary(
                dataset=dataset_name,
                archivo_salida=_relative_path(path),
                filas_entrada=len(df),
                filas_salida=len(df),
                columnas_salida=len(df.columns),
                observacion="Dataset normalizado sin eliminar registros.",
            )
        )
    return summaries


def build_offer_duplicate_log(oferta: pd.DataFrame) -> pd.DataFrame:
    duplicated = oferta[oferta.duplicated(OFFER_KEY_COLUMNS, keep=False)].copy()
    rows: list[dict[str, Any]] = []

    for key_values, group in duplicated.groupby(OFFER_KEY_COLUMNS, dropna=False):
        key_dict = dict(zip(OFFER_KEY_COLUMNS, key_values, strict=True))
        rows.append(
            {
                **key_dict,
                "registros_originales": len(group),
                "nombre_curso_valores": _join_unique(group["nombre_curso"]),
                "cupo_ofertado_valores": _join_unique(group["cupo_ofertado"]),
                "estudiantes_asignados_valores": _join_unique(group["estudiantes_asignados"]),
                "estudiantes_con_nota_valores": _join_unique(group["estudiantes_con_nota"]),
                "jornada_valores": _join_unique(group["jornada"]),
                "horario_valores": _join_unique(group["horario"]),
                "salon_valores": _join_unique(group["salon"]),
                "modalidad_valores": _join_unique(group["modalidad"]),
                "fecha_inicio_valores": _join_unique(group["fecha_inicio"]),
                "fecha_fin_valores": _join_unique(group["fecha_fin"]),
                "metodo_match_valores": _join_unique(group["metodo_match"]),
                "observaciones_valores": _join_unique(group["observaciones"]),
                "criterio_resolucion": (
                    "Se consolido por periodo_academico + codigo_curso + seccion; "
                    "se concatenaron franjas/atributos textuales y se conservaron maximos numericos."
                ),
            }
        )

    return pd.DataFrame(rows)


def consolidate_offer(oferta: pd.DataFrame) -> pd.DataFrame:
    """Consolida oferta academica por periodo, curso y seccion."""

    aggregation = {
        "nombre_curso": _first_non_empty,
        "curso_aperturado": _si_if_any,
        "curso_cancelado": _si_if_any,
        "cupo_ofertado": _max_numeric_as_text,
        "estudiantes_asignados": _max_numeric_as_text,
        "estudiantes_con_nota": _max_numeric_as_text,
        "jornada": _join_unique,
        "horario": _join_unique,
        "salon": _join_unique,
        "modalidad": _join_unique,
        "fecha_inicio": _date_min_or_single,
        "fecha_fin": _date_max_or_single,
        "fuente_archivo": _join_unique,
        "metodo_match": _join_unique,
        "observaciones": _join_unique,
    }

    consolidated = (
        oferta.groupby(OFFER_KEY_COLUMNS, dropna=False, as_index=False)
        .agg(aggregation)
        .sort_values(OFFER_KEY_COLUMNS)
        .reset_index(drop=True)
    )

    ordered_columns = [
        "periodo_academico",
        "codigo_curso",
        "nombre_curso",
        "seccion",
        "curso_aperturado",
        "curso_cancelado",
        "cupo_ofertado",
        "estudiantes_asignados",
        "estudiantes_con_nota",
        "jornada",
        "horario",
        "salon",
        "modalidad",
        "fecha_inicio",
        "fecha_fin",
        "fuente_archivo",
        "metodo_match",
        "observaciones",
    ]
    return consolidated[ordered_columns]


def _summaries_to_dataframe(summaries: list[EtlSummary]) -> pd.DataFrame:
    return pd.DataFrame([summary.__dict__ for summary in summaries])


def _relative_path(path: Any) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def _markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_Sin registros._"

    display_df = df.fillna("").astype(str)
    headers = list(display_df.columns)
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    rows = [
        "| " + " | ".join(row[column].replace("|", "\\|") for column in headers) + " |"
        for _, row in display_df.iterrows()
    ]
    return "\n".join([header_line, separator_line, *rows])


def write_etl_decisions(
    *,
    raw_offer_rows: int,
    consolidated_offer_rows: int,
    duplicate_keys: int,
    summaries: list[EtlSummary],
) -> None:
    summaries_df = _summaries_to_dataframe(summaries)
    content = f"""# Decisiones ETL

Este documento registra las decisiones de limpieza, normalizacion e integracion
aplicadas durante el proyecto.

## Fase 3: Limpieza, normalizacion y ETL

### Alcance

- No se modificaron archivos en `data/raw/`.
- Los datasets normalizados se guardaron en `data/interim/`.
- La oferta academica consolidada se guardo en `data/processed/`.
- La columna `docente` se excluyo del archivo consolidado final de oferta.

### Normalizaciones aplicadas

- Se limpiaron espacios al inicio y al final de campos textuales.
- Se redujeron espacios repetidos dentro de texto.
- Se preservaron codigos de curso como texto para no perder ceros a la izquierda.
- Se normalizaron `periodo_academico`, `periodo_inscripcion` y `seccion` en mayusculas.
- Se agregaron columnas numericas auxiliares para notas y conteos cuando aplica.
- Se agregaron columnas auxiliares de fecha parseada cuando aplica.
- Se agregaron banderas `es_equivalencia`, `es_nsp` y `es_desasignado`.

### Consolidacion de oferta academica

- Filas originales de oferta: {raw_offer_rows}.
- Filas consolidadas de oferta: {consolidated_offer_rows}.
- Llaves duplicadas documentadas: {duplicate_keys}.
- Llave de consolidacion: `periodo_academico + codigo_curso + seccion`.

Reglas aplicadas:

- `nombre_curso`: primer valor no vacio.
- `curso_aperturado` y `curso_cancelado`: `Si` si al menos un registro del grupo indica `Si`.
- `cupo_ofertado`, `estudiantes_asignados`, `estudiantes_con_nota`: maximo numerico del grupo.
- `jornada`, `horario`, `salon`, `modalidad`, `fuente_archivo`, `metodo_match`, `observaciones`: valores unicos concatenados con `; `.
- `fecha_inicio`: valor unico original si no hay conflicto; si hay multiples valores, fecha minima parseada.
- `fecha_fin`: valor unico original si no hay conflicto; si hay multiples valores, fecha maxima parseada.

### Archivos generados

{_markdown_table(summaries_df)}

### Conclusion

La Fase 3 deja los datasets raw normalizados en `data/interim/` y una version
consolidada de oferta academica lista para construir datasets derivados. La
consolidacion resuelve duplicados de llave sin eliminar informacion de horarios
o trazabilidad de fuente.
"""
    write_text(ETL_DECISIONS_PATH, content)


def main() -> None:
    ensure_project_directories()
    raw_datasets = load_all_raw_datasets()
    normalized = normalize_all_datasets(raw_datasets)

    summaries = save_interim_datasets(normalized)

    oferta_normalizada = normalized["oferta_academica"]
    duplicate_log = build_offer_duplicate_log(oferta_normalizada)
    consolidated_offer = consolidate_offer(oferta_normalizada)

    save_table(duplicate_log, OFFER_DUPLICATES_PATH)
    save_table(consolidated_offer, CONSOLIDATED_OFFER_PATH)

    summaries.append(
        EtlSummary(
            dataset="oferta_academica_consolidada",
            archivo_salida=_relative_path(CONSOLIDATED_OFFER_PATH),
            filas_entrada=len(oferta_normalizada),
            filas_salida=len(consolidated_offer),
            columnas_salida=len(consolidated_offer.columns),
            observacion="Oferta consolidada sin columna docente.",
        )
    )

    write_etl_decisions(
        raw_offer_rows=len(oferta_normalizada),
        consolidated_offer_rows=len(consolidated_offer),
        duplicate_keys=len(duplicate_log),
        summaries=summaries,
    )

    print("Limpieza y ETL inicial completados.")
    print(f"Oferta consolidada: {CONSOLIDATED_OFFER_PATH}")
    print(f"Duplicados resueltos: {OFFER_DUPLICATES_PATH}")
    print(f"Decisiones ETL: {ETL_DECISIONS_PATH}")


if __name__ == "__main__":
    main()
