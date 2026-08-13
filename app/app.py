import hashlib
from io import BytesIO

import pandas as pd
import streamlit as st

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)

from utils.data_loader import load_dataset

from utils.data_cleaner import (
    get_column_types,
    get_missing_values,
    get_dataset_summary,
)

from utils.llm_engine import (
    generate_analysis_plan,
    generate_ai_insight,
)

from utils.chart_generator import generate_chart

from utils.query_executor import execute_plan

from utils.result_validator import validate_result


# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="AI Data Analyst",
    page_icon="📊",
    layout="wide",
)


# ==================================================
# HEADER
# ==================================================

st.title("📊 AI Data Analyst")

st.write(
    "Upload a CSV or Excel dataset and explore your data "
    "using natural-language questions."
)


# ==================================================
# SESSION STATE
# ==================================================

if "analysis_history" not in st.session_state:
    st.session_state.analysis_history = []

if "active_dataset_signature" not in st.session_state:
    st.session_state.active_dataset_signature = None


# ==================================================
# FILE UPLOAD
# ==================================================

uploaded_file = st.file_uploader(
    "Upload your dataset",
    type=["csv", "xlsx", "xls"],
)


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def is_single_value_result(result):
    """
    Check whether the result contains exactly
    one row and one column.
    """

    return (
        len(result) == 1
        and len(result.columns) == 1
    )


def format_value(value):
    """
    Format numeric values for display.
    """

    if isinstance(value, (int, float)):
        return f"{value:,.2f}"

    return str(value)


def generate_local_insight(result):
    """
    Generate a basic insight locally for simple
    single-value results.

    This avoids an unnecessary Gemini API call.
    """

    if result.empty:
        return "No results were found for this analysis."

    column_name = result.columns[0]

    value = result.iloc[0, 0]

    formatted_value = format_value(value)

    return (
        f"The {column_name.lower()} is "
        f"{formatted_value}."
    )


# ==================================================
# DATASET SIGNATURE
# ==================================================

def get_dataset_signature(uploaded_file):
    """
    Create a stable signature from the actual uploaded
    file contents.

    This is used to detect when the user uploads a new
    dataset so the previous session history can be cleared.
    """

    file_bytes = uploaded_file.getvalue()

    return hashlib.sha256(
        file_bytes
    ).hexdigest()


# ==================================================
# PDF REPORT
# ==================================================

