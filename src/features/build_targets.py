"""Entrada auxiliar para construir targets analiticos.

Los targets de Fase 4 se generan junto con el dataset maestro en
`src.features.build_derived_datasets`, evitando definiciones duplicadas.
"""

from src.features.build_derived_datasets import main as build_derived_datasets


def main() -> None:
    build_derived_datasets()


if __name__ == "__main__":
    main()
