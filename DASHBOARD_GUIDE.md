# Dashboard Guide

The live dashboard is available at
[construction-insights-excel.streamlit.app](https://construction-insights-excel.streamlit.app).

## Getting Started

1. Open the dashboard.
2. Use the sidebar to choose a view.
3. Select one or more projects under **Filter by Project**.
4. Use **Refresh Data** after replacing or regenerating analysis CSVs.

The dashboard reads CSV files from `analysis_output/`. It does not read raw
Excel files directly at page load.

## Navigation

| View | Use it for |
| --- | --- |
| Overview | Key totals, project summary, active alerts, and high-level charts |
| Cost & Spend | Material spend by project, item, and category |
| Project Comparison | Side-by-side project cost and operating comparisons |
| Contractors | Contractor bills, paid amounts, and contractor ranking |
| Labour | Labour wages, worker counts, and trade breakdowns |
| Inventory | Received, issued, and closing inventory quantities |
| Vendor & Pricing | Quoted rates compared with standard rates and price variance |
| Cashflow | Monthly bank inflows, outflows, and net position |
| Utilities | Utility bills by provider and project |
| Alerts & Flags | Discrepancies and item-master conflicts requiring review |
| Cost Estimator | Material, labour, and full-project budget estimates |

## Cost Estimator

The estimator has three tabs:

- **Material Estimator:** enter quantities for canonical materials.
- **Labour Estimator:** enter worker or trade assumptions.
- **Full Project Budget:** combine material and labour estimates into a budget.

Estimator values are based on the standard rates and historical data embedded
in the dashboard. They are planning estimates, not approved purchase orders.

## Data Refresh Workflow

```bash
python run_pipeline.py
streamlit run dashboard.py
```

After deployment, push the updated files to the connected repository and wait
for Streamlit Cloud to rebuild the app. If the old colors or values remain,
perform a hard browser refresh with `Ctrl+Shift+R`.

## Interpreting Alerts

- **Discrepancy flags** identify values that differ materially from the
  standard or preserved source value.
- **Need receipt** indicates a payment record that requires supporting proof.
- **Advance** identifies an advance payment status.
- Price variance should be reviewed alongside vendor, project, quantity, and
  date context before taking action.