def dataframe_to_pdf_table(result, max_rows=50):
    """
    Convert a DataFrame into a ReportLab table.

    Large results are limited to max_rows so a very large
    query cannot create an unreasonably large PDF.
    """

    if result is None or result.empty:
        return [
            ["No results were returned."]
        ]

    display_result = result.head(max_rows).copy()

    data = [
        [
            str(column)
            for column in display_result.columns
        ]
    ]

    for _, row in display_result.iterrows():

        data.append(
            [
                format_value(value)
                if not pd.isna(value)
                else ""
                for value in row
            ]
        )

    table = Table(
        data,
        repeatRows=1,
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#E8EEF7"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.black,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (-1, -1),
                    "Helvetica",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    return table


def add_chart_to_pdf(story, chart):
    """
    Convert a Plotly chart to PNG and add it to the PDF.

    If Plotly image export is unavailable, the report continues
    without the chart instead of failing completely.
    """

    if chart is None:
        return

    try:

        image_bytes = chart.to_image(
            format="png",
            width=1000,
            height=600,
            scale=1,
        )

        image_buffer = BytesIO(
            image_bytes
        )

        chart_image = Image(
            image_buffer,
            width=7.0 * inch,
            height=4.2 * inch,
        )

        story.append(
            chart_image
        )

        story.append(
            Spacer(1, 0.15 * inch)
        )

    except Exception:

        story.append(
            Paragraph(
                "Chart preview could not be embedded in the PDF.",
                getSampleStyleSheet()["BodyText"],
            )
        )

        story.append(
            Spacer(1, 0.1 * inch)
        )


def generate_session_report(
    dataset_name,
    history,
):
    """
    Generate one PDF containing every successful analysis
    performed during the current dataset session.

    IMPORTANT:
    The COMPLETE current history is passed to this function.
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
        title="AI Data Analyst - Session Report",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        spaceAfter=10,
    )

    section_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=12,
        spaceAfter=8,
    )

    question_style = ParagraphStyle(
        "Question",
        parent=styles["Heading3"],
        fontSize=12,
        spaceAfter=6,
    )

    insight_style = ParagraphStyle(
        "Insight",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=13,
    )

    story = []

    # ==================================================
    # REPORT HEADER
    # ==================================================

    story.append(
        Paragraph(
            "📊 AI Data Analyst",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "Session Analysis Report",
            styles["Heading2"],
        )
    )

    story.append(
        Paragraph(
            f"<b>Dataset:</b> {dataset_name}",
            styles["BodyText"],
        )
    )

    story.append(
        Paragraph(
            f"<b>Questions analyzed:</b> {len(history)}",
            styles["BodyText"],
        )
    )

    story.append(
        Spacer(1, 0.2 * inch)
    )

    # ==================================================
    # ADD EVERY QUESTION
    # ==================================================

    for index, item in enumerate(
        history,
        start=1,
    ):

        story.append(
            Paragraph(
                f"Question {index}",
                section_style,
            )
        )

        question_text = (
            str(item.get("question", ""))
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        story.append(
            Paragraph(
                question_text,
                question_style,
            )
        )

        story.append(
            Paragraph(
                "Analysis Result",
                styles["Heading3"],
            )
        )

        result = item.get("result")

        if result is None or result.empty:

            story.append(
                Paragraph(
                    "No results were returned.",
                    styles["BodyText"],
                )
            )

        elif is_single_value_result(result):

            column_name = str(
                result.columns[0]
            )

            value = format_value(
                result.iloc[0, 0]
            )

            story.append(
                Paragraph(
                    f"<b>{column_name}:</b> {value}",
                    styles["BodyText"],
                )
            )

        else:

            story.append(
                dataframe_to_pdf_table(
                    result
                )
            )

            if len(result) > 50:

                story.append(
                    Spacer(1, 0.05 * inch)
                )

                story.append(
                    Paragraph(
                        "Only the first 50 rows are included "
                        "in this report.",
                        styles["BodyText"],
                    )
                )

        # ==================================================
        # CHART
        # ==================================================

        chart = item.get("chart")

        if chart is not None:

            story.append(
                Paragraph(
                    "Visualization",
                    styles["Heading3"],
                )
            )

            add_chart_to_pdf(
                story,
                chart,
            )

        # ==================================================
        # INSIGHT
        # ==================================================

        insight = item.get(
            "insight",
            "",
        )

        if insight:

            story.append(
                Paragraph(
                    "AI Insight",
                    styles["Heading3"],
                )
            )

            safe_insight = (
                str(insight)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br/>")
            )

            story.append(
                Paragraph(
                    safe_insight,
                    insight_style,
                )
            )

        # ==================================================
        # PAGE BREAK
        # ==================================================

        if index < len(history):

            story.append(
                PageBreak()
            )

    # ==================================================
    # BUILD PDF
    # ==================================================

    document.build(
        story
    )

    buffer.seek(0)

    return buffer.getvalue()


# ==================================================
# CACHED ANALYSIS-PLAN API CALL
# ==================================================

@st.cache_data(
    show_spinner=False,
    ttl=3600,
)
def get_cached_analysis_plan(
    dataset_signature,
    question,
    df,
):
    """
    Cache the Gemini analysis-plan response.

    Repeating the same question against the same dataset
    therefore does not consume another Gemini API call.
    """

    return generate_analysis_plan(
        df,
        question,
    )


# ==================================================
# DATA PROCESSING
# ==================================================

if uploaded_file is not None:

    try:

        # ==================================================
        # LOAD DATASET
        # ==================================================

        df = load_dataset(
            uploaded_file
        )

        dataset_signature = (
            get_dataset_signature(
                uploaded_file
            )
        )

        # ==================================================
        # NEW DATASET = NEW SESSION HISTORY
        # ==================================================

        if (
            st.session_state.active_dataset_signature
            != dataset_signature
        ):

            st.session_state.analysis_history = []

            st.session_state.active_dataset_signature = (
                dataset_signature
            )

        st.success(
            f"Successfully loaded **{uploaded_file.name}**"
        )

        # ==================================================
        # DATASET OVERVIEW
        # ==================================================

        summary = get_dataset_summary(df)

        st.subheader(
            "Dataset Overview"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Rows",
                f"{summary['rows']:,}",
            )

        with col2:

            st.metric(
                "Columns",
                summary["columns"],
            )

        with col3:

            st.metric(
                "Missing Cells",
                f"{summary['missing_cells']:,}",
            )

        with col4:

            st.metric(
                "Duplicate Rows",
                f"{summary['duplicates']:,}",
            )

        # ==================================================
        # DATA PREVIEW
        # ==================================================

        with st.expander(
            "🔍 View Dataset",
            expanded=True,
        ):

            st.dataframe(
                df.head(100),
                use_container_width=True,
            )

        # ==================================================
        # COLUMN INFORMATION
        # ==================================================

        with st.expander(
            "📋 Column Information"
        ):

            column_types = get_column_types(df)

            col1, col2, col3 = st.columns(3)

            with col1:

                st.markdown(
                    "### Numerical"
                )

                for column in column_types[
                    "numerical"
                ]:

                    st.write(
                        f"• {column}"
                    )

                if not column_types[
                    "numerical"
                ]:

                    st.info(
                        "None detected."
                    )

            with col2:

                st.markdown(
                    "### Categorical"
                )

                for column in column_types[
                    "categorical"
                ]:

                    st.write(
                        f"• {column}"
                    )

                if not column_types[
                    "categorical"
                ]:

                    st.info(
                        "None detected."
                    )

            with col3:

                st.markdown(
                    "### Date"
                )

                for column in column_types[
                    "date"
                ]:

                    st.write(
                        f"• {column}"
                    )

                if not column_types[
                    "date"
                ]:

                    st.info(
                        "None detected."
                    )

        # ==================================================
        # DATA QUALITY
        # ==================================================

        with st.expander(
            "🧹 Data Quality"
        ):

            missing_values = (
                get_missing_values(df)
            )

            if missing_values.empty:

                st.success(
                    "No missing values detected."
                )

            else:

                missing_df = (
                    missing_values
                    .reset_index()
                )

                missing_df.columns = [
                    "Column",
                    "Missing Values",
                ]

                missing_df["Missing %"] = (
                    missing_df["Missing Values"]
                    / len(df)
                    * 100
                ).round(2)

                st.dataframe(
                    missing_df,
                    use_container_width=True,
                    hide_index=True,
                )

        # ==================================================
        # ASK YOUR DATA
        # ==================================================

        st.divider()

        st.header(
            "🤖 Ask Your Data"
        )

        st.write(
            "Ask a question about your dataset in plain English."
        )

        question = st.text_input(
            "Your question",
            placeholder=(
                "Example: What are the top 5 products by revenue?"
            ),
        )

        analyze_button = st.button(
            "🔎 Analyze",
            type="primary",
        )

        # ==================================================
        # ANALYZE QUESTION
        # ==================================================

        if analyze_button:

            if not question.strip():

                st.warning(
                    "Please enter a question."
                )

            else:

                try:

                    clean_question = (
                        question.strip()
                    )

                    # ==================================================
                    # GENERATE ANALYSIS + CHART PLAN
                    # ONE GEMINI API CALL
                    # ==================================================

                    with st.spinner(
                        "Understanding your question..."
                    ):

                        ai_response = (
                            get_cached_analysis_plan(
                                dataset_signature,
                                clean_question,
                                df,
                            )
                        )

                    # ==================================================
                    # EXTRACT PLANS
                    # ==================================================

                    analysis_plan = (
                        ai_response.get(
                            "analysis_plan",
                            {},
                        )
                    )

                    chart_plan = (
                        ai_response.get(
                            "chart_plan",
                            {
                                "chart_type": "none",
                                "x_axis": None,
                                "y_axis": None,
                                "title": None,
                            },
                        )
                    )

                    # ==================================================
                    # ANALYSIS DETAILS
                    # ==================================================

                    with st.expander(
                        "🔍 Show Analysis Details"
                    ):

                        st.markdown(
                            "### Analysis Plan"
                        )

                        st.json(
                            analysis_plan
                        )

                        st.markdown(
                            "### Visualization Plan"
                        )

                        st.json(
                            chart_plan
                        )

                    # ==================================================
                    # EXECUTE ANALYSIS
                    # NO API CALL
                    # ==================================================

                    with st.spinner(
                        "Analyzing your data..."
                    ):

                        result = execute_plan(
                            df,
                            analysis_plan,
                        )

                        result = validate_result(
                            result
                        )

                    # ==================================================
                    # AUTOMATIC VISUALIZATION
                    # ==================================================

                    chart = None

                    if not result.empty:

                        single_value = (
                            is_single_value_result(
                                result
                            )
                        )

                        if not single_value:

                            chart_type = (
                                chart_plan.get(
                                    "chart_type",
                                    "none",
                                )
                            )

                            if chart_type != "none":

                                chart = generate_chart(
                                    result,
                                    chart_plan,
                                )

                    else:

                        single_value = False

                    # ==================================================
                    # AI INSIGHT
                    # ==================================================

                    if result.empty:

                        insight = (
                            "No results were found "
                            "for this analysis."
                        )

                    elif single_value:

                        insight = (
                            generate_local_insight(
                                result
                            )
                        )

                    else:

                        with st.spinner(
                            "Generating insight..."
                        ):

                            insight = (
                                generate_ai_insight(
                                    clean_question,
                                    result,
                                )
                            )

                    # ==================================================
                    # SAVE ANALYSIS TO CURRENT SESSION
                    #
                    # IMPORTANT:
                    # The latest question is appended BEFORE
                    # the Session Report section.
                    #
                    # There is NO 5-question limit.
                    # ==================================================

                    st.session_state.analysis_history.append(
                        {
                            "question": clean_question,
                            "result": result.copy(),
                            "chart": chart,
                            "insight": insight,
                            "analysis_plan": analysis_plan,
                            "chart_plan": chart_plan,
                        }
                    )

                    # ==================================================
                    # DISPLAY CURRENT RESULT
                    # ==================================================

                    st.subheader(
                        "📊 Analysis Result"
                    )

                    if result.empty:

                        st.warning(
                            "The analysis returned no results."
                        )

                    else:

                        if single_value:

                            column_name = (
                                result.columns[0]
                            )

                            value = (
                                result.iloc[0, 0]
                            )

                            st.metric(
                                label=column_name,
                                value=format_value(
                                    value
                                ),
                            )

                        else:

                            st.dataframe(
                                result,
                                use_container_width=True,
                                hide_index=True,
                            )

                    # ==================================================
                    # DISPLAY CURRENT VISUALIZATION
                    # ==================================================

                    if (
                        not result.empty
                        and not single_value
                    ):

                        if chart_plan.get(
                            "chart_type",
                            "none",
                        ) != "none":

                            st.subheader(
                                "📈 Visualization"
                            )

                            with st.expander(
                                "🔍 Show Visualization Details"
                            ):

                                st.json(
                                    chart_plan
                                )

                            if chart is not None:

                                # UNIQUE KEY FIX
                                st.plotly_chart(
                                    chart,
                                    use_container_width=True,
                                    key=(
                                        f"current_chart_"
                                        f"{len(st.session_state.analysis_history)}"
                                    ),
                                )

                            else:

                                st.info(
                                    "A suitable visualization "
                                    "could not be generated for "
                                    "this result."
                                )

                        else:

                            st.info(
                                "A visualization is not required "
                                "for this result."
                            )

                    # ==================================================
                    # DISPLAY CURRENT INSIGHT
                    # ==================================================

                    st.subheader(
                        "💡 AI Insight"
                    )

                    st.write(
                        insight
                    )

                    st.success(
                        "Analysis added to the current session report."
                    )

                except Exception as error:

                    st.error(
                        f"Analysis failed: {error}"
                    )

        # ==================================================
        # SESSION REPORT
        #
        # IMPORTANT:
        # This section is AFTER the Analyze section.
        #
        # Therefore the latest question has already been
        # appended to analysis_history.
        #
        # Q1 -> PDF has Q1
        # Q2 -> PDF has Q1 + Q2
        # Q5 -> PDF has Q1 + Q2 + Q3 + Q4 + Q5
        #
        # There is NO LIMIT OF 5 QUESTIONS.
        # ==================================================

        if st.session_state.analysis_history:

            st.divider()

            report_col1, report_col2 = st.columns(
                [3, 1]
            )

            with report_col1:

                st.subheader(
                    "📚 Session Analysis History"
                )

                st.write(
                    f"{len(st.session_state.analysis_history)} "
                    "question(s) in the current session."
                )

            with report_col2:

                report_pdf = generate_session_report(
                    uploaded_file.name,
                    st.session_state.analysis_history,
                )

                st.download_button(
                    "📥 Download Session Report",
                    data=report_pdf,
                    file_name="ai_data_analyst_session_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

            # ==================================================
            # DISPLAY ALL HISTORY
            # ==================================================

            for index, item in enumerate(
                st.session_state.analysis_history,
                start=1,
            ):

                with st.expander(
                    f"Question {index}: {item['question']}"
                ):

                    result = item["result"]

                    if result.empty:

                        st.warning(
                            "No results were returned."
                        )

                    elif is_single_value_result(
                        result
                    ):

                        st.metric(
                            label=str(
                                result.columns[0]
                            ),
                            value=format_value(
                                result.iloc[0, 0]
                            ),
                        )

                    else:

                        st.dataframe(
                            result,
                            use_container_width=True,
                            hide_index=True,
                        )

                    # ==================================================
                    # HISTORY CHART
                    # UNIQUE KEY FIX
                    # ==================================================

                    if item.get("chart") is not None:

                        st.plotly_chart(
                            item["chart"],
                            use_container_width=True,
                            key=f"history_chart_{index}",
                        )

                    st.markdown(
                        "**💡 Insight**"
                    )

                    st.write(
                        item.get(
                            "insight",
                            "",
                        )
                    )

    except Exception as error:

        st.error(
            f"Unable to process the uploaded file: {error}"
        )


# ==================================================
# NO FILE UPLOADED
# ==================================================

else:

    # Reset active session state when no dataset is loaded.

    st.session_state.analysis_history = []

    st.session_state.active_dataset_signature = None

    st.info(
        "Upload a CSV or Excel file to begin your analysis."
    )