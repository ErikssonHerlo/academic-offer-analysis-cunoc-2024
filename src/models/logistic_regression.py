"""Modelo de regresion logistica para targets academicos."""

from __future__ import annotations

from sklearn.linear_model import LogisticRegression

from src.models.classification_common import ClassificationModelSpec, RANDOM_STATE, run_classification_model


def main() -> None:
    spec = ClassificationModelSpec(
        model_key="logistic_regression",
        model_name="Regresion logistica",
        estimator=LogisticRegression(
            class_weight="balanced",
            max_iter=3000,
            random_state=RANDOM_STATE,
            solver="liblinear",
        ),
        scale_numeric_features=True,
        importance_kind="valor_absoluto_coeficiente",
    )
    run_classification_model(spec)


if __name__ == "__main__":
    main()
