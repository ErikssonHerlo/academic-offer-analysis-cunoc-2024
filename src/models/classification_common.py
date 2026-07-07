"""Componentes compartidos para modelos de clasificacion academica."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.config.settings import FIGURES_DIR, PROCESSED_DATA_DIR, PROJECT_ROOT, REPORTS_DIR, TABLES_DIR
from src.data.utils import ensure_project_directories, save_table, write_text
from src.visualization.plots_models import build_model_figures


CLASSIFICATION_DATASET_PATH = PROCESSED_DATA_DIR / "ds_modelo_clasificacion.csv"
MODELS_TABLES_DIR = TABLES_DIR / "models"
MODELS_FIGURES_DIR = FIGURES_DIR / "models"
MODELS_REPORT_PATH = REPORTS_DIR / "resultados_modelos.md"

METRICS_PATH = MODELS_TABLES_DIR / "07_metricas_modelos.csv"
IMPORTANCES_PATH = MODELS_TABLES_DIR / "07_importancias_variables.csv"
CONFUSION_PATH = MODELS_TABLES_DIR / "07_matrices_confusion.csv"
FIGURE_CATALOG_PATH = MODELS_TABLES_DIR / "07_catalogo_figuras_modelos.csv"
VALIDATION_PATH = MODELS_TABLES_DIR / "07_validacion_targets_modelos.csv"

RANDOM_STATE = 2024
TEST_SIZE = 0.25
MIN_CLASS_COUNT_FOR_STRATIFY = 2
TOP_IMPORTANCES_LIMIT = 20

TARGET_COLUMNS: tuple[str, ...] = (
    "necesito_recuperacion",
    "perdida_definitiva",
    "riesgo_retraso_potencial",
    "riesgo_retraso_potencial_amplio",
)

TARGET_DESCRIPTIONS: dict[str, str] = {
    "necesito_recuperacion": "Necesidad observada de recuperacion",
    "perdida_definitiva": "Perdida definitiva observada",
    "riesgo_retraso_potencial": "Riesgo de retraso academico potencial",
    "riesgo_retraso_potencial_amplio": "Riesgo potencial amplio",
}

NUMERIC_FEATURES: tuple[str, ...] = (
    "semestre_pensum",
    "cantidad_cursos_dependientes",
    "cohorte_ingreso",
    "zona_ordinaria",
    "cupo_ofertado_oferta",
    "tasa_ocupacion_cupo",
)

CATEGORICAL_FEATURES: tuple[str, ...] = (
    "codigo_curso",
    "periodo_academico",
    "area_academica",
    "tipo_curso_configurado",
    "requiere_laboratorio",
    "componente_practico",
    "curso_obligatorio",
    "curso_base",
    "nivel_bloqueo_curricular",
)

PROHIBITED_FEATURES: tuple[str, ...] = (
    "docente",
    "estudiante_id_ofuscado",
    "nota_examen_ordinario",
    "nota_total_ordinario",
    "nota_total_final",
    "resultado_final",
)

EXCLUDED_CONTEXT_FEATURES: tuple[str, ...] = (
    "curso_abierto_periodo_siguiente",
    "curso_abierto_siguiente_periodo",
)


@dataclass(frozen=True)
class ClassificationModelSpec:
    """Configuracion minima para ejecutar un modelo de clasificacion."""

    model_key: str
    model_name: str
    estimator: Any
    scale_numeric_features: bool
    importance_kind: str


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


def _as_bool(series: pd.Series) -> pd.Series:
    normalized = series.astype(str).str.strip().str.lower()
    return normalized.isin({"true", "1", "si", "sí", "yes"})


def load_classification_dataset() -> pd.DataFrame:
    """Carga el dataset modelable y normaliza tipos basicos."""

    df = pd.read_csv(CLASSIFICATION_DATASET_PATH)
    for target in TARGET_COLUMNS:
        if target in df.columns:
            df[target] = _as_bool(df[target])
    for column in NUMERIC_FEATURES:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    for column in [*CATEGORICAL_FEATURES, *EXCLUDED_CONTEXT_FEATURES]:
        if column in df.columns:
            df[column] = df[column].astype("string").fillna("sin_dato")
    return df


def validate_modeling_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Valida targets, predictores y variables prohibidas antes de entrenar."""

    rows: list[dict[str, Any]] = []
    present_prohibited = sorted(set(PROHIBITED_FEATURES).intersection(df.columns))
    available_features = _available_features(df)

    rows.append(
        {
            "revision": "variables_prohibidas",
            "estado": "ok" if not present_prohibited else "revisar",
            "detalle": "No se encontraron variables prohibidas como predictoras."
            if not present_prohibited
            else "; ".join(present_prohibited),
        }
    )
    rows.append(
        {
            "revision": "variables_predictoras",
            "estado": "ok" if available_features else "error",
            "detalle": f"{len(available_features)} variables predictoras disponibles.",
        }
    )
    excluded_context = sorted(set(EXCLUDED_CONTEXT_FEATURES).intersection(df.columns))
    rows.append(
        {
            "revision": "variables_contexto_posterior_excluidas",
            "estado": "ok",
            "detalle": (
                "Columnas excluidas como predictores por representar oferta posterior o componentes cercanos "
                f"a targets de riesgo: {'; '.join(excluded_context) if excluded_context else 'ninguna'}."
            ),
        }
    )

    for target in TARGET_COLUMNS:
        if target not in df.columns:
            rows.append({"revision": target, "estado": "error", "detalle": "Target ausente."})
            continue
        counts = df[target].value_counts(dropna=False).to_dict()
        class_count = df[target].nunique(dropna=True)
        minimum_class_count = int(df[target].value_counts().min()) if class_count else 0
        status = "ok" if class_count == 2 and minimum_class_count >= MIN_CLASS_COUNT_FOR_STRATIFY else "revisar"
        rows.append(
            {
                "revision": target,
                "estado": status,
                "detalle": (
                    f"clases={class_count}; minimo_clase={minimum_class_count}; "
                    f"distribucion={counts}"
                ),
            }
        )
    result = pd.DataFrame(rows)
    save_table(result, VALIDATION_PATH)
    return result


