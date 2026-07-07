"""Validacion inicial y perfilamiento de datasets raw."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from src.config.settings import (
    ASSIGNMENT_DROPPED,
    ASSIGNMENT_WITH_GRADE,
    DATASET_SPECS,
    EVALUATION_EQUIVALENCE,
    EVALUATION_FIRST_RECOVERY,
    EVALUATION_ORDINARY,
    EVALUATION_SECOND_RECOVERY,
    PERIOD_ORDER,
    REPORTS_DIR,
    RESULT_APPROVED,
    RESULT_FAILED,
    RESULT_NSP,
    TABLES_DIR,
)
from src.data.load_data import build_raw_dataset_inventory, load_all_raw_datasets
from src.data.utils import (
    EMPTY_VALUES,
    clean_text_series,
    ensure_project_directories,
    parse_numeric,
    save_table,
    write_text,
)


REPORT_PATH = REPORTS_DIR / "data_quality_report.md"
DATASET_PROFILE_PATH = TABLES_DIR / "01_dataset_profile.csv"
SCHEMA_VALIDATION_PATH = TABLES_DIR / "01_schema_validation.csv"
DATA_QUALITY_FINDINGS_PATH = TABLES_DIR / "01_data_quality_findings.csv"

VALID_PERIODS = set(PERIOD_ORDER)
VALID_RESULTS = {RESULT_APPROVED, RESULT_FAILED, RESULT_NSP}
VALID_EVALUATION_OPPORTUNITIES = {
    EVALUATION_ORDINARY,
    EVALUATION_FIRST_RECOVERY,
    EVALUATION_SECOND_RECOVERY,
    EVALUATION_EQUIVALENCE,
}
VALID_ASSIGNMENT_STATES = {ASSIGNMENT_WITH_GRADE, ASSIGNMENT_DROPPED}

EXPECTED_EMPTY_COLUMNS: dict[str, set[str]] = {
    "actas_notas": set(),
    "asignaciones": {"fecha_desasignacion"},
    "oferta_academica": {"docente", "salon", "observaciones"},
    "malla_prerrequisitos": {"codigo_prerrequisito", "semestre_prerrequisito"},
    "calendario_academico": {"fecha_primera_recuperacion", "fecha_segunda_recuperacion"},
    "parametros_academicos": {"observaciones"},
    "configuracion_cursos": {"observaciones"},
}


@dataclass(frozen=True)
class Finding:
    """Hallazgo de calidad de datos."""

    severidad: str
    dataset: str
    regla: str
    columna: str
    hallazgo: str
    cantidad: int
    detalle: str


def _is_empty(series: pd.Series) -> pd.Series:
    cleaned = series.astype("string").str.strip().str.lower()
    return series.isna() | cleaned.isin(EMPTY_VALUES)


def _format_values(values: list[Any], limit: int = 12) -> str:
    cleaned_values = [str(value) for value in values if str(value) != ""]
    if not cleaned_values:
        return ""
    shown = cleaned_values[:limit]
    suffix = "" if len(
        cleaned_values) <= limit else f"; +{len(cleaned_values) - limit} mas"
    return "; ".join(shown) + suffix


def _add_finding(
    findings: list[Finding],
    *,
    severidad: str,
    dataset: str,
    regla: str,
    columna: str = "",
    hallazgo: str,
    cantidad: int = 0,
    detalle: str = "",
) -> None:
    findings.append(
        Finding(
            severidad=severidad,
            dataset=dataset,
            regla=regla,
            columna=columna,
            hallazgo=hallazgo,
            cantidad=int(cantidad),
            detalle=detalle,
        )
    )


def build_schema_validation() -> tuple[pd.DataFrame, list[Finding]]:
    """Valida existencia de archivos y columnas esperadas."""

    rows: list[dict[str, Any]] = []
    findings: list[Finding] = []

    for dataset_name, spec in DATASET_SPECS.items():
        file_exists = spec.path.exists()
        columns_found: list[str] = []
        missing_columns: list[str] = list(spec.required_columns)
        extra_columns: list[str] = []

        if file_exists:
            columns_found = list(pd.read_csv(spec.path, nrows=0).columns)
            expected = set(spec.required_columns)
            found = set(columns_found)
            missing_columns = [
                column for column in spec.required_columns if column not in found]
            extra_columns = [
                column for column in columns_found if column not in expected]
        else:
            _add_finding(
                findings,
                severidad="critico",
                dataset=dataset_name,
                regla="existencia_archivo",
                hallazgo="No existe el archivo raw requerido.",
                detalle=str(spec.path),
            )

        if missing_columns:
            _add_finding(
                findings,
                severidad="critico",
                dataset=dataset_name,
                regla="schema_columnas",
                hallazgo="Faltan columnas requeridas.",
                cantidad=len(missing_columns),
                detalle=_format_values(missing_columns),
            )

        if extra_columns:
            _add_finding(
                findings,
                severidad="info",
                dataset=dataset_name,
                regla="schema_columnas",
                hallazgo="Existen columnas adicionales no definidas en el contrato minimo.",
                cantidad=len(extra_columns),
                detalle=_format_values(extra_columns),
            )

        rows.append(
            {
                "dataset": dataset_name,
                "archivo": spec.filename,
                "existe_archivo": file_exists,
                "columnas_esperadas": len(spec.required_columns),
                "columnas_encontradas": len(columns_found),
                "columnas_faltantes": _format_values(missing_columns, limit=50),
                "columnas_extra": _format_values(extra_columns, limit=50),
                "estado": "ok" if file_exists and not missing_columns else "error",
            }
        )

    return pd.DataFrame(rows), findings


def build_dataset_profile(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Genera perfil por columna para cada dataset raw."""

    rows: list[dict[str, Any]] = []
    for dataset_name, df in datasets.items():
        for column in df.columns:
            empty_count = int(_is_empty(df[column]).sum())
            unique_count = int(df[column].nunique(dropna=False))
            examples = [
                value
                for value in clean_text_series(df[column]).dropna().astype(str).unique().tolist()
                if value
            ]
            rows.append(
                {
                    "dataset": dataset_name,
                    "columna": column,
                    "filas": len(df),
                    "valores_vacios": empty_count,
                    "porcentaje_vacios": round((empty_count / len(df)) * 100, 2) if len(df) else 0,
                    "valores_unicos": unique_count,
                    "ejemplos": _format_values(examples, limit=5),
                }
            )
    return pd.DataFrame(rows)


