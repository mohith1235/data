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

from streamlit.errors import StreamlitSecretNotFoundError

from src.auth import (
    SupabaseAuthError,
    SupabaseConfigurationError,
    normalize_username,
    sign_in,
    sign_out,
    sign_up,
    validate_supabase_config,
)
from src.data_loader import load_dataset
from src.data_profiler import profile_dataset
from src.data_quality import run_quality_checks
from src.ml_detector import detect_problem_type, suggest_target_columns


st.set_page_config(
    page_title="Data Intelligence",
    page_icon=":material/insights:",
    layout="wide",
    initial_sidebar_state="expanded",
)

ACCENT = "#48D7B0"
CHART_BACKGROUND = "#101D2D"
CHART_TEXT = "#C7D4E0"
CHART_GRID = "#29394D"

AUTH_TOKEN_KEY = "supabase_access_token"
AUTH_ID_KEY = "supabase_user_id"


def get_supabase_config():
    try:
        secret = st.secrets.get("supabase")
    except StreamlitSecretNotFoundError:
        return None
    return validate_supabase_config(secret)


def show_auth_notice():
    notice = st.session_state.pop("auth_notice", None)
    if notice:
        level, message = notice
        if level == "success":
            st.success(message)
        else:
            st.warning(message)


def render_auth_setup():
    st.caption("DATA INTELLIGENCE WORKSPACE")
    st.title("Secure your workspace", icon=":material/lock:")
    st.write(
        "Sign-in is not configured yet. Add your Supabase project credentials "
        "to Streamlit secrets to enable ID and password accounts."
    )
    st.caption(
        "Supabase uses a private, non-deliverable internal identity behind each "
        "user ID. No email address is collected."
    )
    st.code(
        '[supabase]\n'
        'url = "https://YOUR_PROJECT.supabase.co"\n'
        'anon_key = "YOUR_SUPABASE_PUBLISHABLE_OR_ANON_KEY"',
        language="toml",
    )
    st.caption(
        "Add these values in Streamlit Community Cloud → App settings → Secrets. "
        "Disable Confirm Email in Supabase Auth settings. Never commit credentials "
        "or share them in chat."
    )


def _store_auth_session(response, username):
    access_token = response.get("access_token")
    if not access_token:
        return False
    st.session_state[AUTH_TOKEN_KEY] = access_token
    st.session_state[AUTH_ID_KEY] = username
    return True


def render_auth_screen(config):
    show_auth_notice()
    st.caption("DATA INTELLIGENCE WORKSPACE")
    st.title("Welcome to Datalens", icon=":material/insights:")
    st.write("Sign in with your ID and password to open your analysis workspace.")

    _, center, _ = st.columns([1, 1.35, 1])
    with center:
        with st.container(border=True):
            sign_in_tab, sign_up_tab = st.tabs(
                ["Sign in", "Create account"]
            )

            with sign_in_tab:
                with st.form("supabase_sign_in"):
                    username = st.text_input(
                        "User ID",
                        autocomplete="username",
                    )
                    password = st.text_input(
                        "Password",
                        type="password",
                        autocomplete="current-password",
                    )
                    submitted = st.form_submit_button(
                        "Sign in",
                        type="primary",
                        width="stretch",
                    )
                if submitted:
                    try:
                        username = normalize_username(username)
                    except SupabaseAuthError as exc:
                        st.error(str(exc))
                    else:
                        if not password:
                            st.error("Enter your password.")
                        else:
                            try:
                                response = sign_in(config, username, password)
                            except SupabaseAuthError as exc:
                                st.error(f"Could not sign in: {exc}")
                            else:
                                if _store_auth_session(response, username):
                                    st.rerun()
                                st.error(
                                    "Sign-in did not return an active session."
                                )

            with sign_up_tab:
                with st.form("supabase_sign_up"):
                    username = st.text_input(
                        "Choose a user ID",
                        key="sign_up_username",
                        autocomplete="username",
                        help=(
                            "3 to 32 characters: letters, numbers, underscores, "
                            "or hyphens. User IDs are case-insensitive."
                        ),
                    )
                    password = st.text_input(
                        "Create a password",
                        key="sign_up_password",
                        type="password",
                        autocomplete="new-password",
                    )
                    confirm_password = st.text_input(
                        "Confirm password",
                        type="password",
                        autocomplete="new-password",
                    )
                    submitted = st.form_submit_button(
                        "Create account",
                        type="primary",
                        width="stretch",
                    )
                if submitted:
                    try:
                        username = normalize_username(username)
                    except SupabaseAuthError as exc:
                        st.error(str(exc))
                    else:
                        if len(password) < 8:
                            st.error("Choose a password with at least 8 characters.")
                        elif password != confirm_password:
                            st.error("The passwords do not match.")
                        else:
                            try:
                                response = sign_up(config, username, password)
                            except SupabaseAuthError as exc:
                                st.error(f"Could not create your account: {exc}")
                            else:
                                if _store_auth_session(response, username):
                                    st.rerun()
                                st.error(
                                    "Account created, but Supabase did not return "
                                    "a session. Disable Confirm Email in Supabase "
                                    "Auth settings for ID-only accounts."
                                )
        st.caption(
            "Forgot your password? Contact the app administrator to reset "
            "your account. No email is collected for recovery."
        )