def _available_features(df: pd.DataFrame) -> list[str]:
    expected_features = [*NUMERIC_FEATURES, *CATEGORICAL_FEATURES]
    return [
        column
        for column in expected_features
        if (
            column in df.columns
            and column not in TARGET_COLUMNS
            and column not in PROHIBITED_FEATURES
            and column not in EXCLUDED_CONTEXT_FEATURES
        )
    ]


def _build_preprocessor(df: pd.DataFrame, scale_numeric_features: bool) -> ColumnTransformer:
    numeric_features = [column for column in NUMERIC_FEATURES if column in df.columns]
    categorical_features = [column for column in CATEGORICAL_FEATURES if column in df.columns]

    numeric_steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric_features:
        numeric_steps.append(("scaler", StandardScaler()))

    transformers: list[tuple[str, Any, list[str]]] = []
    if numeric_features:
        transformers.append(("num", Pipeline(numeric_steps), numeric_features))
    if categorical_features:
        transformers.append(
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                categorical_features,
            )
        )
    return ColumnTransformer(transformers=transformers, remainder="drop", verbose_feature_names_out=True)


def _feature_source(feature_name: str, source_columns: list[str]) -> str:
    clean_name = feature_name.split("__", maxsplit=1)[-1]
    for column in sorted(source_columns, key=len, reverse=True):
        if clean_name == column or clean_name.startswith(f"{column}_"):
            return column
    return clean_name


def _extract_feature_importances(
    pipeline: Pipeline,
    spec: ClassificationModelSpec,
    target: str,
    source_columns: list[str],
) -> pd.DataFrame:
    preprocessor = pipeline.named_steps["preprocessor"]
    estimator = pipeline.named_steps["model"]
    feature_names = list(preprocessor.get_feature_names_out())

    if hasattr(estimator, "coef_"):
        raw_values = np.abs(estimator.coef_[0])
    elif hasattr(estimator, "feature_importances_"):
        raw_values = estimator.feature_importances_
    else:
        raw_values = np.zeros(len(feature_names))

    transformed = pd.DataFrame(
        {
            "modelo": spec.model_key,
            "modelo_nombre": spec.model_name,
            "target": target,
            "target_descripcion": TARGET_DESCRIPTIONS[target],
            "variable_transformada": feature_names,
            "variable": [_feature_source(name, source_columns) for name in feature_names],
            "importancia": raw_values,
            "tipo_importancia": spec.importance_kind,
        }
    )
    grouped = (
        transformed.groupby(["modelo", "modelo_nombre", "target", "target_descripcion", "variable", "tipo_importancia"])
        .agg(importancia=("importancia", "sum"))
        .reset_index()
        .sort_values("importancia", ascending=False)
        .head(TOP_IMPORTANCES_LIMIT)
    )
    total_importance = grouped["importancia"].sum()
    if total_importance > 0:
        grouped["importancia_relativa_top"] = grouped["importancia"] / total_importance
    else:
        grouped["importancia_relativa_top"] = np.nan
    return grouped.reset_index(drop=True)


