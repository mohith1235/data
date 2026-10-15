import pandas as pd


def detect_problem_type(data, target_column):
    """
    Detect whether the target is suitable for
    classification or regression.
    """

    if target_column not in data.columns:
        return "Target column not found"

    target = data[target_column]

    if pd.api.types.is_numeric_dtype(target):
        unique_values = target.nunique()
        total_rows = len(target)

        # Treat as classification only if the numeric target is truly low-cardinality
        # and not just a continuous score/measurement with many unique values.
        if unique_values <= 10 and (unique_values / total_rows) < 0.5:
            return "classification"

        return "regression"

    return "classification"


def suggest_target_columns(data):
    """
    Suggest possible target columns based on dataset structure.
    """

    suggestions = []

    for column in data.columns:
        column_name = str(column).lower()

        if column_name.endswith("_id") or column_name in {"id", "index"}:
            continue

        unique_values = data[column].nunique()

        if unique_values <= 1:
            continue

        suggestions.append(column)

    return suggestions
