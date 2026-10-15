import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns


def generate_statistics(data):
    """Generate descriptive statistics."""

    numerical_data = data.select_dtypes(include="number")

    return numerical_data.describe()


def generate_histograms(data, output_folder="reports/figures"):
    """Generate histograms for numerical columns."""

    os.makedirs(output_folder, exist_ok=True)

    numerical_columns = data.select_dtypes(include="number").columns

    for column in numerical_columns:

        plt.figure(figsize=(8, 5))

        sns.histplot(data[column], kde=True)

        plt.title(f"Distribution of {column}")
        plt.xlabel(column)
        plt.ylabel("Frequency")

        file_path = f"{output_folder}/{column}_distribution.png"

        plt.savefig(file_path, bbox_inches="tight")
        plt.close()

        print(f"Created: {file_path}")


def generate_boxplots(data, output_folder="reports/figures"):
    """Generate box plots for numerical columns."""

    os.makedirs(output_folder, exist_ok=True)

    numerical_columns = data.select_dtypes(include="number").columns

    for column in numerical_columns:

        plt.figure(figsize=(8, 5))

        sns.boxplot(x=data[column])

        plt.title(f"Box Plot of {column}")
        plt.xlabel(column)

        file_path = f"{output_folder}/{column}_boxplot.png"

        plt.savefig(file_path, bbox_inches="tight")
        plt.close()

        print(f"Created: {file_path}")


def generate_correlation_heatmap(
    data,
    output_folder="reports/figures"
):
    """Generate correlation heatmap."""

    os.makedirs(output_folder, exist_ok=True)

    numerical_data = data.select_dtypes(include="number")

    if numerical_data.shape[1] < 2:
        print("Not enough numerical columns for correlation analysis.")
        return

    plt.figure(figsize=(8, 6))

    sns.heatmap(
        numerical_data.corr(),
        annot=True,
        cmap="coolwarm",
        fmt=".2f"
    )

    plt.title("Correlation Heatmap")

    file_path = f"{output_folder}/correlation_heatmap.png"

    plt.savefig(file_path, bbox_inches="tight")
    plt.close()

    print(f"Created: {file_path}")
