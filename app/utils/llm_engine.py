import json
import os
import re

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
# NORMALIZE TEXT
# ==================================================

def normalize_text(value):
    """
    Normalize text for fuzzy column matching.
    """

    if value is None:
        return ""

    value = str(value).strip().lower()

    # Remove punctuation.
    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    # Normalize whitespace.
    value = re.sub(
        r"\s+",
        " ",
        value,
    ).strip()

    return value


# ==================================================
# SINGULARIZE SIMPLE WORD
# ==================================================

def simple_singularize(value):
    """
    Handle common singular/plural column names.

    This is intentionally conservative.
    """

    value = normalize_text(value)

    if value.endswith("ies"):
        return value[:-3] + "y"

    if value.endswith("ses"):
        return value[:-2]

    if value.endswith("xes"):
        return value[:-2]

    if value.endswith("zes"):
        return value[:-2]

    if value.endswith("ches"):
        return value[:-2]

    if value.endswith("shes"):
        return value[:-2]

    if value.endswith("s") and not value.endswith("ss"):
        return value[:-1]

    return value


# ==================================================
# FIND COLUMN FROM QUESTION
# ==================================================

def find_column_from_question(df, question):
    """
    Try to identify the dataset column being requested
    from a natural-language question.

    Example:

        "What are the different departments?"

    Dataset:

        Department

    Returns:

        Department
    """

    question_normalized = normalize_text(question)

    # --------------------------------------------------
    # Exact normalized column match
    # --------------------------------------------------

    for column in df.columns:

        column_normalized = normalize_text(column)

        if column_normalized in question_normalized:
            return column

    # --------------------------------------------------
    # Singular/plural match
    # --------------------------------------------------

    question_words = set(
        question_normalized.split()
    )

    for column in df.columns:

        column_normalized = normalize_text(column)

        column_words = column_normalized.split()

        if not column_words:
            continue

        singular_column = " ".join(
            simple_singularize(word)
            for word in column_words
        )

        singular_question_words = {
            simple_singularize(word)
            for word in question_words
        }

        singular_column_words = set(
            singular_column.split()
        )

        if singular_column_words.issubset(
            singular_question_words
        ):
            return column

    # --------------------------------------------------
    # Partial word match
    # --------------------------------------------------

    for column in df.columns:

        column_normalized = normalize_text(column)

        column_words = column_normalized.split()

        for word in column_words:

            singular_word = simple_singularize(word)

            if singular_word in question_words:
                return column

    return None


# ==================================================
# DETECT DISTINCT / CATEGORY QUESTION
# ==================================================

def is_distinct_category_question(question):
    """
    Detect questions asking for different/unique/distinct
    categories rather than numerical aggregation.
    """

    normalized = normalize_text(question)

    patterns = [
        r"\bdifferent\b",
        r"\bunique\b",
        r"\bdistinct\b",
        r"\bavailable\b",
        r"\bwhat categories\b",
        r"\bwhich categories\b",
        r"\blist\b",
        r"\bshow all\b",
        r"\bwhat are the\b",
        r"\bwhat is the list\b",
    ]

    return any(
        re.search(
            pattern,
            normalized,
        )
        for pattern in patterns
    )


# ==================================================
# NORMALIZE ANALYSIS PLAN
# ==================================================

def normalize_analysis_plan(df, question, response):
    """
    Deterministically correct common AI planning mistakes.

    In particular:

        "What are the different departments?"

    must become:

        operation = "count"
        group_by = ["Department"]
        metric = None
        aggregation = None

    This protects the execution engine from Gemini
    incorrectly selecting aggregate without a metric.
    """

    if not isinstance(response, dict):
        return response

    analysis_plan = response.get(
        "analysis_plan"
    )

    if not isinstance(
        analysis_plan,
        dict
    ):
        return response

    # --------------------------------------------------
    # DISTINCT / DIFFERENT / UNIQUE QUESTIONS
    # --------------------------------------------------

    if is_distinct_category_question(question):

        detected_column = find_column_from_question(
            df,
            question,
        )

        # If Gemini already identified a valid group column,
        # prefer it.
        existing_group_by = analysis_plan.get(
            "group_by"
        )

        if (
            isinstance(existing_group_by, list)
            and existing_group_by
            and all(
                column in df.columns
                for column in existing_group_by
            )
        ):

            detected_column = existing_group_by[0]

        # --------------------------------------------------
        # If a column was identified, force COUNT.
        # --------------------------------------------------

        if detected_column:

            analysis_plan["operation"] = "count"

            analysis_plan["group_by"] = [
                detected_column
            ]

            analysis_plan["metric"] = None

            analysis_plan["aggregation"] = None

            # Distinct category questions should not
            # accidentally be sorted/limited by an invalid
            # dataset column.
            sort_by = analysis_plan.get(
                "sort_by"
            )

            if (
                sort_by
                and sort_by not in df.columns
            ):
                analysis_plan["sort_by"] = None

            # --------------------------------------------------
            # Force correct chart
            # --------------------------------------------------

            chart_plan = response.get(
                "chart_plan"
            )

            if not isinstance(
                chart_plan,
                dict
            ):
                chart_plan = no_chart_plan()

            chart_plan["chart_type"] = "bar"
            chart_plan["x_axis"] = detected_column
            chart_plan["y_axis"] = "Count"

            if not chart_plan.get("title"):
                chart_plan["title"] = (
                    f"Count by {detected_column}"
                )

            response["chart_plan"] = chart_plan

    return response


# ==================================================
# VALIDATE RESPONSE COLUMNS
# ==================================================

