# 📊 AI Data Analyst

> An AI-powered data analysis application that allows users to upload CSV/Excel datasets, ask questions in natural language, generate automated analysis and visualizations, and export complete session reports as PDF.

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red?logo=streamlit)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458?logo=pandas)
![License](https://img.shields.io/badge/License-MIT-green)


An end-to-end AI Data Analyst application that allows users to upload CSV or Excel datasets and analyze them using natural-language questions.

The project combines Python, Pandas, Streamlit, Google Gemini, Plotly, and ReportLab to provide an interactive workflow for dataset exploration, AI-assisted analysis, automatic visualization, insights, and PDF reporting.

🚀 Project Demo

🖥️ Interactive Streamlit Application

The application allows users to upload a dataset and ask questions in plain English.

Dataset Upload
      │
      ▼
Dataset Overview & Data Quality
      │
      ▼
Natural-Language Question
      │
      ▼
AI Analysis Plan
      │
      ▼
Query Execution
      │
      ▼
Validated Result
      │
 ┌────┴───────────────┐
 ▼                    ▼
Visualization       AI Insight
 │                    │
 └─────────┬──────────┘
           ▼
     Session History
           │
           ▼
      PDF Report

📌 Overview

Traditional data analysis often requires users to write code or SQL queries before they can answer simple questions about a dataset.

This project provides a natural-language interface where users can ask questions such as:

What are the top 5 products by sales?

Which region has the highest profit?

What is the total revenue?

Which category performs best?

Show sales by region.

The AI converts the user's question into a structured analysis plan. The application then executes that plan against the uploaded dataset and presents the result without requiring the user to write Pandas code.

⭐ Project Highlights

🤖 Natural-language data analysis

📂 CSV and Excel dataset upload

📊 Automatic dataset overview

🔍 Dataset preview

📋 Automatic column-type detection

🧹 Missing-value and data-quality analysis

🧠 AI-generated analysis plans

⚙️ Programmatic query execution

✅ Result validation

📈 Automatic Plotly visualizations

💡 AI-generated insights

📚 Session analysis history

📄 Multi-question PDF session reports

🔐 Environment-variable based API configuration

⚡ Cached repeated analysis-plan requests

🛡️ Safe handling of local secrets and generated files with .gitignore

📸 Project Preview

Main Application



Analysis Result



Session Report



✨ Features

📂 Dataset Upload

Users can upload:

CSV files

Excel .xlsx files

Excel .xls files

The uploaded dataset is loaded and prepared for analysis.

📊 Dataset Overview

The application displays important dataset statistics including:

Number of rows

Number of columns

Missing cells

Duplicate rows

A preview of the dataset is also available directly in the application.

📋 Column Information

The application automatically categorizes columns into:

Numerical columns

Categorical columns

Date columns

This provides a quick understanding of the structure of an uploaded dataset.

🧹 Data Quality

The application checks the dataset for missing values and displays missing-value information by column.

This gives users a quick view of potential data-quality issues before asking analytical questions.

🤖 Natural-Language Analysis

Users can ask questions about their dataset using plain English.

Example:

What are the top 5 products by revenue?

The AI generates a structured analysis plan based on the dataset and the user's question.

🧠 AI Analysis Planning

The AI does not directly modify the dataset.

Instead, it generates a structured plan that describes the required analysis.

The application then executes the plan using the local dataset.

This separates:

Natural Language Understanding
            ↓
      Analysis Plan
            ↓
     Local Execution
            ↓
       Result

⚙️ Query Execution

The generated analysis plan is passed to the query-execution layer.

The result is then validated before being displayed to the user.

This provides a controlled workflow between AI-generated instructions and dataset operations.

📈 Automatic Visualization

For suitable multi-row analysis results, the application can automatically generate a Plotly visualization based on the AI-generated visualization plan.

Single-value results are displayed as metrics instead of unnecessary charts.

💡 AI Insights

The application provides an insight for the analysis result.

For simple single-value results, a local insight is generated without making another AI request.

For more complex results, an AI-generated insight is provided.

📚 Session Analysis History

Successful analyses are stored in the current Streamlit session.

The history contains:

Question

Analysis result

Visualization

Insight

Analysis plan

Visualization plan

The history is cleared when the Streamlit session is restarted or a different dataset is uploaded.

📄 PDF Session Report

The application can generate one PDF report containing all analyses from the current dataset session.

The report includes:

Dataset name

Number of analyzed questions

Each question

Analysis result

Visualization when available

AI insight

This makes it possible to export a complete analysis session instead of downloading individual results.

🧪 Example Dataset

The repository includes sample datasets for demonstrating the application.

Superstore

A Superstore dataset can be used for questions such as:

What are the top 5 products by sales?

Which region has the highest profit?

What is the total sales?

Which category generates the most profit?

Show sales by region.

HR Employee Attrition

The repository also contains an HR employee attrition dataset for testing analysis across a different type of dataset.

🧠 Application Workflow

Upload CSV / Excel
        │
        ▼
Load Dataset
        │
        ▼
Dataset Summary
        │
        ├── Column Types
        ├── Missing Values
        └── Data Preview
        │
        ▼
Ask Natural-Language Question
        │
        ▼
Google Gemini
        │
        ▼
Analysis Plan + Chart Plan
        │
        ▼
Query Executor
        │
        ▼
Result Validator
        │
        ▼
Analysis Result
        │
 ┌──────┴─────────┐
 ▼                ▼
Plotly Chart    AI Insight
 └──────┬─────────┘
        ▼
Session History
        │
        ▼
PDF Session Report

🔌 AI Integration

The application uses Google Gemini for two main tasks:

1. Analysis Planning

Gemini interprets the user's natural-language question and generates:

Analysis plan

Visualization plan

The analysis plan is then executed locally.

2. Result Insights

For complex analysis results, Gemini generates a concise analytical insight based on the user's question and the returned result.

Repeated analysis-plan requests are cached using Streamlit caching to avoid unnecessary repeated requests during the session.

🛠️ Tech Stack

Category

Technology

🐍 Programming Language

Python

📊 Data Processing

Pandas

🖥️ Web Application

Streamlit

🤖 AI Analysis

Google Gemini

📈 Visualization

Plotly

📄 PDF Generation

ReportLab

🔐 Configuration

Environment Variables

🔧 Version Control

Git

☁️ Repository

GitHub

📂 Project Structure

AI-Data-Analyst/
│
├── app/
│   ├── app.py
│   │
│   └── utils/
│       ├── chart_generator.py
│       ├── data_cleaner.py
│       ├── data_loader.py
│       ├── llm_engine.py
│       ├── query_executor.py
│       └── result_validator.py
│
├── images/
│   ├── ai_data_analyst_app.png
│   ├── ai_data_analyst_result.png
│   └── ai_data_analyst_report.png
│
├── sample_data/
│   ├── superstore.csv
│   └── WA_Fn-UseC_-HR-Employee-Attrition.csv
│
├── sample_report/
│   └── ai_data_analyst_session_report.pdf
│
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt

Update the three image filenames in this section if your actual image filenames are different.

🚀 Installation

1. Clone the Repository

git clone https://github.com/harsh8767/AI-Data-Analyst.git

2. Navigate into the Project

cd AI-Data-Analyst

3. Create a Virtual Environment

Windows

python -m venv venv
venv\Scripts\activate

Linux / macOS

python3 -m venv venv
source venv/bin/activate

4. Install Dependencies

pip install -r requirements.txt

🔐 Environment Variables

Create a local .env file in the project root.

Use .env.example as the template.

Example:

GEMINI_API_KEY=your_api_key_here

Do not commit .env to GitHub.

The repository's .gitignore is configured to exclude the local environment file.

▶️ Run the Application

From the project root:

streamlit run app/app.py

The application will open in your browser.

📌 How to Use the Application

Step 1

Start the Streamlit application.

Step 2

Upload a CSV or Excel dataset.

Step 3

Review:

Dataset overview

Dataset preview

Column information

Data quality

Step 4

Enter a natural-language question.

Example:

What are the top 5 products by sales?

Step 5

Click:

🔎 Analyze

Step 6

Review:

Analysis result

Visualization

AI insight

Analysis details

Step 7

Ask additional questions to build the current session history.

Step 8

Download the complete session analysis as a PDF report.

📄 Sample Report

A sample generated session report is included in:

sample_report/

The report demonstrates how multiple questions, results, visualizations, and insights can be combined into one PDF.

🧪 Example Questions

Using the Superstore dataset, try questions such as:

1. What are the top 5 products by sales?

2. Which region has the highest profit?

3. What is the total sales?

4. Which category generates the most profit?

5. Show sales by region.

You can also ask questions that require aggregations, grouping, sorting, filtering, and suitable visualizations.

⚡ API Usage Optimization

The application is designed to avoid unnecessary AI requests where possible.

For example:

Analysis-plan responses are cached for repeated questions against the same dataset.

Single-value results use a local insight instead of an additional AI insight request.

Query execution and result validation happen locally.

This keeps the AI component focused on tasks that benefit from natural-language understanding and insight generation.

🔒 Security

The project keeps API credentials outside the source code.

Important files such as:

.env

are excluded from version control.

Before pushing the project to GitHub, verify:

git status --ignored

and make sure your real API key is not staged.

⚠️ Limitations

AI-generated analysis plans depend on the quality and clarity of the user's question.

Very large datasets may require additional optimization.

Visualization generation depends on whether the returned result is suitable for charting.

PDF chart embedding depends on Plotly image-export support in the local environment.

Session history is stored only in Streamlit session state and is not persisted to a database.

AI-generated insights should be treated as analytical assistance and verified for important business decisions.

🚀 Future Improvements

Potential future enhancements include:

📊 More advanced visualization types

🧠 Improved analysis-plan validation

🗄️ SQL/database support for large datasets

💾 Persistent analysis history

👥 Multi-user sessions

📤 Excel result export

📑 More advanced PDF report styling

🔎 Follow-up questions using conversational context

📈 Advanced statistical analysis

🧪 Automated testing

☁️ Cloud deployment

🔐 Authentication and user management

🙏 Acknowledgements

This project makes use of the following open-source technologies:

Python

Pandas

Streamlit

Plotly

ReportLab

Google Gemini

Git

👨‍💻 Developer

Harsh Chavan

Computer Engineering Student

Passionate about Artificial Intelligence, Machine Learning, Data Analytics, Python, and Software Development.

GitHub

https://github.com/harsh8767

📜 License

This project is licensed under the MIT License.

See the LICENSE file for more information.