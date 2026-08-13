import pandas as pd


def validate_result(result):
    """
    Validate and clean the result returned by the query executor.
    """

    # No result
    if result is None:
        return pd.DataFrame()

    # Result must be a DataFrame
    if not isinstance(result, pd.DataFrame):
        return pd.DataFrame()

    result = result.copy()

    # Remove completely empty rows
    result = result.dropna(
        how="all"
    )

    # Remove completely empty columns
    result = result.dropna(
        axis=1,
        how="all"
    )

    # Reset index for clean display
    result = result.reset_index(
        drop=True
    )

    return result