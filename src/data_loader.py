import pandas as pd


def load_dataset(file_path):
    """
    Load a CSV dataset.
    """
    try:
        data = pd.read_csv(file_path)

        print("Dataset loaded successfully!")
        print(f"Rows: {data.shape[0]}")
        print(f"Columns: {data.shape[1]}")

        return data

    except Exception as error:
        print(f"Error loading dataset: {error}")
        return None
