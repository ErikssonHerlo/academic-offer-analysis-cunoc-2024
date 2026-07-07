"""Reglas de asociacion academicas sobre transacciones agregadas."""

from __future__ import annotations

from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.config.settings import PROCESSED_DATA_DIR, PROJECT_ROOT, REPORTS_DIR, TABLES_DIR
from src.data.utils import ensure_project_directories, save_table, write_text


ASSOCIATION_INPUT_PATH = PROCESSED_DATA_DIR / "ds_reglas_asociacion.csv"
ASSOCIATION_TABLES_DIR = TABLES_DIR / "association_rules"
ASSOCIATION_REPORT_PATH = REPORTS_DIR / "reglas_asociacion.md"

ITEMSETS_PATH = ASSOCIATION_TABLES_DIR / "08_itemsets_frecuentes.csv"
RULES_PATH = ASSOCIATION_TABLES_DIR / "08_reglas_asociacion.csv"

TRANSACTION_ID_COLUMN = "transaccion_id"
MIN_SUPPORT = 0.05
MIN_CONFIDENCE = 0.60
MIN_LIFT = 1.05
MAX_ITEMSET_SIZE = 3
MAX_CONSEQUENT_SIZE = 1
REPORT_RULE_LIMIT = 15

RELEVANT_CONSEQUENTS: tuple[str, ...] = (
    "perdio",
    "recuperacion",
    "riesgo_retraso",
    "no_abierto_siguiente",
    "aprobo",
)

STRUCTURAL_RISK_COMPONENTS = {"riesgo_retraso", "perdio", "no_abierto_siguiente"}


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


def load_transactions() -> pd.DataFrame:
    """Carga transacciones booleanas para reglas de asociacion."""

    df = pd.read_csv(ASSOCIATION_INPUT_PATH)
    item_columns = [column for column in df.columns if column != TRANSACTION_ID_COLUMN]
    result = df[item_columns].copy()
    for column in item_columns:
        result[column] = result[column].astype(str).str.strip().str.lower().isin({"true", "1", "si", "sí"})
    return result


def _support(transactions: pd.DataFrame, items: tuple[str, ...]) -> float:
    if not items:
        return 0.0
    return float(transactions.loc[:, list(items)].all(axis=1).mean())


def build_frequent_itemsets(transactions: pd.DataFrame) -> pd.DataFrame:
    """Construye itemsets frecuentes hasta un tamano controlado."""

    support_by_itemset: dict[tuple[str, ...], float] = {}
    item_columns = sorted(transactions.columns)
    frequent_singletons = []

    for item in item_columns:
        itemset = (item,)
        item_support = _support(transactions, itemset)
        if item_support >= MIN_SUPPORT:
            support_by_itemset[itemset] = item_support
            frequent_singletons.append(item)

    for size in range(2, MAX_ITEMSET_SIZE + 1):
        for itemset in combinations(frequent_singletons, size):
            item_support = _support(transactions, itemset)
            if item_support >= MIN_SUPPORT:
                support_by_itemset[tuple(sorted(itemset))] = item_support

    rows = [
        {
            "itemset": " + ".join(itemset),
            "items": itemset,
            "tamano_itemset": len(itemset),
            "soporte": support,
            "conteo": int(round(support * len(transactions))),
        }
        for itemset, support in support_by_itemset.items()
    ]
    result = pd.DataFrame(rows)
    return result.sort_values(["tamano_itemset", "soporte", "itemset"], ascending=[True, False, True]).reset_index(
        drop=True
    )


def _has_relevant_consequent(consequent: tuple[str, ...]) -> bool:
    return any(item in RELEVANT_CONSEQUENTS for item in consequent)


def _is_structural_rule(antecedent: tuple[str, ...], consequent: tuple[str, ...]) -> bool:
    """Filtra reglas que solo reexpresan componentes definidos del target."""

    combined = set(antecedent).union(consequent)
    return "riesgo_retraso" in combined and len(combined.intersection(STRUCTURAL_RISK_COMPONENTS)) >= 2


