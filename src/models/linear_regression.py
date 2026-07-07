"""Regresion lineal agregada a nivel curso-periodo."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.config.settings import FIGURES_DIR, PROCESSED_DATA_DIR, PROJECT_ROOT, REPORTS_DIR, TABLES_DIR
from src.data.utils import ensure_project_directories, save_table, write_text
from src.visualization.plots_models import plot_regression_residuals


COURSE_PERIOD_PATH = PROCESSED_DATA_DIR / "ds_resumen_curso_periodo_2024.csv"
CONTINUITY_PATH = PROCESSED_DATA_DIR / "ds_continuidad_oferta_2024.csv"
REGRESSION_TABLES_DIR = TABLES_DIR / "regression"
MODELS_FIGURES_DIR = FIGURES_DIR / "models"
REGRESSION_REPORT_PATH = REPORTS_DIR / "regresion_lineal.md"

METRICS_PATH = REGRESSION_TABLES_DIR / "08_metricas_regresion.csv"
COEFFICIENTS_PATH = REGRESSION_TABLES_DIR / "08_coeficientes_regresion.csv"
PREDICTIONS_PATH = REGRESSION_TABLES_DIR / "08_predicciones_regresion.csv"
FIGURE_CATALOG_PATH = REGRESSION_TABLES_DIR / "08_catalogo_figuras_regresion.csv"
RESIDUAL_FIGURE_PATH = MODELS_FIGURES_DIR / "08_regresion_residuos.png"

RANDOM_STATE = 2024
TEST_SIZE = 0.25
MIN_RESULTS_PER_ROW = 10
TARGET_COLUMN = "tasa_perdida_definitiva"

NUMERIC_FEATURES: tuple[str, ...] = (
    "orden_periodo",
    "semestre_pensum",
    "cantidad_cursos_dependientes",
    "secciones_abiertas",
    "cupo_total_ofertado",
    "estudiantes_asignados",
    "estudiantes_desasignados",
    "tasa_ocupacion_cupo",
    "indice_continuidad_oferta_anual",
)

CATEGORICAL_FEATURES: tuple[str, ...] = (
    "periodo_academico",
    "area_academica",
    "tipo_curso_configurado",
    "requiere_laboratorio",
    "curso_obligatorio",
    "curso_base",
    "curso_bloqueante",
    "nivel_bloqueo_curricular",
    "patron_oferta",
)

RESULT_DERIVED_EXCLUDED: tuple[str, ...] = (
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
    "indice_dependencia_recuperacion",
    "promedio_zona_ordinaria",
    "promedio_examen_ordinario",
    "promedio_nota_total_ordinario",
    "estudiantes_sin_oportunidad_inmediata",
    "estudiantes_en_riesgo_retraso_curricular",
)


def _relative_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def _format_metric(value: Any) -> str:
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return "sin dato"
    return f"{numeric:.3f}"


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


def load_regression_dataset() -> pd.DataFrame:
    """Carga datos agregados y anexa continuidad anual por curso."""

    course_period = pd.read_csv(COURSE_PERIOD_PATH)
    continuity = pd.read_csv(
        CONTINUITY_PATH,
        usecols=["codigo_curso", "cantidad_periodos_abierto", "indice_continuidad_oferta", "patron_oferta"],
    ).rename(columns={"indice_continuidad_oferta": "indice_continuidad_oferta_anual"})

    df = course_period.merge(continuity, on="codigo_curso", how="left")
    for column in [*NUMERIC_FEATURES, TARGET_COLUMN, "estudiantes_con_acta_ordinaria"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    for column in CATEGORICAL_FEATURES:
        df[column] = df[column].astype("string").fillna("sin_dato")

    df = df[df["estudiantes_con_acta_ordinaria"].ge(MIN_RESULTS_PER_ROW)]
    df = df.dropna(subset=[TARGET_COLUMN]).reset_index(drop=True)
    return df


def _build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]),
                list(NUMERIC_FEATURES),
            ),
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(drop="first", handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                list(CATEGORICAL_FEATURES),
            ),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    )


def _feature_source(feature_name: str) -> str:
    clean_name = feature_name.split("__", maxsplit=1)[-1]
    for column in sorted([*NUMERIC_FEATURES, *CATEGORICAL_FEATURES], key=len, reverse=True):
        if clean_name == column or clean_name.startswith(f"{column}_"):
            return column
    return clean_name


def train_regression(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Entrena regresion lineal y devuelve metricas, coeficientes y predicciones."""

    feature_columns = [*NUMERIC_FEATURES, *CATEGORICAL_FEATURES]
    x = df[feature_columns].copy()
    y = df[TARGET_COLUMN].copy()
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )

    pipeline = Pipeline(
        [
            ("preprocessor", _build_preprocessor()),
            ("model", LinearRegression()),
        ]
    )
    pipeline.fit(x_train, y_train)
    y_pred = pipeline.predict(x_test)
    residuals = y_test.to_numpy() - y_pred
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))

    metrics = pd.DataFrame(
        [
            {
                "modelo": "linear_regression",
                "modelo_nombre": "Regresion lineal agregada",
                "target": TARGET_COLUMN,
                "unidad_analisis": "curso-periodo",
                "n_total": len(df),
                "n_train": len(x_train),
                "n_test": len(x_test),
                "test_size": TEST_SIZE,
                "random_state": RANDOM_STATE,
                "r2": float(r2_score(y_test, y_pred)),
                "mae": float(mean_absolute_error(y_test, y_pred)),
                "rmse": rmse,
            }
        ]
    )

    feature_names = list(pipeline.named_steps["preprocessor"].get_feature_names_out())
    coefficients = pd.DataFrame(
        {
            "variable_transformada": feature_names,
            "variable": [_feature_source(feature) for feature in feature_names],
            "coeficiente": pipeline.named_steps["model"].coef_,
        }
    )
    coefficients["coeficiente_absoluto"] = coefficients["coeficiente"].abs()
    coefficients = coefficients.sort_values("coeficiente_absoluto", ascending=False).reset_index(drop=True)

    predictions = x_test.copy()
    predictions["valor_real"] = y_test.to_numpy()
    predictions["valor_predicho"] = y_pred
    predictions["residuo"] = residuals
    predictions = predictions.reset_index(drop=True)
    return metrics, coefficients, predictions


