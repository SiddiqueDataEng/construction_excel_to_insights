"""
Satti Group – Live Construction Analytics Dashboard
====================================================
Run with:  streamlit run dashboard.py
"""

import os
import warnings
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

warnings.filterwarnings("ignore")

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Satti Group – Construction Dashboard",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Colour scheme ──────────────────────────────────────────────────────────────
BRAND      = "#12355B"
ACCENT     = "#007C83"
GREEN      = "#16803C"
AMBER      = "#B45309"
RED_C      = "#B42318"
TEXT       = "#172033"
MUTED      = "#526173"
LIGHT_BG   = "#F5F7FA"
PROJ_COLORS = {
    "SATTI_MALL":  "#12355B",
    "SATTI_PLAZA": "#007C83",
    "SATTI_APTS":  "#16803C",
}
PROJECT_LABELS = {
    "SATTI_MALL":  "Satti Mall (2006–08)",
    "SATTI_PLAZA": "Satti Plaza (2011–14)",
    "SATTI_APTS":  "Satti Apartments (2015–18)",
}
ANALYST_DIR = "analysis_output"

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Main background and base text */
[data-testid="stAppViewContainer"] {
    background: #F5F7FA;
    --text-color: #172033;
    --secondary-text-color: #526173;
    --background-color: #F5F7FA;
    --secondary-background-color: #FFFFFF;
    --primary-color: #007C83;
}
[data-testid="stAppViewContainer"] .main,
[data-testid="stAppViewContainer"] main,
[data-testid="stAppViewContainer"] .block-container { color: #172033 !important; }
[data-testid="stAppViewContainer"] main .stMarkdown,
[data-testid="stAppViewContainer"] main h1,
[data-testid="stAppViewContainer"] main h2,
[data-testid="stAppViewContainer"] main h3,
[data-testid="stAppViewContainer"] main p,
[data-testid="stAppViewContainer"] main label,
[data-testid="stAppViewContainer"] main [data-testid="stWidgetLabel"],
[data-testid="stAppViewContainer"] main [data-testid="stWidgetLabel"] * {
    color: #172033 !important;
}
[data-testid="stAppViewContainer"] main [role="tab"],
[data-testid="stAppViewContainer"] main [role="tab"] * {
    color: #526173 !important;
}
[data-testid="stAppViewContainer"] main [role="tab"][aria-selected="true"],
[data-testid="stAppViewContainer"] main [role="tab"][aria-selected="true"] * {
    color: #12355B !important;
}
[data-testid="stAppViewContainer"] main [data-testid="stTabs"] [data-baseweb="tab"],
[data-testid="stAppViewContainer"] main [data-testid="stTabs"] [data-baseweb="tab"] *,
[data-testid="stAppViewContainer"] main [data-testid="stTabs"] [role="tab"],
[data-testid="stAppViewContainer"] main [data-testid="stTabs"] [role="tab"] *,
[data-testid="stAppViewContainer"] main [data-baseweb="tab-list"] button,
[data-testid="stAppViewContainer"] main [data-baseweb="tab-list"] button * {
    color: #12355B !important;
    font-weight: 700 !important;
    opacity: 1 !important;
    background-color: transparent !important;
}
[data-testid="stAppViewContainer"] main [data-testid="stTabs"] [aria-selected="true"],
[data-testid="stAppViewContainer"] main [data-testid="stTabs"] [aria-selected="true"] *,
[data-testid="stAppViewContainer"] main [data-baseweb="tab-list"] button[aria-selected="true"],
[data-testid="stAppViewContainer"] main [data-baseweb="tab-list"] button[aria-selected="true"] * {
    color: #12355B !important;
    font-weight: 800 !important;
}
[data-testid="stAppViewContainer"] main [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    background-color: #12355B !important;
}
[data-testid="stAppViewContainer"] main [data-baseweb="tab-list"] [data-baseweb="tab-highlight"],
[data-testid="stAppViewContainer"] main [data-baseweb="tab-list"] button::after {
    background-color: #12355B !important;
    border-color: #12355B !important;
}
[data-testid="stAppViewContainer"] main input,
[data-testid="stAppViewContainer"] main textarea,
[data-testid="stAppViewContainer"] main [data-baseweb="input"],
[data-testid="stAppViewContainer"] main [data-baseweb="input"] input {
    color: #172033 !important;
    background: #FFFFFF !important;
    border-color: #9AAABD !important;
}
[data-testid="stAppViewContainer"] main [data-baseweb="input"] button {
    color: #12355B !important;
    background: #E8EEF5 !important;
    border-color: #9AAABD !important;
}
[data-testid="stAppViewContainer"] main [data-testid="stAlert"] {
    color: #172033 !important;
    background: #E8F2FB !important;
    border: 1px solid #A8C7E3 !important;
}
[data-testid="stAppViewContainer"] main [data-testid="stAlert"] p {
    color: #172033 !important;
}
.dashboard-hero h1,
.dashboard-hero p { color: #FFFFFF !important; }
[data-testid="stSidebar"]          { background: #12355B; }
[data-testid="stSidebar"] * { color: #ffffff !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label { color: #D9E7F5 !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div { background: #1B4772; border-color: #76A8CF; }
[data-testid="stSidebar"] [data-baseweb="select"] input { color: #ffffff !important; }
[data-testid="stSidebar"] [data-baseweb="tag"] { background: #007C83; }
[data-testid="stSidebar"] button { border-color: #76A8CF; }

/* KPI cards */
.kpi-card {
    background: white;
    border-radius: 12px;
    padding: 18px 20px 14px 20px;
    box-shadow: 0 2px 8px rgba(18,53,91,0.12);
    border: 1px solid #D6DEE8;
    border-left: 5px solid #007C83;
    margin-bottom: 2px;
}
.kpi-card.red   { border-left-color: #B42318; }
.kpi-card.green { border-left-color: #16803C; }
.kpi-card.amber { border-left-color: #B45309; }
.kpi-label  { font-size: 12px; color: #526173; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; }
.kpi-value  { font-size: 26px; color: #12355B; font-weight: 800; line-height: 1.2; }
.kpi-delta  { font-size: 12px; color: #526173; margin-top: 2px; }

/* Alert boxes */
.alert-red   { background:#FDECEC; border:1px solid #F3B5B1; border-left:4px solid #B42318; padding:10px 14px; border-radius:6px; color:#7A271A; font-size:13px; margin-bottom:6px;}
.alert-amber { background:#FFF4E5; border:1px solid #F2C78F; border-left:4px solid #B45309; padding:10px 14px; border-radius:6px; color:#713B12; font-size:13px; margin-bottom:6px;}
.alert-green { background:#EAF6EE; border:1px solid #A8D5B5; border-left:4px solid #16803C; padding:10px 14px; border-radius:6px; color:#14532D; font-size:13px; margin-bottom:6px;}

/* Section headers */
.section-header {
    font-size: 17px; font-weight: 700; color: #12355B;
    border-bottom: 2px solid #007C83; padding-bottom: 4px;
    margin-top: 10px; margin-bottom: 12px;
}
/* Tables */
.dataframe { font-size: 12px !important; }
[data-testid="stDataFrame"] { border: 1px solid #D6DEE8; }
.estimator-label {
    color: #172033 !important;
    font-size: 13px;
    font-weight: 700;
    line-height: 1.25;
    min-height: 34px;
    margin: 8px 0 5px 0;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=60)
def load():
    def csv(name, **kw):
        p = os.path.join(ANALYST_DIR, f"{name}.csv")
        return pd.read_csv(p, **kw) if os.path.exists(p) else pd.DataFrame()

    cost        = csv("cost_by_item")
    payments    = csv("payment_status")
    labour      = csv("labour_by_trade")
    contractors = csv("contractor_summary")
    inventory   = csv("inventory_summary")
    prices      = csv("vendor_price_compare")
    cashflow    = csv("bank_cashflow")
    utilities   = csv("utility_bills")
    flags       = csv("discrepancy_flags")
    conflicts   = csv("item_master_conflicts")
    bills       = csv("bills_matched")

    # Numeric coercion
    for df, cols in [
        (cost,        ["total_spend"]),
        (payments,    ["count","total"]),
        (labour,      ["workers","total_wages"]),
        (contractors, ["num_bills","total_paid"]),
        (inventory,   ["total_received","total_issued","avg_closing"]),
        (prices,      ["quoted_rate","std_rate","pct_vs_std"]),
        (cashflow,    ["total_debit","total_credit","net","txn_count"]),
        (utilities,   ["months","total_paid"]),
        (bills,       ["qty","rate","total","match_score"]),
        (conflicts,   ["rate_a","rate_b","diff_pct"]),
    ]:
        for c in cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

    # Normalise project col name (some have _project, some project)
    for df in [cost, payments, labour, contractors, inventory, utilities, bills]:
        if "_project" in df.columns and "project" not in df.columns:
            df.rename(columns={"_project": "project"}, inplace=True)

    # Pretty project labels
    def relabel(df):
        if "project" in df.columns:
            df["project_label"] = df["project"].map(PROJECT_LABELS).fillna(df["project"])
        return df

    for df in [cost, payments, labour, contractors, inventory, utilities, bills]:
        relabel(df)

    # Cashflow: parse period
    if not cashflow.empty and "year_month" in cashflow.columns:
        cashflow["period"] = pd.to_datetime(
            cashflow["year_month"].astype(str).str[:7], format="%Y-%m", errors="coerce"
        )

    return cost, payments, labour, contractors, inventory, prices, cashflow, utilities, flags, conflicts, bills


cost, payments, labour, contractors, inventory, prices, cashflow, utilities, flags, conflicts, bills = load()

# ── Canonical item list & std rates ───────────────────────────────────────────
STD_RATES = {
    "STL-RB-12": ("12mm Steel Rebar",      "kg",   130),
    "STL-RB-16": ("16mm Steel Rebar",      "kg",   140),
    "CEM-OPC-50":("OPC Cement 50kg Bag",   "bag",  950),
    "BRK-CLS-A": ("Class-A Red Brick",     "1000",14000),
    "AGG-CRS-34":("Coarse Aggregate 3/4",  "cft",   55),
    "SND-RVR":   ("River Sand",            "cft",   35),
    "PIP-GI-1":  ('1" GI Pipe',            "rft",  180),
    "PIP-GI-2":  ('2" GI Pipe',            "rft",  310),
    "WIR-COP-7": ("7/0.029 Copper Wire",   "mtr",   95),
    "WIR-COP-3": ("3/0.029 Copper Wire",   "mtr",   55),
    "PLY-MR-12": ("12mm MR Plywood",       "sht", 2200),
    "PAI-OIL-W": ("Oil Paint White 4L",    "tin", 1800),
    "TIL-CER-12":("Ceramic Tile 12x12",    "sft",   85),
    "SAN-WC-STD":("Standard WC/Commode",   "nos",12500),
    "GLS-CLR-6": ("6mm Clear Glass",       "sft",  220),
    "ALM-WIN-4": ('4ft Aluminum Window',   "nos",14500),
    "GEN-25KVA": ("25 KVA Generator",      "nos",950000),
    "CBL-ARM-95":("95mm² Armoured Cable",  "mtr",  850),
    "MRB-IMP-W": ("Imported White Marble", "sft",  680),
    "CNC-RDY-M20":("M20 Ready Mix Conc.",  "cft",  420),
}

ALL_PROJECTS = sorted(cost["project"].dropna().unique().tolist()) if not cost.empty else []

# ── Helper ─────────────────────────────────────────────────────────────────────
def pkr(n):
    if pd.isna(n): return "—"
    if n >= 1e7:   return f"PKR {n/1e7:.2f} Cr"
    if n >= 1e5:   return f"PKR {n/1e5:.1f} L"
    return f"PKR {n:,.0f}"

def kpi(label, value, delta=None, color="blue"):
    cls = {"blue":"", "red":"red", "green":"green", "amber":"amber"}[color]
    delta_html = f'<div class="kpi-delta">{delta}</div>' if delta else ""
    st.markdown(
        f'<div class="kpi-card {cls}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'{delta_html}'
        f'</div>', unsafe_allow_html=True
    )

def alert(msg, level="red"):
    st.markdown(f'<div class="alert-{level}">{msg}</div>', unsafe_allow_html=True)

def section(title):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)

def estimator_label(text):
    st.markdown(f'<div class="estimator-label">{text}</div>', unsafe_allow_html=True)

def chart_layout(fig, title="", height=380):
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=TEXT), x=0),
        height=height,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Segoe UI, Arial", size=12, color=TEXT),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(color=TEXT, size=11),
            bgcolor="rgba(255,255,255,0.92)",
        ),
        hoverlabel=dict(bgcolor=BRAND, font=dict(color="white", size=12)),
    )
    fig.update_xaxes(
        showgrid=False, zeroline=False,
        tickfont=dict(color=MUTED), title_font=dict(color=TEXT),
    )
    fig.update_yaxes(
        showgrid=True, gridcolor="#DCE3EB", zeroline=False,
        tickfont=dict(color=MUTED), title_font=dict(color=TEXT),
    )
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🏗️ Satti Group")
    st.markdown("**Construction Analytics**")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["🏠 Overview",
         "💰 Cost & Spend",
         "🏢 Project Comparison",
         "🔧 Contractors",
         "👷 Labour",
         "📦 Inventory",
         "🏷️ Vendor & Pricing",
         "🏦 Cashflow",
         "⚡ Utilities",
         "⚠️ Alerts & Flags",
         "🔮 Cost Estimator"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("**Filter by Project**")
    selected_projects = st.multiselect(
        "Projects",
        options=ALL_PROJECTS,
        default=ALL_PROJECTS,
        format_func=lambda x: PROJECT_LABELS.get(x, x),
        label_visibility="collapsed"
    )
    if not selected_projects:
        selected_projects = ALL_PROJECTS

    st.markdown("---")
    st.markdown('<div style="font-size:11px; color:#D9E7F5; margin-top:8px;">'
                '📊 Data: 405 raw Excel files<br>'
                '🔁 Pipeline: Clean → Match → Analyze<br>'
                '🧠 Fuzzy matching: rapidfuzz<br>'
                '⚠️ 13 discrepancy flags active</div>',
                unsafe_allow_html=True)

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# ── Filter helper ──────────────────────────────────────────────────────────────
def filt(df, col="project"):
    if df.empty or col not in df.columns:
        return df
    return df[df[col].isin(selected_projects)]

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 – OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Overview":
    st.markdown(f"""
    <div class='dashboard-hero' style='background:linear-gradient(90deg,{BRAND},{ACCENT});
         padding:22px 28px; border-radius:12px; margin-bottom:18px;'>
        <h1 style='color:white;margin:0;font-size:28px;'>
            🏗️ Satti Group – Construction Analytics Dashboard
        </h1>
        <p style='color:#D9E7F5;margin:6px 0 0 0;font-size:14px;'>
            Satti Mall (2006–08) &nbsp;|&nbsp; Satti Plaza (2011–14)
            &nbsp;|&nbsp; Satti Apartments (2015–18)
            &nbsp;&nbsp;·&nbsp;&nbsp; 100+ Residential & Commercial Units
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI row ────────────────────────────────────────────────────────────────
    cf = filt(cost)
    pf = filt(payments)
    lf = filt(labour)
    kf = filt(contractors)

    total_material  = cf["total_spend"].sum()
    paid_amt        = pf[pf["status_norm"].str.upper() == "PAID"]["total"].sum() if not pf.empty and "status_norm" in pf.columns else 0
    total_wages     = lf["total_wages"].sum()
    contractor_paid = kf["total_paid"].sum()
    n_flags         = len(flags)
    total_workers   = lf["workers"].sum()

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: kpi("Material Spend",    pkr(total_material),    "All projects combined")
    with c2: kpi("Payments Made",     pkr(paid_amt),          "Verified payments",      "green")
    with c3: kpi("Contractor Total",  pkr(contractor_paid),   "8 contractors",           "blue")
    with c4: kpi("Labour Wages",      pkr(total_wages),       f"{int(total_workers)} workers")
    with c5: kpi("Data Flags",        str(n_flags),           "Requires review",         "amber" if n_flags < 20 else "red")
    with c6: kpi("Projects",          "3",                    "Mall · Plaza · Apts")

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns([3, 2])

    # Project cost comparison bar
    with col_l:
        section("📊 Total Spend by Project")
        if not cf.empty:
            proj_sum = cf.groupby(["project","project_label"])["total_spend"].sum().reset_index()
            fig = px.bar(
                proj_sum, x="project_label", y="total_spend",
                color="project",
                color_discrete_map={k: v for k, v in PROJ_COLORS.items()},
                text_auto=".3s",
                labels={"total_spend": "PKR", "project_label": ""},
            )
            fig.update_traces(textposition="outside", textfont_size=12)
            chart_layout(fig, height=320)
            st.plotly_chart(fig, width='stretch')

    # Cost breakdown donut
    with col_r:
        section("🥧 Cost Category Mix")
        if not cf.empty:
            top_items = cf.groupby("canon_name")["total_spend"].sum().nlargest(8).reset_index()
            fig2 = px.pie(
                top_items, names="canon_name", values="total_spend",
                hole=0.5,
                color_discrete_sequence=px.colors.sequential.Blues_r,
            )
            fig2.update_traces(textposition="inside", textinfo="percent+label",
                               textfont_size=10)
            chart_layout(fig2, height=320)
            st.plotly_chart(fig2, width='stretch')

    col_a, col_b = st.columns(2)

    # Labour by project
    with col_a:
        section("👷 Labour Wages by Project")
        if not lf.empty:
            lab_sum = lf.groupby(["project","project_label"])["total_wages"].sum().reset_index()
            fig3 = px.bar(
                lab_sum, x="project_label", y="total_wages",
                color="project",
                color_discrete_map=PROJ_COLORS,
                text_auto=".3s",
                labels={"total_wages": "PKR", "project_label": ""},
            )
            chart_layout(fig3, height=280)
            st.plotly_chart(fig3, width='stretch')

    # Payment status
    with col_b:
        section("💳 Payment Status Distribution")
        if not pf.empty and "status_norm" in pf.columns:
            pay_sum = pf.groupby("status_norm")["total"].sum().reset_index()
            clr_map = {"PAID": GREEN, "UNPAID": RED_C, "PARTIAL": AMBER,
                       "ADVANCE": ACCENT, "UNKNOWN": "#9CA3AF",
                       "NEED RECEIPT": AMBER}
            fig4 = px.pie(
                pay_sum, names="status_norm", values="total",
                color="status_norm", color_discrete_map=clr_map,
                hole=0.4,
            )
            fig4.update_traces(textposition="inside", textinfo="percent+label")
            chart_layout(fig4, height=280)
            st.plotly_chart(fig4, width='stretch')

    # Active alerts summary
    section("⚠️ Active Alerts")
    a1, a2, a3 = st.columns(3)
    with a1:
        alert(f"🔴 <b>{n_flags} data discrepancy flags</b> detected across vendor quotes, "
              f"item master files and purchase bills. Review before finalising reports.", "red")
    with a2:
        n_conflicts = len(conflicts)
        alert(f"🟡 <b>{n_conflicts} item master conflict(s)</b> — same material coded differently "
              f"with >5% rate difference between source files. Do not overwrite existing values.", "amber")
    with a3:
        unmatched = bills[~bills["matched"].astype(str).str.lower().isin(["true","1"])].shape[0] if not bills.empty else 0
        alert(f"🟢 <b>{unmatched} unmatched bill line items</b> could not be mapped to canonical "
              f"item codes. Manual review may improve cost accuracy.", "green")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 – COST & SPEND
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💰 Cost & Spend":
    st.title("💰 Cost & Material Spend Analysis")

    cf = filt(cost)

    # Top items treemap
    section("🗺️ Material Spend Treemap")
    if not cf.empty:
        cf2 = cf.copy()
        cf2["project_label"] = cf2["project"].map(PROJECT_LABELS).fillna(cf2["project"])
        fig = px.treemap(
            cf2, path=["project_label","canon_name"],
            values="total_spend",
            color="total_spend",
            color_continuous_scale="Blues",
            hover_data={"total_spend": ":,.0f"},
        )
        fig.update_traces(textinfo="label+value+percent parent")
        fig.update_layout(height=450, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, width='stretch')

    col1, col2 = st.columns(2)

    with col1:
        section("📉 Top 10 Highest Cost Items")
        if not cf.empty:
            top10 = cf.groupby("canon_name")["total_spend"].sum().nlargest(10).reset_index()
            fig2 = px.bar(
                top10.sort_values("total_spend"),
                x="total_spend", y="canon_name", orientation="h",
                color="total_spend", color_continuous_scale="Blues",
                labels={"total_spend": "PKR", "canon_name": ""},
                text_auto=".3s",
            )
            fig2.update_traces(textposition="outside")
            chart_layout(fig2, height=380)
            st.plotly_chart(fig2, width='stretch')

    with col2:
        section("📊 Project-wise Item Breakdown")
        if not cf.empty:
            pivot_df = cf.groupby(["project_label","canon_name"])["total_spend"].sum().reset_index()
            fig3 = px.bar(
                pivot_df, x="canon_name", y="total_spend",
                color="project_label",
                barmode="group",
                labels={"total_spend": "PKR", "canon_name": "Item", "project_label": "Project"},
                color_discrete_sequence=[BRAND, ACCENT, GREEN],
            )
            fig3.update_xaxes(tickangle=-35, tickfont_size=9)
            chart_layout(fig3, height=380)
            st.plotly_chart(fig3, width='stretch')

    # Detailed table
    section("📋 Full Cost Breakdown Table")
    if not cf.empty:
        tbl = cf.groupby(["project_label","canon_code","canon_name"])["total_spend"] \
                .sum().reset_index().sort_values(["project_label","total_spend"], ascending=[True,False])
        tbl["total_spend"] = tbl["total_spend"].apply(lambda x: f"PKR {x:,.0f}")
        tbl.columns = ["Project","Item Code","Item Name","Total Spend"]

        # Compute % of project total
        raw_spend = cf.groupby(["project_label","canon_code","canon_name"])["total_spend"] \
                      .sum().reset_index().sort_values(["project_label","total_spend"], ascending=[True,False])
        proj_totals = raw_spend.groupby("project_label")["total_spend"].transform("sum")
        raw_spend["% Share"] = (raw_spend["total_spend"] / proj_totals * 100).round(1).astype(str) + "%"
        raw_spend["Total Spend"] = raw_spend["total_spend"].apply(lambda x: f"PKR {x:,.0f}")
        raw_spend = raw_spend.drop(columns=["total_spend"])
        raw_spend.columns = ["Project","Item Code","Item Name","% Share","Total Spend"]

        st.dataframe(raw_spend, width='stretch', height=400)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 – PROJECT COMPARISON
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏢 Project Comparison":
    st.title("🏢 Project Comparison")

    cf  = filt(cost)
    lf  = filt(labour)
    kf  = filt(contractors)
    uf  = filt(utilities)

    # Summary KPIs per project
    section("📊 Key Metrics per Project")
    proj_cost  = cf.groupby(["project","project_label"])["total_spend"].sum().reset_index()
    proj_wages = lf.groupby(["project","project_label"])["total_wages"].sum().reset_index() if not lf.empty else pd.DataFrame()
    proj_contr = kf.groupby(["project","project_label"])["total_paid"].sum().reset_index() if not kf.empty else pd.DataFrame()

    cols = st.columns(len(selected_projects))
    for i, proj in enumerate(selected_projects):
        label = PROJECT_LABELS.get(proj, proj)
        mat   = proj_cost[proj_cost["project"]==proj]["total_spend"].sum()
        wages = proj_wages[proj_wages["project"]==proj]["total_wages"].sum() if not proj_wages.empty else 0
        contr = proj_contr[proj_contr["project"]==proj]["total_paid"].sum() if not proj_contr.empty else 0
        with cols[i]:
            st.markdown(f"**{label}**")
            kpi("Materials",   pkr(mat))
            kpi("Labour",      pkr(wages))
            kpi("Contractors", pkr(contr))
            kpi("TOTAL",       pkr(mat + wages + contr), color="blue")

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)

    # Stacked bar: cost categories per project
    with col_l:
        section("📊 Cost Composition per Project")
        if not cf.empty:
            cat_proj = cf.groupby(["project_label","canon_name"])["total_spend"].sum().reset_index()
            # Take top 10 items only for clarity
            top_names = cf.groupby("canon_name")["total_spend"].sum().nlargest(10).index
            cat_proj  = cat_proj[cat_proj["canon_name"].isin(top_names)]
            fig = px.bar(
                cat_proj, x="project_label", y="total_spend",
                color="canon_name",
                barmode="stack",
                labels={"total_spend":"PKR","project_label":"","canon_name":"Item"},
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            chart_layout(fig, height=380)
            st.plotly_chart(fig, width='stretch')

    with col_r:
        section("📊 Labour Trade Mix per Project")
        if not lf.empty:
            fig2 = px.bar(
                lf, x="project_label", y="total_wages",
                color="trade", barmode="stack",
                labels={"total_wages":"PKR","project_label":"","trade":"Trade"},
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            chart_layout(fig2, height=380)
            st.plotly_chart(fig2, width='stretch')

    # Radar chart – project profile
    section("🕸️ Project Profile Radar")
    if not cf.empty and not lf.empty and not kf.empty:
        radar_rows = []
        for proj in selected_projects:
            label = PROJECT_LABELS.get(proj, proj)
            mat   = cf[cf["project"]==proj]["total_spend"].sum() / 1e6
            wages = lf[lf["project"]==proj]["total_wages"].sum() / 1e6 if not lf.empty else 0
            contr = kf[kf["project"]==proj]["total_paid"].sum() / 1e6 if not kf.empty else 0
            items = cf[cf["project"]==proj]["canon_name"].nunique()
            util  = uf[uf["project"]==proj]["total_paid"].sum() / 1e4 if not uf.empty else 0
            radar_rows.append({
                "Project": label,
                "Materials (M PKR)": mat,
                "Labour (M PKR)": wages,
                "Contractors (M PKR)": contr,
                "Item Variety": items,
                "Utilities (10K PKR)": util,
            })

        radar_df = pd.DataFrame(radar_rows)
        cats = ["Materials (M PKR)","Labour (M PKR)","Contractors (M PKR)","Item Variety","Utilities (10K PKR)"]
        fig3 = go.Figure()
        colors = [BRAND, ACCENT, GREEN]
        for i, row in radar_df.iterrows():
            vals = [row[c] for c in cats] + [row[cats[0]]]
            fig3.add_trace(go.Scatterpolar(
                r=vals, theta=cats + [cats[0]],
                fill="toself", name=row["Project"],
                line_color=colors[i % len(colors)],
                opacity=0.7,
            ))
        fig3.update_layout(
            polar=dict(radialaxis=dict(visible=True, showticklabels=False)),
            height=380, paper_bgcolor="white",
            legend=dict(orientation="h", y=-0.1),
            margin=dict(l=40, r=40, t=30, b=40),
        )
        st.plotly_chart(fig3, width='stretch')

    # Utility comparison
    section("⚡ Utility Costs Comparison")
    if not uf.empty:
        fig4 = px.bar(
            uf, x="project_label", y="total_paid",
            color="utility", barmode="group",
            labels={"total_paid":"PKR","project_label":"","utility":"Utility"},
            color_discrete_map={"IESCO": AMBER, "SNGPL": RED_C, "WASA": ACCENT},
        )
        chart_layout(fig4, height=300)
        st.plotly_chart(fig4, width='stretch')


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 – CONTRACTORS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔧 Contractors":
    st.title("🔧 Contractor Bills & Payments")

    kf = filt(contractors)

    if kf.empty:
        st.info("No contractor data for selected projects.")
    else:
        # KPI row
        total_c   = kf["total_paid"].sum()
        avg_bill  = kf["total_paid"].sum() / kf["num_bills"].sum() if kf["num_bills"].sum() else 0
        n_contrs  = kf["contractor_name"].nunique()

        c1, c2, c3 = st.columns(3)
        with c1: kpi("Total Contractor Spend", pkr(total_c))
        with c2: kpi("Avg Bill Value",          pkr(avg_bill))
        with c3: kpi("Active Contractors",      str(n_contrs))

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            section("💰 Contractor Spend – All Projects")
            contr_sum = kf.groupby("contractor_name")["total_paid"].sum().reset_index()
            contr_sum = contr_sum.sort_values("total_paid", ascending=True)
            fig = px.bar(
                contr_sum, x="total_paid", y="contractor_name",
                orientation="h",
                color="total_paid",
                color_continuous_scale="Blues",
                text_auto=".3s",
                labels={"total_paid": "PKR", "contractor_name": ""},
            )
            fig.update_traces(textposition="outside")
            chart_layout(fig, height=380)
            st.plotly_chart(fig, width='stretch')

        with col2:
            section("📊 Bills Count vs Amount per Contractor")
            fig2 = px.scatter(
                kf, x="num_bills", y="total_paid",
                size="total_paid", color="project_label",
                hover_name="contractor_name",
                labels={"num_bills": "Number of Bills", "total_paid": "Total Paid (PKR)",
                        "project_label": "Project"},
                color_discrete_map={v: c for v, c in zip(PROJECT_LABELS.values(), [BRAND, ACCENT, GREEN])},
            )
            chart_layout(fig2, height=380)
            st.plotly_chart(fig2, width='stretch')

        section("📊 Contractor Spend by Project (Grouped)")
        fig3 = px.bar(
            kf, x="contractor_name", y="total_paid",
            color="project_label", barmode="group",
            text_auto=".3s",
            labels={"total_paid": "PKR", "contractor_name": "Contractor", "project_label": "Project"},
            color_discrete_sequence=[BRAND, ACCENT, GREEN],
        )
        fig3.update_xaxes(tickangle=-20, tickfont_size=11)
        chart_layout(fig3, height=350)
        st.plotly_chart(fig3, width='stretch')

        section("📋 Contractor Details Table")
        disp = kf[["project_label","contractor_code","contractor_name","num_bills","total_paid"]].copy()
        disp["Avg per Bill"] = (disp["total_paid"] / disp["num_bills"]).round(0)
        disp["total_paid"]   = disp["total_paid"].apply(lambda x: f"PKR {x:,.0f}")
        disp["Avg per Bill"] = disp["Avg per Bill"].apply(lambda x: f"PKR {x:,.0f}")
        disp.columns = ["Project","Code","Contractor","Bills","Total Paid","Avg per Bill"]
        st.dataframe(disp, width='stretch')


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 – LABOUR
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👷 Labour":
    st.title("👷 Labour & Workforce Analytics")

    lf = filt(labour)

    if lf.empty:
        st.info("No labour data.")
    else:
        total_wages   = lf["total_wages"].sum()
        total_workers = lf["workers"].sum()
        avg_wage      = total_wages / total_workers if total_workers else 0

        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi("Total Wages Paid",   pkr(total_wages))
        with c2: kpi("Total Worker Count", f"{int(total_workers):,}")
        with c3: kpi("Avg Wage per Worker",pkr(avg_wage))
        with c4: kpi("Trade Categories",   str(lf["trade"].nunique()))

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            section("💰 Wages by Trade")
            trade_sum = lf.groupby("trade")[["total_wages","workers"]].sum().reset_index()
            trade_sum = trade_sum.sort_values("total_wages", ascending=True)
            fig = px.bar(
                trade_sum, x="total_wages", y="trade",
                orientation="h",
                color="total_wages",
                color_continuous_scale="Blues",
                text_auto=".3s",
                labels={"total_wages":"PKR","trade":""},
            )
            fig.update_traces(textposition="outside")
            chart_layout(fig, height=380)
            st.plotly_chart(fig, width='stretch')

        with col2:
            section("👥 Worker Count by Trade")
            fig2 = px.pie(
                trade_sum, names="trade", values="workers",
                color_discrete_sequence=px.colors.qualitative.Set2,
                hole=0.4,
            )
            fig2.update_traces(textposition="inside", textinfo="percent+label", textfont_size=10)
            chart_layout(fig2, height=380)
            st.plotly_chart(fig2, width='stretch')

        section("📊 Wages Comparison: Trade × Project")
        fig3 = px.bar(
            lf, x="trade", y="total_wages",
            color="project_label", barmode="group",
            labels={"total_wages":"PKR","trade":"Trade","project_label":"Project"},
            color_discrete_sequence=[BRAND, ACCENT, GREEN],
        )
        fig3.update_xaxes(tickangle=-15)
        chart_layout(fig3, height=340)
        st.plotly_chart(fig3, width='stretch')

        section("📊 Average Daily Rate vs Worker Count (Bubble)")
        lf2 = lf.copy()
        lf2["avg_wage_per_worker"] = lf2["total_wages"] / lf2["workers"].replace(0, np.nan)
        fig4 = px.scatter(
            lf2, x="trade", y="avg_wage_per_worker",
            size="workers", color="project_label",
            labels={"avg_wage_per_worker":"Avg Wage/Worker (PKR)","trade":"Trade","project_label":"Project"},
            color_discrete_map={v: c for v, c in zip(PROJECT_LABELS.values(), [BRAND, ACCENT, GREEN])},
        )
        chart_layout(fig4, height=320)
        st.plotly_chart(fig4, width='stretch')

        section("📋 Labour Summary Table")
        lf3 = lf.copy()
        lf3["avg_per_worker"] = (lf3["total_wages"] / lf3["workers"].replace(0,np.nan)).round(0)
        lf3["total_wages"]    = lf3["total_wages"].apply(lambda x: f"PKR {x:,.0f}")
        lf3["avg_per_worker"] = lf3["avg_per_worker"].apply(lambda x: f"PKR {x:,.0f}" if pd.notna(x) else "—")
        lf3 = lf3[["project_label","trade","workers","total_wages","avg_per_worker"]]
        lf3.columns = ["Project","Trade","Workers","Total Wages","Avg Wage/Worker"]
        st.dataframe(lf3, width='stretch')


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6 – INVENTORY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📦 Inventory":
    st.title("📦 Site Inventory & Stock Management")

    inv = filt(inventory)

    if inv.empty:
        st.info("No inventory data.")
    else:
        total_rec  = inv["total_received"].sum()
        total_iss  = inv["total_issued"].sum()
        surplus    = inv[inv["avg_closing"] > 50].shape[0]
        low_stock  = inv[inv["avg_closing"] < 5].shape[0]

        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi("Total Received",  f"{total_rec:,.0f} units")
        with c2: kpi("Total Issued",    f"{total_iss:,.0f} units")
        with c3: kpi("Surplus Items",   str(surplus),  color="amber")
        with c4: kpi("Low Stock Items", str(low_stock), color="red")

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            section("📊 Received vs Issued by Item")
            inv_melt = inv.groupby("canon_name")[["total_received","total_issued"]].sum().reset_index()
            inv_melt = pd.melt(inv_melt, id_vars="canon_name",
                               value_vars=["total_received","total_issued"],
                               var_name="Type", value_name="Quantity")
            inv_melt["Type"] = inv_melt["Type"].map(
                {"total_received": "Received", "total_issued": "Issued"})
            fig = px.bar(
                inv_melt, x="canon_name", y="Quantity",
                color="Type", barmode="group",
                color_discrete_map={"Received": ACCENT, "Issued": GREEN},
                labels={"canon_name": ""},
            )
            fig.update_xaxes(tickangle=-35, tickfont_size=9)
            chart_layout(fig, height=380)
            st.plotly_chart(fig, width='stretch')

        with col2:
            section("📊 Avg Closing Stock Heatmap")
            inv_pivot = inv.groupby(["canon_name","project_label"])["avg_closing"].mean().unstack(fill_value=0)
            fig2 = px.imshow(
                inv_pivot,
                color_continuous_scale="Blues",
                aspect="auto",
                labels=dict(x="Project", y="Item", color="Avg Stock"),
            )
            fig2.update_layout(height=380, margin=dict(l=0,r=0,t=30,b=0))
            st.plotly_chart(fig2, width='stretch')

        # Stock efficiency waterfall
        section("📉 Stock Utilisation Rate by Item")
        inv_eff = inv.groupby("canon_name")[["total_received","total_issued"]].sum().reset_index()
        inv_eff = inv_eff[inv_eff["total_received"] > 0].copy()
        inv_eff["utilisation_pct"] = (inv_eff["total_issued"] / inv_eff["total_received"] * 100).round(1)
        inv_eff = inv_eff.sort_values("utilisation_pct", ascending=True)
        fig3 = px.bar(
            inv_eff, x="utilisation_pct", y="canon_name",
            orientation="h",
            color="utilisation_pct",
            color_continuous_scale=["red","orange","green"],
            labels={"utilisation_pct": "% Used", "canon_name": ""},
            text_auto=True,
        )
        fig3.add_vline(x=80, line_dash="dash", line_color="gray",
                       annotation_text="80% target", annotation_position="top right")
        chart_layout(fig3, height=420)
        st.plotly_chart(fig3, width='stretch')

        # Alerts
        section("🚨 Stock Alerts")
        low = inv[inv["avg_closing"] < 5][["project_label","canon_name","avg_closing"]]
        if not low.empty:
            for _, r in low.iterrows():
                alert(f"🔴 Low stock: <b>{r['canon_name']}</b> [{r['project_label']}] — avg closing: {r['avg_closing']:.1f} units", "red")
        surplus_items = inv[inv["avg_closing"] > 100][["project_label","canon_name","avg_closing"]]
        if not surplus_items.empty:
            for _, r in surplus_items.iterrows():
                alert(f"🟡 Surplus: <b>{r['canon_name']}</b> [{r['project_label']}] — avg closing: {r['avg_closing']:.1f} units", "amber")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 7 – VENDOR & PRICING
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏷️ Vendor & Pricing":
    st.title("🏷️ Vendor Quotes & Price Analysis")

    vp = prices.copy()

    if vp.empty:
        st.info("No vendor price data.")
    else:
        # KPI
        overpriced = (vp["pct_vs_std"] > 25).sum()
        underpriced= (vp["pct_vs_std"] < -25).sum()
        acceptable = (vp["pct_vs_std"].abs() <= 10).sum()

        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi("Total Vendor Quotes", str(len(vp)))
        with c2: kpi("Acceptable (<±10%)",  str(acceptable), color="green")
        with c3: kpi("Overpriced (>+25%)",  str(overpriced), color="red")
        with c4: kpi("Underpriced (<-25%)",  str(underpriced), color="amber")

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            section("📊 Price Deviation from Standard (%)")
            vp_sorted = vp.sort_values("pct_vs_std")
            vp_sorted["color"] = vp_sorted["pct_vs_std"].apply(
                lambda x: "Overpriced" if x > 25 else ("Underpriced" if x < -25 else "Acceptable")
            )
            fig = px.bar(
                vp_sorted.head(30), x="pct_vs_std", y="canon_name",
                color="color",
                orientation="h",
                color_discrete_map={"Overpriced": RED_C, "Underpriced": AMBER, "Acceptable": GREEN},
                labels={"pct_vs_std": "% vs Standard", "canon_name": ""},
                hover_data=["vendor","quoted_rate","std_rate"],
            )
            fig.add_vline(x=0, line_color="gray", line_dash="dash")
            fig.add_vline(x=25, line_color=RED_C, line_dash="dot", annotation_text="+25%")
            fig.add_vline(x=-25, line_color=AMBER, line_dash="dot", annotation_text="-25%")
            chart_layout(fig, height=420)
            st.plotly_chart(fig, width='stretch')

        with col2:
            section("📊 Vendor Price Scatter: Quoted vs Standard")
            fig2 = px.scatter(
                vp, x="std_rate", y="quoted_rate",
                color="canon_name",
                size=vp["pct_vs_std"].abs().fillna(1) + 1,
                hover_data=["vendor","pct_vs_std"],
                labels={"std_rate":"Standard Rate","quoted_rate":"Quoted Rate"},
                color_discrete_sequence=px.colors.qualitative.Plotly,
            )
            # Add y=x line
            max_val = max(vp["std_rate"].max(), vp["quoted_rate"].max())
            fig2.add_trace(go.Scatter(x=[0,max_val], y=[0,max_val],
                                       mode="lines", line=dict(color="gray",dash="dash"),
                                       name="Parity line", showlegend=True))
            chart_layout(fig2, height=420)
            st.plotly_chart(fig2, width='stretch')

        # Item selector for vendor comparison
        section("🔍 Vendor Rate Comparison for Selected Item")
        item_options = sorted(vp["canon_name"].unique().tolist())
        sel_item = st.selectbox("Select Material", item_options)
        item_df  = vp[vp["canon_name"] == sel_item].copy()
        std_r    = item_df["std_rate"].iloc[0] if not item_df.empty else None

        if not item_df.empty:
            c_left, c_right = st.columns([2, 1])
            with c_left:
                item_df = item_df.sort_values("quoted_rate")
                item_df["assessment"] = item_df["pct_vs_std"].apply(
                    lambda x: "✓ Best" if x == item_df["pct_vs_std"].min()
                    else ("✗ High" if x > 25 else "✓ OK")
                )
                fig3 = px.bar(
                    item_df, x="vendor", y="quoted_rate",
                    color="pct_vs_std",
                    color_continuous_scale="RdYlGn_r",
                    text_auto=".0f",
                    labels={"quoted_rate":"PKR","vendor":"Vendor"},
                    hover_data=["pct_vs_std","assessment"],
                )
                if std_r:
                    fig3.add_hline(y=std_r, line_dash="dash", line_color=BRAND,
                                   annotation_text=f"Std Rate: PKR {std_r:,.0f}")
                fig3.update_xaxes(tickangle=-25)
                chart_layout(fig3, height=340)
                st.plotly_chart(fig3, width='stretch')
            with c_right:
                st.markdown("**Recommended Vendor**")
                best = item_df.loc[item_df["quoted_rate"].idxmin()]
                st.success(f"✅ **{best['vendor']}**\nRate: PKR {best['quoted_rate']:,.0f}\n"
                           f"vs Std: {best['pct_vs_std']:+.1f}%")
                st.markdown("**All Quotes**")
                disp = item_df[["vendor","quoted_rate","pct_vs_std"]].copy()
                disp.columns = ["Vendor","Rate (PKR)","vs Std (%)"]
                st.dataframe(disp.reset_index(drop=True), width='stretch')


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 8 – CASHFLOW
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏦 Cashflow":
    st.title("🏦 Bank Cashflow Analysis")

    cf = cashflow.copy()

    if cf.empty:
        st.info("No cashflow data.")
    else:
        cf = cf.dropna(subset=["period"])
        cf = cf.sort_values("period")

        total_out = cf["total_debit"].sum()
        total_in  = cf["total_credit"].sum()
        net_pos   = cf["net"].sum()
        peak_out  = cf["total_debit"].max()

        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi("Total Outflow",  pkr(total_out), color="red")
        with c2: kpi("Total Inflow",   pkr(total_in),  color="green")
        with c3: kpi("Net Position",   pkr(net_pos),   color="green" if net_pos >= 0 else "red")
        with c4: kpi("Peak Month Out", pkr(peak_out),  color="amber")

        st.markdown("<br>", unsafe_allow_html=True)

        # Area chart – cashflow over time
        section("📈 Monthly Cashflow Over Time")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=cf["period"], y=cf["total_credit"],
            fill="tozeroy", name="Inflow",
            line=dict(color=GREEN, width=2),
            fillcolor="rgba(0,176,80,0.15)",
        ))
        fig.add_trace(go.Scatter(
            x=cf["period"], y=-cf["total_debit"],
            fill="tozeroy", name="Outflow",
            line=dict(color=RED_C, width=2),
            fillcolor="rgba(192,0,0,0.15)",
        ))
        fig.add_trace(go.Scatter(
            x=cf["period"], y=cf["net"],
            name="Net", line=dict(color=BRAND, width=2.5, dash="dash"),
        ))
        fig.add_hline(y=0, line_color="gray", line_dash="dot")
        chart_layout(fig, "Monthly Bank Cashflow (PKR)", height=420)
        st.plotly_chart(fig, width='stretch')

        col1, col2 = st.columns(2)

        with col1:
            section("📊 Top 10 Highest Outflow Months")
            top10_out = cf.nlargest(10, "total_debit")[["period","total_debit","total_credit","net"]]
            top10_out["period"] = top10_out["period"].dt.strftime("%b-%Y")
            top10_out.columns = ["Month","Outflow","Inflow","Net"]
            for c2_ in ["Outflow","Inflow","Net"]:
                top10_out[c2_] = top10_out[c2_].apply(lambda x: f"PKR {x:,.0f}")
            st.dataframe(top10_out.reset_index(drop=True), width='stretch')

        with col2:
            section("📊 Annual Cashflow Summary")
            cf["year"] = cf["period"].dt.year
            annual = cf.groupby("year")[["total_debit","total_credit","net"]].sum().reset_index()
            fig2 = px.bar(
                annual, x="year", y=["total_debit","total_credit"],
                barmode="group",
                labels={"value":"PKR","year":"Year","variable":"Type"},
                color_discrete_map={"total_debit":RED_C,"total_credit":GREEN},
            )
            fig2.update_xaxes(type="category")
            chart_layout(fig2, height=320)
            st.plotly_chart(fig2, width='stretch')

        # Rolling average
        section("📉 3-Month Rolling Average Net Position")
        cf["rolling_net"] = cf["net"].rolling(3, min_periods=1).mean()
        fig3 = px.line(
            cf, x="period", y="rolling_net",
            labels={"rolling_net":"3M Avg Net (PKR)","period":""},
            color_discrete_sequence=[ACCENT],
        )
        fig3.add_hline(y=0, line_color="red", line_dash="dash")
        fig3.update_traces(line_width=2.5)
        chart_layout(fig3, height=280)
        st.plotly_chart(fig3, width='stretch')


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 9 – UTILITIES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚡ Utilities":
    st.title("⚡ Utility Bills – IESCO / SNGPL / WASA")

    uf = filt(utilities)

    if uf.empty:
        st.info("No utility data.")
    else:
        total_util = uf["total_paid"].sum()
        avg_monthly = (uf["total_paid"] / uf["months"].replace(0, np.nan)).mean()

        c1, c2, c3 = st.columns(3)
        with c1: kpi("Total Utility Spend", pkr(total_util))
        with c2: kpi("Avg Monthly Bill",    pkr(avg_monthly))
        with c3: kpi("Utility Types",       str(uf["utility"].nunique()))

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            section("📊 Utility Spend by Type")
            util_type = uf.groupby("utility")["total_paid"].sum().reset_index()
            fig = px.pie(
                util_type, names="utility", values="total_paid",
                color="utility",
                color_discrete_map={"IESCO": AMBER, "SNGPL": RED_C, "WASA": ACCENT},
                hole=0.4,
            )
            fig.update_traces(textinfo="percent+label+value", textfont_size=11)
            chart_layout(fig, height=320)
            st.plotly_chart(fig, width='stretch')

        with col2:
            section("📊 Utility Costs per Project")
            fig2 = px.bar(
                uf, x="utility", y="total_paid",
                color="project_label", barmode="group",
                labels={"total_paid":"PKR","utility":"Utility","project_label":"Project"},
                color_discrete_sequence=[BRAND, ACCENT, GREEN],
            )
            chart_layout(fig2, height=320)
            st.plotly_chart(fig2, width='stretch')

        section("📋 Utility Details")
        ud = uf.copy()
        ud["avg_monthly"] = (ud["total_paid"] / ud["months"].replace(0,np.nan)).round(0)
        ud["total_paid"]  = ud["total_paid"].apply(lambda x: f"PKR {x:,.0f}")
        ud["avg_monthly"] = ud["avg_monthly"].apply(lambda x: f"PKR {x:,.0f}" if pd.notna(x) else "—")
        ud = ud[["project_label","utility","months","total_paid","avg_monthly"]]
        ud.columns = ["Project","Utility","Months","Total Paid","Avg/Month"]
        st.dataframe(ud.reset_index(drop=True), width='stretch')


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 10 – ALERTS & FLAGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚠️ Alerts & Flags":
    st.title("⚠️ Alerts, Discrepancies & Data Quality")

    # Summary KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Total Flags",       str(len(flags)),     color="red")
    with c2: kpi("Item Conflicts",    str(len(conflicts)), color="amber")
    with c3:
        price_flags = flags[flags["field"]=="rate"].shape[0] if not flags.empty else 0
        kpi("Price Deviations", str(price_flags), color="amber")
    with c4:
        master_flags = flags[flags["field"]=="std_rate"].shape[0] if not flags.empty else 0
        kpi("Master Conflicts", str(master_flags), color="red")

    st.markdown("<br>", unsafe_allow_html=True)

    # Discrepancy flags
    section("🔴 Discrepancy Log – Review Required (Do NOT Overwrite)")
    if not flags.empty:
        for _, r in flags.iterrows():
            existing = r.get("existing_value","")
            new_val  = r.get("new_value","")
            try:
                ev = float(existing); nv = float(new_val)
                diff = abs(nv - ev) / ev * 100 if ev else 0
                sev  = "red" if diff > 25 else "amber"
                alert(
                    f"<b>{r.get('item_name','')}</b> [{r.get('item_code','')}] — "
                    f"<b>{r.get('field','').upper()}</b>: "
                    f"existing <code>{ev:,.0f}</code> → new <code>{nv:,.0f}</code> "
                    f"({diff:+.1f}%)  <i>{r.get('note','')}</i><br>"
                    f"<small>Source: {r.get('source_file','')}</small>",
                    sev
                )
            except Exception:
                alert(
                    f"<b>{r.get('item_name','')}</b> — {r.get('note','')} "
                    f"[{r.get('source_file','')}]", "amber"
                )
    else:
        alert("✅ No discrepancy flags found.", "green")

    # Item master conflicts
    section("🟡 Item Master Conflicts")
    if not conflicts.empty:
        for _, r in conflicts.iterrows():
            diff = r.get("diff_pct", 0)
            alert(
                f"<b>{r.get('canon_name','')}</b> [{r.get('canon_code','')}] — "
                f"Rate in <code>{r.get('source_a','')}</code>: PKR {float(r.get('rate_a',0)):,.0f} &nbsp;|&nbsp; "
                f"Rate in <code>{r.get('source_b','')}</code>: PKR {float(r.get('rate_b',0)):,.0f} "
                f"(<b>{diff:.1f}% difference</b>)",
                "red" if diff > 25 else "amber"
            )
    else:
        alert("✅ No item master conflicts found.", "green")

    # Price deviation summary chart
    section("📊 Vendor Price Deviations – All Items")
    if not prices.empty:
        vp2 = prices.copy()
        vp2["deviation_abs"] = vp2["pct_vs_std"].abs()
        vp2["severity"] = pd.cut(
            vp2["deviation_abs"],
            bins=[-np.inf, 10, 25, np.inf],
            labels=["✓ Acceptable","⚠ Review","✗ Investigate"]
        )
        sev_counts = vp2["severity"].value_counts().reset_index()
        sev_counts.columns = ["Severity","Count"]
        fig = px.bar(
            sev_counts, x="Severity", y="Count",
            color="Severity",
            color_discrete_map={"✓ Acceptable": GREEN, "⚠ Review": AMBER, "✗ Investigate": RED_C},
            text_auto=True,
        )
        chart_layout(fig, height=300)
        st.plotly_chart(fig, width='stretch')

    # Full flags table
    section("📋 Full Discrepancy Log Table")
    if not flags.empty:
        st.dataframe(flags, width='stretch', height=300)
    else:
        st.info("No flags to display.")

    # Data quality metrics
    section("📊 Data Quality Summary")
    if not bills.empty:
        total_lines  = len(bills)
        matched      = bills["matched"].astype(str).str.lower().isin(["true","1"]).sum()
        unmatched    = total_lines - matched
        match_pct    = matched / total_lines * 100

        q1, q2, q3, q4 = st.columns(4)
        with q1: kpi("Total Bill Lines",   f"{total_lines:,}")
        with q2: kpi("Fuzzy Matched",      f"{matched:,}",   f"{match_pct:.1f}%", "green")
        with q3: kpi("Unmatched Lines",    f"{unmatched:,}", "Needs review",      "amber")
        with q4:
            high_conf = (bills["match_score"] >= 90).sum()
            kpi("High Confidence (≥90)", f"{high_conf:,}", "Score ≥ 90", "green")

        # Match score distribution
        fig2 = px.histogram(
            bills[bills["match_score"].notna()],
            x="match_score", nbins=20,
            color_discrete_sequence=[ACCENT],
            labels={"match_score":"Fuzzy Match Score"},
        )
        fig2.add_vline(x=72, line_dash="dash", line_color=AMBER,
                       annotation_text="Min threshold (72)")
        fig2.add_vline(x=90, line_dash="dash", line_color=GREEN,
                       annotation_text="High confidence (90)")
        chart_layout(fig2, "Match Score Distribution", height=280)
        st.plotly_chart(fig2, width='stretch')


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 11 – COST ESTIMATOR
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔮 Cost Estimator":
    st.title("🔮 Construction Cost Estimator")
    st.markdown(
        "Interactive tool to estimate material and labour cost for a new project "
        "based on historical Satti Group data."
    )

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["🧱 Material Estimator", "👷 Labour Estimator", "📊 Full Project Budget"])

    # ── Tab 1: Material ────────────────────────────────────────────────────────
    with tab1:
        section("🧱 Material Cost Estimator")
        st.markdown("Enter quantities for each material. Rates pulled from canonical price master.")

        est_rows = []
        material_list = list(STD_RATES.items())

        # Display in groups of 4
        n_cols = 4
        for i in range(0, len(material_list), n_cols):
            row_items = material_list[i:i+n_cols]
            cols = st.columns(n_cols)
            for j, (code, (name, unit, std_rate)) in enumerate(row_items):
                # Find lowest vendor rate
                vp_item = prices[prices["canon_code"] == code] if not prices.empty else pd.DataFrame()
                min_rate = vp_item["quoted_rate"].min() if not vp_item.empty else std_rate
                min_rate = min_rate if pd.notna(min_rate) else std_rate

                with cols[j]:
                    estimator_label(f"{name} ({unit}) @ PKR {std_rate:,}")
                    qty = st.number_input(
                        f"Quantity for {name}",
                        min_value=0.0, value=0.0, step=10.0,
                        key=f"mat_{code}", label_visibility="collapsed"
                    )
                    est_rows.append({
                        "Code": code, "Material": name, "Unit": unit,
                        "Qty": qty, "Std Rate": std_rate,
                        "Best Rate": round(min_rate, 0),
                        "Std Cost": qty * std_rate,
                        "Best Cost": qty * min_rate,
                    })

        est_df = pd.DataFrame(est_rows)
        est_df = est_df[est_df["Qty"] > 0]

        if not est_df.empty:
            total_std  = est_df["Std Cost"].sum()
            total_best = est_df["Best Cost"].sum()
            savings    = total_std - total_best

            st.markdown("---")
            ce1, ce2, ce3 = st.columns(3)
            with ce1: kpi("Estimated Cost (Std Rates)", pkr(total_std))
            with ce2: kpi("Estimated Cost (Best Rates)", pkr(total_best), color="green")
            with ce3: kpi("Potential Savings", pkr(savings), color="amber")

            # Breakdown chart
            fig = px.bar(
                est_df, x="Material",
                y=["Std Cost","Best Cost"],
                barmode="group",
                color_discrete_map={"Std Cost": ACCENT, "Best Cost": GREEN},
                labels={"value":"PKR","Material":""},
                text_auto=".3s",
            )
            fig.update_xaxes(tickangle=-25, tickfont_size=10)
            chart_layout(fig, "Std vs Best Rate Comparison", height=350)
            st.plotly_chart(fig, width='stretch')

            # Summary table
            est_df["Std Cost"]  = est_df["Std Cost"].apply(lambda x: f"PKR {x:,.0f}")
            est_df["Best Cost"] = est_df["Best Cost"].apply(lambda x: f"PKR {x:,.0f}")
            est_df["Std Rate"]  = est_df["Std Rate"].apply(lambda x: f"PKR {x:,.0f}")
            est_df["Best Rate"] = est_df["Best Rate"].apply(lambda x: f"PKR {x:,.0f}")
            st.dataframe(est_df[["Code","Material","Unit","Qty","Std Rate","Best Rate","Std Cost","Best Cost"]],
                         width='stretch')
        else:
            st.info("Enter quantities above to see your estimate.")

    # ── Tab 2: Labour Estimator ────────────────────────────────────────────────
    with tab2:
        section("👷 Labour Cost Estimator")

        labour_rates = {
            "Mason": 900, "Helper": 600, "Electrician": 1200,
            "Plumber": 1100, "Carpenter": 1000, "Painter": 850,
            "Welder": 1100, "Supervisor": 1800, "Site Engineer": 2500,
            "Security Guard": 700,
        }

        # Historical avg from data
        if not labour.empty:
            hist_avg = labour.groupby("trade")["total_wages"].sum() / labour.groupby("trade")["workers"].sum()
            hist_avg = hist_avg.to_dict()
        else:
            hist_avg = {}

        st.markdown("Enter workers and duration (days):")
        estimator_label("Project Duration (days)")
        duration_days = st.slider("Project Duration (days)", 30, 1200, 365, step=15,
                      label_visibility="collapsed")

        lab_rows = []
        cols_l   = st.columns(5)
        for i, (trade, daily_rate) in enumerate(labour_rates.items()):
            hist = hist_avg.get(trade, daily_rate)
            with cols_l[i % 5]:
                estimator_label(f"{trade} - PKR {daily_rate}/day")
                n = st.number_input(f"Workers: {trade}",
                                    min_value=0, value=0, step=1,
                                    key=f"lab_{trade}", label_visibility="collapsed")
                lab_rows.append({
                    "Trade": trade, "Count": n,
                    "Daily Rate": daily_rate,
                    "Hist Avg Daily": round(hist / 26, 0) if hist > daily_rate else daily_rate,
                    "Total Cost": n * daily_rate * duration_days,
                })

        lab_df = pd.DataFrame(lab_rows)
        lab_df = lab_df[lab_df["Count"] > 0]

        if not lab_df.empty:
            total_labour = lab_df["Total Cost"].sum()
            total_heads  = lab_df["Count"].sum()

            cl1, cl2, cl3 = st.columns(3)
            with cl1: kpi("Total Labour Cost", pkr(total_labour))
            with cl2: kpi("Total Workforce",   str(int(total_heads)))
            with cl3: kpi("Duration",          f"{duration_days} days")

            figL = px.bar(
                lab_df.sort_values("Total Cost", ascending=True),
                x="Total Cost", y="Trade",
                orientation="h", color="Total Cost",
                color_continuous_scale="Blues",
                text_auto=".3s",
                labels={"Total Cost":"PKR","Trade":""},
            )
            chart_layout(figL, "Labour Cost by Trade", height=320)
            st.plotly_chart(figL, width='stretch')

        else:
            st.info("Enter worker counts above to see your estimate.")

    # ── Tab 3: Full Project Budget ─────────────────────────────────────────────
    with tab3:
        section("📊 Full Project Budget Builder")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            estimator_label("Project Name")
            proj_name   = st.text_input("Project Name", "New Satti Tower", label_visibility="collapsed")
            estimator_label("Total Built-up Area (sft)")
            total_area  = st.number_input("Total Built-up Area (sft)", 1000, 500000, 50000,
                                          step=500, label_visibility="collapsed")
            estimator_label("Number of Floors")
            floors      = st.number_input("Number of Floors", 1, 30, 5, label_visibility="collapsed")
        with col_b2:
            estimator_label("Project Type")
            proj_type   = st.selectbox("Project Type", ["Residential","Commercial","Mixed-Use"],
                                       label_visibility="collapsed")
            estimator_label("Contingency %")
            contingency = st.slider("Contingency %", 0, 25, 10, label_visibility="collapsed")
            estimator_label("Site Overhead %")
            overhead    = st.slider("Site Overhead %", 0, 20, 8, label_visibility="collapsed")

        # Rough cost per sft benchmarks from historical data
        benchmarks = {
            "Residential": {"civil": 1800, "electrical": 350, "plumbing": 280,
                            "finishing": 600, "hvac": 150, "misc": 200},
            "Commercial":  {"civil": 2200, "electrical": 500, "plumbing": 300,
                            "finishing": 800, "hvac": 350, "misc": 250},
            "Mixed-Use":   {"civil": 2000, "electrical": 420, "plumbing": 290,
                            "finishing": 700, "hvac": 250, "misc": 220},
        }
        bm = benchmarks[proj_type]

        st.markdown("---")
        budget_rows = []
        total_base  = 0
        for head, rate in bm.items():
            cost_head = total_area * rate
            total_base += cost_head
            budget_rows.append({"Head": head.title(), "Rate/sft": rate,
                                 "Area (sft)": total_area, "Cost": cost_head})

        contingency_amt = total_base * contingency / 100
        overhead_amt    = total_base * overhead    / 100
        grand_total     = total_base + contingency_amt + overhead_amt

        bud_df = pd.DataFrame(budget_rows)

        bc1, bc2, bc3, bc4 = st.columns(4)
        with bc1: kpi("Base Cost",   pkr(total_base))
        with bc2: kpi("Contingency", pkr(contingency_amt), color="amber")
        with bc3: kpi("Overheads",   pkr(overhead_amt))
        with bc4: kpi("GRAND TOTAL", pkr(grand_total), color="blue")

        # Cost/sft
        st.metric("Cost per Sq. Ft.", f"PKR {grand_total/total_area:,.0f}")

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            fig_b = px.bar(
                bud_df.sort_values("Cost"),
                x="Cost", y="Head", orientation="h",
                color="Cost", color_continuous_scale="Blues",
                text_auto=".3s",
                labels={"Cost":"PKR","Head":""},
            )
            chart_layout(fig_b, "Cost Breakdown by Head", height=320)
            st.plotly_chart(fig_b, width='stretch')
        with col_c2:
            final_rows = bud_df[["Head","Cost"]].copy()
            final_rows = pd.concat([
                final_rows,
                pd.DataFrame([{"Head":"Contingency","Cost":contingency_amt},
                               {"Head":"Overhead",   "Cost":overhead_amt}])
            ])
            fig_p = px.pie(
                final_rows, names="Head", values="Cost",
                color_discrete_sequence=px.colors.sequential.Blues_r,
                hole=0.4,
            )
            fig_p.update_traces(textinfo="percent+label", textfont_size=10)
            chart_layout(fig_p, height=320)
            st.plotly_chart(fig_p, width='stretch')

        st.markdown("---")
        st.markdown(f"""
        ### 📋 Budget Summary – {proj_name}
        | Head             | Rate/sft | Amount (PKR)       |
        |------------------|---------|--------------------|
        """ + "\n".join([
            f"| {r['Head']} | PKR {r['Rate/sft']:,} | PKR {r['Cost']:,.0f} |"
            for _, r in bud_df.iterrows()
        ]) + f"""
        | **Contingency ({contingency}%)** | — | PKR {contingency_amt:,.0f} |
        | **Overhead ({overhead}%)** | — | PKR {overhead_amt:,.0f} |
        | **GRAND TOTAL** | — | **PKR {grand_total:,.0f}** |
        """)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="text-align:center; font-size:12px; color:#9CA3AF;">'
    '🏗️ Satti Group Construction Analytics · '
    'Data pipeline: 405 raw Excel files → Clean → Fuzzy Match → Analyze · '
    'Built with Python, Pandas, Plotly & Streamlit'
    '</div>',
    unsafe_allow_html=True
)

