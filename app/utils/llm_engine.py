import json
import os

import pandas as pd
from dotenv import load_dotenv
from google import genai


# ==================================================
# ENVIRONMENT CONFIGURATION
# ==================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is not configured. "
        "Add it to your .env file."
    )


# ==================================================
# GEMINI CLIENT
# ==================================================

client = genai.Client(
    api_key=API_KEY
)

MODEL_NAME = "gemini-3.5-flash-lite"


# ==================================================
# DEFAULT CHART PLAN
# ==================================================

def no_chart_plan():
    """
    Return a safe default chart plan.
    """

    return {
        "chart_type": "none",
        "x_axis": None,
        "y_axis": None,
        "title": None,
    }


# ==================================================
# ERROR HANDLING
# ==================================================

def is_rate_limit_error(error):
    """
    Detect Gemini quota / rate-limit errors.
    """

    error_message = str(error).lower()

    return (
        "429" in error_message
        or "quota" in error_message
        or "rate limit" in error_message
        or "resource_exhausted" in error_message
    )


# ==================================================
# ANALYSIS PLAN + CHART PLAN
# ==================================================

def generate_analysis_plan(df, question):
    """
    Convert a natural-language question into:

    1. A structured analysis plan.
    2. A visualization plan.

    Both plans are generated using ONE Gemini API call.

    Gemini:
        Understands the user's question.

    Pandas:
        Executes the analysis.

    Plotly:
        Renders the visualization.
    """

    # --------------------------------------------------
    # DATASET SCHEMA
    # --------------------------------------------------

    columns = [
        {
            "name": str(column),
            "dtype": str(df[column].dtype),
        }
        for column in df.columns
    ]

    schema = json.dumps(
        columns,
        indent=2
    )

    # --------------------------------------------------
    # PROMPT
    # --------------------------------------------------

    prompt = f"""
You are an AI Data Analyst and Data Visualization Expert.

You are given a dataset schema and a user's question.

Create:

1. A structured analysis plan.
2. A visualization plan.

Both plans MUST be returned in ONE JSON response.

DATASET SCHEMA:
{schema}

USER QUESTION:
{question}


==================================================
SUPPORTED ANALYSIS OPERATIONS
==================================================

1. aggregate

Use aggregate for numerical calculations.

Examples:

- total sales
- average salary
- average salary by department
- total sales by region
- maximum profit by region
- minimum salary
- top products by sales
- bottom products by sales


2. count

Use count for:

- how many rows
- number of customers
- count of records
- how many employees
- frequency of categories
- different / unique / distinct categories

Examples:

- how many rows are there
- how many employees are in the dataset
- what are the different education fields
- what are the unique departments
- list the different regions
- show unique job roles

IMPORTANT:

When the user asks for different, unique, distinct,
available, or a list of categories, use:

operation = "count"

group_by = ["category_column"]

metric = null

aggregation = null

For example:

User:
"What are the different education fields?"

If the dataset contains "EducationField", generate:

operation = "count"
group_by = ["EducationField"]
metric = null
aggregation = null

This produces one row for each distinct EducationField
and a Count column showing how many records belong
to each category.


3. filter

Examples:

- show employees from HR
- show products with sales greater than 1000
- show customers from California


4. describe

Examples:

- summary statistics
- statistical overview
- describe the dataset


==================================================
ANALYSIS PLAN
==================================================

Use exactly:

{{
    "analysis_plan": {{
        "operation": "aggregate",
        "group_by": [],
        "metric": null,
        "aggregation": null,
        "filters": [],
        "sort_by": null,
        "sort_order": "descending",
        "limit": null
    }}
}}

For filters use:

{{
    "column": "column_name",
    "operator": "==",
    "value": "value"
}}

Allowed filter operators:

==
!=
>
>=
<
<=
contains


==================================================
ANALYSIS RULES
==================================================

- Use ONLY columns that exist in the dataset.
- Never invent column names.
- Do not generate Python code.
- Do not generate SQL.

For totals:
    aggregation = "sum"

For averages:
    aggregation = "mean"

For highest numerical values:
    aggregation = "max"

For lowest numerical values:
    aggregation = "min"

For top records:
    sort_order = "descending"

For bottom records:
    sort_order = "ascending"

For "top 5":
    limit = 5

For "top 10":
    limit = 10

For "bottom 5":
    limit = 5

For "bottom 10":
    limit = 10

If the user asks for a total without grouping:

    group_by = []

If the user asks for a numerical value by category:

    group_by = ["category_column"]

If the user asks for different, unique, distinct,
or available categories:

    operation = "count"

    group_by = ["category_column"]

    metric = null

    aggregation = null

The metric must be a numerical column when
using aggregate operations.

IMPORTANT:

Do NOT use aggregate for a question that only asks
for different, unique, distinct, or available
categories.

For example:

User:
"What are the different education fields?"

Correct:

operation = "count"
group_by = ["EducationField"]
metric = null
aggregation = null

Incorrect:

operation = "aggregate"
group_by = ["EducationField"]
metric = null


==================================================
VISUALIZATION PLAN
==================================================

Use exactly:

{{
    "chart_plan": {{
        "chart_type": "none",
        "x_axis": null,
        "y_axis": null,
        "title": null
    }}
}}

Allowed chart types:

- bar
- line
- pie
- none


==================================================
VISUALIZATION RULES
==================================================

Use "bar" for:

- category comparisons
- top/bottom rankings
- grouped numerical comparisons
- category frequency/count comparisons

Use "line" for:

- time trends
- chronological data

Use "pie" only for:

- parts of a whole
- category contribution to a total

Use "none" when:

- the result is a single value
- visualization does not add value
- a chart would be misleading

IMPORTANT:

- x_axis MUST be an existing dataset column.
- y_axis MUST be an existing dataset column OR "Count"
  for category frequency results.
- Never invent dataset column names.
- For pie charts, x_axis is the category.
- For pie charts, y_axis is the numerical value.
- For single-value questions, chart_type MUST be "none".
- For category frequency/count results, use a bar chart.
- For category frequency/count results, x_axis should be
  the grouped category column and y_axis should be "Count".


==================================================
IMPORTANT CHART RULE
==================================================

The chart plan should match the expected output
of the analysis plan.

Example 1:

User:
"What are the top 5 products by sales?"

Analysis:

group_by = ["Product"]
metric = "Sales"
aggregation = "sum"
sort_by = "Sales"
sort_order = "descending"
limit = 5

Chart:

chart_type = "bar"
x_axis = "Product"
y_axis = "Sales"


Example 2:

User:
"What are the different education fields?"

Analysis:

operation = "count"
group_by = ["EducationField"]
metric = null
aggregation = null

Chart:

chart_type = "bar"
x_axis = "EducationField"
y_axis = "Count"


Example 3:

User:
"What are the different departments?"

Analysis:

operation = "count"
group_by = ["Department"]
metric = null
aggregation = null

Chart:

chart_type = "bar"
x_axis = "Department"
y_axis = "Count"


==================================================
RETURN FORMAT
==================================================

Return ONLY valid JSON.

Do not include markdown.

Do not include explanations.

Return exactly:

{{
    "analysis_plan": {{
        "operation": "aggregate",
        "group_by": [],
        "metric": null,
        "aggregation": null,
        "filters": [],
        "sort_by": null,
        "sort_order": "descending",
        "limit": null
    }},
    "chart_plan": {{
        "chart_type": "none",
        "x_axis": null,
        "y_axis": null,
        "title": null
    }}
}}
"""

    # --------------------------------------------------
    # GEMINI REQUEST
    # --------------------------------------------------

    try:

        interaction = client.interactions.create(
            model=MODEL_NAME,
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": {
                    "type": "object",
                    "properties": {

                        # ==================================
                        # ANALYSIS PLAN
                        # ==================================

                        "analysis_plan": {
                            "type": "object",
                            "properties": {

                                "operation": {
                                    "type": "string"
                                },

                                "group_by": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                },

                                "metric": {
                                    "type": [
                                        "string",
                                        "null"
                                    ]
                                },

                                "aggregation": {
                                    "type": [
                                        "string",
                                        "null"
                                    ]
                                },

                                "filters": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {

                                            "column": {
                                                "type": "string"
                                            },

                                            "operator": {
                                                "type": "string"
                                            },

                                            "value": {
                                                "type": "string"
                                            }
                                        },
                                        "required": [
                                            "column",
                                            "operator",
                                            "value"
                                        ]
                                    }
                                },

                                "sort_by": {
                                    "type": [
                                        "string",
                                        "null"
                                    ]
                                },

                                "sort_order": {
                                    "type": "string"
                                },

                                "limit": {
                                    "type": [
                                        "integer",
                                        "null"
                                    ]
                                }
                            },

                            "required": [
                                "operation",
                                "group_by",
                                "metric",
                                "aggregation",
                                "filters",
                                "sort_by",
                                "sort_order",
                                "limit"
                            ]
                        },

                        # ==================================
                        # CHART PLAN
                        # ==================================

                        "chart_plan": {
                            "type": "object",
                            "properties": {

                                "chart_type": {
                                    "type": "string"
                                },

                                "x_axis": {
                                    "type": [
                                        "string",
                                        "null"
                                    ]
                                },

                                "y_axis": {
                                    "type": [
                                        "string",
                                        "null"
                                    ]
                                },

                                "title": {
                                    "type": [
                                        "string",
                                        "null"
                                    ]
                                }
                            },

                            "required": [
                                "chart_type",
                                "x_axis",
                                "y_axis",
                                "title"
                            ]
                        }
                    },

                    "required": [
                        "analysis_plan",
                        "chart_plan"
                    ]
                }
            }
        )

        # --------------------------------------------------
        # PARSE RESPONSE
        # --------------------------------------------------

        response = json.loads(
            interaction.output_text
        )

        # --------------------------------------------------
        # SAFETY CHECK
        # --------------------------------------------------

        if "analysis_plan" not in response:

            raise ValueError(
                "AI response does not contain "
                "an analysis plan."
            )

        if "chart_plan" not in response:

            response["chart_plan"] = (
                no_chart_plan()
            )

        return response

    except Exception as error:

        if is_rate_limit_error(error):

            raise RuntimeError(
                "The AI service rate limit has been reached. "
                "Your dataset analysis requires Gemini to "
                "understand the question. Please wait until "
                "the quota resets and try again."
            )

        raise RuntimeError(
            "Unable to generate the analysis plan."
        )


