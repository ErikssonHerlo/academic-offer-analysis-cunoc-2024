"""Modelo de arbol de decision para targets academicos."""

from __future__ import annotations

from sklearn.tree import DecisionTreeClassifier

from src.models.classification_common import ClassificationModelSpec, RANDOM_STATE, run_classification_model


def main() -> None:
    spec = ClassificationModelSpec(
        model_key="decision_tree",
        model_name="Arbol de decision",
        estimator=DecisionTreeClassifier(
            class_weight="balanced",
            max_depth=6,
            min_samples_leaf=20,
            random_state=RANDOM_STATE,
        ),
        scale_numeric_features=False,
        importance_kind="importancia_gini",
    )
    run_classification_model(spec)


if __name__ == "__main__":
    main()