def _train_target_model(
    df: pd.DataFrame,
    spec: ClassificationModelSpec,
    target: str,
) -> tuple[dict[str, Any], dict[str, Any], pd.DataFrame]:
    feature_columns = _available_features(df)
    y = df[target].astype(bool)
    x = df[feature_columns].copy()
    class_counts = y.value_counts()
    stratify = y if y.nunique() == 2 and class_counts.min() >= MIN_CLASS_COUNT_FOR_STRATIFY else None

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=stratify,
    )

    pipeline = Pipeline(
        [
            ("preprocessor", _build_preprocessor(x_train, spec.scale_numeric_features)),
            ("model", spec.estimator),
        ]
    )
    pipeline.fit(x_train, y_train)
    y_pred = pipeline.predict(x_test)

    if hasattr(pipeline, "predict_proba"):
        y_score = pipeline.predict_proba(x_test)[:, 1]
    elif hasattr(pipeline, "decision_function"):
        y_score = pipeline.decision_function(x_test)
    else:
        y_score = None

    roc_auc = roc_auc_score(y_test, y_score) if y_score is not None and y_test.nunique() == 2 else np.nan
    average_precision = (
        average_precision_score(y_test, y_score) if y_score is not None and y_test.nunique() == 2 else np.nan
    )
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred, labels=[False, True]).ravel()

    metrics = {
        "modelo": spec.model_key,
        "modelo_nombre": spec.model_name,
        "target": target,
        "target_descripcion": TARGET_DESCRIPTIONS[target],
        "n_train": len(y_train),
        "n_test": len(y_test),
        "positivos_train": int(y_train.sum()),
        "positivos_test": int(y_test.sum()),
        "prevalencia_test": float(y_test.mean()),
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc,
        "average_precision": average_precision,
        "estratificado": stratify is not None,
    }
    confusion = {
        "modelo": spec.model_key,
        "modelo_nombre": spec.model_name,
        "target": target,
        "target_descripcion": TARGET_DESCRIPTIONS[target],
        "verdaderos_negativos": int(tn),
        "falsos_positivos": int(fp),
        "falsos_negativos": int(fn),
        "verdaderos_positivos": int(tp),
    }
    importances = _extract_feature_importances(pipeline, spec, target, feature_columns)
    return metrics, confusion, importances


def _read_existing_table(path: Path, columns: list[str]) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame(columns=columns)


def _replace_model_rows(existing: pd.DataFrame, incoming: pd.DataFrame, model_key: str) -> pd.DataFrame:
    if existing.empty:
        return incoming.copy()
    filtered = existing[~existing["modelo"].eq(model_key)].copy()
    return pd.concat([filtered, incoming], ignore_index=True)


def _sort_model_table(df: pd.DataFrame) -> pd.DataFrame:
    model_order = {"logistic_regression": 1, "decision_tree": 2, "random_forest": 3}
    target_order = {target: index for index, target in enumerate(TARGET_COLUMNS, start=1)}
    result = df.copy()
    result["_modelo_orden"] = result["modelo"].map(model_order).fillna(99)
    result["_target_orden"] = result["target"].map(target_order).fillna(99)
    result = result.sort_values(["_modelo_orden", "_target_orden"]).drop(columns=["_modelo_orden", "_target_orden"])
    return result.reset_index(drop=True)


