import os

import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def prepare_data(data, target_column):
    """Prepare numerical features and target."""

    numerical_data = data.select_dtypes(include="number")

    X = numerical_data.drop(columns=[target_column])
    y = numerical_data[target_column]

    return X, y


def save_model(model, model_name, output_dir="models"):
    """Save a trained model to disk."""

    os.makedirs(output_dir, exist_ok=True)

    file_name = f"{model_name.lower().replace(' ', '_')}.joblib"
    file_path = os.path.join(output_dir, file_name)

    joblib.dump(model, file_path)

    return file_path


def train_regression_models(data, target_column):
    """Train and evaluate multiple regression models."""

    X, y = prepare_data(data, target_column)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
    )

    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(
            n_estimators=100,
            random_state=42,
        ),
    }

    results = {}
    trained_models = {}

    for name, model in models.items():

        model.fit(X_train, y_train)

        predictions = model.predict(X_test)

        mae = mean_absolute_error(y_test, predictions)
        mse = mean_squared_error(y_test, predictions)
        rmse = mse ** 0.5
        r2 = r2_score(y_test, predictions)

        results[name] = {
            "MAE": mae,
            "RMSE": rmse,
            "R2": r2,
        }

        trained_models[name] = model

    comparison_rows = [
        {
            "Model": name,
            "RMSE": metrics["RMSE"],
            "R2": metrics["R2"],
        }
        for name, metrics in results.items()
    ]

    comparison_rows.sort(key=lambda row: row["RMSE"])

    selected_model_name = comparison_rows[0]["Model"]
    selected_model = trained_models[selected_model_name]
    saved_model_path = save_model(selected_model, selected_model_name)

    return {
        "results": results,
        "comparison": comparison_rows,
        "selected_model": selected_model_name,
        "selection_metric": "RMSE",
        "saved_model_path": saved_model_path,
    }