def render_account_controls(config):
    username = st.session_state.get(AUTH_ID_KEY, "")
    with st.sidebar:
        st.caption("SIGNED IN")
        st.text(username)
        if st.button("Sign out", icon=":material/logout:", width="stretch"):
            try:
                sign_out(config, st.session_state.get(AUTH_TOKEN_KEY, ""))
            except SupabaseAuthError as exc:
                st.session_state["auth_notice"] = (
                    "warning",
                    f"Your local session ended, but Supabase sign-out failed: {exc}",
                )
            else:
                st.session_state["auth_notice"] = (
                    "success",
                    "You have been signed out.",
                )
            st.session_state.pop(AUTH_TOKEN_KEY, None)
            st.session_state.pop(AUTH_ID_KEY, None)
            st.rerun()


def load_data_from_source(uploaded_file):
    if uploaded_file is not None:
        return pd.read_csv(uploaded_file)

    default_path = os.path.join("data", "students.csv")
    if os.path.exists(default_path):
        return load_dataset(default_path)

    return None


def render_brand_sidebar():
    with st.sidebar:
        st.markdown("### :material/insights: **DATALENS**")
        st.caption("DATA INTELLIGENCE WORKSPACE")
        st.markdown("#### Your dataset")
        return st.file_uploader(
            "Import a CSV file",
            type=["csv"],
            help="Your file is analyzed in this session.",
        )


def render_sidebar_status(data, uploaded_file):
    with st.sidebar:
        if data is not None:
            source_name = (
                uploaded_file.name if uploaded_file is not None else "Local dataset"
            )
            with st.container(border=True):
                st.badge(
                    "Dataset ready",
                    icon=":material/check_circle:",
                    color="green",
                )
                st.text(source_name)
                st.caption(
                    f"{len(data):,} rows · {len(data.columns):,} columns"
                )
        else:
            st.caption(
                "Upload a CSV to unlock your overview, data quality checks, "
                "exploration, and modeling workspace."
            )


def render_welcome():
    st.caption("DATA INTELLIGENCE WORKSPACE")
    st.title("Make better decisions with your data.", icon=":material/insights:")
    st.write(
        "A calm, clear workspace to understand your data, surface quality issues, "
        "and discover what matters."
    )

    with st.container(border=True):
        st.subheader("Start with a dataset", icon=":material/upload_file:")
        st.write(
            "Choose a CSV in the sidebar. Your analysis will be ready as soon as "
            "the file is loaded."
        )

    with st.container(horizontal=True):
        with st.container(border=True):
            st.markdown("**:material/space_dashboard: Understand**")
            st.caption("See the shape and key statistics of your dataset.")
        with st.container(border=True):
            st.markdown("**:material/verified: Validate**")
            st.caption("Check missing values, duplicates, and unusual columns.")
        with st.container(border=True):
            st.markdown("**:material/query_stats: Explore**")
            st.caption("Visualize distributions and compare relationships.")


