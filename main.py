from pathlib import Path

from src.data_loader import load_dataset
from src.data_profiler import profile_dataset, print_profile
from src.data_quality import run_quality_checks, print_quality_report
from src.eda import (
    generate_statistics,
    generate_histograms,
    generate_boxplots,
    generate_correlation_heatmap,
)
from src.ml_detector import detect_problem_type, suggest_target_columns
from src.model_trainer import train_regression_models


def save_summary_report(data, target_column, profile, quality_report, training_result):
    """Save a plain-text summary report for the dataset and model run."""
    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)
    report_path = output_dir / "summary_report.txt"

    rows = data.shape[0]
    columns = data.shape[1]
    numeric_columns = len(profile["numerical_columns"])
    categorical_columns = len(profile["categorical_columns"])

    model_summary = []
    for model_name, metrics in training_result["results"].items():
        model_summary.append(
            f"{model_name}: MAE={metrics['MAE']:.2f}, RMSE={metrics['RMSE']:.2f}, R2={metrics['R2']:.2f}"
        )

    content = [
        "Data Intelligence System Summary Report",
        "====================================",
        f"Rows: {rows}",
        f"Columns: {columns}",
        f"Numeric columns: {numeric_columns}",
        f"Categorical columns: {categorical_columns}",
        f"Duplicate rows: {profile['duplicate_rows']}",
        f"Missing values: {int(sum(quality_report['missing_values'].values)) if not quality_report['missing_values'].empty else 0}",
        f"Target column: {target_column}",
        "",
        "Model results:",
        *model_summary,
        "",
        f"Selected model: {training_result['selected_model']}",
        f"Selection metric: {training_result['selection_metric']}",
        f"Saved model path: {training_result['saved_model_path']}",
    ]

    report_path.write_text("\n".join(content), encoding="utf-8")
    print(f"\nSaved summary report: {report_path}")


file_path = "data/students.csv"

data = load_dataset(file_path)

if data is not None:

    # Profile the dataset
    profile = profile_dataset(data)
    print_profile(profile)

    # Check data quality
    quality_report = run_quality_checks(data)
    print_quality_report(quality_report)

    # EDA
    print("\n========== DESCRIPTIVE STATISTICS ==========")

    statistics = generate_statistics(data)

    print(statistics)

    print("\n========== GENERATING VISUALIZATIONS ==========")

    generate_histograms(data)
    generate_boxplots(data)
    generate_correlation_heatmap(data)

    print("\n========== ML ANALYSIS ==========")

    possible_targets = suggest_target_columns(data)

    print("\nPossible target columns:")

    for column in possible_targets:
        print(f"  - {column}")

    target_column = "Marks"

    problem_type = detect_problem_type(
        data,
        target_column,
    )

    print(f"\nSelected target: {target_column}")
    print(f"Detected problem type: {problem_type}")

    if problem_type == "regression":

        print("\n========== MODEL TRAINING ==========")

        training_result = train_regression_models(
            data,
            target_column,
        )

        results = training_result["results"]
        comparison = training_result["comparison"]

        print("\n========== MODEL COMPARISON ==========")
        print(f"{'Model':<22} {'RMSE':>10} {'R²':>10}")
        print("-" * 46)

        for row in comparison:
            print(f"{row['Model']:<22} {row['RMSE']:>9.2f} {row['R2']:>9.2f}")

        print("-" * 46)
        print(f"Selected model: {training_result['selected_model']}")
        print(f"Selection metric: {training_result['selection_metric']}")
        print(f"Saved model: {training_result['saved_model_path']}")

        print("\nDetailed metrics:")
        for model_name, metrics in results.items():
            print(f"\n{model_name}")
            print(f"MAE:  {metrics['MAE']:.2f}")
            print(f"RMSE: {metrics['RMSE']:.2f}")
            print(f"R²:   {metrics['R2']:.2f}")

        save_summary_report(data, target_column, profile, quality_report, training_result)