def build_figure_catalog(predictions: pd.DataFrame) -> pd.DataFrame:
    """Construye catalogo interpretativo de figuras de regresion."""

    mean_abs_residual = predictions["residuo"].abs().mean()
    return pd.DataFrame(
        [
            {
                "figura": RESIDUAL_FIGURE_PATH.name,
                "pregunta_analitica": "Que tan alineadas estan las tasas reales y predichas de perdida definitiva?",
                "descripcion": "Dispersion de residuos contra valores predichos y comparacion entre valor real y predicho.",
                "interpretacion": (
                    f"El residuo absoluto promedio observado en prueba es {_format_metric(mean_abs_residual)} "
                    "puntos de tasa."
                ),
                "conclusion": "La grafica permite revisar errores agregados y detectar dispersion, sin afirmar causalidad.",
                "ruta": _relative_path(RESIDUAL_FIGURE_PATH),
            }
        ]
    )


def _report_metrics_table(metrics: pd.DataFrame) -> pd.DataFrame:
    table = metrics[["modelo_nombre", "n_total", "n_train", "n_test", "r2", "mae", "rmse"]].copy()
    for column in ["r2", "mae", "rmse"]:
        table[column] = table[column].map(_format_metric)
    return table


def _report_coefficients_table(coefficients: pd.DataFrame) -> pd.DataFrame:
    table = coefficients.head(15)[["variable", "variable_transformada", "coeficiente"]].copy()
    table["coeficiente"] = table["coeficiente"].map(_format_metric)
    return table


