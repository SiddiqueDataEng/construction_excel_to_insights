"""
STEP 2 – Fuzzy Item Matching + Analysis
========================================
• Loads the cleaned CSVs from step 1
• Fuzzy-matches item codes/descriptions across all files to a canonical item master
• Builds analysis DataFrames:
    - project_costs       : total cost per project per category
    - vendor_spend        : spend per vendor per project
    - item_price_variances: same item, different prices across vendors → FLAG
    - labour_summary      : wages per project per month
    - contractor_payments : running bill totals per contractor per project
    - payment_status      : paid vs unpaid breakdown
    - monthly_cashflow    : combined in/out per month per project
• Saves all to  analysis_output/  as CSVs + a master Excel
• Also produces  analysis_output/discrepancy_flags.csv  (the "don't overwrite" list)
"""

import os
import re
import warnings
import pandas as pd
import numpy as np
from rapidfuzz import fuzz, process

warnings.filterwarnings("ignore")

CLEAN_DIR  = "cleaned_data"
OUT_DIR    = "analysis_output"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Canonical item master (source of truth) ────────────────────────────────────
CANONICAL_ITEMS = [
    ("STL-RB-12",  "12mm Steel Rebar",          "kg",    130),
    ("STL-RB-16",  "16mm Steel Rebar",          "kg",    140),
    ("CEM-OPC-50", "OPC Cement 50kg Bag",       "bag",   950),
    ("BRK-CLS-A",  "Class-A Red Brick",         "1000", 14000),
    ("AGG-CRS-34", "Coarse Aggregate 3/4 inch", "cft",    55),
    ("SND-RVR",    "River Sand",                "cft",    35),
    ("PIP-GI-1",   '1" GI Pipe',                "rft",  180),
    ("PIP-GI-2",   '2" GI Pipe',                "rft",  310),
    ("WIR-COP-7",  "7/0.029 Copper Wire",       "mtr",   95),
    ("WIR-COP-3",  "3/0.029 Copper Wire",       "mtr",   55),
    ("PLY-MR-12",  "12mm MR Plywood Sheet",     "sht", 2200),
    ("PAI-OIL-W",  "Oil Paint (White) 4Ltr",    "tin", 1800),
    ("TIL-CER-12", "Ceramic Floor Tile 12x12",  "sft",   85),
    ("SAN-WC-STD", "Standard WC/Commode",       "nos", 12500),
    ("GLS-CLR-6",  "6mm Clear Glass",           "sft",  220),
    ("ALM-WIN-4",  '4ft Aluminum Window',        "nos", 14500),
    ("GEN-25KVA",  "25 KVA Generator",          "nos", 950000),
    ("CBL-ARM-95", "95mm² Armoured Cable",      "mtr",  850),
    ("MRB-IMP-W",  "Imported White Marble",     "sft",  680),
    ("CNC-RDY-M20","M20 Ready Mix Concrete",    "cft",  420),
]

canon_df = pd.DataFrame(CANONICAL_ITEMS,
                         columns=["canon_code","canon_name","unit","std_rate"])
# All canonical tokens for fuzzy matching
canon_tokens = (canon_df["canon_code"] + " " + canon_df["canon_name"]).tolist()


# ── Fuzzy match one raw token → canonical row ──────────────────────────────────
def fuzzy_match_item(raw_code, raw_desc, threshold=72):
    """
    Returns (canon_code, canon_name, match_score) or (None,None,0).
    Tries code first (exact/partial), then falls back to description fuzzy.
    """
    raw_code = str(raw_code).strip().upper() if pd.notna(raw_code) else ""
    raw_desc = str(raw_desc).strip()        if pd.notna(raw_desc) else ""

    # 1. Try exact code match
    exact = canon_df[canon_df["canon_code"] == raw_code]
    if not exact.empty:
        row = exact.iloc[0]
        return row["canon_code"], row["canon_name"], 100

    # 2. Strip non-alphanumeric and retry
    raw_code_stripped = re.sub(r"[^A-Z0-9]", "", raw_code)
    for _, crow in canon_df.iterrows():
        if re.sub(r"[^A-Z0-9]", "", crow["canon_code"]) == raw_code_stripped and raw_code_stripped:
            return crow["canon_code"], crow["canon_name"], 95

    # 3. Fuzzy on combined code+desc vs canonical combined tokens
    combined_raw = f"{raw_code} {raw_desc}".strip()
    if not combined_raw:
        return None, None, 0

    match = process.extractOne(
        combined_raw, canon_tokens,
        scorer=fuzz.token_sort_ratio,
        score_cutoff=threshold
    )
    if match:
        matched_token, score, idx = match
        row = canon_df.iloc[idx]
        return row["canon_code"], row["canon_name"], score

    # 4. Try description alone with lower threshold
    match2 = process.extractOne(
        raw_desc, [r[1] for r in CANONICAL_ITEMS],
        scorer=fuzz.partial_ratio,
        score_cutoff=60
    )
    if match2:
        _, score, idx = match2
        row = canon_df.iloc[idx]
        return row["canon_code"], row["canon_name"], score

    return None, None, 0


