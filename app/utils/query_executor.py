import pandas as pd


# ==================================================
# ALLOWED OPERATORS
# ==================================================

ALLOWED_OPERATORS = {
    "==",
    "!=",
    ">",
    ">=",
    "<",
    "<=",
    "contains",
}


# ==================================================
# ALLOWED AGGREGATIONS
# ==================================================

ALLOWED_AGGREGATIONS = {
    "sum",
    "mean",
    "median",
    "min",
    "max",
    "count",
}


# ==================================================
# ALLOWED OPERATIONS
# ==================================================

ALLOWED_OPERATIONS = {
    "aggregate",
    "count",
    "filter",
    "describe",
}


# ==================================================
# VALIDATE COLUMN
# ==================================================

def validate_column(df, column):
    """
    Make sure the requested column exists.
    """

    if column is None:
        return

    if column not in df.columns:
        raise ValueError(
            f"Column '{column}' does not exist in the dataset."
        )


# ==================================================
# DETECT CATEGORY-ONLY COUNT REQUEST
# ==================================================

def is_category_count_request(plan):
    """
    Detect plans that represent a request for distinct /
    different / unique categories.

    This is intentionally based on the generated plan,
    not the original question.

    Example:

        operation = aggregate
        group_by = ["Department"]
        metric = None
        aggregation = None

    is treated as a category count request.

    This protects the application if the LLM incorrectly
    chooses aggregate instead of count.
    """

    operation = plan.get("operation")

    group_by = plan.get(
        "group_by",
        []
    )

    metric = plan.get("metric")

    aggregation = plan.get("aggregation")

    if operation != "aggregate":
        return False

    if not group_by:
        return False

    if metric is not None:
        return False

    if aggregation is not None:
        return False

    return True


# ==================================================
# NORMALIZE PLAN
# ==================================================

def normalize_plan(plan):
    """
    Normalize common LLM mistakes before validation.

    In particular, convert:

        aggregate
        group_by = ["Department"]
        metric = None
        aggregation = None

    into:

        count
        group_by = ["Department"]
        metric = None
        aggregation = None
    """

    if not isinstance(plan, dict):
        return plan

    normalized = dict(plan)

    if is_category_count_request(normalized):

        normalized["operation"] = "count"
        normalized["metric"] = None
        normalized["aggregation"] = None

    return normalized


# ==================================================
# VALIDATE PLAN
# ==================================================

def validate_plan(df, plan):
    """
    Validate the AI-generated analysis plan
    before executing it.
    """

    if not isinstance(plan, dict):
        raise ValueError(
            "Analysis plan must be a dictionary."
        )

    operation = plan.get("operation")

    if operation not in ALLOWED_OPERATIONS:
        raise ValueError(
            f"Unsupported operation: {operation}"
        )

    # --------------------------------------------------
    # GROUP BY
    # --------------------------------------------------

    group_by = plan.get(
        "group_by",
        []
    )

    if group_by is None:
        group_by = []

    if not isinstance(group_by, list):
        raise ValueError(
            "group_by must be a list."
        )

    for column in group_by:

        validate_column(
            df,
            column
        )

    # --------------------------------------------------
    # METRIC
    # --------------------------------------------------

    metric = plan.get(
        "metric"
    )

    if metric:
        validate_column(
            df,
            metric
        )

    # --------------------------------------------------
    # SORT BY
    # --------------------------------------------------

    sort_by = plan.get(
        "sort_by"
    )

    if sort_by:

        # "Count" is a generated result column and
        # therefore does not need to exist in df.

        if sort_by != "Count":

            validate_column(
                df,
                sort_by
            )

    # --------------------------------------------------
    # SORT ORDER
    # --------------------------------------------------

    sort_order = plan.get(
        "sort_order",
        "descending"
    )

    if sort_order not in {
        "ascending",
        "descending",
    }:

        raise ValueError(
            "sort_order must be "
            "'ascending' or 'descending'."
        )

    # --------------------------------------------------
    # AGGREGATION
    # --------------------------------------------------

    aggregation = plan.get(
        "aggregation"
    )

    if (
        aggregation
        and aggregation not in ALLOWED_AGGREGATIONS
    ):

        raise ValueError(
            f"Unsupported aggregation: {aggregation}"
        )

    # --------------------------------------------------
    # FILTERS
    # --------------------------------------------------

    filters = plan.get(
        "filters",
        []
    )

    if filters is None:
        filters = []

    if not isinstance(
        filters,
        list
    ):

        raise ValueError(
            "filters must be a list."
        )

    for filter_condition in filters:

        if not isinstance(
            filter_condition,
            dict
        ):

            raise ValueError(
                "Each filter must be an object."
            )

        column = filter_condition.get(
            "column"
        )

        operator = filter_condition.get(
            "operator"
        )

        if not column:

            raise ValueError(
                "Filter column is missing."
            )

        if not operator:

            raise ValueError(
                "Filter operator is missing."
            )

        validate_column(
            df,
            column
        )

        if operator not in ALLOWED_OPERATORS:

            raise ValueError(
                f"Unsupported operator: {operator}"
            )

    # --------------------------------------------------
    # LIMIT
    # --------------------------------------------------

    limit = plan.get(
        "limit"
    )

    if limit is not None:

        try:

            limit = int(
                limit
            )

        except (
            TypeError,
            ValueError,
        ):

            raise ValueError(
                "limit must be an integer."
            )

        if limit <= 0:

            raise ValueError(
                "limit must be greater than zero."
            )


