"""Entrada auxiliar para construir indicadores base.

La Fase 4 construye indicadores agregados dentro de
`src.features.build_derived_datasets` para mantener una sola fuente de verdad
entre datasets maestro, resumen curso-periodo y continuidad.
"""

from src.features.build_derived_datasets import main as build_derived_datasets


def main() -> None:
    build_derived_datasets()


if __name__ == "__main__":
    main()