def render_summary_cards(data):
    profile = profile_dataset(data)
    quality = run_quality_checks(data)
    missing_total = int(quality["missing_values"].sum())

    with st.container(horizontal=True):
        st.metric("Records", f"{profile['rows']:,}", border=True)
        st.metric("Features", profile["columns"], border=True)
        st.metric("Missing values", missing_total, border=True)
        st.metric(
            "Numeric features",
            len(profile["numerical_columns"]),
            border=True,
        )


def render_overview(data):
    st.header("At a glance", icon=":material/space_dashboard:")
    st.caption("A high-level summary of the data you’re working with.")
    render_summary_cards(data)

    preview_col, summary_col = st.columns([1.2, 1])
    with preview_col:
        with st.container(border=True):
            st.subheader("Data preview")
            st.dataframe(data.head(10), width="stretch", hide_index=True)
    with summary_col:
        with st.container(border=True):
            st.subheader("Summary statistics")
            numeric_summary = data.describe(include="number").T
            if numeric_summary.empty:
                st.caption("No numeric features are available for summary.")
            else:
                st.dataframe(numeric_summary, width="stretch")


def render_profile(data):
    profile = profile_dataset(data)
    st.header("Dataset profile", icon=":material/table_chart:")
    st.caption("Inspect column types, completeness, and dataset shape.")

    with st.container(horizontal=True):
        st.metric("Rows", f"{profile['rows']:,}", border=True)
        st.metric("Columns", profile["columns"], border=True)
        st.metric("Duplicate rows", profile["duplicate_rows"], border=True)

    with st.container(border=True):
        st.subheader("Column details")
        st.dataframe(
            pd.DataFrame(profile["columns_info"]),
            width="stretch",
            hide_index=True,
        )


def render_quality(data):
    report = run_quality_checks(data)
    missing_values = report["missing_values"]
    missing_df = pd.DataFrame(
        {
            "Column": list(missing_values.keys()),
            "Missing values": list(missing_values.values),
        }
    )
    missing_df = missing_df[missing_df["Missing values"] > 0]

    st.header("Data quality", icon=":material/verified:")
    st.caption("Quick checks to help you trust what goes into your analysis.")

    if missing_df.empty:
        st.success("No missing values detected.", icon=":material/check_circle:")
    else:
        with st.container(border=True):
            st.subheader("Missing values")
            st.dataframe(missing_df, width="stretch", hide_index=True)

    with st.container(horizontal=True):
        st.metric("Duplicate rows", report["duplicates"], border=True)
        st.metric(
            "Constant columns",
            len(report["constant_columns"]),
            border=True,
        )
        st.metric(
            "High-cardinality columns",
            len(report["high_cardinality_columns"]),
            border=True,
        )

    if report["constant_columns"]:
        st.warning(f"Constant columns: {report['constant_columns']}")
    if report["high_cardinality_columns"]:
        st.warning(f"High-cardinality columns: {report['high_cardinality_columns']}")
    if report["numeric_outliers"]:
        st.warning(f"Potential numerical outliers: {report['numeric_outliers']}")
    else:
        st.success("No potential numerical outliers detected.")


def style_chart_axes(axes):
    for axis in axes:
        axis.set_facecolor(CHART_BACKGROUND)
        axis.tick_params(colors=CHART_TEXT)
        axis.xaxis.label.set_color(CHART_TEXT)
        axis.yaxis.label.set_color(CHART_TEXT)
        axis.title.set_color("#F3F7FA")
        axis.grid(color=CHART_GRID, linewidth=0.7, alpha=0.75)
        axis.set_axisbelow(True)
        for spine in axis.spines.values():
            spine.set_color(CHART_GRID)


