"""Utilidades compartidas para carga, limpieza ligera y escritura de salidas."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.config.settings import (
    NO_VALUE,
    REQUIRED_DIRECTORIES,
    SPECIAL_EQ_VALUE,
    YES_VALUE,
)


EMPTY_VALUES = {"", "nan", "none", "null", "na", "n/a"}


def ensure_project_directories() -> None:
    """Crea los directorios requeridos por el proyecto si no existen."""

    for directory in REQUIRED_DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)


def normalize_column_name(column_name: Any) -> str:
    """Convierte un nombre de columna a snake_case ASCII."""

    text = str(column_name).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve una copia del dataframe con columnas en snake_case."""

    result = df.copy()
    result.columns = [normalize_column_name(
        column) for column in result.columns]
    return result


def clean_text_series(series: pd.Series) -> pd.Series:
    """Limpia espacios repetidos y valores vacios en una serie de texto."""

    cleaned = series.astype("string").str.strip()
    cleaned = cleaned.str.replace(r"\s+", " ", regex=True)
    return cleaned.mask(cleaned.str.lower().isin(EMPTY_VALUES))


def parse_numeric(series: pd.Series, special_values: set[str] | None = None) -> pd.Series:
    """Convierte una serie a numerica conservando especiales como nulos."""

    values_to_null = {SPECIAL_EQ_VALUE}
    if special_values:
        values_to_null.update(special_values)

    cleaned = clean_text_series(series)
    cleaned = cleaned.mask(cleaned.isin(values_to_null))
    return pd.to_numeric(cleaned, errors="coerce")


def _parse_date_component(value: Any, component_index: int) -> pd.Timestamp:
    if pd.isna(value):
        return pd.NaT

    text = str(value).strip()
    if not text or text.lower() in EMPTY_VALUES:
        return pd.NaT

    parts = [part.strip() for part in text.split("/") if part.strip()]
    if not parts:
        return pd.NaT

    selected_index = min(component_index, len(parts) - 1)
    return pd.to_datetime(parts[selected_index], errors="coerce")


def parse_date_or_range_start(value: Any) -> pd.Timestamp:
    """Extrae la fecha inicial de un valor ISO simple o rango ISO."""

    return _parse_date_component(value, 0)


def parse_date_or_range_end(value: Any) -> pd.Timestamp:
    """Extrae la fecha final de un valor ISO simple o rango ISO."""

    return _parse_date_component(value, 1)


def si_no_to_bool(series: pd.Series) -> pd.Series:
    """Convierte etiquetas Si/No a booleanos pandas nullable."""

    normalized = clean_text_series(series)
    normalized = normalized.str.lower().map(
        {
            YES_VALUE.lower(): True,
            "si": True,
            "s": True,
            "true": True,
            "1": True,
            NO_VALUE.lower(): False,
            "n": False,
            "false": False,
            "0": False,
        }
    )
    return normalized.astype("boolean")


def safe_divide(numerator: Any, denominator: Any) -> Any:
    """Divide evitando infinitos cuando el denominador es cero o nulo."""

    numerator_array = np.asarray(numerator, dtype="float64")
    denominator_array = np.asarray(denominator, dtype="float64")
    result = np.divide(
        numerator_array,
        denominator_array,
        out=np.full_like(numerator_array, np.nan, dtype="float64"),
        where=denominator_array != 0,
    )

    if np.isscalar(numerator) and np.isscalar(denominator):
        return float(result)
    return result


def save_table(df: pd.DataFrame, path: Path, **to_csv_kwargs: Any) -> None:
    """Guarda una tabla CSV creando el directorio padre."""

    path.parent.mkdir(parents=True, exist_ok=True)
    kwargs = {"index": False}
    kwargs.update(to_csv_kwargs)
    df.to_csv(path, **kwargs)


def save_figure(fig: Any, path: Path, *, dpi: int = 300) -> None:
    """Guarda una figura matplotlib con parametros consistentes."""

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")


def write_text(path: Path, content: str) -> None:
    """Escribe un archivo de texto UTF-8 creando el directorio padre."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