def validate_duplicate_rows(datasets: dict[str, pd.DataFrame], findings: list[Finding]) -> None:
    for dataset_name, df in datasets.items():
        duplicated_rows = int(df.duplicated().sum())
        if duplicated_rows:
            _add_finding(
                findings,
                severidad="medio",
                dataset=dataset_name,
                regla="duplicados_exactos",
                hallazgo="Existen filas completamente duplicadas.",
                cantidad=duplicated_rows,
            )


def validate_key_duplicates(datasets: dict[str, pd.DataFrame], findings: list[Finding]) -> None:
    for dataset_name, spec in DATASET_SPECS.items():
        if not spec.key_columns:
            continue
        df = datasets[dataset_name]
        missing_key_columns = [
            column for column in spec.key_columns if column not in df.columns]
        if missing_key_columns:
            continue
        duplicated_keys = int(df.duplicated(
            subset=list(spec.key_columns), keep=False).sum())
        if duplicated_keys:
            _add_finding(
                findings,
                severidad="alto",
                dataset=dataset_name,
                regla="duplicados_llave",
                columna=" + ".join(spec.key_columns),
                hallazgo="Existen registros con llave principal duplicada.",
                cantidad=duplicated_keys,
            )


def validate_critical_empty_values(datasets: dict[str, pd.DataFrame], findings: list[Finding]) -> None:
    for dataset_name, spec in DATASET_SPECS.items():
        df = datasets[dataset_name]
        expected_empty = EXPECTED_EMPTY_COLUMNS.get(dataset_name, set())
        for column in spec.required_columns:
            if column not in df.columns or column in expected_empty:
                continue
            empty_count = int(_is_empty(df[column]).sum())
            if empty_count:
                _add_finding(
                    findings,
                    severidad="medio",
                    dataset=dataset_name,
                    regla="nulos_criticos",
                    columna=column,
                    hallazgo="La columna requerida tiene valores vacios no esperados.",
                    cantidad=empty_count,
                )


