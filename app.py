import streamlit as st
import pandas as pd
from datetime import date, datetime
from io import BytesIO
from email.message import EmailMessage
import smtplib
import uuid

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# =========================================================
# CONFIGURATION & BRAND THEMING
# =========================================================

st.set_page_config(
    page_title="ALPINE HERBS | Daily Field Report",
    page_icon="🌿",
    layout="wide"
)

ALPINE_DARK = "#0D2818"       # Deep pine black-green
ALPINE_PRIMARY = "#164E33"    # Rich Himalayan evergreen
ALPINE_ACCENT = "#2D7D52"     # Fresh herb green
ALPINE_MINT = "#EAF2EC"       # Subtle card background
ALPINE_BORDER = "#C8DCCF"     # Clean soft boundary

EMAIL_TO = st.secrets.get("smtp_to", "Alpineherbsinfo@gmail.com")

# =========================================================
# CUSTOM CSS THEMING
# =========================================================

st.markdown(f"""
<style>
/* Main Container Spacing */
.block-container {{
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1550px;
}}

/* Header Banner */
.brand-header {{
    background: linear-gradient(135deg, {ALPINE_DARK} 0%, {ALPINE_PRIMARY} 100%);
    color: white;
    padding: 1.2rem 1.8rem;
    border-radius: 10px;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 12px rgba(13, 40, 24, 0.12);
}}
.brand-title {{
    font-size: 1.7rem;
    font-weight: 800;
    letter-spacing: 0.5px;
    margin: 0;
    color: #FFFFFF;
}}
.brand-sub {{
    font-size: 0.85rem;
    color: #D3E6DA;
    margin: 0.2rem 0 0 0;
    letter-spacing: 1px;
    font-weight: 500;
}}

/* Section Card Header Styling */
h3, h2, h1 {{
    color: {ALPINE_PRIMARY} !important;
    font-weight: 700;
}}

/* Top Border Highlight for Metrics */
div[data-testid="stMetric"] {{
    background: {ALPINE_MINT} !important;
    border: 1px solid {ALPINE_BORDER} !important;
    border-top: 4px solid {ALPINE_ACCENT} !important;
    padding: 10px 14px !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}}

div[data-testid="stMetricLabel"] {{
    font-size: 0.76rem !important;
    font-weight: 600 !important;
    color: {ALPINE_PRIMARY} !important;
    text-transform: uppercase;
}}

div[data-testid="stMetricValue"] {{
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    color: {ALPINE_DARK} !important;
}}

/* Primary Buttons */
div.stButton > button[kind="primary"] {{
    background: linear-gradient(180deg, {ALPINE_PRIMARY} 0%, {ALPINE_DARK} 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px;
    padding: 0.55rem 1.2rem;
    border-radius: 6px;
    box-shadow: 0 2px 6px rgba(22, 78, 51, 0.25);
}}

div.stButton > button[kind="primary"]:hover {{
    background: {ALPINE_ACCENT} !important;
    box-shadow: 0 4px 10px rgba(45, 125, 82, 0.35);
}}
</style>
""", unsafe_allow_html=True)