def render_eda(data):
    numeric_cols = data.select_dtypes(include="number").columns.tolist()

    st.header("Explore the data", icon=":material/query_stats:")
    st.caption("Review feature distributions and relationships at a glance.")

    if not numeric_cols:
        st.warning("No numeric columns are available to visualize.")
        return

    chart_columns = st.columns(2)
    for index, column in enumerate(numeric_cols):
        chart_column = chart_columns[index % 2]
        with chart_column:
            with st.container(border=True):
                fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
                fig.patch.set_facecolor(CHART_BACKGROUND)

                sns.histplot(
                    data[column],
                    kde=True,
                    color=ACCENT,
                    ax=axes[0],
                )
                axes[0].set_title(f"{column} distribution")
                axes[0].set_xlabel(column)

                sns.boxplot(
                    x=data[column],
                    color="#8B9DFF",
                    ax=axes[1],
                )
                axes[1].set_title(f"{column} range")
                axes[1].set_xlabel(column)

                style_chart_axes(axes)
                st.pyplot(fig)
                plt.close(fig)

    with st.container(border=True):
        st.subheader("Feature correlation")
        fig, axis = plt.subplots(figsize=(8, 5))
        fig.patch.set_facecolor(CHART_BACKGROUND)
        heatmap = sns.heatmap(
            data[numeric_cols].corr(),
            annot=True,
            cmap=sns.color_palette(
                ["#172538", "#286F70", ACCENT],
                as_cmap=True,
            ),
            fmt=".2f",
            linewidths=0.5,
            linecolor=CHART_GRID,
            ax=axis,
        )
        colorbar = heatmap.collections[0].colorbar
        colorbar.ax.tick_params(colors=CHART_TEXT)
        colorbar.outline.set_edgecolor(CHART_GRID)
        style_chart_axes([axis])
        st.pyplot(fig)
        plt.close(fig)


def render_modeling(data):
    st.header("Predictive modeling", icon=":material/online_prediction:")
    st.caption("Compare regression models and select the best-performing fit.")
    candidate_targets = suggest_target_columns(data)

    if not candidate_targets:
        st.warning("No suitable target column was found for modeling.")
        return

    with st.container(border=True):
        target = st.selectbox("Choose a target column", candidate_targets)
        problem_type = detect_problem_type(data, target)
        st.caption(f"Detected problem type: **{problem_type}**")

        if problem_type != "regression":
            st.warning("Classification modeling is not available yet.")
            return

        train_clicked = st.button(
            "Train regression models",
            type="primary",
            icon=":material/play_arrow:",
        )

    if not train_clicked:
        return

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
    st.subheader("Model comparison")
    with st.container(border=True):
        st.dataframe(
            pd.DataFrame(result["comparison"]),
            width="stretch",
            hide_index=True,
        )

    st.subheader(f"Selected model · {result['selected_model']}")
    st.caption(
        f"Selected using {result['selection_metric']}. "
        f"Saved to `{result['saved_model_path']}`."
    )
    with st.container(horizontal=True):
        for name, metrics in result["results"].items():
            with st.container(border=True):
                st.markdown(f"**{name}**")
                st.metric("RMSE", f"{metrics['RMSE']:.2f}")
                st.caption(
                    f"MAE {metrics['MAE']:.2f} · R² {metrics['R2']:.2f}"
                )


def main():
    try:
        config = get_supabase_config()
    except SupabaseConfigurationError as exc:
        st.error(f"Supabase authentication is misconfigured: {exc}")
        return

    if config is None:
        render_auth_setup()
        return

    if (
        st.session_state.get(AUTH_TOKEN_KEY)
        and not st.session_state.get(AUTH_ID_KEY)
    ):
        st.session_state.pop(AUTH_TOKEN_KEY, None)

    if not st.session_state.get(AUTH_TOKEN_KEY):
        render_auth_screen(config)
        return

    render_account_controls(config)
    uploaded_file = render_brand_sidebar()
    data = load_data_from_source(uploaded_file)
    render_sidebar_status(data, uploaded_file)

    if data is None:
        render_welcome()
        return

    st.caption("DATA INTELLIGENCE WORKSPACE")
    st.title("Dataset intelligence", icon=":material/insights:")
    st.caption(
        "A clear view of your data’s structure, quality, patterns, and potential."
    )

    overview_tab, profile_tab, quality_tab, eda_tab, model_tab = st.tabs(
        [
            ":material/space_dashboard: Overview",
            ":material/table_chart: Profile",
            ":material/verified: Quality",
            ":material/query_stats: Explore",
            ":material/online_prediction: Model",
        ]
    )

    with overview_tab:
        render_overview(data)

    with profile_tab:
        render_profile(data)

    with quality_tab:
        render_quality(data)

    with eda_tab:
        render_eda(data)

    with model_tab:
        render_modeling(data)


if __name__ == "__main__":
    main()
