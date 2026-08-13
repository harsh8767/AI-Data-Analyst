import pandas as pd
import plotly.express as px


# ==================================================
# ALLOWED CHART TYPES
# ==================================================

ALLOWED_CHART_TYPES = {
    "bar",
    "line",
    "pie",
    "none",
}


# ==================================================
# NO CHART
# ==================================================

def no_chart():
    """
    Return None when no suitable chart can be generated.
    """

    return None


# ==================================================
# FIND NUMERIC COLUMN
# ==================================================

def find_numeric_column(df, exclude=None):
    """
    Find the first suitable numeric column.
    """

    exclude = exclude or []

    numeric_columns = list(
        df.select_dtypes(
            include="number"
        ).columns
    )

    for column in numeric_columns:

        if column not in exclude:
            return column

    return None


# ==================================================
# FIND CATEGORY COLUMN
# ==================================================

def find_category_column(df, exclude=None):
    """
    Find the first suitable categorical column.
    """

    exclude = exclude or []

    for column in df.columns:

        if column in exclude:
            continue

        if (
            pd.api.types.is_object_dtype(df[column])
            or pd.api.types.is_categorical_dtype(df[column])
            or pd.api.types.is_string_dtype(df[column])
        ):
            return column

    return None


# ==================================================
# NORMALIZE CHART PLAN
# ==================================================

def normalize_chart_plan(result, chart_plan):
    """
    Validate and repair the chart plan returned by Gemini.

    This prevents a slightly imperfect AI response from
    breaking visualization generation.
    """

    if result is None or result.empty:
        return no_chart()

    if not isinstance(chart_plan, dict):
        chart_plan = {}

    chart_type = chart_plan.get(
        "chart_type",
        "none"
    )

    if not isinstance(chart_type, str):
        chart_type = "none"

    chart_type = chart_type.strip().lower()

    # --------------------------------------------------
    # INVALID CHART TYPE
    # --------------------------------------------------

    if chart_type not in ALLOWED_CHART_TYPES:

        chart_type = "none"

    # --------------------------------------------------
    # EXPLICITLY NO CHART
    # --------------------------------------------------

    if chart_type == "none":

        return no_chart()

    x_axis = chart_plan.get(
        "x_axis"
    )

    y_axis = chart_plan.get(
        "y_axis"
    )

    title = chart_plan.get(
        "title"
    )

    # --------------------------------------------------
    # VALIDATE EXISTING COLUMNS
    # --------------------------------------------------

    if x_axis not in result.columns:

        x_axis = None

    if y_axis not in result.columns:

        y_axis = None

    # --------------------------------------------------
    # FIND MISSING AXES
    # --------------------------------------------------

    numeric_columns = list(
        result.select_dtypes(
            include="number"
        ).columns
    )

    # --------------------------------------------------
    # BAR / LINE
    # --------------------------------------------------

    if chart_type in {
        "bar",
        "line",
    }:

        # If y-axis is missing, find a numeric column.

        if y_axis is None:

            y_axis = find_numeric_column(
                result
            )

        # If x-axis is missing, prefer a non-numeric
        # category column.

        if x_axis is None:

            x_axis = find_category_column(
                result,
                exclude=[y_axis],
            )

        # If there is no category column but there
        # are multiple columns, use the first column.

        if (
            x_axis is None
            and len(result.columns) >= 2
        ):

            for column in result.columns:

                if column != y_axis:

                    x_axis = column
                    break

    # --------------------------------------------------
    # PIE
    # --------------------------------------------------

    elif chart_type == "pie":

        if x_axis is None:

            x_axis = find_category_column(
                result
            )

        if y_axis is None:

            y_axis = find_numeric_column(
                result,
                exclude=[x_axis],
            )

    # --------------------------------------------------
    # FINAL VALIDATION
    # --------------------------------------------------

    if not x_axis or not y_axis:

        return no_chart()

    if x_axis not in result.columns:

        return no_chart()

    if y_axis not in result.columns:

        return no_chart()

    # --------------------------------------------------
    # RETURN NORMALIZED PLAN
    # --------------------------------------------------

    return {
        "chart_type": chart_type,
        "x_axis": x_axis,
        "y_axis": y_axis,
        "title": title,
    }


# ==================================================
# GENERATE CHART
# ==================================================

def generate_chart(result, chart_plan):
    """
    Generate a Plotly chart safely from an AI-generated
    chart plan.

    The function never raises an exception for normal
    visualization problems. It simply returns None.
    """

    if result is None:

        return None

    if not isinstance(
        result,
        pd.DataFrame
    ):

        return None

    if result.empty:

        return None

    # --------------------------------------------------
    # NORMALIZE AI PLAN
    # --------------------------------------------------

    normalized_plan = normalize_chart_plan(
        result,
        chart_plan,
    )

    if normalized_plan is None:

        return None

    chart_type = normalized_plan[
        "chart_type"
    ]

    x_axis = normalized_plan[
        "x_axis"
    ]

    y_axis = normalized_plan[
        "y_axis"
    ]

    title = normalized_plan.get(
        "title"
    )

    # --------------------------------------------------
    # PREPARE DATA
    # --------------------------------------------------

    chart_data = result.copy()

    # Remove completely empty rows.

    chart_data = chart_data.dropna(
        how="all"
    )

    if chart_data.empty:

        return None

    # Remove rows where the required chart
    # values are missing.

    chart_data = chart_data.dropna(
        subset=[
            x_axis,
            y_axis,
        ]
    )

    if chart_data.empty:

        return None

    # --------------------------------------------------
    # MAKE SURE Y-AXIS IS NUMERIC
    # --------------------------------------------------

    if not pd.api.types.is_numeric_dtype(
        chart_data[y_axis]
    ):

        converted = pd.to_numeric(
            chart_data[y_axis],
            errors="coerce",
        )

        if converted.notna().any():

            chart_data[y_axis] = converted

        else:

            return None

    # --------------------------------------------------
    # BAR CHART
    # --------------------------------------------------

    if chart_type == "bar":

        try:

            fig = px.bar(
                chart_data,
                x=x_axis,
                y=y_axis,
                title=title,
            )

            return fig

        except Exception:

            return None

    # --------------------------------------------------
    # LINE CHART
    # --------------------------------------------------

    if chart_type == "line":

        try:

            fig = px.line(
                chart_data,
                x=x_axis,
                y=y_axis,
                title=title,
                markers=True,
            )

            return fig

        except Exception:

            return None

    # --------------------------------------------------
    # PIE CHART
    # --------------------------------------------------

    if chart_type == "pie":

        try:

            # Pie charts require positive numerical
            # values to be meaningful.

            pie_data = chart_data[
                chart_data[y_axis] >= 0
            ].copy()

            if pie_data.empty:

                return None

            fig = px.pie(
                pie_data,
                names=x_axis,
                values=y_axis,
                title=title,
            )

            return fig

        except Exception:

            return None

    return None