def validate_periods(datasets: dict[str, pd.DataFrame], findings: list[Finding]) -> None:
    for dataset_name, df in datasets.items():
        for column in ("periodo_academico", "periodo_inscripcion"):
            if column not in df.columns:
                continue
            values = set(clean_text_series(df[column]).dropna().astype(str))
            invalid_values = sorted(values - VALID_PERIODS)
            if invalid_values:
                _add_finding(
                    findings,
                    severidad="alto",
                    dataset=dataset_name,
                    regla="periodos_validos",
                    columna=column,
                    hallazgo="Existen periodos fuera de la codificacion esperada.",
                    cantidad=len(invalid_values),
                    detalle=_format_values(invalid_values),
                )


def validate_expected_categories(datasets: dict[str, pd.DataFrame], findings: list[Finding]) -> None:
    category_rules = {
        "actas_notas": {
            "resultado": VALID_RESULTS,
            "oportunidad_evaluacion": VALID_EVALUATION_OPPORTUNITIES,
        },
        "asignaciones": {
            "estado_asignacion": VALID_ASSIGNMENT_STATES,
        },
    }

    for dataset_name, columns in category_rules.items():
        df = datasets[dataset_name]
        for column, valid_values in columns.items():
            values = set(clean_text_series(df[column]).dropna().astype(str))
            invalid_values = sorted(values - valid_values)
            if invalid_values:
                _add_finding(
                    findings,
                    severidad="alto",
                    dataset=dataset_name,
                    regla="categorias_validas",
                    columna=column,
                    hallazgo="Existen categorias fuera del conjunto esperado.",
                    cantidad=len(invalid_values),
                    detalle=_format_values(invalid_values),
                )


def validate_course_codes(datasets: dict[str, pd.DataFrame], findings: list[Finding]) -> None:
    catalog_codes = set(clean_text_series(
        datasets["catalogo_cursos"]["codigo_curso"]).dropna().astype(str))
    course_code_checks = {
        "actas_notas": ["codigo_curso"],
        "asignaciones": ["codigo_curso"],
        "oferta_academica": ["codigo_curso"],
        "malla_prerrequisitos": ["codigo_curso", "codigo_prerrequisito"],
        "configuracion_cursos": ["codigo_curso"],
    }

    for dataset_name, columns in course_code_checks.items():
        df = datasets[dataset_name]
        for column in columns:
            codes = set(clean_text_series(df[column]).dropna().astype(str))
            unknown_codes = sorted(codes - catalog_codes)
            if unknown_codes:
                _add_finding(
                    findings,
                    severidad="alto",
                    dataset=dataset_name,
                    regla="codigos_curso_catalogo",
                    columna=column,
                    hallazgo="Existen codigos de curso que no aparecen en el catalogo.",
                    cantidad=len(unknown_codes),
                    detalle=_format_values(unknown_codes),
                )


def validate_student_ids(datasets: dict[str, pd.DataFrame], findings: list[Finding]) -> None:
    registered_students = set(
        clean_text_series(datasets["estudiantes_inscritos"]
                          ["estudiante_id_ofuscado"]).dropna().astype(str)
    )
    for dataset_name in ("actas_notas", "asignaciones"):
        df = datasets[dataset_name]
        students = set(clean_text_series(
            df["estudiante_id_ofuscado"]).dropna().astype(str))
        unknown_students = sorted(students - registered_students)
        if unknown_students:
            _add_finding(
                findings,
                severidad="alto",
                dataset=dataset_name,
                regla="estudiantes_inscritos",
                columna="estudiante_id_ofuscado",
                hallazgo="Existen estudiantes no presentes en el padron 2024.",
                cantidad=len(unknown_students),
                detalle=f"{len(unknown_students)} identificadores ofuscados fuera del padron; no se listan por privacidad.",
            )


