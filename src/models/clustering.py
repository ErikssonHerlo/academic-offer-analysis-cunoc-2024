"""Clustering descriptivo de cursos criticos."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.config.settings import FIGURES_DIR, PROCESSED_DATA_DIR, PROJECT_ROOT, REPORTS_DIR, TABLES_DIR, YES_VALUE
from src.data.utils import ensure_project_directories, safe_divide, save_table, write_text
from src.visualization.plots_clusters import plot_cluster_profile, plot_cluster_scatter


CLUSTERING_INPUT_PATH = PROCESSED_DATA_DIR / "ds_cursos_criticos_clustering.csv"
CLUSTERS_TABLES_DIR = TABLES_DIR / "clusters"
CLUSTERS_FIGURES_DIR = FIGURES_DIR / "clusters"
CLUSTERING_REPORT_PATH = REPORTS_DIR / "clustering_cursos.md"

METRICS_PATH = CLUSTERS_TABLES_DIR / "08_metricas_clustering.csv"
CLUSTERED_COURSES_PATH = CLUSTERS_TABLES_DIR / "08_cursos_clusterizados.csv"
PROFILE_PATH = CLUSTERS_TABLES_DIR / "08_perfil_clusters.csv"
FIGURE_CATALOG_PATH = CLUSTERS_TABLES_DIR / "08_catalogo_figuras_clustering.csv"

RANDOM_STATE = 2024
MIN_CLUSTERS = 2
MAX_CLUSTERS = 6
COMMON_AREA_NAME = "Ciencias Basicas y Complementarias"
PROFESSIONAL_AREA_GROUP = "Area profesional"

BASE_NUMERIC_FEATURES: tuple[str, ...] = (
    "tasa_perdida_definitiva_2024",
    "tasa_recuperacion_2024",
    "indice_continuidad_oferta",
    "estudiantes_sin_oportunidad_inmediata_2024",
    "estudiantes_en_riesgo_retraso_curricular_2024",
    "cantidad_cursos_dependientes",
    "tasa_ocupacion_promedio_2024",
    "total_estudiantes_asignados_2024",
    "total_estudiantes_con_nota_2024",
)

DERIVED_FEATURES: tuple[str, ...] = (
    "es_curso_base",
    "es_curso_bloqueante",
    "nivel_bloqueo_valor",
)

CLUSTERING_FEATURES: tuple[str, ...] = (*BASE_NUMERIC_FEATURES, *DERIVED_FEATURES)

LEVEL_MAP: dict[str, int] = {
    "bajo": 1,
    "medio": 2,
    "alto": 3,
}


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


def _format_percent(value: Any) -> str:
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return "sin dato"
    return f"{numeric:.1%}"


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


def _as_yes_no(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().eq(YES_VALUE.lower()).astype(int)


def load_clustering_data() -> pd.DataFrame:
    """Carga y prepara el dataset de cursos criticos."""

    df = pd.read_csv(CLUSTERING_INPUT_PATH)
    result = df.copy()
    for column in BASE_NUMERIC_FEATURES:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    result["es_curso_base"] = _as_yes_no(result["curso_base"])
    result["es_curso_bloqueante"] = _as_yes_no(result["curso_bloqueante"])
    result["nivel_bloqueo_valor"] = (
        result["nivel_bloqueo_curricular"].astype("string").str.strip().str.lower().map(LEVEL_MAP).fillna(0)
    )
    result["grupo_area"] = np.where(result["area_academica"].eq(COMMON_AREA_NAME), "Area comun", PROFESSIONAL_AREA_GROUP)
    result["curso_etiqueta"] = result["codigo_curso"].astype(str) + " - " + result["nombre_curso"].astype(str)
    return result


def _feature_matrix(df: pd.DataFrame) -> np.ndarray:
    pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    return pipeline.fit_transform(df[list(CLUSTERING_FEATURES)])


def evaluate_cluster_counts(matrix: np.ndarray) -> pd.DataFrame:
    """Evalua opciones de K para seleccionar un agrupamiento reproducible."""

    max_clusters = min(MAX_CLUSTERS, len(matrix) - 1)
    rows = []
    for cluster_count in range(MIN_CLUSTERS, max_clusters + 1):
        estimator = KMeans(n_clusters=cluster_count, random_state=RANDOM_STATE, n_init="auto")
        labels = estimator.fit_predict(matrix)
        rows.append(
            {
                "k": cluster_count,
                "inercia": float(estimator.inertia_),
                "silhouette": float(silhouette_score(matrix, labels)),
                "davies_bouldin": float(davies_bouldin_score(matrix, labels)),
                "calinski_harabasz": float(calinski_harabasz_score(matrix, labels)),
            }
        )
    result = pd.DataFrame(rows)
    result["k_seleccionado"] = result["silhouette"].eq(result["silhouette"].max())
    return result.sort_values(["silhouette", "k"], ascending=[False, True]).reset_index(drop=True)


def assign_clusters(df: pd.DataFrame, matrix: np.ndarray, selected_k: int) -> pd.DataFrame:
    """Asigna clusters y componentes principales a cada curso."""

    estimator = KMeans(n_clusters=selected_k, random_state=RANDOM_STATE, n_init="auto")
    labels = estimator.fit_predict(matrix)
    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    coordinates = pca.fit_transform(matrix)

    result = df.copy()
    result["cluster"] = labels
    result["pc1"] = coordinates[:, 0]
    result["pc2"] = coordinates[:, 1]
    result["varianza_pca_2_componentes"] = float(pca.explained_variance_ratio_.sum())
    return result.sort_values(["cluster", "area_academica", "codigo_curso"]).reset_index(drop=True)


def build_cluster_profile(clustered: pd.DataFrame) -> pd.DataFrame:
    """Construye un perfil agregado e interpretable por cluster."""

    profile = clustered.groupby("cluster", observed=False).agg(
        cursos=("codigo_curso", "nunique"),
        total_estudiantes_con_nota_2024=("total_estudiantes_con_nota_2024", "sum"),
        tasa_perdida_definitiva_2024_media=("tasa_perdida_definitiva_2024", "mean"),
        tasa_recuperacion_2024_media=("tasa_recuperacion_2024", "mean"),
        indice_continuidad_oferta_media=("indice_continuidad_oferta", "mean"),
        estudiantes_sin_oportunidad_inmediata_2024=("estudiantes_sin_oportunidad_inmediata_2024", "sum"),
        estudiantes_en_riesgo_retraso_curricular_2024=("estudiantes_en_riesgo_retraso_curricular_2024", "sum"),
        cantidad_cursos_dependientes_media=("cantidad_cursos_dependientes", "mean"),
        cursos_bloqueantes=("es_curso_bloqueante", "sum"),
        cursos_base=("es_curso_base", "sum"),
        cursos_area_profesional=("grupo_area", lambda values: int(values.eq(PROFESSIONAL_AREA_GROUP).sum())),
    )
    profile = profile.reset_index()
    profile["proporcion_area_profesional"] = safe_divide(profile["cursos_area_profesional"], profile["cursos"])
    profile["etiqueta_descriptiva"] = profile.apply(_cluster_label, axis=1)
    return profile.sort_values("cluster").reset_index(drop=True)


def _cluster_label(row: pd.Series) -> str:
    without_evaluable_activity = row["total_estudiantes_con_nota_2024"] == 0
    high_loss = row["tasa_perdida_definitiva_2024_media"] >= 0.30
    low_continuity = row["indice_continuidad_oferta_media"] <= 0.40
    high_risk = row["estudiantes_en_riesgo_retraso_curricular_2024"] >= 60
    mostly_professional = row["proporcion_area_profesional"] >= 0.60

    if without_evaluable_activity:
        return "Sin actividad evaluada observable"
    if high_loss and low_continuity and mostly_professional:
        return "Alta perdida y baja continuidad profesional"
    if high_risk and low_continuity:
        return "Riesgo curricular con continuidad limitada"
    if high_loss:
        return "Perdida relativa alta"
    if mostly_professional:
        return "Profesional con criticidad moderada"
    return "Criticidad baja o intermedia"


def build_figure_catalog(clustered: pd.DataFrame, profile: pd.DataFrame) -> pd.DataFrame:
    """Genera metadatos interpretativos para figuras de clustering."""

    scatter_path = CLUSTERS_FIGURES_DIR / "08_clusters_cursos.png"
    profile_path = CLUSTERS_FIGURES_DIR / "08_perfil_clusters.png"
    largest_cluster = profile.sort_values("cursos", ascending=False).iloc[0]
    highest_loss_cluster = profile.sort_values("tasa_perdida_definitiva_2024_media", ascending=False).iloc[0]

    return pd.DataFrame(
        [
            {
                "figura": scatter_path.name,
                "pregunta_analitica": "Que perfiles de cursos criticos emergen al combinar perdida, continuidad y bloqueo curricular?",
                "descripcion": "Dispersion de cursos sobre dos componentes principales, coloreada por cluster asignado.",
                "interpretacion": (
                    f"El cluster con mayor cantidad de cursos es el {int(largest_cluster['cluster'])}, "
                    f"con {int(largest_cluster['cursos'])} cursos."
                ),
                "conclusion": "La agrupacion permite priorizar perfiles de cursos, no categorias naturales definitivas.",
                "ruta": _relative_path(scatter_path),
            },
            {
                "figura": profile_path.name,
                "pregunta_analitica": "Como difieren los clusters en perdida, recuperacion, continuidad y area profesional?",
                "descripcion": "Barras comparativas de indicadores promedio por cluster.",
                "interpretacion": (
                    f"El cluster {int(highest_loss_cluster['cluster'])} presenta la mayor tasa media de perdida "
                    f"definitiva observada: {_format_percent(highest_loss_cluster['tasa_perdida_definitiva_2024_media'])}."
                ),
                "conclusion": "El perfil promedio ayuda a explicar por que ciertos cursos deben revisarse junto con continuidad de oferta.",
                "ruta": _relative_path(profile_path),
            },
        ]
    )


def _report_profile_table(profile: pd.DataFrame) -> pd.DataFrame:
    table = profile[
        [
            "cluster",
            "etiqueta_descriptiva",
            "cursos",
            "tasa_perdida_definitiva_2024_media",
            "tasa_recuperacion_2024_media",
            "indice_continuidad_oferta_media",
            "proporcion_area_profesional",
            "estudiantes_en_riesgo_retraso_curricular_2024",
        ]
    ].copy()
    for column in [
        "tasa_perdida_definitiva_2024_media",
        "tasa_recuperacion_2024_media",
        "indice_continuidad_oferta_media",
        "proporcion_area_profesional",
    ]:
        table[column] = table[column].map(_format_percent)
    return table


def _report_metrics_table(metrics: pd.DataFrame) -> pd.DataFrame:
    table = metrics.sort_values("k").copy()
    for column in ["inercia", "silhouette", "davies_bouldin", "calinski_harabasz"]:
        table[column] = table[column].map(_format_metric)
    return table


def write_report(metrics: pd.DataFrame, profile: pd.DataFrame, figure_catalog: pd.DataFrame) -> None:
    selected = metrics[metrics["k_seleccionado"]].iloc[0]
    generated_tables = pd.DataFrame(
        [
            {"tabla": "08_metricas_clustering", "ruta": _relative_path(METRICS_PATH)},
            {"tabla": "08_cursos_clusterizados", "ruta": _relative_path(CLUSTERED_COURSES_PATH)},
            {"tabla": "08_perfil_clusters", "ruta": _relative_path(PROFILE_PATH)},
            {"tabla": "08_catalogo_figuras_clustering", "ruta": _relative_path(FIGURE_CATALOG_PATH)},
        ]
    )

    figure_sections = []
    for _, row in figure_catalog.iterrows():
        figure_sections.append(
            f"""### {row['figura']}

