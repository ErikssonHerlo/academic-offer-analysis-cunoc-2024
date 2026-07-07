"""Graficos para modelos de clasificacion."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.data.utils import save_figure


FIGURE_SIZE_WIDE = (11, 6)
FIGURE_SIZE_GRID = (12, 10)
PRIMARY_COLOR = "#2f6f73"
SECONDARY_COLOR = "#d98c4a"
ACCENT_COLOR = "#7a4f9a"
NEUTRAL_COLOR = "#6f7782"
GRID_COLOR = "#d8dde3"
CONFUSION_CMAP = "YlGnBu"
TOP_VARIABLES_LIMIT = 12


def _format_count(value: float) -> str:
    return f"{value:,.0f}".replace(",", " ")


def _format_metric(value: float) -> str:
    if pd.isna(value):
        return "sin dato"
    return f"{value:.3f}"


def _label_vertical_bars(ax: plt.Axes) -> None:
    for container in ax.containers:
        labels = [_format_metric(bar.get_height()) if bar.get_height() else "" for bar in container]
        ax.bar_label(container, labels=labels, padding=3, fontsize=8)


def _label_horizontal_bars(ax: plt.Axes) -> None:
    for container in ax.containers:
        labels = [_format_metric(bar.get_width()) if bar.get_width() else "" for bar in container]
        ax.bar_label(container, labels=labels, padding=4, fontsize=8)


def _finish_figure(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    save_figure(fig, path)
    plt.close(fig)


def _relative_output_path(path: Path) -> str:
    parts = path.parts
    if "outputs" in parts:
        index = parts.index("outputs")
        return str(Path(*parts[index:]))
    return str(path)


def plot_metric_overview(metrics: pd.DataFrame, path: Path) -> None:
    """Grafica F1 y ROC-AUC promedio por modelo."""

    summary = (
        metrics.groupby(["modelo", "modelo_nombre"], as_index=False)
        .agg(f1=("f1", "mean"), roc_auc=("roc_auc", "mean"), recall=("recall", "mean"))
        .sort_values("modelo")
    )
    x = np.arange(len(summary))
    width = 0.26

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_WIDE)
    ax.bar(x - width, summary["f1"], width, label="F1", color=PRIMARY_COLOR)
    ax.bar(x, summary["roc_auc"], width, label="ROC-AUC", color=SECONDARY_COLOR)
    ax.bar(x + width, summary["recall"], width, label="Recall", color=ACCENT_COLOR)
    ax.set_title("Metricas promedio por modelo de clasificacion")
    ax.set_ylabel("Valor promedio")
    ax.set_ylim(0, 1.08)
    ax.set_xticks(x)
    ax.set_xticklabels(summary["modelo_nombre"], rotation=15, ha="right")
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8)
    ax.legend()
    _label_vertical_bars(ax)
    _finish_figure(fig, path)


def plot_confusion_matrices_for_model(confusion: pd.DataFrame, model_key: str, path: Path) -> None:
    """Grafica matrices de confusion por target para un modelo."""

    data = confusion[confusion["modelo"].eq(model_key)].copy()
    data = data.sort_values("target")
    fig, axes = plt.subplots(2, 2, figsize=FIGURE_SIZE_GRID)
    axes_flat = axes.ravel()

    for ax, (_, row) in zip(axes_flat, data.iterrows(), strict=False):
        matrix = np.array(
            [
                [row["verdaderos_negativos"], row["falsos_positivos"]],
                [row["falsos_negativos"], row["verdaderos_positivos"]],
            ],
            dtype=float,
        )
        image = ax.imshow(matrix, cmap=CONFUSION_CMAP)
        ax.set_title(str(row["target_descripcion"]))
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(["Pred. no", "Pred. si"])
        ax.set_yticklabels(["Real no", "Real si"])
        for y_index in range(matrix.shape[0]):
            for x_index in range(matrix.shape[1]):
                ax.text(
                    x_index,
                    y_index,
                    _format_count(matrix[y_index, x_index]),
                    ha="center",
                    va="center",
                    color="black",
                    fontsize=11,
                    fontweight="bold",
                )
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)

    for ax in axes_flat[len(data) :]:
        ax.axis("off")

    model_name = data["modelo_nombre"].iloc[0] if not data.empty else model_key
    fig.suptitle(f"Matrices de confusion - {model_name}", y=1.02)
    _finish_figure(fig, path)


def plot_importances_for_model(importances: pd.DataFrame, model_key: str, path: Path) -> None:
    """Grafica variables con mayor importancia agregada por modelo."""

    data = importances[importances["modelo"].eq(model_key)].copy()
    summary = (
        data.groupby(["modelo_nombre", "variable"], as_index=False)
        .agg(importancia=("importancia", "mean"))
        .sort_values("importancia", ascending=False)
        .head(TOP_VARIABLES_LIMIT)
        .sort_values("importancia", ascending=True)
    )

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_WIDE)
    ax.barh(summary["variable"], summary["importancia"], color=PRIMARY_COLOR)
    model_name = summary["modelo_nombre"].iloc[0] if not summary.empty else model_key
    ax.set_title(f"Variables destacadas - {model_name}")
    ax.set_xlabel("Importancia promedio en targets")
    ax.grid(axis="x", color=GRID_COLOR, linewidth=0.8)
    _label_horizontal_bars(ax)
    _finish_figure(fig, path)


def build_model_figures(
    metrics: pd.DataFrame,
    confusion: pd.DataFrame,
    importances: pd.DataFrame,
    output_dir: Path,
) -> pd.DataFrame:
    """Genera figuras de modelos y devuelve su catalogo interpretativo."""

    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, str]] = []

    if not metrics.empty:
        metrics_path = output_dir / "07_metricas_modelos.png"
        plot_metric_overview(metrics, metrics_path)
        best_model = (
            metrics.groupby("modelo_nombre", as_index=False)
            .agg(f1=("f1", "mean"))
            .sort_values("f1", ascending=False)
            .iloc[0]
        )
        records.append(
            {
                "figura": metrics_path.name,
                "pregunta_analitica": "Que modelo presenta mejor equilibrio promedio entre metricas de clasificacion?",
                "descripcion": "Barras comparativas de F1, ROC-AUC y recall promedio por modelo.",
                "interpretacion": (
                    f"El modelo con mayor F1 promedio observado es {best_model['modelo_nombre']} "
                    f"con {_format_metric(best_model['f1'])}."
                ),
                "conclusion": "La comparacion permite elegir modelos por equilibrio de metricas, no solo por exactitud global.",
                "ruta": _relative_output_path(metrics_path),
            }
        )

    for model_key, model_metrics in metrics.groupby("modelo", observed=False):
        model_name = model_metrics["modelo_nombre"].iloc[0]
        confusion_path = output_dir / f"07_matrices_confusion_{model_key}.png"
        plot_confusion_matrices_for_model(confusion, model_key, confusion_path)
        records.append(
            {
                "figura": confusion_path.name,
                "pregunta_analitica": f"Como se distribuyen aciertos y errores para {model_name}?",
                "descripcion": f"Matrices de confusion por target para {model_name}.",
                "interpretacion": "Las celdas muestran verdaderos negativos, falsos positivos, falsos negativos y verdaderos positivos para cada target.",
                "conclusion": "La matriz de confusion ayuda a revisar si el modelo esta capturando casos positivos o concentrandose en la clase mayoritaria.",
                "ruta": _relative_output_path(confusion_path),
            }
        )

        importance_path = output_dir / f"07_importancias_{model_key}.png"
        plot_importances_for_model(importances, model_key, importance_path)
        top_variable = (
            importances[importances["modelo"].eq(model_key)]
            .groupby("variable", as_index=False)
            .agg(importancia=("importancia", "mean"))
            .sort_values("importancia", ascending=False)
            .head(1)
        )
        variable_text = top_variable["variable"].iloc[0] if not top_variable.empty else "sin dato"
        records.append(
            {
                "figura": importance_path.name,
                "pregunta_analitica": f"Que variables pesan mas en {model_name}?",
                "descripcion": f"Ranking agregado de variables con mayor importancia para {model_name}.",
                "interpretacion": f"La variable agregada con mayor importancia promedio es {variable_text}.",
                "conclusion": "Las importancias orientan la lectura explicativa del modelo, sin implicar causalidad.",
                "ruta": _relative_output_path(importance_path),
            }
        )

    return pd.DataFrame(records)