def validate_numeric_ranges(datasets: dict[str, pd.DataFrame], findings: list[Finding]) -> None:
    numeric_ranges = {
        "actas_notas": {
            "zona": (0, 70),
            "nota_examen": (0, 30),
            "nota_total": (0, 100),
        }
    }
    allowed_special_values = {
        "zona": {"EQ"},
        "nota_examen": {"EQ", RESULT_NSP},
        "nota_total": {"EQ"},
    }

    for dataset_name, columns in numeric_ranges.items():
        df = datasets[dataset_name]
        for column, (minimum, maximum) in columns.items():
            numeric = parse_numeric(df[column])
            cleaned = clean_text_series(df[column])
            non_empty = cleaned.notna()
            is_allowed_special = cleaned.isin(
                allowed_special_values.get(column, set()))
            non_numeric = int(
                (non_empty & ~is_allowed_special & numeric.isna()).sum())
            out_of_range = int(
                ((numeric < minimum) | (numeric > maximum)).sum())
            if non_numeric:
                _add_finding(
                    findings,
                    severidad="medio",
                    dataset=dataset_name,
                    regla="rangos_numericos",
                    columna=column,
                    hallazgo="Existen valores no numericos en una columna de nota.",
                    cantidad=non_numeric,
                    detalle="No incluye valores especiales esperados como EQ o NSP.",
                )
            if out_of_range:
                _add_finding(
                    findings,
                    severidad="alto",
                    dataset=dataset_name,
                    regla="rangos_numericos",
                    columna=column,
                    hallazgo=f"Existen valores fuera del rango esperado [{minimum}, {maximum}].",
                    cantidad=out_of_range,
                )


def validate_special_values(datasets: dict[str, pd.DataFrame], findings: list[Finding]) -> None:
    actas = datasets["actas_notas"]
    assignments = datasets["asignaciones"]
    eq_count = int((actas["nota_total"].astype(str).str.strip() == "EQ").sum())
    nsp_count = int((actas["resultado"].astype(
        str).str.strip() == RESULT_NSP).sum())
    dropped_count = int((assignments["estado_asignacion"].astype(
        str).str.strip() == ASSIGNMENT_DROPPED).sum())

    for dataset_name, column, value, count in (
        ("actas_notas", "nota_total", "EQ", eq_count),
        ("actas_notas", "resultado", RESULT_NSP, nsp_count),
        ("asignaciones", "estado_asignacion", ASSIGNMENT_DROPPED, dropped_count),
    ):
        _add_finding(
            findings,
            severidad="info",
            dataset=dataset_name,
            regla="valores_especiales",
            columna=column,
            hallazgo=f"Conteo de valor especial `{value}`.",
            cantidad=count,
            detalle="Valor conservado para analisis posterior.",
        )


def run_quality_validations(datasets: dict[str, pd.DataFrame]) -> list[Finding]:
    findings: list[Finding] = []
    validate_duplicate_rows(datasets, findings)
    validate_key_duplicates(datasets, findings)
    validate_critical_empty_values(datasets, findings)
    validate_periods(datasets, findings)
    validate_expected_categories(datasets, findings)
    validate_course_codes(datasets, findings)
    validate_student_ids(datasets, findings)
    validate_numeric_ranges(datasets, findings)
    validate_special_values(datasets, findings)
    return findings


def findings_to_dataframe(findings: list[Finding]) -> pd.DataFrame:
    columns = ["severidad", "dataset", "regla",
               "columna", "hallazgo", "cantidad", "detalle"]
    if not findings:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame([finding.__dict__ for finding in findings], columns=columns)


def _severity_counts(findings_df: pd.DataFrame) -> dict[str, int]:
    if findings_df.empty:
        return {}
    return findings_df["severidad"].value_counts().to_dict()


def _markdown_table(df: pd.DataFrame) -> str:
    """Genera una tabla Markdown simple sin dependencias opcionales."""

    if df.empty:
        return "_Sin registros._"

    display_df = df.fillna("").astype(str)
    headers = list(display_df.columns)
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    row_lines = [
        "| " + " | ".join(row[column].replace("|", "\\|")
                          for column in headers) + " |"
        for _, row in display_df.iterrows()
    ]
    return "\n".join([header_line, separator_line, *row_lines])


