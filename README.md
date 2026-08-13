# 📊 AI Data Analyst

> An end-to-end AI-powered data analysis application that allows users to upload CSV or Excel datasets, ask questions in natural language, generate structured analysis plans, execute data analysis locally, create visualizations and AI insights, and export complete analysis sessions as PDF reports.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-blue?logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/Streamlit-App-red?logo=streamlit" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/Pandas-Data%20Analysis-150458?logo=pandas" alt="Pandas"/>
  <img src="https://img.shields.io/badge/Plotly-Visualization-3F4F75?logo=plotly" alt="Plotly"/>
  <img src="https://img.shields.io/badge/Google%20Gemini-AI%20Analysis-4285F4?logo=google" alt="Google Gemini"/>
  <img src="https://img.shields.io/badge/ReportLab-PDF%20Reports-orange" alt="ReportLab"/>
</p>

---

# 📌 Overview

AI Data Analyst is an end-to-end data analysis application that allows users to upload CSV or Excel datasets and analyze them using natural-language questions.

The project combines Python, Pandas, Streamlit, Google Gemini, Plotly, and ReportLab to provide an interactive workflow for dataset exploration, AI-assisted analysis, automatic visualization, analytical insights, session history, and PDF reporting.

Instead of manually writing Pandas code or SQL queries, users can interact with their datasets using plain English.

### Example Questions

- What are the top 5 products by sales?
- Which region has the highest profit?
- What is the total sales?
- Which category generates the most profit?
- Show sales by region.

The AI converts the user's natural-language question into a structured analysis plan. The application then executes that plan against the uploaded dataset and presents the validated result.

---

# 🚀 Features

### 📂 Dataset Upload

- CSV support
- Excel (.xlsx, .xls) support
- Automatic dataset loading
- Dataset change detection

### 📊 Dataset Overview

- Total rows
- Total columns
- Missing cell count
- Duplicate row count

### 🔍 Data Preview

- Interactive table preview
- View first 100 rows
- Scrollable dataset inspection

### 📋 Column Intelligence

Automatic identification of:

- Numerical columns
- Categorical columns
- Date columns

### 🧹 Data Quality Analysis

- Missing value detection
- Missing percentage calculation
- Data quality summary

### 🤖 Natural Language Analytics

Users can ask questions in plain English.

Examples:

```text
What are the top 10 products by sales?

Which region generated the highest profit?

Show sales by category.

What is the average discount?

Which customer segment contributes the most revenue?
```

### 🧠 AI Analysis Planning

Google Gemini generates:

- Structured analysis plan
- Aggregation strategy
- Filtering logic
- Sorting instructions
- Visualization recommendation

### ⚙️ Local Query Execution

The generated plan is executed locally using Pandas.

Benefits:

- Faster execution
- Lower API usage
- Better privacy
- Reproducible results

### 📈 Automatic Visualizations

Supported visualizations include:

- Bar charts
- Line charts
- Pie charts
- Scatter plots

Generated automatically based on AI recommendations.

### 💡 AI Insights

The application generates analytical insights explaining:

- Key trends
- Significant observations
- Business implications
- Important findings

### 📚 Session History

The application maintains:

- Question history
- Results
- Charts
- Insights

for the currently uploaded dataset.

### 📄 PDF Report Generation

Generate a professional PDF report containing:

- All session questions
- Results
- Visualizations
- AI insights

---

# 🏗️ Application Workflow

```text
1. Upload Dataset
          │
          ▼
2. Dataset Overview
          │
          ▼
3. Ask Question
          │
          ▼
4. Gemini Generates Analysis Plan
          │
          ▼
5. Execute Analysis Locally
          │
          ▼
6. Validate Result
          │
          ▼
7. Generate Visualization
          │
          ▼
8. Generate Insight
          │
          ▼
9. Save Session History
          │
          ▼
10. Export PDF Report
```

---

# 🧠 AI Integration

The application uses Google Gemini for:

### Analysis Planning

Input:

- Dataset metadata
- User question

Output:

- Analysis plan
- Visualization plan

### Insight Generation

Input:

- User question
- Analysis result

Output:

- Human-readable analytical insight

### API Optimization

The application minimizes Gemini usage by:

- Caching repeated analysis-plan requests
- Generating local insights for simple metrics
- Executing data operations locally

---

# 🛠️ Tech Stack

| Component | Technology |
|------------|------------|
| Frontend | Streamlit |
| Data Processing | Pandas |
| AI Model | Google Gemini |
| Visualization | Plotly |
| PDF Generation | ReportLab |
| Environment Variables | python-dotenv |
| Spreadsheet Support | OpenPyXL |

---

# 📂 Project Structure

```text
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
│   ├── sample_analysis.png
│   └── sample_report.png
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
```

---

# ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/harsh8767/AI-Data-Analyst.git

cd AI-Data-Analyst
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

Mac/Linux:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Environment Variables

Create a `.env` file:

```env
GOOGLE_API_KEY=YOUR_GEMINI_API_KEY
```

Example:

```env
GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxx
```

---

# ▶️ Run Application

```bash
streamlit run app/app.py
```

Open:

```text
http://localhost:8501
```

---

# 📸 Screenshots

## Application Interface

```text
images/app-dashboard..png
```

## Analysis Example

```text
images/data-analysis.png
```

## PDF Report Download

```text
images/pdf-report.png
```

---

# 📄 Sample Report

A sample generated report is included:

```text
sample_report/
└── ai_data_analyst_session_report.pdf
```

This demonstrates:

- Multi-question analysis
- Tables
- Visualizations
- AI insights
- Session-based reporting

---

# 🔒 Security

- API keys stored in `.env`
- `.env` excluded via `.gitignore`
- No database storage
- Session history stored only in memory
- Dataset data remains local

---

# ⚡ Performance Optimizations

### Cached Analysis Plans

Repeated questions against the same dataset:

- Reuse cached Gemini responses
- Reduce API costs
- Improve responsiveness

### Local Query Execution

Only planning and insight generation require AI.

Data processing occurs locally using Pandas.

### Limited PDF Tables

Large results are automatically truncated to prevent oversized PDF files.

---

# 🚧 Current Limitations

- Works only with structured tabular datasets
- Requires a valid Gemini API key
- Extremely large datasets may impact performance
- Visualization recommendations depend on AI output

---

# 🔮 Future Improvements

- Multi-dataset analysis
- Advanced filtering UI
- Dashboard generation
- Scheduled reports
- Cloud deployment
- User authentication
- Database-backed history
- Additional chart types
- Conversational memory

---

# 👨‍💻 Developer

## Harsh Chavan

Computer Engineering Student

Passionate about **Artificial Intelligence, Machine Learning, Data Analytics, SQL, Power BI, and Python Development**.

### GitHub

https://github.com/harsh8767

### LinkedIn

https://www.linkedin.com/in/harsh-chavan-1646a2257/

---

# 📜 License

This project is licensed under the MIT License.

Feel free to fork, modify, and extend the project for educational and personal use.