def write_report(metrics: pd.DataFrame, coefficients: pd.DataFrame, figure_catalog: pd.DataFrame) -> None:
    generated_tables = pd.DataFrame(
        [
            {"tabla": "08_metricas_regresion", "ruta": _relative_path(METRICS_PATH)},
            {"tabla": "08_coeficientes_regresion", "ruta": _relative_path(COEFFICIENTS_PATH)},
            {"tabla": "08_predicciones_regresion", "ruta": _relative_path(PREDICTIONS_PATH)},
            {"tabla": "08_catalogo_figuras_regresion", "ruta": _relative_path(FIGURE_CATALOG_PATH)},
        ]
    )
    excluded_table = pd.DataFrame({"variable_excluida": RESULT_DERIVED_EXCLUDED})

    figure_sections = []
    for _, row in figure_catalog.iterrows():
        figure_sections.append(
            f"""### {row['figura']}

![{row['descripcion']}](../figures/models/{row['figura']})

- Pregunta analitica: {row['pregunta_analitica']}
- Descripcion: {row['descripcion']}
- Interpretacion: {row['interpretacion']}
- Conclusion: {row['conclusion']}
- Ruta: `{row['ruta']}`
"""
        )

    content = f"""# Regresion lineal agregada

## Objetivo

Estimar de forma exploratoria la asociacion entre caracteristicas agregadas de
oferta, volumen, continuidad y estructura curricular con la tasa de perdida
definitiva a nivel curso-periodo.

El modelo es descriptivo y no causal. No debe usarse para diagnosticar
estudiantes ni para atribuir responsabilidades individuales.

## Controles metodologicos

- Unidad de analisis: curso-periodo.
- Target: `{TARGET_COLUMN}`.
- Se filtran filas con menos de {MIN_RESULTS_PER_ROW} registros ordinarios para
  evitar tasas inestables.
- Se excluyen variables derivadas directamente de resultados academicos finales
  para reducir fuga de informacion.
- No se usa `docente` ni identificadores individuales.

## Tablas generadas

{_markdown_table(generated_tables)}

## Metricas

{_markdown_table(_report_metrics_table(metrics))}

## Coeficientes destacados

{_markdown_table(_report_coefficients_table(coefficients))}

Los coeficientes se reportan como lectura exploratoria. Su signo y magnitud
dependen del conjunto de variables, escalamiento y codificacion de categorias.

## Variables excluidas por cercania al resultado

{_markdown_table(excluded_table)}

## Figuras generadas e interpretacion

{"".join(figure_sections)}

## Limitaciones

- La regresion usa observaciones de 2024 y no reconstruye trayectorias
  academicas completas.
- Las variables categoricas se expanden mediante one-hot encoding, por lo que
  los coeficientes deben interpretarse respecto a categorias de referencia
  implicitas.
- Algunas relaciones pueden ser no lineales; este modelo resume solo una
  aproximacion lineal agregada.
- La tasa de perdida definitiva puede verse afectada por tamanos de muestra y
  heterogeneidad entre cursos.

## Conclusion

La regresion lineal agregada aporta una lectura complementaria sobre como se
asocian continuidad, volumen, periodo, area y estructura curricular con la tasa
de perdida definitiva observada. Sus resultados deben usarse para orientar
preguntas y priorizar cursos, no para afirmar causalidad.
"""
    write_text(REGRESSION_REPORT_PATH, content)


def main() -> None:
    ensure_project_directories()
    REGRESSION_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    df = load_regression_dataset()
    metrics, coefficients, predictions = train_regression(df)
    plot_regression_residuals(predictions, RESIDUAL_FIGURE_PATH)
    figure_catalog = build_figure_catalog(predictions)

    save_table(metrics, METRICS_PATH)
    save_table(coefficients, COEFFICIENTS_PATH)
    save_table(predictions, PREDICTIONS_PATH)
    save_table(figure_catalog, FIGURE_CATALOG_PATH)
    write_report(metrics, coefficients, figure_catalog)

    print(f"Regresion lineal completada. Reporte: {_relative_path(REGRESSION_REPORT_PATH)}")


if __name__ == "__main__":
    main()
