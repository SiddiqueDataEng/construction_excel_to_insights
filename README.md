# Construction Excel to Insights

Construction finance and operations analytics for Satti Group projects. The
project cleans Excel source files, matches construction items to a canonical
item master, produces analysis CSVs, and serves the results through a
Streamlit dashboard.

## Live Dashboard

[Open the Satti Group Construction Dashboard](https://construction-insights-excel.streamlit.app)

## What It Does

- Normalizes dates, amounts, text, and source column names.
- Fuzzy-matches item descriptions and codes with `rapidfuzz`.
- Produces spend, labour, contractor, inventory, payment, cashflow, utility,
  vendor pricing, and discrepancy outputs.
- Preserves traceability through match audits and discrepancy flags.
- Provides an interactive Streamlit dashboard and construction cost estimator.

## Project Structure

| Path | Purpose |
| --- | --- |
| `dashboard.py` | Streamlit dashboard and cost estimator |
| `run_pipeline.py` | Runs cleaning, analysis, and Excel report generation |
| `step1_clean.py` | Cleans and normalizes source workbooks |
| `step2_match_analyze.py` | Matches items and creates analysis CSVs |
| `step3_report.py` | Builds `Satti_Group_Report.xlsx` |
| `analysis_output/` | Dashboard-ready CSV outputs |
| `cleaned_data/` | Normalized intermediate CSVs |
| `requirements.txt` | Python dependencies |

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Run the dashboard:

```bash
streamlit run dashboard.py
```

Run the data pipeline:

```bash
python run_pipeline.py
```

The pipeline expects raw workbooks in `satti_group_raw_data/` and writes
normalized data to `cleaned_data/`, analysis CSVs to `analysis_output/`, and
the Excel report to `Satti_Group_Report.xlsx`.

## Documentation

- [Dashboard Guide](DASHBOARD_GUIDE.md)
- [Current Analysis Report](ANALYSIS_REPORT.md)

## Dependencies

The project uses Python, pandas, NumPy, Plotly, Streamlit, RapidFuzz, and
openpyxl. Install the exact dependency set from `requirements.txt`.