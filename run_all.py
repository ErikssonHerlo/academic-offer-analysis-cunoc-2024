"""Ejecutor principal del pipeline del proyecto.

Este archivo orquesta las fases tecnicas. En Fase 0 los modulos existen como
puntos de entrada verificables; en fases posteriores se reemplazaran los
placeholders por implementaciones completas.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable


PIPELINE_MODULES: tuple[str, ...] = (
    "src.data.validate_data",
    "src.data.clean_data",
    "src.features.build_derived_datasets",
    "src.analysis.eda",
    "src.analysis.statistical_tests",
    "src.models.logistic_regression",
    "src.models.decision_tree",
    "src.models.random_forest",
    "src.models.clustering",
    "src.models.association_rules",
    "src.models.linear_regression",
)


def _load_main(module_name: str) -> Callable[[], None]:
    module = importlib.import_module(module_name)
    main = getattr(module, "main", None)
    if not callable(main):
        raise AttributeError(f"El modulo {module_name} no expone una funcion main().")
    return main


def main() -> None:
    for module_name in PIPELINE_MODULES:
        print(f"Ejecutando {module_name}...")
        _load_main(module_name)()


if __name__ == "__main__":
    main()