# ── Load cleaned CSVs ──────────────────────────────────────────────────────────
def load_folder_csv(folder_name):
    path = os.path.join(CLEAN_DIR, f"{folder_name}_ALL.csv")
    if os.path.exists(path):
        try:
            return pd.read_csv(path, dtype=str, low_memory=False)
        except Exception as e:
            print(f"  WARNING: could not load {path}: {e}")
    return pd.DataFrame()


def to_float(series):
    return pd.to_numeric(series, errors="coerce")


# ══════════════════════════════════════════════════════════════════════════════
# ANALYSIS FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

discrepancy_flags = []   # accumulate all flags here


def flag(source_file, item_code, item_name, field, existing_val, new_val, note):
    discrepancy_flags.append({
        "source_file":  source_file,
        "item_code":    item_code,
        "item_name":    item_name,
        "field":        field,
        "existing_value": existing_val,
        "new_value":    new_val,
        "note":         note,
    })


# ── A. Purchase Bills analysis ─────────────────────────────────────────────────
def analyze_purchase_bills():
    print("  Analyzing purchase bills…")
    df = load_folder_csv("purchase_bills")
    # Fuzzy match items — load all three project bill CSVs
    all_bill_dfs = []
    for folder_name in os.listdir(CLEAN_DIR):
        if folder_name != "purchase_bills":
            continue
        folder_path = os.path.join(CLEAN_DIR, folder_name)
        if not os.path.isdir(folder_path):
            continue
        for fname in os.listdir(folder_path):
            if not fname.endswith(".csv"):
                continue
            try:
                fdf = pd.read_csv(os.path.join(folder_path, fname), dtype=str, low_memory=False)
                all_bill_dfs.append(fdf)
            except Exception:
                pass
    if all_bill_dfs:
        df = pd.concat(all_bill_dfs, ignore_index=True)
    
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Fuzzy match items
    results = []
    for _, row in df.iterrows():
        code  = row.get("item_code", "")
        desc  = row.get("description", "")
        canon_code, canon_name, score = fuzzy_match_item(code, desc)

        qty   = to_float(pd.Series([row.get("qty", "")])).iloc[0]
        rate  = to_float(pd.Series([row.get("rate", "")])).iloc[0]
        total = to_float(pd.Series([row.get("total", row.get("amount", ""))])).iloc[0]

        if pd.isna(total) and pd.notna(qty) and pd.notna(rate):
            total = qty * rate

        results.append({
            "project":       row.get("_project", "UNKNOWN"),
            "source_file":   row.get("_source_file", ""),
            "raw_code":      code,
            "raw_desc":      desc,
            "canon_code":    canon_code,
            "canon_name":    canon_name,
            "match_score":   score,
            "qty":           qty,
            "rate":          rate,
            "total":         total,
            "date":          row.get("date", ""),
            "vendor":        row.get("vendor", row.get("description", "")),
            "doc_no":        row.get("doc_no", ""),
            "matched":       canon_code is not None,
        })

    bills_df = pd.DataFrame(results)

    # Price variance flags: same canon item, rate differs >20% from std_rate
    merged = bills_df.merge(canon_df[["canon_code","std_rate"]], on="canon_code", how="left")
    merged["std_rate"] = pd.to_numeric(merged["std_rate"], errors="coerce")
    variance_mask = (
        merged["std_rate"].notna() &
        merged["rate"].notna() &
        (abs(merged["rate"] - merged["std_rate"]) / merged["std_rate"] > 0.20)
    )
    for _, r in merged[variance_mask].iterrows():
        flag(r["source_file"], r["canon_code"], r["canon_name"],
             "rate",
             r["std_rate"],
             r["rate"],
             f"Rate deviation {abs(r['rate']-r['std_rate'])/r['std_rate']*100:.1f}% from standard")

    # Project cost by canonical item
    cost_by_item = (bills_df[bills_df["matched"]]
                    .groupby(["project","canon_code","canon_name"])["total"]
                    .sum().reset_index()
                    .rename(columns={"total":"total_spend"}))
    cost_by_item["total_spend"] = cost_by_item["total_spend"].round(0)

    # Vendor spend
    # vendor column may be mixed with description – use source_file vendor hint
    vendor_col = bills_df.get("vendor", pd.Series(dtype=str)) if "vendor" in bills_df.columns else pd.Series(dtype=str)

    return bills_df, cost_by_item