# ==================================================
# APPLY FILTER
# ==================================================

def apply_filter(df, condition):
    """
    Apply one filter condition to the dataframe.
    """

    column = condition["column"]
    operator = condition["operator"]
    value = condition.get("value")

    series = df[column]

    # --------------------------------------------------
    # EQUALITY
    # --------------------------------------------------

    if operator == "==":

        if pd.api.types.is_numeric_dtype(series):

            try:

                numeric_value = float(
                    value
                )

                return df[
                    series == numeric_value
                ]

            except (
                TypeError,
                ValueError,
            ):

                pass

        return df[
            series.astype(str).str.strip()
            == str(value).strip()
        ]

    # --------------------------------------------------
    # NOT EQUAL
    # --------------------------------------------------

    if operator == "!=":

        if pd.api.types.is_numeric_dtype(series):

            try:

                numeric_value = float(
                    value
                )

                return df[
                    series != numeric_value
                ]

            except (
                TypeError,
                ValueError,
            ):

                pass

        return df[
            series.astype(str).str.strip()
            != str(value).strip()
        ]

    # --------------------------------------------------
    # CONTAINS
    # --------------------------------------------------

    if operator == "contains":

        return df[
            series.astype(str)
            .str.contains(
                str(value),
                case=False,
                na=False,
                regex=False,
            )
        ]

    # --------------------------------------------------
    # NUMERIC COMPARISONS
    # --------------------------------------------------

    try:

        numeric_value = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        numeric_value = value

    try:

        if operator == ">":

            return df[
                series > numeric_value
            ]

        if operator == ">=":

            return df[
                series >= numeric_value
            ]

        if operator == "<":

            return df[
                series < numeric_value
            ]

        if operator == "<=":

            return df[
                series <= numeric_value
            ]

    except TypeError:

        raise ValueError(
            f"Cannot apply '{operator}' "
            f"comparison to column '{column}'."
        )

    raise ValueError(
        f"Unsupported operator: {operator}"
    )


# ==================================================
# APPLY FILTERS
# ==================================================

def apply_filters(df, filters):
    """
    Apply all filters sequentially.
    """

    working_df = df

    for condition in filters:

        working_df = apply_filter(
            working_df,
            condition
        )

        if working_df.empty:
            break

    return working_df


# ==================================================
# EXECUTE PLAN
# ==================================================