![{row['descripcion']}](../figures/clusters/{row['figura']})

- Pregunta analitica: {row['pregunta_analitica']}
- Descripcion: {row['descripcion']}
- Interpretacion: {row['interpretacion']}
- Conclusion: {row['conclusion']}
- Ruta: `{row['ruta']}`
"""
        )

    content = f"""# Clustering de cursos criticos

## Objetivo

Agrupar cursos segun indicadores agregados de perdida definitiva, recuperacion,
continuidad de oferta, bloqueo curricular y volumen academico observado en
2024.

El clustering es descriptivo. Los clusters no son categorias naturales ni
prueban causalidad; sirven para resumir perfiles de cursos que pueden requerir
lectura academica conjunta.

## Tablas generadas

{_markdown_table(generated_tables)}

## Seleccion de K

{_markdown_table(_report_metrics_table(metrics))}

Se selecciona `k={int(selected['k'])}` porque obtuvo el mayor silhouette entre
las opciones evaluadas de {MIN_CLUSTERS} a {MAX_CLUSTERS} clusters, cuando el
tamano del dataset lo permite.

## Perfil de clusters

{_markdown_table(_report_profile_table(profile))}

## Figuras generadas e interpretacion

{"".join(figure_sections)}

## Limitaciones

- El resultado depende de las variables agregadas disponibles para 2024.
- Las variables fueron escaladas para que los conteos y tasas puedan compararse
  dentro del algoritmo.