# ── B. Payment Vouchers ────────────────────────────────────────────────────────
def analyze_payments():
    print("  Analyzing payment vouchers…")
    df = load_folder_csv("payment_vouchers")
    if df.empty:
        return pd.DataFrame()

    amount_col = next((c for c in ["amount","total","debit"] if c in df.columns), None)
    if amount_col:
        df["amount_clean"] = to_float(df[amount_col])
    else:
        df["amount_clean"] = np.nan

    status_col = next((c for c in ["remarks","status","payment_status"] if c in df.columns), None)
    if status_col:
        df["status_norm"] = df[status_col].str.strip().str.upper()
    else:
        df["status_norm"] = "UNKNOWN"

    df["status_norm"] = df["status_norm"].replace({
        "PAID": "PAID", "OK": "PAID", "VERIFIED": "PAID",
        "UNPAID": "UNPAID", "PENDING": "UNPAID",
        "PARTIAL": "PARTIAL",
        "": "UNKNOWN", "NAN": "UNKNOWN",
    })

    payment_summary = (df.groupby(["_project","status_norm"])["amount_clean"]
                         .agg(count="count", total="sum")
                         .reset_index())
    payment_summary["total"] = payment_summary["total"].round(0)

    return payment_summary


# ── C. Labour wages ────────────────────────────────────────────────────────────
def analyze_labour():
    print("  Analyzing labour wages…")
    df = load_folder_csv("labour_wages")
    if df.empty:
        return pd.DataFrame()

    net_col = next((c for c in ["total","net_pay","amount","net_payment"] if c in df.columns), None)
    if net_col:
        df["net_clean"] = to_float(df[net_col])
    else:
        df["net_clean"] = np.nan

    trade_col = next((c for c in ["trade","designation","category"] if c in df.columns), None)

    if trade_col:
        labour_by_trade = (df.groupby(["_project", trade_col])["net_clean"]
                             .agg(workers="count", total_wages="sum")
                             .reset_index()
                             .rename(columns={trade_col: "trade"}))
    else:
        labour_by_trade = (df.groupby(["_project"])["net_clean"]
                             .agg(workers="count", total_wages="sum")
                             .reset_index())
        labour_by_trade["trade"] = "All"

    labour_by_trade["total_wages"] = labour_by_trade["total_wages"].round(0)
    return labour_by_trade


# ── D. Contractor running bills ────────────────────────────────────────────────
def analyze_contractors():
    print("  Analyzing contractor running bills…")
    df = load_folder_csv("contractor_bills")
    if df.empty:
        return pd.DataFrame()

    amt_col = next((c for c in ["net_payable","total","amount","net_amt"] if c in df.columns), None)
    if amt_col:
        df["amt_clean"] = to_float(df[amt_col])
    else:
        df["amt_clean"] = np.nan

    # Extract contractor from filename
    def extract_contractor(src):
        for code in ["C001","C002","C003","C004","C005","C006","C007","C008"]:
            if code in str(src):
                return code
        return "UNKNOWN"

    df["contractor_code"] = df["_source_file"].apply(extract_contractor)

    contractor_map = {
        "C001": "Ahmad & Bros Construction",
        "C002": "Iqbal Electrical",
        "C003": "Rehman Plumbing",
        "C004": "Noor Finishing",
        "C005": "Baig Steel Fabricators",
        "C006": "Qamar Civil Engineers",
        "C007": "Bilal Tiles & Flooring",
        "C008": "Sultan HVAC",
    }
    df["contractor_name"] = df["contractor_code"].map(contractor_map).fillna("Unknown")

    contractor_summary = (df.groupby(["_project","contractor_code","contractor_name"])["amt_clean"]
                            .agg(num_bills="count", total_paid="sum")
                            .reset_index())
    contractor_summary["total_paid"] = contractor_summary["total_paid"].round(0)
    return contractor_summary


