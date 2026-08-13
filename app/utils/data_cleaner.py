import pandas as pd


def get_column_types(df):
    numerical_columns = df.select_dtypes(
        include=["int64", "float64", "int32", "float32"]
    ).columns.tolist()

    categorical_columns = df.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    date_columns = df.select_dtypes(
        include=["datetime64[ns]", "datetime64[ns, UTC]"]
    ).columns.tolist()

    return {
        "numerical": numerical_columns,
        "categorical": categorical_columns,
        "date": date_columns,
    }


def get_missing_values(df):
    missing = df.isnull().sum()

    missing = missing[missing > 0].sort_values(ascending=False)

    return missing


def get_dataset_summary(df):
    return {
        "rows": df.shape[0],
        "columns": df.shape[1],
        "duplicates": int(df.duplicated().sum()),
        "missing_cells": int(df.isnull().sum().sum()),
    }