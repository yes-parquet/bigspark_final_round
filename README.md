# BigSpark Interview Submission

This repository contains my submission for the final round interview at BigSpark. It demonstrates a comprehensive data approach by providing both a detailed research report and an interactive data product.

The project features:
1.  **Exploratory Data Analysis (EDA) Notebook**: A deep dive into data quality and statistical insights.
2.  **Streaming Dashboard**: A `Streamlit` application for interactive data exploration.

## Tools Used
- Antigravity: This code repo was made with the assistance of the Gemini models using Antigravity IDE (Human-assisted agentic mode).
- ChatGPT: For EDA insights and inspirations for the 'interestion' part of this project.
- **[Polars](https://pola.rs/)**: Used for rapid, memory-efficient data loading and cleaning.
- **[DuckDB](https://duckdb.org/)**: Leveraged for writing analytical SQL queries directly on top of Polars DataFrames.
- **Plotly Express / Seaborn**: Used for rendering professional-grade charts.
- **Streamlit**: Used to build the interactive web dashboard.

## Project Structure
```text
.
├── data/                                # Contains the 3 raw CSV datasets
├── eda/                                 # Jupyter Notebook for research and exploration
│   └── bigspark_eda.ipynb
├── dashboard/                           # Streamlit application source code
│   └── app.py
├── requirements.txt                     # List of Python dependencies
└── README.md                            # Project overview
```

## Getting Started

1. **Clone the repository.**
2. **Set up a virtual environment and install dependencies:**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

### Option 1: View the Research Report (Notebook)
Open the `eda/bigspark_eda.ipynb` file in your preferred notebook environment.

### Option 2: Run the Interactive Dashboard
```bash
streamlit run dashboard/app.py
```
The dashboard will open at `http://localhost:8501`.

## Key Findings Breakdown
- **NHS Appointments:** Identified trailing namespaces and mixed casing in names. Discovered that the majority of appointments are follow-ups and identified scheduling bottlenecks.
- **SaaS CRM:** Revealed inconsistencies in UK country names (`U.K.`, `UK`, `Scotland`, etc.). Analyzed billing issues against churn, identifying a strong correlation between `card_failed`/`overdue` statuses and `cancelled` subscriptions.
- **UK eCommerce Orders:** Highlighted missing `vat_rate` and `country_code` values. Aggregated order values against `suspected_fraud` and identified significant variations in maximum order values for flagged transactions.

### Advanced Operational Analytics (trying to make use of this data for real-life scenarios)
- **Statistical Anomaly Detection:** Instead of manual thresholds, established regional baselines and tracked dynamic rolling Z-Scores across `order_value` in the eCommerce dataset. Successfully isolated and flagged transactions falling outside `> 2.5` standard deviations from their country's mean.
- **SaaS Cohort Retention:** Moved beyond a blended 'Churn Rate' to build monthly `Signup Cohorts`, tracking and visualizing longitudinal retention drops correlated strictly to specific signup months.
- **Bayesian Conditional Probability (Healthcare):** Rather than simply counting NHS "no-shows", mathematically derived the conditional probability `P(No-show | Delay >= 30 mins)`. This conclusively isolated scheduling delays as a causal friction point increasing abandonment rates vs the global baseline.