def _save_combined_outputs(
    model_key: str,
    metrics: pd.DataFrame,
    confusion: pd.DataFrame,
    importances: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    existing_metrics = _read_existing_table(METRICS_PATH, list(metrics.columns))
    existing_confusion = _read_existing_table(CONFUSION_PATH, list(confusion.columns))
    existing_importances = _read_existing_table(IMPORTANCES_PATH, list(importances.columns))

    combined_metrics = _sort_model_table(_replace_model_rows(existing_metrics, metrics, model_key))
    combined_confusion = _sort_model_table(_replace_model_rows(existing_confusion, confusion, model_key))
    combined_importances = _sort_model_table(_replace_model_rows(existing_importances, importances, model_key))

    save_table(combined_metrics, METRICS_PATH)
    save_table(combined_confusion, CONFUSION_PATH)
    save_table(combined_importances, IMPORTANCES_PATH)
    return combined_metrics, combined_confusion, combined_importances


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


def _build_metrics_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    if metrics.empty:
        return metrics
    summary = metrics[
        [
            "modelo_nombre",
            "target_descripcion",
            "prevalencia_test",
            "accuracy",
            "precision",
            "recall",
            "f1",
            "roc_auc",
            "average_precision",
        ]
    ].copy()
    for column in ["prevalencia_test", "accuracy", "precision", "recall", "f1", "roc_auc", "average_precision"]:
        summary[column] = summary[column].map(_format_metric)
    return summary.rename(
        columns={
            "modelo_nombre": "modelo",
            "target_descripcion": "target",
            "prevalencia_test": "prevalencia_test",
            "average_precision": "precision_promedio",
        }
    )


def _build_best_models_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    if metrics.empty:
        return metrics
    rows = []
    for target, group in metrics.groupby("target", observed=False):
        best_f1 = group.sort_values(["f1", "recall", "roc_auc"], ascending=False).iloc[0]
        best_recall = group.sort_values(["recall", "f1", "roc_auc"], ascending=False).iloc[0]
        rows.append(
            {
                "target": TARGET_DESCRIPTIONS.get(target, target),
                "mejor_f1": best_f1["modelo_nombre"],
                "f1": _format_metric(best_f1["f1"]),
                "mejor_recall": best_recall["modelo_nombre"],
                "recall": _format_metric(best_recall["recall"]),
                "lectura": "F1 balancea precision y recall; recall prioriza capturar casos positivos observados.",
            }
        )
    return pd.DataFrame(rows)


def _build_top_importances_summary(importances: pd.DataFrame) -> pd.DataFrame:
    if importances.empty:
        return importances
    rows = []
    for (model_name, target), group in importances.groupby(["modelo_nombre", "target"], observed=False):
        top = group.sort_values("importancia", ascending=False).head(5)
        rows.append(
            {
                "modelo": model_name,
                "target": TARGET_DESCRIPTIONS.get(target, target),
                "variables_destacadas": ", ".join(top["variable"].astype(str).tolist()),
            }
        )
    return pd.DataFrame(rows)


def _build_report(
    metrics: pd.DataFrame,
    confusion: pd.DataFrame,
    importances: pd.DataFrame,
    figure_catalog: pd.DataFrame,
) -> str:
    metrics_summary = _build_metrics_summary(metrics)
    best_summary = _build_best_models_summary(metrics)
    top_importances = _build_top_importances_summary(importances)

    generated_tables = pd.DataFrame(
        [
            {"tabla": "07_metricas_modelos", "ruta": _relative_path(METRICS_PATH)},
            {"tabla": "07_importancias_variables", "ruta": _relative_path(IMPORTANCES_PATH)},
            {"tabla": "07_matrices_confusion", "ruta": _relative_path(CONFUSION_PATH)},
            {"tabla": "07_catalogo_figuras_modelos", "ruta": _relative_path(FIGURE_CATALOG_PATH)},
            {"tabla": "07_validacion_targets_modelos", "ruta": _relative_path(VALIDATION_PATH)},
        ]
    )

    lines = [
        "# Resultados de modelos de clasificacion",
        "",
        "## Objetivo",
        "",
        "Entrenar modelos exploratorios de clasificacion para describir patrones predictivos asociados a recuperacion, perdida definitiva y riesgo de retraso academico potencial en los registros modelables de 2024.",
        "",
        "La lectura de esta fase es explicativa y comparativa. Los modelos no demuestran causalidad y no deben interpretarse como diagnosticos individuales.",
        "",
        "## Controles metodologicos",
        "",
        "- Se utiliza `data/processed/ds_modelo_clasificacion.csv`, que excluye desasignados y variables con fuga de informacion.",
        "- No se utiliza `docente`, identificadores individuales ni notas finales como predictores.",
        "- Las columnas de oferta posterior se excluyen como predictores para evitar que el modelo use componentes cercanos a los targets de riesgo.",
        "- Las particiones de entrenamiento y prueba usan estratificacion cuando el target tiene ambas clases con frecuencia suficiente.",
        f"- Se usa `random_state={RANDOM_STATE}` y `test_size={TEST_SIZE}` para reproducibilidad.",
        "- Las metricas se interpretan junto con la prevalencia del target; no se usa accuracy como unica referencia.",
        "",
        "## Tablas generadas",
        "",
        _markdown_table(generated_tables),
        "",
        "## Metricas por modelo y target",
        "",
        _markdown_table(metrics_summary),
        "",
        "## Modelos destacados por target",
        "",
        _markdown_table(best_summary),
        "",
        "## Variables con mayor peso exploratorio",
        "",
        _markdown_table(top_importances),
        "",
        "Estas variables no deben interpretarse como causas. Indican que el modelo las uso para separar patrones observados en el conjunto de prueba, dentro de las variables disponibles y la ventana 2024.",
        "",
        "## Figuras generadas e interpretacion",
        "",
    ]

    for figure in figure_catalog.to_dict("records"):
        figure_path = figure["ruta"]
        relative_to_report = Path("../figures/models") / Path(figure_path).name
        lines.extend(
            [
                f"### {figure['figura']}",
                "",
                f"![{figure['descripcion']}]({relative_to_report.as_posix()})",
                "",
                f"- Pregunta analitica: {figure['pregunta_analitica']}",
                f"- Descripcion: {figure['descripcion']}",
                f"- Interpretacion: {figure['interpretacion']}",
                f"- Conclusion: {figure['conclusion']}",
                f"- Ruta: `{figure_path}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Limitaciones",
            "",
            "- Los modelos se entrenan con registros observados de 2024; no reconstruyen la trayectoria academica completa.",
            "- `codigo_curso` puede capturar diferencias estructurales entre cursos; por eso sus importancias deben leerse junto con area, semestre, continuidad y variables curriculares.",
            "- La zona ordinaria es una variable academica previa al cierre final del curso, pero su disponibilidad operativa puede depender del momento en que se quiera aplicar el modelo.",
            "- Las clases positivas tienen prevalencias distintas; por eso precision, recall, F1, ROC-AUC y precision promedio deben revisarse en conjunto.",
            "- No se utiliza informacion de docentes, presupuesto, contratacion, horas docentes ni identificadores individuales.",
            "",
            "## Conclusion",
            "",
            "La Fase 7 deja modelos de clasificacion reproducibles para comparar regresion logistica, arbol de decision y Random Forest sobre los cuatro targets academicos definidos. Los resultados sirven para priorizar variables y cursos en analisis posteriores, manteniendo una lectura exploratoria, agregada y sin afirmaciones causales.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_classification_model(spec: ClassificationModelSpec) -> None:
    """Entrena todos los targets para un modelo y actualiza entregables."""

    ensure_project_directories()
    df = load_classification_dataset()
    validate_modeling_dataset(df)

    metrics_rows: list[dict[str, Any]] = []
    confusion_rows: list[dict[str, Any]] = []
    importance_tables: list[pd.DataFrame] = []

    for target in TARGET_COLUMNS:
        if target not in df.columns or df[target].nunique(dropna=True) < 2:
            continue
        metrics, confusion, importances = _train_target_model(df, spec, target)
        metrics_rows.append(metrics)
        confusion_rows.append(confusion)
        importance_tables.append(importances)

    metrics_df = pd.DataFrame(metrics_rows)
    confusion_df = pd.DataFrame(confusion_rows)
    importances_df = pd.concat(importance_tables, ignore_index=True) if importance_tables else pd.DataFrame()

    combined_metrics, combined_confusion, combined_importances = _save_combined_outputs(
        spec.model_key,
        metrics_df,
        confusion_df,
        importances_df,
    )
    figure_catalog = build_model_figures(combined_metrics, combined_confusion, combined_importances, MODELS_FIGURES_DIR)
    save_table(figure_catalog, FIGURE_CATALOG_PATH)
    write_text(MODELS_REPORT_PATH, _build_report(combined_metrics, combined_confusion, combined_importances, figure_catalog))

    print(
        f"Modelo {spec.model_name}: {len(metrics_df)} targets entrenados. "
        f"Reporte: {_relative_path(MODELS_REPORT_PATH)}"
    )