# ── E. Inventory analysis ──────────────────────────────────────────────────────
def analyze_inventory():
    print("  Analyzing inventory…")
    df = load_folder_csv("inventory")
    if df.empty:
        return pd.DataFrame()

    for col in ["opening_stock","received","issued","closing_stock"]:
        if col in df.columns:
            df[col] = to_float(df[col])

    # Fuzzy match items
    records = []
    for _, row in df.iterrows():
        code  = row.get("item_code", "")
        desc  = row.get("description", "")
        canon_code, canon_name, score = fuzzy_match_item(code, desc)
        records.append({
            "project":       row.get("_project","UNKNOWN"),
            "canon_code":    canon_code,
            "canon_name":    canon_name,
            "match_score":   score,
            "received":      row.get("received", np.nan),
            "issued":        row.get("issued",   np.nan),
            "closing_stock": row.get("closing_stock", np.nan),
        })

    inv_df = pd.DataFrame(records)
    inv_df = inv_df[inv_df["canon_code"].notna()]

    inv_summary = (inv_df.groupby(["project","canon_code","canon_name"])
                         .agg(total_received=("received","sum"),
                              total_issued  =("issued",  "sum"),
                              avg_closing   =("closing_stock","mean"))
                         .reset_index())
    for c in ["total_received","total_issued","avg_closing"]:
        inv_summary[c] = inv_summary[c].round(1)
    return inv_summary


# ── F. Vendor price list – price comparison across vendors ─────────────────────
def analyze_vendor_prices():
    print("  Analyzing vendor price lists…")
    df = load_folder_csv("vendor_price_lists")
    if df.empty:
        return pd.DataFrame()

    records = []
    for _, row in df.iterrows():
        code  = row.get("item_code", "")
        desc  = row.get("description", "")
        rate  = to_float(pd.Series([row.get("rate", row.get("amount", ""))])).iloc[0]
        vendor = row.get("vendor", row.get("_source_file",""))
        # Extract vendor name from filename: V001_Pak_Steel_Traders_PriceList.csv
        fn = str(row.get("_source_file",""))
        vm = re.search(r"V\d+_(.+)_PriceList", fn)
        vendor_clean = vm.group(1).replace("_"," ") if vm else vendor

        canon_code, canon_name, score = fuzzy_match_item(code, desc)
        if canon_code and pd.notna(rate):
            records.append({
                "vendor":      vendor_clean,
                "canon_code":  canon_code,
                "canon_name":  canon_name,
                "match_score": score,
                "quoted_rate": rate,
            })

    price_df = pd.DataFrame(records)
    if price_df.empty:
        return pd.DataFrame()

    # Pivot: items vs vendors
    pivot = (price_df.groupby(["canon_code","canon_name","vendor"])["quoted_rate"]
                     .mean().reset_index())

    # Merge with std_rate to show deviation
    pivot = pivot.merge(canon_df[["canon_code","std_rate"]], on="canon_code", how="left")
    pivot["pct_vs_std"] = ((pivot["quoted_rate"] - pivot["std_rate"])
                            / pivot["std_rate"] * 100).round(1)

    # Flag big deviations
    for _, r in pivot[abs(pivot["pct_vs_std"]) > 25].iterrows():
        flag(r["vendor"], r["canon_code"], r["canon_name"],
             "quoted_rate", r["std_rate"], r["quoted_rate"],
             f"Vendor quote {r['pct_vs_std']:+.1f}% vs standard")

    return pivot


# ── G. Bank statement cashflow ─────────────────────────────────────────────────
def analyze_bank():
    print("  Analyzing bank statements…")
    df = load_folder_csv("bank_statements")
    if df.empty:
        return pd.DataFrame()

    df["debit_clean"]  = to_float(df.get("debit",  pd.Series(dtype=str)))
    df["credit_clean"] = to_float(df.get("credit", pd.Series(dtype=str)))
    df["date_clean"]   = pd.to_datetime(df.get("date", pd.Series(dtype=str)),
                                         errors="coerce")
    df["year_month"]   = df["date_clean"].dt.to_period("M").astype(str)

    cashflow = (df.groupby("year_month")
                  .agg(total_debit =("debit_clean", "sum"),
                       total_credit=("credit_clean","sum"),
                       txn_count   =("debit_clean", "count"))
                  .reset_index())
    cashflow["net"] = (cashflow["total_credit"] - cashflow["total_debit"]).round(0)
    cashflow["total_debit"]  = cashflow["total_debit"].round(0)
    cashflow["total_credit"] = cashflow["total_credit"].round(0)
    return cashflow


