"""Graficos para clustering de cursos criticos."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.data.utils import save_figure


FIGURE_SIZE_WIDE = (11, 6)
PRIMARY_COLOR = "#2f6f73"
SECONDARY_COLOR = "#d98c4a"
ACCENT_COLOR = "#7a4f9a"
NEUTRAL_COLOR = "#6f7782"
GRID_COLOR = "#d8dde3"
CLUSTER_CMAP = "tab10"


def _format_metric(value: float) -> str:
    if pd.isna(value):
        return "sin dato"
    return f"{value:.2f}"


def _finish_figure(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    save_figure(fig, path)
    plt.close(fig)


def _label_vertical_bars(ax: plt.Axes) -> None:
    for container in ax.containers:
        labels = [_format_metric(bar.get_height()) if bar.get_height() else "" for bar in container]
        ax.bar_label(container, labels=labels, padding=3, fontsize=8)


def plot_cluster_scatter(clustered_courses: pd.DataFrame, path: Path) -> None:
    """Grafica cursos clusterizados sobre dos componentes principales."""

    data = clustered_courses.copy()
    fig, ax = plt.subplots(figsize=FIGURE_SIZE_WIDE)
    scatter = ax.scatter(
        data["pc1"],
        data["pc2"],
        c=data["cluster"],
        cmap=CLUSTER_CMAP,
        s=np.clip(data["total_estudiantes_con_nota_2024"].fillna(0).to_numpy(), 20, 180),
        alpha=0.78,
        edgecolor="white",
        linewidth=0.7,
    )
    ax.set_title("Cursos criticos agrupados por perfil observado")
    ax.set_xlabel("Componente principal 1")
    ax.set_ylabel("Componente principal 2")
    ax.grid(color=GRID_COLOR, linewidth=0.8)
    legend = ax.legend(*scatter.legend_elements(), title="Cluster", loc="best")
    ax.add_artist(legend)
    _finish_figure(fig, path)


def plot_cluster_profile(cluster_profile: pd.DataFrame, path: Path) -> None:
    """Grafica indicadores promedio por cluster."""

    metric_columns = [
        "tasa_perdida_definitiva_2024_media",
        "tasa_recuperacion_2024_media",
        "indice_continuidad_oferta_media",
        "proporcion_area_profesional",
    ]
    labels = [
        "Perdida definitiva",
        "Recuperacion",
        "Continuidad",
        "Area profesional",
    ]
    data = cluster_profile.sort_values("cluster").copy()
    x = np.arange(len(data))
    width = 0.18
    colors = [PRIMARY_COLOR, SECONDARY_COLOR, ACCENT_COLOR, NEUTRAL_COLOR]

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_WIDE)
    for index, (column, label) in enumerate(zip(metric_columns, labels, strict=True)):
        offset = (index - (len(metric_columns) - 1) / 2) * width
        ax.bar(x + offset, data[column], width, label=label, color=colors[index])

    ax.set_title("Perfil promedio de clusters de cursos")
    ax.set_ylabel("Valor promedio")
    ax.set_ylim(0, max(1.05, float(data[metric_columns].max().max()) * 1.15))
    ax.set_xticks(x)
    ax.set_xticklabels([f"Cluster {cluster}" for cluster in data["cluster"]])
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8)
    ax.legend()
    _label_vertical_bars(ax)
    _finish_figure(fig, path)
