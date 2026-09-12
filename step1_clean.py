"""
STEP 1 – Clean & Normalize
==========================
Reads every raw Excel file in satti_group_raw_data/, applies:
  • Date normalization  → ISO YYYY-MM-DD
  • Amount normalization → plain float (strips PKR, commas, /-, TBD, blanks)
  • Text normalization   → strip, title-case for names, upper for codes
  • Column-name normalization per file type
  • Flags any cell that was coerced/suspicious

Outputs:
  cleaned_data/  – one clean CSV per source file
  cleaned_data/cleaning_log.csv – what was changed and why
"""

import os
import re
import warnings
import pandas as pd
from datetime import datetime

warnings.filterwarnings("ignore")

RAW_DIR     = "satti_group_raw_data"
CLEAN_DIR   = "cleaned_data"
os.makedirs(CLEAN_DIR, exist_ok=True)

# ── Date parsing ───────────────────────────────────────────────────────────────
DATE_FMTS = [
    "%d/%m/%Y", "%m-%d-%Y", "%d-%b-%Y", "%Y/%m/%d",
    "%d.%m.%Y", "%B %d, %Y", "%d/%m/%y", "%Y-%m-%d",
    "%b-%Y",    "%m/%d/%Y",  "%d-%m-%Y",
]

def parse_date(val):
    if pd.isna(val) or str(val).strip() == "":
        return None, False
    s = str(val).strip()
    # Already a datetime object from openpyxl
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d"), False
    for fmt in DATE_FMTS:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d"), False
        except ValueError:
            pass
    # pandas fallback
    try:
        return pd.to_datetime(s, dayfirst=True).strftime("%Y-%m-%d"), False
    except Exception:
        return s, True   # could not parse → flag it

# ── Amount parsing ─────────────────────────────────────────────────────────────
def parse_amount(val):
    if pd.isna(val) or str(val).strip() in ("", "TBD", "-", "N/A", "n/a"):
        return None, True   # blank/TBD → flag
    if isinstance(val, (int, float)):
        return float(val), False
    s = str(val).strip()
    # Remove PKR, Rs., Rs , commas, /-, trailing spaces
    s = re.sub(r"(?i)pkr\s*", "", s)
    s = re.sub(r"(?i)rs\.?\s*", "", s)
    s = s.replace(",", "").replace("/-", "").replace(" ", "")
    s = s.replace("%", "")
    try:
        return float(s), False
    except ValueError:
        return None, True

# ── Text cleaning ──────────────────────────────────────────────────────────────
def clean_text(val):
    if pd.isna(val):
        return ""
    return str(val).strip()