# ── H. Utility bills ──────────────────────────────────────────────────────────
def analyze_utilities():
    print("  Analyzing utility bills…")
    df = load_folder_csv("utility_bills")
    if df.empty:
        return pd.DataFrame()

    total_col = next((c for c in ["total","amount","net_pay"] if c in df.columns), None)
    if total_col:
        df["total_clean"] = to_float(df[total_col])
    else:
        df["total_clean"] = np.nan

    # Extract utility type from filename
    def get_util(src):
        for u in ["IESCO","SNGPL","WASA"]:
            if u in str(src).upper():
                return u
        return "OTHER"

    df["utility"] = df["_source_file"].apply(get_util)

    util_summary = (df.groupby(["_project","utility"])["total_clean"]
                      .agg(months="count", total_paid="sum")
                      .reset_index())
    util_summary["total_paid"] = util_summary["total_paid"].round(0)
    return util_summary


# ── I. Item master conflict detection ─────────────────────────────────────────
def analyze_item_master_conflicts():
    print("  Checking item master conflicts…")
    df = load_folder_csv("item_masters")
    if df.empty:
        return pd.DataFrame()

    rate_col = next((c for c in ["rate","std_rate","unit_cost","price"] if c in df.columns), None)
    code_col = next((c for c in ["item_code","code","part_number"] if c in df.columns), None)
    desc_col = next((c for c in ["description","item_name","material"] if c in df.columns), None)

    records = []
    seen = {}   # canon_code → {rate, name, source}

    for _, row in df.iterrows():
        code  = row.get(code_col, "") if code_col else ""
        desc  = row.get(desc_col, "") if desc_col else ""
        rate_raw = row.get(rate_col, "") if rate_col else ""
        rate  = to_float(pd.Series([rate_raw])).iloc[0]
        src   = row.get("_source_file","")

        canon_code, canon_name, score = fuzzy_match_item(code, desc)
        if not canon_code:
            continue

        if canon_code in seen:
            prev = seen[canon_code]
            if pd.notna(rate) and pd.notna(prev["rate"]):
                diff_pct = abs(rate - prev["rate"]) / prev["rate"] * 100 if prev["rate"] else 0
                if diff_pct > 5:
                    flag(src, canon_code, canon_name,
                         "std_rate", prev["rate"], rate,
                         f"Item master conflict: {diff_pct:.1f}% rate difference "
                         f"between {prev['source']} and {src}")
                    records.append({
                        "canon_code":  canon_code,
                        "canon_name":  canon_name,
                        "source_a":    prev["source"],
                        "rate_a":      prev["rate"],
                        "source_b":    src,
                        "rate_b":      rate,
                        "diff_pct":    round(diff_pct, 1),
                    })
        else:
            seen[canon_code] = {"rate": rate, "source": src, "name": canon_name}

    conflict_df = pd.DataFrame(records)
    return conflict_df


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def run():
    print("\n=== STEP 2: Fuzzy Matching & Analysis ===\n")

    bills_df,    cost_by_item     = analyze_purchase_bills()
    payment_df                    = analyze_payments()
    labour_df                     = analyze_labour()
    contractor_df                 = analyze_contractors()
    inventory_df                  = analyze_inventory()
    vendor_price_df               = analyze_vendor_prices()
    cashflow_df                   = analyze_bank()
    utility_df                    = analyze_utilities()
    conflict_df                   = analyze_item_master_conflicts()

    # Save all analysis outputs
    outputs = {
        "cost_by_item":         cost_by_item,
        "payment_status":       payment_df,
        "labour_by_trade":      labour_df,
        "contractor_summary":   contractor_df,
        "inventory_summary":    inventory_df,
        "vendor_price_compare": vendor_price_df,
        "bank_cashflow":        cashflow_df,
        "utility_bills":        utility_df,
        "item_master_conflicts":conflict_df,
    }

    for name, df in outputs.items():
        if df is not None and not df.empty:
            df.to_csv(os.path.join(OUT_DIR, f"{name}.csv"), index=False)
            print(f"  ✓ {name}.csv  ({len(df)} rows)")

    # Discrepancy flags (the "don't overwrite" list)
    flags_df = pd.DataFrame(discrepancy_flags)
    flags_df.to_csv(os.path.join(OUT_DIR, "discrepancy_flags.csv"), index=False)
    print(f"\n  ✓ discrepancy_flags.csv  ({len(flags_df)} flags)")

    # Also save bills with fuzzy match info for traceability
    if bills_df is not None and not bills_df.empty:
        bills_df.to_csv(os.path.join(OUT_DIR, "bills_matched.csv"), index=False)
        matched_pct = bills_df["matched"].mean() * 100
        print(f"  ✓ bills_matched.csv  ({len(bills_df)} rows, {matched_pct:.1f}% items matched)")

    print("\nDone.\n")
    return outputs, flags_df


if __name__ == "__main__":
    run()
