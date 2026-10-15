import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
try:
    import streamlit as st
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "Streamlit is required to run this app. Install it with: pip install streamlit"
    ) from exc

from src.data_loader import load_dataset
from src.data_profiler import profile_dataset
from src.data_quality import run_quality_checks
from src.ml_detector import detect_problem_type, suggest_target_columns


st.set_page_config(page_title="Data Intelligence System", layout="wide")

st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background: #000000;
        color: #f5f5f5;
    }
    .stApp {
        background: #000000;
        color: #f5f5f5;
    }
    div[data-testid="stTabs"] button {
        font-weight: 600;
        background: #111111;
        color: #f5f5f5;
        border: 1px solid #333333;
        border-radius: 8px 8px 0 0;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    div[data-testid="stDataFrame"] {
        background: #111111;
    }
    .stMetric {
        background: #111111;
        border: 1px solid #2d2d2d;
        border-radius: 8px;
        padding: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_data_from_source(uploaded_file):
    if uploaded_file is not None:
        return pd.read_csv(uploaded_file)

    default_path = os.path.join("data", "students.csv")
    if os.path.exists(default_path):
        loaded = load_dataset(default_path)
        return loaded

    st.error("No dataset found. Please upload a CSV file.")
    return None


def render_summary_cards(data):
    profile = profile_dataset(data)
    quality = run_quality_checks(data)

    missing_total = int(sum(quality["missing_values"].values)) if not quality["missing_values"].empty else 0

    metric_cols = st.columns(4)
    metric_cols[0].metric("Rows", f"{profile['rows']:,}")
    metric_cols[1].metric("Columns", profile["columns"])
    metric_cols[2].metric("Missing values", missing_total)
    metric_cols[3].metric("Numeric columns", len(profile["numerical_columns"]))


def render_overview(data):
    st.subheader("Dataset overview")
    render_summary_cards(data)
    st.dataframe(data.head(10), width="stretch")

    numeric_summary = data.describe(include="number").T
    st.subheader("Summary statistics")
    st.dataframe(numeric_summary, width="stretch")


def render_profile(data):
    profile = profile_dataset(data)

    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", profile["rows"])
    c2.metric("Columns", profile["columns"])
    c3.metric("Duplicate rows", profile["duplicate_rows"])

    profile_df = pd.DataFrame(profile["columns_info"])
    st.dataframe(profile_df, width="stretch")


def render_quality(data):
    report = run_quality_checks(data)

    missing_series = report["missing_values"]
    missing_df = pd.DataFrame({
        "Column": list(missing_series.keys()),
        "Missing values": list(missing_series.values),
    })

    st.subheader("Missing values")
    if missing_df.empty:
        st.success("No missing values detected")
    else:
        st.dataframe(missing_df, width="stretch")

    st.subheader("Duplicates and constants")
    col1, col2, col3 = st.columns(3)
    col1.metric("Duplicate rows", report["duplicates"])
    col2.metric("Constant columns", len(report["constant_columns"]))
    col3.metric("High-cardinality columns", len(report["high_cardinality_columns"]))

    if report["constant_columns"]:
        st.warning(f"Constant columns: {report['constant_columns']}")
    if report["high_cardinality_columns"]:
        st.warning(f"High-cardinality columns: {report['high_cardinality_columns']}")

    if report["numeric_outliers"]:
        st.warning(f"Potential outliers: {report['numeric_outliers']}")
    else:
        st.success("No potential numerical outliers detected")


def render_eda(data):
    numeric_cols = data.select_dtypes(include="number").columns.tolist()

    if not numeric_cols:
        st.warning("No numeric columns to analyze")
        return

    for col in numeric_cols:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))

        sns.histplot(data[col], kde=True, ax=axes[0])
        axes[0].set_title(f"Distribution of {col}")
        axes[0].set_xlabel(col)

        sns.boxplot(x=data[col], ax=axes[1])
        axes[1].set_title(f"Box plot of {col}")
        axes[1].set_xlabel(col)

        st.pyplot(fig)

    corr = data[numeric_cols].corr()
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
    ax.set_title("Correlation heatmap")
    st.pyplot(fig)


def render_modeling(data):
    candidate_targets = suggest_target_columns(data)

    if not candidate_targets:
        st.warning("No suitable target column found for modeling.")
        return

    target = st.selectbox("Choose a target column", candidate_targets)
    problem_type = detect_problem_type(data, target)

    st.info(f"Detected problem type: {problem_type}")

    if problem_type != "regression":
        st.warning("Classification modeling is not implemented in this version.")
        return

    if st.button("Train regression model"):
        try:
            from src.model_trainer import train_regression_models
        except ImportError as exc:
            st.error(
                "Could not load the scikit-learn model trainer. Windows Application "
                "Control may be blocking one of its native files. Ask your system "
                "administrator to allow the installed scikit-learn package, then "
                f"restart the app. Details: {exc}"
            )
            return

        result = train_regression_models(data, target)

        comparison_df = pd.DataFrame(result["comparison"])
        st.subheader("Model comparison")
        st.dataframe(comparison_df, width="stretch")

        st.subheader("Selected model")
        st.success(f"Best model: {result['selected_model']} ({result['selection_metric']})")
        st.write(f"Saved model path: {result['saved_model_path']}")

        st.subheader("Detailed metrics")
        for name, metrics in result["results"].items():
            st.markdown(f"### {name}")
            col1, col2, col3 = st.columns(3)
            col1.metric("MAE", f"{metrics['MAE']:.2f}")
            col2.metric("RMSE", f"{metrics['RMSE']:.2f}")
            col3.metric("R²", f"{metrics['R2']:.2f}")


def main():
    st.title("Data Intelligence System")
    st.caption("Upload a CSV dataset or use the default student dataset")

    uploaded_file = st.file_uploader("Upload CSV data", type=["csv"])
    data = load_data_from_source(uploaded_file)

    if data is None:
        return

    tabs = st.tabs(["Overview", "Profile", "Quality", "EDA", "Model"])

    with tabs[0]:
        render_overview(data)

    with tabs[1]:
        render_profile(data)

    with tabs[2]:
        render_quality(data)

    with tabs[3]:
        render_eda(data)

    with tabs[4]:
        render_modeling(data)


if __name__ == "__main__":
    main()