- Los clusters deben interpretarse como perfiles descriptivos y no como
  diagnosticos individuales de cursos.
- No se utilizan docentes ni identificadores individuales.

## Conclusion

La agrupacion de cursos criticos sintetiza patrones de perdida, recuperacion,
continuidad y bloqueo curricular en perfiles comparables. Estos perfiles ayudan
a complementar los rankings de Fase 5 y la inferencia de Fase 6, manteniendo
una lectura exploratoria y sin afirmar causalidad.
"""
    write_text(CLUSTERING_REPORT_PATH, content)


def main() -> None:
    ensure_project_directories()
    CLUSTERS_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    CLUSTERS_FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    data = load_clustering_data()
    matrix = _feature_matrix(data)
    metrics = evaluate_cluster_counts(matrix)
    selected_k = int(metrics[metrics["k_seleccionado"]].iloc[0]["k"])
    clustered = assign_clusters(data, matrix, selected_k)
    profile = build_cluster_profile(clustered)

    plot_cluster_scatter(clustered, CLUSTERS_FIGURES_DIR / "08_clusters_cursos.png")
    plot_cluster_profile(profile, CLUSTERS_FIGURES_DIR / "08_perfil_clusters.png")
    figure_catalog = build_figure_catalog(clustered, profile)

    save_table(metrics.sort_values("k").reset_index(drop=True), METRICS_PATH)
    save_table(clustered, CLUSTERED_COURSES_PATH)
    save_table(profile, PROFILE_PATH)
    save_table(figure_catalog, FIGURE_CATALOG_PATH)
    write_report(metrics, profile, figure_catalog)

    print(f"Clustering completado con k={selected_k}. Reporte: {_relative_path(CLUSTERING_REPORT_PATH)}")


if __name__ == "__main__":
    main()
