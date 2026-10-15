from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_DIR / "docs" / "data_intelligence_system_report.pdf"

styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=24,
        leading=29,
        textColor=colors.HexColor("#17324D"),
        spaceAfter=8,
    )
)
styles.add(
    ParagraphStyle(
        name="Subtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=11,
        textColor=colors.HexColor("#52606D"),
        spaceAfter=22,
    )
)
styles.add(
    ParagraphStyle(
        name="Section",
        parent=styles["Heading2"],
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#17324D"),
        spaceBefore=14,
        spaceAfter=7,
    )
)
styles.add(
    ParagraphStyle(
        name="Body",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=14,
        spaceAfter=7,
    )
)
styles.add(
    ParagraphStyle(
        name="Small",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#52606D"),
    )
)
styles.add(
    ParagraphStyle(
        name="ReportCode",
        fontName="Courier",
        fontSize=7.2,
        leading=9.2,
        leftIndent=7,
        rightIndent=7,
        textColor=colors.HexColor("#1F2933"),
        backColor=colors.HexColor("#F1F5F9"),
        borderColor=colors.HexColor("#CBD5E1"),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=9,
    )
)


def paragraph(text, style="Body"):
    return Paragraph(escape(text).replace("\n", "<br/>"), styles[style])


def code(text):
    return Preformatted(text.strip("\n"), styles["ReportCode"])


def section(title):
    return Paragraph(escape(title), styles["Section"])


def footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
    canvas.line(18 * mm, 14 * mm, 192 * mm, 14 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#52606D"))
    canvas.drawString(18 * mm, 9 * mm, "Data Intelligence System")
    canvas.drawRightString(192 * mm, 9 * mm, f"Page {document.page}")
    canvas.restoreState()


def build_report():
    document = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=20 * mm,
        title="Data Intelligence System Project Report",
        author="Data Intelligence System",
    )

    story = [
        Paragraph("Data Intelligence System", styles["ReportTitle"]),
        Paragraph("Technical project report with code examples and explanations", styles["Subtitle"]),
        paragraph("Generated from the current project implementation on 24 September 2026.", "Small"),
        Spacer(1, 10),
        section("1. Executive Summary"),
        paragraph(
            "The Data Intelligence System is a Python application for loading CSV data, profiling its structure, checking data quality, generating exploratory visualizations, and training regression models. It provides two interfaces: a command-line pipeline in main.py and an interactive Streamlit dashboard in app.py."
        ),
        paragraph(
            "The sample workflow uses data/students.csv, creates visualizations under reports/figures, and saves the selected trained model under models/. The dashboard is currently available at http://localhost:8501 when Streamlit is running."
        ),
        section("2. Main Features"),
        paragraph(
            "Dataset loading: reads CSV files with Pandas and reports the row and column count.\n"
            "Dataset profiling: reports dimensions, data types, missing values, unique values, duplicates, and numerical or categorical columns.\n"
            "Quality checks: detects missing values, duplicates, constant columns, high-cardinality columns, and possible numerical outliers using the IQR method.\n"
            "Exploratory data analysis: creates descriptive statistics, histograms, box plots, and a correlation heatmap.\n"
            "Machine learning: compares Linear Regression and Random Forest Regression using MAE, RMSE, and R2.\n"
            "Interactive dashboard: exposes the analysis through Streamlit tabs for Overview, Profile, Quality, EDA, and Model."
        ),
        section("3. Project Structure"),
    ]

    structure = [
        ["Path", "Purpose"],
        ["app.py", "Streamlit dashboard interface"],
        ["main.py", "Command-line analysis and reporting pipeline"],
        ["src/data_loader.py", "CSV loading helper"],
        ["src/data_profiler.py", "Dataset structure and profile calculations"],
        ["src/data_quality.py", "Data quality checks"],
        ["src/eda.py", "Statistics and visualizations"],
        ["src/ml_detector.py", "Target suggestions and problem-type detection"],
        ["src/model_trainer.py", "Regression training, evaluation, and model saving"],
        ["data/students.csv", "Sample input dataset"],
        ["models/", "Saved Joblib models"],
        ["reports/", "Generated text reports and figures"],
    ]
    table = Table(structure, colWidths=[52 * mm, 116 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17324D")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEADING", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.extend([table, section("4. Core Code Examples")])
    story.extend(
        [
            paragraph("CSV loading is kept in a small reusable function. It returns a DataFrame when loading succeeds and None when an error occurs."),
            code('''def load_dataset(file_path):\n    try:\n        data = pd.read_csv(file_path)\n        print(f"Rows: {data.shape[0]}")\n        print(f"Columns: {data.shape[1]}")\n        return data\n    except Exception as error:\n        print(f"Error loading dataset: {error}")\n        return None'''),
            paragraph("The profiler builds a dictionary that the command-line interface and Streamlit dashboard can both consume."),
            code('''profile["rows"] = data.shape[0]\nprofile["columns"] = data.shape[1]\nprofile["duplicate_rows"] = int(data.duplicated().sum())\nprofile["numerical_columns"] = list(\n    data.select_dtypes(include="number").columns\n)'''),
            paragraph("The IQR quality rule flags values below Q1 - 1.5*IQR or above Q3 + 1.5*IQR."),
            code('''Q1 = data[column].quantile(0.25)\nQ3 = data[column].quantile(0.75)\nIQR = Q3 - Q1\nlower_bound = Q1 - 1.5 * IQR\nupper_bound = Q3 + 1.5 * IQR'''),
            paragraph("Model training splits the numerical data into training and test sets, evaluates two regressors, sorts them by RMSE, and saves the best model."),
            code('''X_train, X_test, y_train, y_test = train_test_split(\n    X, y, test_size=0.2, random_state=42\n)\n\nmodels = {\n    "Linear Regression": LinearRegression(),\n    "Random Forest": RandomForestRegressor(\n        n_estimators=100, random_state=42\n    ),\n}'''),
            paragraph("The dashboard loads either an uploaded CSV file or the default data/students.csv file, then renders each analysis area in a separate tab."),
            code('''uploaded_file = st.file_uploader("Upload CSV data", type=["csv"])\ndata = load_data_from_source(uploaded_file)\ntabs = st.tabs(["Overview", "Profile", "Quality", "EDA", "Model"])'''),
        ]
    )
    story.append(PageBreak())
    story.extend(
        [
            section("5. Execution Flow"),
            paragraph("1. The application loads the selected CSV dataset.\n2. The data is profiled and checked for common quality problems.\n3. Numerical columns are used to generate statistics and plots.\n4. Candidate target columns are suggested.\n5. If the target is suitable for regression, Linear Regression and Random Forest models are trained.\n6. Metrics are compared, the lowest-RMSE model is selected, and the model is saved with Joblib."),
            section("6. How to Run"),
            paragraph("Use the project virtual environment on Windows:"),
            code('''cd C:\\Users\\mohit\\OneDrive\\Desktop\\data-intelligence-system\n.\\venv\\Scripts\\Activate.ps1\npython -m streamlit run app.py --server.port 8501'''),
            paragraph("Then open http://localhost:8501 in a browser. The command-line pipeline can be run with:"),
            code('''python main.py'''),
            paragraph("The project also includes a desktop launcher. It starts the dashboard and manages its process lifetime, including cleanup when the launcher closes."),
            section("7. Dependencies"),
            paragraph("The project uses Pandas and NumPy for data handling, Matplotlib and Seaborn for visualization, Scikit-learn for machine learning, Joblib for model persistence, and Streamlit for the dashboard."),
            section("8. Strengths"),
            paragraph("The code is split into focused modules, so data loading, profiling, quality checks, EDA, and modeling can be reused by both interfaces. The workflow is easy to demonstrate with the included sample dataset, and the saved model and text report make results persistent."),
            section("9. Current Limitations and Recommended Improvements"),
            paragraph("Classification is detected but not implemented in the training workflow. The modeling code expects numerical features and does not yet include categorical encoding, missing-value imputation, or feature scaling. Validation currently uses one train/test split rather than cross-validation. The next improvements should be input validation, a configurable target column for the command-line pipeline, classification support, richer tests, and cross-validation for more reliable model comparison."),
            section("10. Conclusion"),
            paragraph("This project provides a complete introductory data intelligence workflow: load, understand, validate, visualize, model, and save results. Its modular structure makes it a useful foundation for adding more datasets, models, quality rules, and production-grade validation."),
        ]
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"Created: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_report()
