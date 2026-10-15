import pandas as pd


def profile_dataset(data):
    """Analyze the basic structure and quality of a dataset."""

    profile = {}

    # Basic information
    profile["rows"] = data.shape[0]
    profile["columns"] = data.shape[1]

    # Column information
    profile["columns_info"] = []

    for column in data.columns:
        column_info = {
            "name": column,
            "data_type": str(data[column].dtype),
            "missing_values": int(data[column].isnull().sum()),
            "unique_values": int(data[column].nunique()),
        }

        profile["columns_info"].append(column_info)

    # Duplicate rows
    profile["duplicate_rows"] = int(data.duplicated().sum())

    # Numerical and categorical columns
    profile["numerical_columns"] = list(
        data.select_dtypes(include="number").columns
    )

    profile["categorical_columns"] = list(
        data.select_dtypes(include="object").columns
    )

    return profile


def print_profile(profile):
    """Display the dataset profile."""

    print("\n========== DATA PROFILE ==========")

    print(f"Rows: {profile['rows']}")
    print(f"Columns: {profile['columns']}")
    print(f"Duplicate rows: {profile['duplicate_rows']}")

    print("\nNumerical columns:")
    for column in profile["numerical_columns"]:
        print(f"  - {column}")

    print("\nCategorical columns:")
    for column in profile["categorical_columns"]:
        print(f"  - {column}")

    print("\nColumn details:")

    for column in profile["columns_info"]:
        print(
            f"\n{column['name']}"
            f"\n  Type: {column['data_type']}"
            f"\n  Missing: {column['missing_values']}"
            f"\n  Unique: {column['unique_values']}"
        )