def execute_plan(df, plan):
    """
    Execute an AI-generated analysis plan
    using Pandas.

    No API calls are made here.
    """

    # --------------------------------------------------
    # NORMALIZE PLAN FIRST
    # --------------------------------------------------

    plan = normalize_plan(
        plan
    )

    # --------------------------------------------------
    # VALIDATE
    # --------------------------------------------------

    validate_plan(
        df,
        plan
    )

    # --------------------------------------------------
    # COPY DATA
    # --------------------------------------------------

    working_df = df.copy()

    # --------------------------------------------------
    # APPLY FILTERS
    # --------------------------------------------------

    filters = plan.get(
        "filters",
        []
    )

    if filters:

        working_df = apply_filters(
            working_df,
            filters
        )

    operation = plan["operation"]

    # ==================================================
    # DESCRIBE
    # ==================================================

    if operation == "describe":

        numerical_df = (
            working_df
            .select_dtypes(
                include="number"
            )
        )

        if numerical_df.empty:

            return pd.DataFrame()

        return numerical_df.describe().T

    # ==================================================
    # COUNT
    # ==================================================

    if operation == "count":

        group_by = plan.get(
            "group_by",
            []
        )

        # --------------------------------------------------
        # GROUPED COUNT
        # --------------------------------------------------

        if group_by:

            result = (
                working_df
                .groupby(
                    group_by,
                    dropna=False
                )
                .size()
                .reset_index(
                    name="Count"
                )
            )

            # --------------------------------------------------
            # SORTING
            # --------------------------------------------------

            sort_by = plan.get(
                "sort_by"
            )

            sort_order = plan.get(
                "sort_order",
                "descending"
            )

            ascending = (
                sort_order == "ascending"
            )

            if (
                sort_by
                and sort_by in result.columns
            ):

                result = result.sort_values(
                    by=sort_by,
                    ascending=ascending,
                )

            else:

                result = result.sort_values(
                    by="Count",
                    ascending=ascending,
                )

            # --------------------------------------------------
            # LIMIT
            # --------------------------------------------------

            limit = plan.get(
                "limit"
            )

            if limit is not None:

                result = result.head(
                    int(limit)
                )

            return result.reset_index(
                drop=True
            )

        # --------------------------------------------------
        # TOTAL ROW COUNT
        # --------------------------------------------------

        return pd.DataFrame(
            {
                "Count": [
                    len(working_df)
                ]
            }
        )

    # ==================================================
    # FILTER
    # ==================================================

    if operation == "filter":

        limit = plan.get(
            "limit"
        )

        if limit is not None:

            return (
                working_df
                .head(
                    int(limit)
                )
                .reset_index(
                    drop=True
                )
            )

        return working_df.reset_index(
            drop=True
        )

    # ==================================================
    # AGGREGATION
    # ==================================================

    if operation == "aggregate":

        group_by = plan.get(
            "group_by",
            []
        )

        metric = plan.get(
            "metric"
        )

        aggregation = plan.get(
            "aggregation"
        )

        # --------------------------------------------------
        # SAFETY: CATEGORY-ONLY REQUEST
        # --------------------------------------------------

        if (
            group_by
            and not metric
            and not aggregation
        ):

            result = (
                working_df
                .groupby(
                    group_by,
                    dropna=False
                )
                .size()
                .reset_index(
                    name="Count"
                )
            )

            # --------------------------------------------------
            # SORT
            # --------------------------------------------------

            sort_order = plan.get(
                "sort_order",
                "descending"
            )

            ascending = (
                sort_order == "ascending"
            )

            sort_by = plan.get(
                "sort_by"
            )

            if (
                sort_by
                and sort_by in result.columns
            ):

                result = result.sort_values(
                    by=sort_by,
                    ascending=ascending,
                )

            else:

                result = result.sort_values(
                    by="Count",
                    ascending=ascending,
                )

            # --------------------------------------------------
            # LIMIT
            # --------------------------------------------------

            limit = plan.get(
                "limit"
            )

            if limit is not None:

                result = result.head(
                    int(limit)
                )

            return result.reset_index(
                drop=True
            )

        # --------------------------------------------------
        # NORMAL AGGREGATION VALIDATION
        # --------------------------------------------------

        if not metric:

            raise ValueError(
                "An aggregation requires "
                "a metric column."
            )

        if not aggregation:

            raise ValueError(
                "An aggregation function "
                "is required."
            )

        # --------------------------------------------------
        # EMPTY DATA AFTER FILTER
        # --------------------------------------------------

        if working_df.empty:

            if group_by:

                return pd.DataFrame(
                    columns=group_by + [
                        f"{aggregation}_{metric}"
                    ]
                )

            return pd.DataFrame(
                {
                    metric: [
                        0
                        if aggregation == "sum"
                        else None
                    ]
                }
            )

        # ==================================================
        # COUNT AGGREGATION
        # ==================================================

        if aggregation == "count":

            if group_by:

                result = (
                    working_df
                    .groupby(
                        group_by,
                        dropna=False
                    )[metric]
                    .count()
                    .reset_index()
                )

                result = result.rename(
                    columns={
                        metric:
                        f"count_{metric}"
                    }
                )

            else:

                result = pd.DataFrame(
                    {
                        metric: [
                            working_df[
                                metric
                            ].count()
                        ]
                    }
                )

        # ==================================================
        # OTHER AGGREGATIONS
        # ==================================================

        else:

            # --------------------------------------------------
            # NUMERIC VALIDATION
            # --------------------------------------------------

            if aggregation in {
                "sum",
                "mean",
                "median",
            }:

                if not pd.api.types.is_numeric_dtype(
                    working_df[metric]
                ):

                    raise ValueError(
                        f"Column '{metric}' must be numeric "
                        f"for {aggregation} aggregation."
                    )

            # --------------------------------------------------
            # GROUPED AGGREGATION
            # --------------------------------------------------

            if group_by:

                result = (
                    working_df
                    .groupby(
                        group_by,
                        dropna=False
                    )[metric]
                    .agg(aggregation)
                    .reset_index()
                )

                result = result.rename(
                    columns={
                        metric:
                        f"{aggregation}_{metric}"
                    }
                )

            # --------------------------------------------------
            # GLOBAL AGGREGATION
            # --------------------------------------------------

            else:

                value = getattr(
                    working_df[metric],
                    aggregation
                )()

                result = pd.DataFrame(
                    {
                        metric: [
                            value
                        ]
                    }
                )

        # ==================================================
        # SORTING
        # ==================================================

        sort_by = plan.get(
            "sort_by"
        )

        sort_order = plan.get(
            "sort_order",
            "descending"
        )

        ascending = (
            sort_order == "ascending"
        )

        if (
            sort_by
            and sort_by in result.columns
        ):

            result = result.sort_values(
                by=sort_by,
                ascending=ascending,
            )

        else:

            result_column = (
                f"{aggregation}_{metric}"
                if group_by
                else metric
            )

            if result_column in result.columns:

                result = result.sort_values(
                    by=result_column,
                    ascending=ascending,
                )

        # ==================================================
        # LIMIT
        # ==================================================

        limit = plan.get(
            "limit"
        )

        if limit is not None:

            result = result.head(
                int(limit)
            )

        return result.reset_index(
            drop=True
        )

    # ==================================================
    # UNKNOWN OPERATION
    # ==================================================

    raise ValueError(
        "Unable to execute the requested analysis."
    )