def validate_analysis_response(df, response):
    """
    Ensure Gemini did not invent dataset columns.
    """

    if not isinstance(response, dict):
        raise ValueError(
            "AI response must be a dictionary."
        )

    analysis_plan = response.get(
        "analysis_plan"
    )

    if not isinstance(
        analysis_plan,
        dict
    ):
        raise ValueError(
            "AI response does not contain "
            "a valid analysis plan."
        )

    # --------------------------------------------------
    # GROUP BY
    # --------------------------------------------------

    group_by = analysis_plan.get(
        "group_by",
        []
    )

    if group_by is None:
        group_by = []

    for column in group_by:

        if column not in df.columns:
            raise ValueError(
                f"AI selected invalid column '{column}'."
            )

    # --------------------------------------------------
    # METRIC
    # --------------------------------------------------

    metric = analysis_plan.get(
        "metric"
    )

    if metric is not None:

        if metric not in df.columns:
            raise ValueError(
                f"AI selected invalid metric column "
                f"'{metric}'."
            )

    # --------------------------------------------------
    # SORT BY
    # --------------------------------------------------

    sort_by = analysis_plan.get(
        "sort_by"
    )

    if sort_by is not None:

        # Count results may use generated "Count".
        if (
            sort_by != "Count"
            and sort_by not in df.columns
        ):
            raise ValueError(
                f"AI selected invalid sort column "
                f"'{sort_by}'."
            )

    # --------------------------------------------------
    # FILTER COLUMNS
    # --------------------------------------------------

    filters = analysis_plan.get(
        "filters",
        []
    )

    if filters is None:
        filters = []

    for condition in filters:

        column = condition.get(
            "column"
        )

        if column not in df.columns:
            raise ValueError(
                f"AI selected invalid filter column "
                f"'{column}'."
            )

    return True


# ==================================================
# ANALYSIS PLAN + CHART PLAN
# ==================================================

def generate_analysis_plan(df, question):
    """
    Convert a natural-language question into:

    1. A structured analysis plan.
    2. A visualization plan.

    Gemini generates the initial plan.

    A deterministic normalization layer then fixes
    common planning mistakes before execution.
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
        indent=2,
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
- different categories
- unique categories
- distinct categories
- available categories
- lists of category values

IMPORTANT:

Questions containing words such as:

- different
- unique
- distinct
- available
- list
- show all

usually mean the user wants category values.

For these questions use:

operation = "count"

group_by = ["category_column"]

metric = null

aggregation = null

Example:

User:
"What are the different departments?"

If the dataset contains:

Department

Return:

operation = "count"
group_by = ["Department"]
metric = null
aggregation = null

The result will contain:

Department | Count


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

Use:

{{
    "operation": "aggregate",
    "group_by": [],
    "metric": null,
    "aggregation": null,
    "filters": [],
    "sort_by": null,
    "sort_order": "descending",
    "limit": null
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


==================================================
DISTINCT CATEGORY RULE
==================================================

This rule is extremely important.

If the user asks:

"What are the different departments?"

"What are the unique departments?"

"List the departments."

"What are the available departments?"

"What are the distinct departments?"

"What departments are there?"

Then DO NOT use aggregate.

Use:

operation = "count"

group_by = ["Department"]

metric = null

aggregation = null

The grouped count operation automatically produces:

Department | Count


==================================================
VISUALIZATION
==================================================

Allowed chart types:

- bar
- line
- pie
- none

Use bar for:

- category comparisons
- rankings
- grouped numerical comparisons
- category frequency/count comparisons

Use line for:

- time trends
- chronological data

Use pie only for:

- parts of a whole
- category contribution to a total

Use none for:

- single values
- results where visualization adds no value


For category frequency/count results:

chart_type = "bar"

x_axis = grouped category column

y_axis = "Count"


==================================================
IMPORTANT EXAMPLES
==================================================

Example:

User:
"What are the different departments?"

Correct:

{{
    "operation": "count",
    "group_by": ["Department"],
    "metric": null,
    "aggregation": null,
    "filters": [],
    "sort_by": null,
    "sort_order": "descending",
    "limit": null
}}

Chart:

{{
    "chart_type": "bar",
    "x_axis": "Department",
    "y_axis": "Count",
    "title": "Count by Department"
}}


Example:

User:
"What are the top 5 products by sales?"

Correct:

{{
    "operation": "aggregate",
    "group_by": ["Product"],
    "metric": "Sales",
    "aggregation": "sum",
    "filters": [],
    "sort_by": "Sales",
    "sort_order": "descending",
    "limit": 5
}}

Chart:

{{
    "chart_type": "bar",
    "x_axis": "Product",
    "y_axis": "Sales",
    "title": "Top 5 Products by Sales"
}}


==================================================
RETURN FORMAT
==================================================

Return ONLY valid JSON.

Do not include markdown.

Do not include explanations.

Return:

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

            response["chart_plan"] = no_chart_plan()

        # --------------------------------------------------
        # DETERMINISTIC NORMALIZATION
        # --------------------------------------------------

        response = normalize_analysis_plan(
            df,
            question,
            response,
        )

        # --------------------------------------------------
        # VALIDATE AI RESPONSE
        # --------------------------------------------------

        validate_analysis_response(
            df,
            response,
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
            f"Unable to generate the analysis plan: {error}"
        )


# ==================================================
# LOCAL INSIGHT ENGINE
# ==================================================

def generate_local_insight(question, result):
    """
    Generate an AI-style insight locally using Pandas.

    No Gemini API call is made.
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
    Generate an insight without consuming Gemini API quota.

    One user question therefore uses only one Gemini
    request for the analysis plan.
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