def build_rules(frequent_itemsets: pd.DataFrame) -> pd.DataFrame:
    """Construye reglas filtradas por soporte, confianza y lift."""

    if frequent_itemsets.empty:
        return pd.DataFrame()

    supports = {
        tuple(row["items"]): float(row["soporte"])
        for _, row in frequent_itemsets.iterrows()
    }
    rows = []
    for itemset, itemset_support in supports.items():
        if len(itemset) < 2:
            continue
        items = tuple(itemset)
        for antecedent_size in range(1, len(items)):
            for antecedent in combinations(items, antecedent_size):
                antecedent = tuple(sorted(antecedent))
                consequent = tuple(sorted(set(items) - set(antecedent)))
                if len(consequent) > MAX_CONSEQUENT_SIZE or _is_structural_rule(antecedent, consequent):
                    continue
                antecedent_support = supports.get(antecedent)
                consequent_support = supports.get(consequent)
                if not antecedent_support or not consequent_support:
                    continue

                confidence = itemset_support / antecedent_support
                lift = confidence / consequent_support
                if confidence < MIN_CONFIDENCE or lift < MIN_LIFT:
                    continue

                rows.append(
                    {
                        "antecedente": " + ".join(antecedent),
                        "consecuente": " + ".join(consequent),
                        "tamano_antecedente": len(antecedent),
                        "tamano_consecuente": len(consequent),
                        "soporte": itemset_support,
                        "confianza": confidence,
                        "lift": lift,
                        "soporte_antecedente": antecedent_support,
                        "soporte_consecuente": consequent_support,
                        "leverage": itemset_support - antecedent_support * consequent_support,
                        "consecuente_relevante": _has_relevant_consequent(consequent),
                    }
                )

    result = pd.DataFrame(rows)
    if result.empty:
        return result
    return result.sort_values(
        ["consecuente_relevante", "lift", "confianza", "soporte"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)


def _report_rules_table(rules: pd.DataFrame) -> pd.DataFrame:
    columns = ["antecedente", "consecuente", "soporte", "confianza", "lift", "leverage"]
    table = rules.head(REPORT_RULE_LIMIT).loc[:, columns].copy()
    for column in ["soporte", "confianza", "lift", "leverage"]:
        table[column] = table[column].map(_format_metric)
    return table


def _report_itemsets_table(itemsets: pd.DataFrame) -> pd.DataFrame:
    columns = ["itemset", "tamano_itemset", "soporte", "conteo"]
    table = itemsets.head(REPORT_RULE_LIMIT).loc[:, columns].copy()
    table["soporte"] = table["soporte"].map(_format_metric)
    return table


def write_report(itemsets: pd.DataFrame, rules: pd.DataFrame, transaction_count: int) -> None:
    generated_tables = pd.DataFrame(
        [
            {"tabla": "08_itemsets_frecuentes", "ruta": _relative_path(ITEMSETS_PATH)},
            {"tabla": "08_reglas_asociacion", "ruta": _relative_path(RULES_PATH)},
        ]
    )
    top_rule = rules.iloc[0] if not rules.empty else None
    top_rule_text = (
        f"`{top_rule['antecedente']}` -> `{top_rule['consecuente']}` con lift {_format_metric(top_rule['lift'])}"
        if top_rule is not None
        else "no se generaron reglas con los umbrales definidos"
    )

    content = f"""# Reglas de asociacion academicas

## Objetivo

Identificar coocurrencias frecuentes entre caracteristicas academicas
agregadas, resultados observados, recuperacion, continuidad y riesgo de retraso
academico potencial.

Las reglas de asociacion no demuestran causalidad. Una regla indica que un
conjunto de items aparece junto con otro con cierta frecuencia dentro de las
transacciones observadas.

## Parametros

- Transacciones analizadas: {transaction_count}
- Soporte minimo: {_format_metric(MIN_SUPPORT)}
- Confianza minima: {_format_metric(MIN_CONFIDENCE)}
- Lift minimo: {_format_metric(MIN_LIFT)}
- Tamano maximo de itemset: {MAX_ITEMSET_SIZE}

## Tablas generadas

{_markdown_table(generated_tables)}

## Itemsets frecuentes principales

{_markdown_table(_report_itemsets_table(itemsets))}

## Reglas principales

{_markdown_table(_report_rules_table(rules))}

La regla con mayor prioridad segun lift, confianza y soporte es {top_rule_text}.
Esta lectura debe usarse como patron de coocurrencia, no como explicacion causal.

## Limitaciones

- Las reglas dependen de la codificacion booleana del dataset derivado.
- Los items frecuentes pueden reflejar volumen de area, periodo o semestre, por
  lo que deben leerse junto con los indicadores de Fase 5.
- Un lift alto en una regla poco frecuente requiere cautela aunque cumpla el
  soporte minimo.
- No se exponen identificadores individuales ni se utiliza informacion docente.

## Conclusion

Las reglas de asociacion complementan el analisis al mostrar combinaciones de
condiciones que aparecen juntas en los registros modelables de 2024. Su valor
principal es exploratorio: orientar preguntas sobre perdida, recuperacion,
oferta posterior y riesgo potencial sin afirmar causalidad.
"""
    write_text(ASSOCIATION_REPORT_PATH, content)


def main() -> None:
    ensure_project_directories()
    ASSOCIATION_TABLES_DIR.mkdir(parents=True, exist_ok=True)

    transactions = load_transactions()
    itemsets = build_frequent_itemsets(transactions)
    rules = build_rules(itemsets)

    save_itemsets = itemsets.drop(columns=["items"]) if "items" in itemsets.columns else itemsets
    save_table(save_itemsets, ITEMSETS_PATH)
    save_table(rules, RULES_PATH)
    write_report(itemsets, rules, len(transactions))

    print(f"Reglas de asociacion completadas. Reglas generadas: {len(rules)}")


if __name__ == "__main__":
    main()
