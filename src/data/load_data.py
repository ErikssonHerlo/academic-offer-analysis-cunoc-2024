"""Funciones base para cargar datasets raw."""

from __future__ import annotations

import pandas as pd

from src.config.settings import DATASET_SPECS
from src.data.utils import ensure_project_directories, normalize_column_names


def load_raw_dataset(dataset_name: str) -> pd.DataFrame:
    """Carga un dataset raw por nombre logico configurado."""

    try:
        spec = DATASET_SPECS[dataset_name]
    except KeyError as exc:
        valid_names = ", ".join(sorted(DATASET_SPECS))
        raise KeyError(f"Dataset no configurado: {dataset_name}. Opciones: {valid_names}") from exc
    if not spec.path.exists():
        raise FileNotFoundError(f"No existe el archivo requerido: {spec.path}")
    return pd.read_csv(spec.path, dtype=str, keep_default_na=False)


def load_raw_dataset_normalized(dataset_name: str) -> pd.DataFrame:
    """Carga un dataset raw y normaliza nombres de columnas."""

    return normalize_column_names(load_raw_dataset(dataset_name))


def load_all_raw_datasets() -> dict[str, pd.DataFrame]:
    """Carga todos los datasets raw definidos en settings."""

    return {name: load_raw_dataset(name) for name in DATASET_SPECS}


def load_all_raw_datasets_normalized() -> dict[str, pd.DataFrame]:
    """Carga todos los datasets raw con nombres de columnas normalizados."""

    return {name: normalize_column_names(df) for name, df in load_all_raw_datasets().items()}


def build_raw_dataset_inventory(datasets: dict[str, pd.DataFrame] | None = None) -> pd.DataFrame:
    """Construye un inventario ligero de dimensiones y rutas raw."""

    loaded = datasets if datasets is not None else load_all_raw_datasets()
    rows = []
    for dataset_name, spec in DATASET_SPECS.items():
        df = loaded[dataset_name]
        rows.append(
            {
                "dataset": dataset_name,
                "archivo": spec.filename,
                "ruta": str(spec.path),
                "filas": len(df),
                "columnas": len(df.columns),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    """Punto de entrada para validar carga basica de datasets raw."""

    ensure_project_directories()
    datasets = load_all_raw_datasets()
    inventory = build_raw_dataset_inventory(datasets)
    print("Carga de datasets raw completada.")
    print(inventory.to_string(index=False))


if __name__ == "__main__":
    main()