def normalize_code(val):
    """Upper-case, remove spaces around hyphens."""
    s = clean_text(val).upper()
    s = re.sub(r"\s*-\s*", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s

# ── Column-name guesser ────────────────────────────────────────────────────────
# Maps any messy header variant → canonical name
HEADER_MAP = {
    # serial / index
    r"^(s\.?no\.?|sr\.?|#|no\.?)$": "row_no",
    # item/material code
    r"(item.?code|part.?no|part#|code|ref#)": "item_code",
    # description / name
    r"(description|particulars|material|item.?name|product.?name|item$)": "description",
    # unit
    r"(unit|uom|uom\b|nos/kg|unit\.?)": "unit",
    # quantity
    r"(qty|quantity|nos\.|attendance|days.?present|days$)": "qty",
    # rate / unit price
    r"(rate|unit.?cost|unit.?price|price|d\.?rate|rate\s*\(rs\))": "rate",
    # amount / subtotal
    r"(amount|sub.?total|ext\.?.?amount|gross.?wages|total.?rs)": "amount",
    # gst / tax
    r"(gst|tax|vat)": "gst",
    # total / net
    r"(^total$|net.?amt|net.?pay|net.?payable|net.?payment|grand.?total)": "total",
    # date fields
    r"(date$|bill.?date|invoice.?date|payment.?date|paid.?date)": "date",
    # vendor / payee
    r"(vendor|supplier|payee|paid.?to)": "vendor",
    # project
    r"(project)": "project",
    # invoice / voucher number
    r"(invoice|bill.?no|voucher.?no|pv.?no|inv.?no|vno|voucherno)": "doc_no",
    # remarks / notes
    r"(remarks|notes|note|remark|status|comment)": "remarks",
    # debit
    r"(debit|payment$|out$)": "debit",
    # credit
    r"(credit|receipt$|in$)": "credit",
    # balance
    r"(balance|bal\.)": "balance",
    # opening / closing
    r"(opening|op\..?bal|op\..?stock)": "opening_stock",
    r"(closing|cl\..?stock)": "closing_stock",
    # received / issued
    r"(received|purchases|in$)": "received",
    r"(issued|consumption|out$)": "issued",
    # name (people)
    r"(worker.?name|name|emp.?name)": "name",
    # trade / designation
    r"(trade|designation|category|title)": "trade",
    # advance / deduction
    r"(advance|adv\.)": "advance",
    # month
    r"(month)": "month",
}

def normalize_columns(cols):
    """Return list of canonical column names, keeping unknown ones as-is."""
    result = []
    for c in cols:
        c_clean = str(c).strip().lower()
        matched = False
        for pattern, canonical in HEADER_MAP.items():
            if re.search(pattern, c_clean):
                result.append(canonical)
                matched = True
                break
        if not matched:
            result.append(c_clean.replace(" ", "_"))
    # Deduplicate: if same canonical appears twice, suffix with _2, _3 ...
    seen = {}
    final = []
    for name in result:
        if name in seen:
            seen[name] += 1
            final.append(f"{name}_{seen[name]}")
        else:
            seen[name] = 1
            final.append(name)
    return final

# ── Column type detection ──────────────────────────────────────────────────────
AMOUNT_COLS  = {"rate","amount","gst","total","debit","credit","balance",
                "opening_stock","closing_stock","received","issued","advance",
                "net_pay","gross_wages","contract_value","this_bill","retention"}
DATE_COLS    = {"date","bill_date","payment_date","paid_date","due_date"}
CODE_COLS    = {"item_code","doc_no"}

def is_amount_col(name):
    return any(a in name for a in AMOUNT_COLS)

def is_date_col(name):
    return any(d in name for d in DATE_COLS) or name == "date"

# ── Skip rows detector ─────────────────────────────────────────────────────────
def find_header_row(df_raw):
    """
    Many files have 2-5 junk rows before the actual header.
    Heuristic: first row where >50% of cells are non-empty strings
    and at least one cell matches a known header keyword.
    """
    header_keywords = re.compile(
        r"(code|item|qty|rate|amount|date|vendor|description|unit|"
        r"material|part|invoice|voucher|balance|debit|credit|name|trade)", re.I)
    for i, row in df_raw.iterrows():
        non_empty = row.dropna()
        if len(non_empty) < 2:
            continue
        text_vals = [str(v) for v in non_empty if str(v).strip()]
        matches   = sum(1 for t in text_vals if header_keywords.search(t))
        if matches >= 2 and len(text_vals) >= 3:
            return i
    return 0

# ── Core file cleaner ──────────────────────────────────────────────────────────
cleaning_log = []   # list of dicts

def clean_file(src_path, rel_path):
    """Read one Excel file, find its header, clean all data, return clean DataFrame."""
    try:
        # Read with no header to let us find the header row ourselves
        df_raw = pd.read_excel(src_path, header=None, dtype=str)
    except Exception as e:
        cleaning_log.append({"file": rel_path, "issue": f"CANNOT READ: {e}",
                             "row": "", "col": "", "original": "", "cleaned": ""})
        return None

    header_row_idx = find_header_row(df_raw)
    headers_raw    = df_raw.iloc[header_row_idx].tolist()
    headers_clean  = normalize_columns(headers_raw)
    data           = df_raw.iloc[header_row_idx + 1:].copy()
    data.columns   = headers_clean

    # Drop rows that are entirely empty or are sub-header noise
    data.dropna(how="all", inplace=True)
    # Drop rows where every cell is blank after stripping
    data = data[data.apply(
        lambda r: any(str(v).strip() not in ("", "nan") for v in r), axis=1)]

    # Drop columns that are entirely blank after cleaning
    data = data.loc[:, data.apply(
        lambda c: any(str(v).strip() not in ("", "nan") for v in c), axis=0)]

    data.reset_index(drop=True, inplace=True)

    # ── Cell-level cleaning ────────────────────────────────────────────────────
    for col in data.columns:
        for idx in data.index:
            raw_val = data.at[idx, col]

            if is_date_col(col):
                cleaned, flagged = parse_date(raw_val)
                data.at[idx, col] = cleaned
                if flagged:
                    cleaning_log.append({
                        "file": rel_path, "issue": "UNPARSEABLE_DATE",
                        "row": idx, "col": col,
                        "original": raw_val, "cleaned": cleaned
                    })

            elif is_amount_col(col):
                cleaned, flagged = parse_amount(raw_val)
                data.at[idx, col] = cleaned
                if flagged and str(raw_val).strip() not in ("", "nan"):
                    cleaning_log.append({
                        "file": rel_path, "issue": "UNPARSEABLE_AMOUNT",
                        "row": idx, "col": col,
                        "original": raw_val, "cleaned": cleaned
                    })

            elif col in CODE_COLS:
                data.at[idx, col] = normalize_code(raw_val)

            else:
                data.at[idx, col] = clean_text(raw_val)

    # Add source metadata columns
    data["_source_file"] = rel_path
    parts = rel_path.replace("\\","/").split("/")
    data["_folder"]      = parts[0] if len(parts) > 1 else ""
    # Try to infer project from filename (check full path, not just first match)
    rel_upper = rel_path.upper().replace("\\","/")
    if "SATTI_APTS" in rel_upper or "SATTI_APT" in rel_upper or "_APTS_" in rel_upper:
        data["_project"] = "SATTI_APTS"
    elif "SATTI_PLAZA" in rel_upper or "_PLAZA_" in rel_upper or "_PLZ_" in rel_upper:
        data["_project"] = "SATTI_PLAZA"
    elif "SATTI_MALL" in rel_upper or "_MALL_" in rel_upper:
        data["_project"] = "SATTI_MALL"
    else:
        data["_project"] = "SATTI_MALL"  # default to Mall for unlabelled files

    return data


# ── Walk all raw files ─────────────────────────────────────────────────────────
def run():
    all_summaries = {}  # folder → list of DataFrames
    file_count = 0

    for folder_name in sorted(os.listdir(RAW_DIR)):
        folder_path = os.path.join(RAW_DIR, folder_name)
        if not os.path.isdir(folder_path):
            continue

        out_folder = os.path.join(CLEAN_DIR, folder_name)
        os.makedirs(out_folder, exist_ok=True)
        folder_dfs = []

        for fname in sorted(os.listdir(folder_path)):
            if not fname.endswith(".xlsx"):
                continue
            src  = os.path.join(folder_path, fname)
            rel  = os.path.join(folder_name, fname)
            df   = clean_file(src, rel)
            if df is None or df.empty:
                continue

            # Save individual clean CSV
            out_csv = os.path.join(out_folder, fname.replace(".xlsx", ".csv"))
            df.to_csv(out_csv, index=False)
            folder_dfs.append(df)
            file_count += 1

        # Combine all files in this folder into one master CSV
        if folder_dfs:
            try:
                combined = pd.concat(folder_dfs, ignore_index=True)
                combined.to_csv(os.path.join(CLEAN_DIR, f"{folder_name}_ALL.csv"), index=False)
                all_summaries[folder_name] = combined
            except Exception as e:
                print(f"  WARNING: could not combine {folder_name}: {e}")

    # Save cleaning log
    log_df = pd.DataFrame(cleaning_log)
    log_df.to_csv(os.path.join(CLEAN_DIR, "cleaning_log.csv"), index=False)

    print(f"  Cleaned {file_count} files → {CLEAN_DIR}/")
    print(f"  Cleaning log: {len(cleaning_log)} issues flagged")
    return all_summaries


if __name__ == "__main__":
    print("\n=== STEP 1: Cleaning & Normalizing ===\n")
    summaries = run()
    print("\nDone.\n")