# App Banner
st.markdown("""
<div class="brand-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div class="brand-title">🌿 ALPINE HERBS PVT. LTD.</div>
            <div class="brand-sub">BIRGUNJ, NEPAL &nbsp;|&nbsp; MEDICAL REPRESENTATIVE DAILY FIELD CLOSING</div>
        </div>
        <div style="text-align: right; font-size: 0.8rem; color: #E0EFE5; line-height: 1.4;">
            <div><strong>ISO GMP Standard</strong></div>
            <div>Field Operations Portal</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# HELPER FUNCTIONS & BLANK SCHEMAS
# =========================================================

def money(value):
    try:
        return f"Rs. {float(value or 0):,.2f}"
    except (TypeError, ValueError):
        return "Rs. 0.00"

def nepali_date(d):
    try:
        import nepali_datetime
        bs = nepali_datetime.date.from_datetime_date(d)
        return f"{bs.year:04d}-{bs.month:02d}-{bs.day:02d} B.S."
    except Exception:
        return "2083-07-04 B.S."

def numeric_columns(df, columns):
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df

def generate_report_no(d):
    suffix = uuid.uuid4().hex[:4].upper()
    return f"ALP-{d.strftime('%Y%m%d')}-{suffix}"

# Completely blank entry templates (No dummy data)
def blank_sales():
    return pd.DataFrame([{
        "Client / Party Name": "",
        "Goods / Product Name": "",
        "Qty": 0.0,
        "FOC Qty": 0.0,
        "Sale Rate (Rs.)": 0.0,
        "Cash Collected (Rs.)": 0.0,
        "Credit Given (Rs.)": 0.0,
        "Client Address": "",
        "Invoice No.": ""
    }])

def blank_office():
    return pd.DataFrame([{
        "Expense Details": "",
        "Paid To / Vendor": "",
        "Payment Mode": "Cash",
        "Amount (Rs.)": 0.0,
        "Remarks": ""
    }])

def blank_staff():
    return pd.DataFrame([{
        "Staff / Personnel Name": "",
        "Purpose / Details": "",
        "Payment Type": "Staff Advance",
        "Amount (Rs.)": 0.0,
        "Remarks": ""
    }])

def blank_ledger():
    return pd.DataFrame([{
        "Client / Party Name": "",
        "Reference": "",
        "Previous Due (Rs.)": 0.0,
        "New Credit (Rs.)": 0.0,
        "Payment Received (Rs.)": 0.0,
        "Returns / Adjustments (Rs.)": 0.0
    }])

# =========================================================
# SESSION STATE & RESET HANDLING
# =========================================================

if "form_id" not in st.session_state:
    st.session_state.form_id = 1

today = date.today()
if "report_date" not in st.session_state:
    st.session_state.report_date = today

if "report_no" not in st.session_state:
    st.session_state.report_no = generate_report_no(today)

if "staff_name" not in st.session_state:
    st.session_state.staff_name = ""

if "route" not in st.session_state:
    st.session_state.route = ""

if "sales" not in st.session_state:
    st.session_state.sales = blank_sales()

if "office" not in st.session_state:
    st.session_state.office = blank_office()

if "staff" not in st.session_state:
    st.session_state.staff = blank_staff()

if "ledger" not in st.session_state:
    st.session_state.ledger = blank_ledger()

def reset_form_to_blank():
    """Wipes all rows and advances form key to give fresh blank tables."""
    st.session_state.form_id += 1
    st.session_state.report_no = generate_report_no(st.session_state.report_date)
    st.session_state.sales = blank_sales()
    st.session_state.office = blank_office()
    st.session_state.staff = blank_staff()
    st.session_state.ledger = blank_ledger()

# =========================================================
# REPORT METADATA CONTAINER
# =========================================================

with st.container(border=True):
    st.markdown("#### 📋 Tour & Medical Representative Details")
    c1, c2, c3, c4 = st.columns([1.1, 1.3, 1.3, 1.1])

    with c1:
        report_date = st.date_input("Date (A.D.)", value=st.session_state.report_date)
        st.session_state.report_date = report_date
        st.caption(f"🇳🇵 **Miti (B.S.):** `{nepali_date(report_date)}`")

    with c2:
        staff_name = st.text_input("MR / Staff Name", value=st.session_state.staff_name, placeholder="e.g. Pritam Gupta")
        st.session_state.staff_name = staff_name

    with c3:
        route = st.text_input("Route / Area Covered", value=st.session_state.route, placeholder="e.g. Birgunj To Lautan")
        st.session_state.route = route

    with c4:
        st.text_input("Report Reference No.", value=st.session_state.report_no, disabled=True)

# =========================================================
# 1. SALES & CASH COLLECTION ENTRIES
# =========================================================

st.subheader("1. Sales & Cash Collections Grid")
st.caption("Enter product sales or cash collections. Click any cell to edit or use '+' at the bottom to add rows.")

sales = st.data_editor(
    st.session_state.sales,
    num_rows="dynamic",
    hide_index=True,
    use_container_width=True,
    key=f"sales_grid_{st.session_state.form_id}",
    column_config={
        "Client / Party Name": st.column_config.TextColumn("Client / Party Name"),
        "Goods / Product Name": st.column_config.TextColumn("Goods / Product Name"),
        "Qty": st.column_config.NumberColumn("Qty", min_value=0.0, step=1.0),
        "FOC Qty": st.column_config.NumberColumn("FOC (Bonus)", min_value=0.0, step=1.0),
        "Sale Rate (Rs.)": st.column_config.NumberColumn("Sale Rate (Rs.)", min_value=0.0, format="%.2f"),
        "Cash Collected (Rs.)": st.column_config.NumberColumn("Cash Collected (Rs.)", min_value=0.0, format="%.2f"),
        "Credit Given (Rs.)": st.column_config.NumberColumn("Credit Given (Rs.)", min_value=0.0, format="%.2f"),
        "Client Address": st.column_config.TextColumn("Client Address"),
        "Invoice No.": st.column_config
