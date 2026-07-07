"""Graficos reutilizables para el analisis exploratorio."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
import pandas as pd

from src.config.settings import PERIOD_LABELS, PERIOD_ORDER
from src.data.utils import save_figure


FIGURE_SIZE_WIDE = (10, 6)
FIGURE_SIZE_TALL = (12, 14)
PRIMARY_COLOR = "#2f6f73"
SECONDARY_COLOR = "#d98c4a"
ACCENT_COLOR = "#7a4f9a"
NEUTRAL_COLOR = "#6f7782"
GRID_COLOR = "#d8dde3"
HEATMAP_COLORS = ["#f2f4f7", "#2f6f73"]


def _format_count(value: float) -> str:
    return f"{value:,.0f}".replace(",", " ")


def _format_percent(value: float) -> str:
    return f"{value:.1%}"


def _label_vertical_bars(ax: plt.Axes) -> None:
    for container in ax.containers:
        labels = [_format_count(bar.get_height()) if bar.get_height() else "" for bar in container]
        ax.bar_label(container, labels=labels, padding=3, fontsize=8)


def _label_horizontal_bars(ax: plt.Axes, labels: list[str] | None = None) -> None:
    for container in ax.containers:
        if labels is None:
            bar_labels = [_format_count(bar.get_width()) if bar.get_width() else "" for bar in container]
        else:
            bar_labels = labels
        ax.bar_label(container, labels=bar_labels, padding=4, fontsize=8)


def _period_labels(periods: pd.Series | list[str]) -> list[str]:
    return [PERIOD_LABELS.get(str(period), str(period)) for period in periods]


def _format_percent_axis(ax: plt.Axes) -> None:
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")


def _finish_figure(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    save_figure(fig, path)
    plt.close(fig)


def plot_offer_by_period(indicators: pd.DataFrame, path: Path) -> None:
    """Grafica cursos ofertados y no ofertados por periodo."""

    data = indicators.copy()
    x = np.arange(len(data))
    width = 0.38

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_WIDE)
    ax.bar(x - width / 2, data["cursos_ofertados"], width, label="Ofertados", color=PRIMARY_COLOR)
    ax.bar(x + width / 2, data["cursos_no_ofertados"], width, label="No ofertados", color=NEUTRAL_COLOR)

    ax.set_title("Cursos ofertados y no ofertados por periodo")
    ax.set_ylabel("Cantidad de cursos")
    ax.set_xticks(x)
    ax.set_xticklabels(_period_labels(data["periodo_academico"]), rotation=20, ha="right")
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8)
    ax.legend()
    _label_vertical_bars(ax)
    _finish_figure(fig, path)


def plot_assignments_by_period(indicators: pd.DataFrame, path: Path) -> None:
    """Grafica asignaciones y estudiantes con nota por periodo."""

    data = indicators.copy()
    x = np.arange(len(data))
    width = 0.38

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_WIDE)
    ax.bar(x - width / 2, data["estudiantes_asignados"], width, label="Asignaciones", color=PRIMARY_COLOR)
    ax.bar(x + width / 2, data["estudiantes_con_nota"], width, label="Con nota", color=SECONDARY_COLOR)

    ax.set_title("Asignaciones y estudiantes con nota por periodo")
    ax.set_ylabel("Cantidad de registros")
    ax.set_xticks(x)
    ax.set_xticklabels(_period_labels(data["periodo_academico"]), rotation=20, ha="right")
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8)
    ax.legend()
    _label_vertical_bars(ax)
    _finish_figure(fig, path)


def plot_offer_by_area_group_period(indicators: pd.DataFrame, path: Path) -> None:
    """Grafica cursos ofertados por periodo y grupo academico."""

    pivot = indicators.pivot_table(
        index="periodo_academico",
        columns="grupo_area",
        values="cursos_ofertados",
        aggfunc="sum",
        fill_value=0,
        observed=False,
    ).reindex(PERIOD_ORDER)

    x = np.arange(len(pivot))
    width = 0.38
    groups = list(pivot.columns)
    colors = [PRIMARY_COLOR, SECONDARY_COLOR, ACCENT_COLOR]

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_WIDE)
    for index, group in enumerate(groups):
        offset = (index - (len(groups) - 1) / 2) * width
        ax.bar(x + offset, pivot[group], width, label=group, color=colors[index % len(colors)])

    ax.set_title("Cursos ofertados por periodo y grupo academico")
    ax.set_ylabel("Cantidad de cursos ofertados")
    ax.set_xticks(x)
    ax.set_xticklabels(_period_labels(pivot.index.tolist()), rotation=20, ha="right")
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8)
    ax.legend()
    _label_vertical_bars(ax)
    _finish_figure(fig, path)


def plot_top_definitive_loss(top_courses: pd.DataFrame, path: Path) -> None:
    """Grafica cursos con mayor perdida definitiva observada."""

    data = top_courses.sort_values("perdida_definitiva", ascending=True)
    labels = data["curso_etiqueta"]

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_WIDE)
    ax.barh(labels, data["perdida_definitiva"], color=SECONDARY_COLOR)
    ax.set_title("Cursos con mayor perdida definitiva")
    ax.set_xlabel("Cantidad de estudiantes")
    ax.grid(axis="x", color=GRID_COLOR, linewidth=0.8)
    _label_horizontal_bars(ax)
    _finish_figure(fig, path)


def plot_professional_critical_courses(courses: pd.DataFrame, path: Path) -> None:
    """Grafica cursos profesionales con mayor perdida relativa y baja continuidad."""

    data = courses.sort_values("tasa_perdida_definitiva", ascending=True)
    labels = data["curso_etiqueta"]
    bar_labels = [
        f"{_format_percent(rate)} | n={_format_count(total)} | cont={_format_percent(continuity)}"
        for rate, total, continuity in zip(
            data["tasa_perdida_definitiva"],
            data["estudiantes_con_acta_ordinaria"],
            data["indice_continuidad_oferta"],
            strict=True,
        )
    ]

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_WIDE)
    ax.barh(labels, data["tasa_perdida_definitiva"], color=SECONDARY_COLOR)
    ax.set_title("Cursos profesionales con mayor perdida relativa")
    ax.set_xlabel("Tasa de perdida definitiva")
    ax.xaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.grid(axis="x", color=GRID_COLOR, linewidth=0.8)
    _label_horizontal_bars(ax, bar_labels)
    ax.set_xlim(0, max(data["tasa_perdida_definitiva"].max() * 1.35, 0.1))
    _finish_figure(fig, path)


def plot_retake_flow_by_area_group(indicators: pd.DataFrame, path: Path) -> None:
    """Grafica perdidas, recursamientos y aprobaciones posteriores por grupo."""

    data = indicators.copy()
    x = np.arange(len(data))
    width = 0.25

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_WIDE)
    ax.bar(x - width, data["perdidas_definitivas"], width, label="Perdidas", color=NEUTRAL_COLOR)
    ax.bar(x, data["recursamientos_observables"], width, label="Recursaron", color=PRIMARY_COLOR)
    ax.bar(x + width, data["aprobaciones_posteriores"], width, label="Aprobaron despues", color=SECONDARY_COLOR)

    ax.set_title("Flujo posterior despues de perdida por grupo academico")
    ax.set_ylabel("Cantidad de registros")
    ax.set_xticks(x)
    ax.set_xticklabels(data["grupo_area"], rotation=0)
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8)
    ax.legend()
    _label_vertical_bars(ax)
    _finish_figure(fig, path)


def plot_professional_loss_without_later_offer(courses: pd.DataFrame, path: Path) -> None:
    """Grafica cursos profesionales con perdida y sin oferta posterior observada."""

    data = courses.sort_values("perdidas_sin_oferta_posterior_2024", ascending=True)
    labels = data["curso_etiqueta"]
    bar_labels = [
        f"{_format_count(losses)} | tasa={_format_percent(rate)}"
        for losses, rate in zip(
            data["perdidas_sin_oferta_posterior_2024"],
            data["tasa_perdidas_sin_oferta_posterior"],
            strict=True,
        )
    ]

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_WIDE)
    ax.barh(labels, data["perdidas_sin_oferta_posterior_2024"], color=ACCENT_COLOR)
    ax.set_title("Cursos profesionales con perdida y sin oferta posterior")
    ax.set_xlabel("Perdidas sin oferta posterior observable en 2024")
    ax.grid(axis="x", color=GRID_COLOR, linewidth=0.8)
    _label_horizontal_bars(ax, bar_labels)
    _finish_figure(fig, path)


def plot_offer_heatmap(heatmap: pd.DataFrame, path: Path) -> None:
    """Grafica matriz curso-periodo de oferta observada."""

    period_columns = [f"abierto_{period}" for period in PERIOD_ORDER]
    matrix = heatmap[period_columns].astype(int).to_numpy()

    fig_height = max(FIGURE_SIZE_TALL[1], len(heatmap) * 0.18)
    fig, ax = plt.subplots(figsize=(FIGURE_SIZE_TALL[0], fig_height))
    ax.imshow(matrix, aspect="auto", cmap=ListedColormap(HEATMAP_COLORS), vmin=0, vmax=1)

    ax.set_title("Oferta observada por curso y periodo")
    ax.set_xticks(np.arange(len(PERIOD_ORDER)))
    ax.set_xticklabels(PERIOD_ORDER)
    ax.set_yticks(np.arange(len(heatmap)))
    ax.set_yticklabels(heatmap["curso_etiqueta"], fontsize=7)
    ax.set_xlabel("Periodo academico")
    ax.set_ylabel("Curso")

    ax.set_xticks(np.arange(-0.5, len(PERIOD_ORDER), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(heatmap), 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=0.8)
    ax.tick_params(which="minor", bottom=False, left=False)
    _finish_figure(fig, path)


def plot_approval_distribution_by_semester(course_period: pd.DataFrame, path: Path) -> None:
    """Grafica distribucion de tasa de aprobacion ordinaria por semestre."""

    data = course_period.dropna(subset=["semestre_pensum", "tasa_aprobacion_ordinaria"]).copy()
    data = data[data["estudiantes_con_acta_ordinaria"] > 0]
    semesters = sorted(data["semestre_pensum"].astype(int).unique())
    values = [
        data.loc[data["semestre_pensum"].astype(int).eq(semester), "tasa_aprobacion_ordinaria"].to_numpy()
        for semester in semesters
    ]

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_WIDE)
    boxplot = ax.boxplot(values, tick_labels=[str(semester) for semester in semesters], patch_artist=True)
    for patch in boxplot["boxes"]:
        patch.set_facecolor(PRIMARY_COLOR)
        patch.set_alpha(0.6)

    ax.set_title("Distribucion de aprobacion ordinaria por semestre del pensum")
    ax.set_xlabel("Semestre del pensum")
    ax.set_ylabel("Tasa de aprobacion ordinaria")
    _format_percent_axis(ax)
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8)
    _finish_figure(fig, path)


def plot_loss_vs_continuity(continuity: pd.DataFrame, path: Path) -> None:
    """Grafica relacion descriptiva entre perdida definitiva y continuidad."""

    data = continuity.copy()
    sizes = np.clip(data["total_estudiantes_con_nota_2024"].fillna(0).to_numpy(), 10, None)

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_WIDE)
    scatter = ax.scatter(
        data["indice_continuidad_oferta"],
        data["tasa_perdida_definitiva_2024"],
        s=sizes * 3,
        c=data["estudiantes_en_riesgo_retraso_curricular_2024"],
        cmap="viridis",
        alpha=0.75,
        edgecolor="white",
        linewidth=0.6,
    )
    ax.set_title("Perdida definitiva y continuidad de oferta por curso")
    ax.set_xlabel("Indice de continuidad de oferta")
    ax.set_ylabel("Tasa de perdida definitiva")
    _format_percent_axis(ax)
    ax.grid(color=GRID_COLOR, linewidth=0.8)
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label("Estudiantes en riesgo potencial curricular")
    _finish_figure(fig, path)


def plot_risk_by_area(risk_by_area: pd.DataFrame, path: Path) -> None:
    """Grafica riesgo potencial curricular por area academica."""

    data = risk_by_area.sort_values("estudiantes_en_riesgo_retraso_curricular", ascending=True)

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_WIDE)
    ax.barh(data["area_academica"], data["estudiantes_en_riesgo_retraso_curricular"], color=ACCENT_COLOR)
    ax.set_title("Riesgo de retraso academico potencial por area")
    ax.set_xlabel("Cantidad de estudiantes")
    ax.grid(axis="x", color=GRID_COLOR, linewidth=0.8)
    _label_horizontal_bars(ax)
    _finish_figure(fig, path)