# ==================================================
# LOCAL INSIGHT ENGINE
# ==================================================

def generate_local_insight(question, result):
    """
    Generate an AI-style insight locally using Pandas.

    IMPORTANT:

    This function makes ZERO Gemini API calls.

    It handles:

    - single values
    - totals
    - averages
    - counts
    - grouped results
    - rankings
    - highest values
    - lowest values
    """

    if result.empty:

        return (
            "No results were found for this analysis."
        )

    result = result.copy()

    # ==================================================
    # SINGLE VALUE
    # ==================================================

    if (
        len(result) == 1
        and len(result.columns) == 1
    ):

        column = result.columns[0]
        value = result.iloc[0, 0]

        if pd.isna(value):

            return (
                f"No value was available for {column}."
            )

        if isinstance(
            value,
            (int, float)
        ):

            if float(value).is_integer():

                formatted = (
                    f"{int(value):,}"
                )

            else:

                formatted = (
                    f"{value:,.2f}"
                )

            return (
                f"The {column} is {formatted}."
            )

        return (
            f"The {column} is {value}."
        )

    # ==================================================
    # ONE ROW / MULTIPLE COLUMNS
    # ==================================================

    if len(result) == 1:

        row = result.iloc[0]

        parts = []

        for column in result.columns:

            value = row[column]

            if pd.isna(value):
                continue

            if isinstance(
                value,
                (int, float)
            ):

                if float(value).is_integer():

                    value = (
                        f"{int(value):,}"
                    )

                else:

                    value = (
                        f"{value:,.2f}"
                    )

            parts.append(
                f"{column} is {value}"
            )

        if parts:

            return (
                "The result shows that "
                + ", ".join(parts)
                + "."
            )

    # ==================================================
    # GROUPED RESULT
    # ==================================================

    if len(result.columns) >= 2:

        numeric_columns = list(
            result.select_dtypes(
                include="number"
            ).columns
        )

        if numeric_columns:

            value_column = (
                numeric_columns[-1]
            )

            category_columns = [
                column
                for column in result.columns
                if column != value_column
            ]

            category_column = (
                category_columns[0]
                if category_columns
                else None
            )

            if category_column:

                working = result.dropna(
                    subset=[
                        category_column,
                        value_column,
                    ]
                )

                if not working.empty:

                    highest = working.loc[
                        working[value_column].idxmax()
                    ]

                    lowest = working.loc[
                        working[value_column].idxmin()
                    ]

                    high_value = (
                        highest[value_column]
                    )

                    low_value = (
                        lowest[value_column]
                    )

                    if isinstance(
                        high_value,
                        (int, float)
                    ):

                        if float(high_value).is_integer():

                            high_value = (
                                f"{int(high_value):,}"
                            )

                        else:

                            high_value = (
                                f"{high_value:,.2f}"
                            )

                    if isinstance(
                        low_value,
                        (int, float)
                    ):

                        if float(low_value).is_integer():

                            low_value = (
                                f"{int(low_value):,}"
                            )

                        else:

                            low_value = (
                                f"{low_value:,.2f}"
                            )

                    return (
                        f"{highest[category_column]} "
                        f"has the highest "
                        f"{value_column} at "
                        f"{high_value}. "
                        f"{lowest[category_column]} "
                        f"has the lowest "
                        f"value at {low_value}."
                    )

    # ==================================================
    # GENERIC FALLBACK
    # ==================================================

    return (
        f"The analysis returned "
        f"{len(result):,} result(s)."
    )


# ==================================================
# AI INSIGHT
# ==================================================

def generate_ai_insight(question, result):
    """
    Generate an insight without consuming Gemini
    API quota.

    The current free-tier optimized architecture
    intentionally uses the local insight engine.

    This means:

        1 user question
        =
        1 Gemini API request

    The insight itself requires ZERO additional
    Gemini requests.
    """

    return generate_local_insight(
        question,
        result,
    )


# ==================================================
# BACKWARD COMPATIBILITY
# ==================================================

def generate_chart_plan(question, result):
    """
    Backward-compatible function.

    The application should use the chart_plan returned
    by generate_analysis_plan().

    This function performs ZERO Gemini API calls.
    """

    return no_chart_plan()
