"""Modelo Random Forest para targets academicos."""

from __future__ import annotations

from sklearn.ensemble import RandomForestClassifier

from src.models.classification_common import ClassificationModelSpec, RANDOM_STATE, run_classification_model


def main() -> None:
    spec = ClassificationModelSpec(
        model_key="random_forest",
        model_name="Random Forest",
        estimator=RandomForestClassifier(
            class_weight="balanced",
            max_depth=10,
            min_samples_leaf=10,
            n_estimators=300,
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
        scale_numeric_features=False,
        importance_kind="importancia_gini_promedio",
    )
    run_classification_model(spec)


if __name__ == "__main__":
    main()