def build_markdown_report(
    inventory_df: pd.DataFrame,
    schema_df: pd.DataFrame,
    findings_df: pd.DataFrame,
) -> str:
    severity_counts = _severity_counts(findings_df)
    errors = schema_df[schema_df["estado"] != "ok"]
    high_findings = findings_df[findings_df["severidad"].isin(
        ["critico", "alto"])]

    lines = [
        "# Reporte de calidad de datos",
        "",
        "## Objetivo",
        "",
        "Validar la existencia, estructura y consistencia inicial de los diez datasets raw antes del ETL.",
        "",
        "## Resumen de carga",
        "",
        _markdown_table(
            inventory_df[["dataset", "archivo", "filas", "columnas"]]),
        "",
        "## Validacion de esquema",
        "",
        _markdown_table(schema_df[["dataset", "existe_archivo",
                        "columnas_esperadas", "columnas_encontradas", "estado"]]),
        "",
        "## Resumen de hallazgos",
        "",
    ]

    if findings_df.empty:
        lines.append("No se registraron hallazgos de calidad de datos.")
    else:
        lines.extend(
            [
                f"- Criticos: {severity_counts.get('critico', 0)}",
                f"- Altos: {severity_counts.get('alto', 0)}",
                f"- Medios: {severity_counts.get('medio', 0)}",
                f"- Informativos: {severity_counts.get('info', 0)}",
            ]
        )

    lines.extend(["", "## Hallazgos de calidad de datos", ""])

    if high_findings.empty:
        lines.append(
            "No se encontraron hallazgos criticos o altos en las validaciones iniciales.")
    else:
        lines.append(
            _markdown_table(
                high_findings[
                    ["severidad", "dataset", "regla", "columna",
                        "hallazgo", "cantidad", "detalle"]
                ]
            )
        )

    lines.extend(["", "## Decisiones de limpieza aplicadas", ""])
    lines.append(
        "No se aplicaron transformaciones ni eliminaciones de registros en esta fase.")
    lines.append(
        "Los archivos raw se leyeron en modo texto para preservar codigos con ceros a la izquierda.")
    lines.append(
        "Los valores especiales `EQ`, `NSP` y `desasignado` se reportan y se conservaran para el ETL.")

    lines.extend(["", "## Conclusion", ""])
    if not errors.empty:
        lines.append(
            "La validacion detecto errores de esquema que deben resolverse antes de continuar al ETL.")
    elif not high_findings.empty:
        lines.append(
            "Los datasets cargan correctamente, pero existen hallazgos altos que deben revisarse antes de construir datasets derivados."
        )
    else:
        lines.append(
            "Los datasets raw cargan correctamente y no presentan bloqueos criticos para iniciar la fase de limpieza y ETL."
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    ensure_project_directories()
    schema_df, schema_findings = build_schema_validation()

    if (schema_df["estado"] != "ok").any():
        findings_df = findings_to_dataframe(schema_findings)
        save_table(schema_df, SCHEMA_VALIDATION_PATH)
        save_table(findings_df, DATA_QUALITY_FINDINGS_PATH)
        report = build_markdown_report(pd.DataFrame(), schema_df, findings_df)
        write_text(REPORT_PATH, report)
        raise SystemExit(
            "Existen errores de esquema. Revisar outputs/reports/data_quality_report.md")

    datasets = load_all_raw_datasets()
    inventory_df = build_raw_dataset_inventory(datasets)
    profile_df = build_dataset_profile(datasets)
    findings = schema_findings + run_quality_validations(datasets)
    findings_df = findings_to_dataframe(findings)

    save_table(profile_df, DATASET_PROFILE_PATH)
    save_table(schema_df, SCHEMA_VALIDATION_PATH)
    save_table(findings_df, DATA_QUALITY_FINDINGS_PATH)
    write_text(REPORT_PATH, build_markdown_report(
        inventory_df, schema_df, findings_df))

    print("Validacion de calidad de datos completada.")
    print(f"Reporte: {REPORT_PATH}")
    print(f"Perfil: {DATASET_PROFILE_PATH}")
    print(f"Esquema: {SCHEMA_VALIDATION_PATH}")
    print(f"Hallazgos: {DATA_QUALITY_FINDINGS_PATH}")


if __name__ == "__main__":
    main()
