# Current Analysis Report

Generated from the CSV files in `analysis_output/` on 2026-09-12.

## Executive Summary

The current outputs cover three projects: Satti Apartments, Satti Mall, and
Satti Plaza. The analysis contains material costs, contractor payments,
labour, inventory, payment status, vendor pricing, cashflow, and discrepancy
records.

| Metric | Current value |
| --- | ---: |
| Material spend in `cost_by_item.csv` | PKR 1,685,742,535 |
| Contractor payments in `contractor_summary.csv` | PKR 2,227,686,728 |
| Contractor bills | 889 |
| Labour wages | PKR 12,059,250 |
| Labour worker records | 549 |
| Discrepancy flags | 13 |
| Distinct flagged items | 3 |
| Inventory received | 40,419.9 units |
| Inventory issued | 26,316.0 units |
| Vendor-price comparison items | 19 |

## Payment Status

| Status | Records | Amount |
| --- | ---: | ---: |
| Paid | 13 | PKR 12,560,355 |
| Advance | 6 | PKR 8,240,987 |
| Need receipt | 5 | PKR 8,252,352 |

The `Need receipt` records should be reviewed before treating the related
payments as fully supported expenditure.

## Discrepancy Review

There are 13 discrepancy flags across three item codes. The sample includes
rate differences for coarse aggregate, copper wire, and 1-inch GI pipe. The
largest visible deviations in the current output are above 100 percent from
the standard rate for coarse aggregate.

These records are review signals. They should be checked against the original
bill, quantity, supplier quotation, delivery date, and approved rate before
any value is overwritten.

## Recommended Follow-up

1. Review the 13 discrepancy records against original purchase bills.
2. Collect supporting receipts for the five `NEED RECEIPT` records.
3. Investigate high-volume contractor payments and reconcile them with running
   bills and payment vouchers.
4. Compare vendor quotes for the 19 tracked canonical items before the next
   procurement cycle.
5. Refresh the pipeline after corrections and compare the new outputs with the
   current report.

## Source Files

This report is based on:

- `cost_by_item.csv`
- `contractor_summary.csv`
- `labour_by_trade.csv`
- `payment_status.csv`
- `discrepancy_flags.csv`
- `inventory_summary.csv`
- `vendor_price_compare.csv`

For interactive charts and project filtering, use the
[Streamlit dashboard](https://construction-insights-excel.streamlit.app).