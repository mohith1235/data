import pandas as pd


def check_missing_values(data):
    """Check for missing values in every column."""

    missing = data.isnull().sum()

    return missing[missing > 0]


def check_duplicates(data):
    """Count duplicate rows."""

    return int(data.duplicated().sum())


def check_constant_columns(data):
    """Find columns containing only one unique value."""

    constant_columns = []

    for column in data.columns:
        if data[column].nunique() <= 1:
            constant_columns.append(column)

    return constant_columns


def check_high_cardinality(data):
    """Find columns with many unique values."""

    high_cardinality = []

    for column in data.columns:

        unique_count = data[column].nunique()

        if unique_count / len(data) > 0.8:
            high_cardinality.append(column)

    return high_cardinality


def check_numeric_outliers(data):
    """Detect potential numerical outliers using the IQR method."""

    outliers = {}

    numerical_columns = data.select_dtypes(include="number").columns

    for column in numerical_columns:

        Q1 = data[column].quantile(0.25)
        Q3 = data[column].quantile(0.75)

        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outlier_count = (
            (data[column] < lower_bound)
            | (data[column] > upper_bound)
        ).sum()

        if outlier_count > 0:
            outliers[column] = int(outlier_count)

    return outliers


def run_quality_checks(data):

    quality_report = {}

    quality_report["missing_values"] = check_missing_values(data)

    quality_report["duplicates"] = check_duplicates(data)

    quality_report["constant_columns"] = check_constant_columns(data)

    quality_report["high_cardinality_columns"] = check_high_cardinality(data)

    quality_report["numeric_outliers"] = check_numeric_outliers(data)

    return quality_report


def print_quality_report(report):

    print("\n========== DATA QUALITY REPORT ==========")

    # Missing values
    print("\nMissing values:")

    if len(report["missing_values"]) == 0:
        print("  ✓ No missing values detected")
    else:
        for column, count in report["missing_values"].items():
            print(f"  ⚠ {column}: {count}")

    # Duplicates
    print("\nDuplicate rows:")

    if report["duplicates"] == 0:
        print("  ✓ No duplicate rows detected")
    else:
        print(f"  ⚠ {report['duplicates']} duplicate rows")

    # Constant columns
    print("\nConstant columns:")

    if not report["constant_columns"]:
        print("  ✓ No constant columns detected")
    else:
        for column in report["constant_columns"]:
            print(f"  ⚠ {column}")

    # High cardinality
    print("\nHigh-cardinality columns:")

    if not report["high_cardinality_columns"]:
        print("  ✓ None detected")
    else:
        for column in report["high_cardinality_columns"]:
            print(f"  ⚠ {column}")

    # Outliers
    print("\nPotential numerical outliers:")

    if not report["numeric_outliers"]:
        print("  ✓ No potential outliers detected")
    else:
        for column, count in report["numeric_outliers"].items():
            print(f"  ⚠ {column}: {count}")
