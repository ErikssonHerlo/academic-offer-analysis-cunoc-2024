"""Funciones base para cargar datasets raw."""

from __future__ import annotations

import pandas as pd

from src.config.settings import DATASET_SPECS


def load_raw_dataset(dataset_name: str) -> pd.DataFrame:
    """Carga un dataset raw por nombre logico configurado."""

    try:
        spec = DATASET_SPECS[dataset_name]
    except KeyError as exc:
        valid_names = ", ".join(sorted(DATASET_SPECS))
        raise KeyError(f"Dataset no configurado: {dataset_name}. Opciones: {valid_names}") from exc
    return pd.read_csv(spec.path, dtype=str, keep_default_na=False)


def load_all_raw_datasets() -> dict[str, pd.DataFrame]:
    """Carga todos los datasets raw definidos en settings."""

    return {name: load_raw_dataset(name) for name in DATASET_SPECS}
