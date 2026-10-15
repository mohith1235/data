# Data Intelligence System

A lightweight data intelligence platform for analyzing datasets, checking quality, generating EDA insights, and training a regression model automatically.

## Features

- Dataset loading from CSV files
- Basic profiling of rows, columns, and data types
- Missing-value and duplicate checks
- Constant and high-cardinality column detection
- Numeric outlier detection
- Descriptive statistics
- Histogram, box plot, and correlation visualizations
- Regression model training and comparison
- Supabase-backed user ID and password accounts
- Streamlit dashboard for interactive use

## Project structure

- `main.py` — command-line data pipeline
- `app.py` — Streamlit dashboard interface
- `src/` — data loading, profiling, quality checks, EDA, and modeling logic
- `data/` — sample dataset files
- `reports/figures/` — generated plots
- `models/` — saved trained model files

## Setup

1. Open a terminal in the project folder.
2. Create a virtual environment if needed:
   `python -m venv venv`
3. Activate it:
   - Windows PowerShell: `./venv/Scripts/Activate.ps1`
4. Install dependencies:
   `python -m pip install -r requirements.txt`

## Run the command-line version

```bash
python main.py
```

This will:
- load the dataset
- profile the data
- print a quality report
- generate charts in the `reports/figures` folder
- train regression models and save the selected model

## Run the dashboard

```bash
python -m streamlit run app.py
```

Or use the desktop launcher:

- `local_dashboard_launcher.py`
- `data-intelligence-system-launcher.bat`

## Configure public account sign-in

The dashboard uses Supabase Auth for user ID and password registration and
sign-in, without collecting email addresses. See [DEPLOY.md](DEPLOY.md) for
Supabase setup and Streamlit Cloud Secrets configuration. Password recovery
requires an administrator, and uploaded CSV files remain in the current
Streamlit session rather than being saved to user accounts.

User IDs are 3-32 characters, case-insensitive, and may contain letters,
numbers, underscores, or hyphens. Passwords must contain at least 8 characters.

## Sample dataset

The local `data/students.csv` file is not included in the GitHub repository. Upload
a CSV file through the dashboard, or place your own dataset at that path for local
use.

## Dependencies

- pandas
- numpy
- scikit-learn
- matplotlib
- seaborn
- joblib
- streamlit