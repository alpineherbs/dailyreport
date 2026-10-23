import streamlit as st
import pandas as pd
from datetime import date, datetime
from io import BytesIO
from email.message import EmailMessage
import smtplib
import uuid
import os

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

# Professional Alpine Forest Theme Palette
ALPINE_DARK = "#0D2818"       # Deep pine black-green
ALPINE_PRIMARY = "#164E33"    # Rich Himalayan evergreen
ALPINE_ACCENT = "#2D7D52"     # Fresh herb green
ALPINE_MINT = "#EAF2EC"       # Subtle card background
ALPINE_BORDER = "#C8DCCF"     # Clean soft boundary
ALPINE_GOLD = "#C59B27"       # Executive highlight

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
# HELPER FUNCTIONS
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

def blank_sales():
    return pd.DataFrame([
        {"Client / Party Name": "Ali health clinic", "Goods / Product Name": "Narayani zyme 100ml", "Qty": 10.0, "FOC Qty": 10.0, "Sale Rate (Rs.)": 172.4, "Cash Collected (Rs.)": 0.0, "Credit Given (Rs.)": 1724.0, "Client Address": "Birgunj", "Invoice No.": ""},
        {"Client / Party Name": "Ali health clinic", "Goods / Product Name": "Narayani zyme 200ml", "Qty": 10.0, "FOC Qty": 10.0, "Sale Rate (Rs.)": 103.4, "Cash Collected (Rs.)": 0.0, "Credit Given (Rs.)": 1034.0, "Client Address": "Birgunj", "Invoice No.": ""},
        {"Client / Party Name": "Shoalal medical", "Goods / Product Name": "Provita", "Qty": 10.0, "FOC Qty": 0.0, "Sale Rate (Rs.)": 150.0, "Cash Collected (Rs.)": 0.0, "Credit Given (Rs.)": 1500.0, "Client Address": "Lautan", "Invoice No.": ""},
        {"Client / Party Name": "Ali health clinic", "Goods / Product Name": "Past Balance Recovery", "Qty": 0.0, "FOC Qty": 0.0, "Sale Rate (Rs.)": 0.0, "Cash Collected (Rs.)": 1500.0, "Credit Given (Rs.)": 0.0, "Client Address": "Birgunj", "Invoice No.": ""},
        {"Client / Party Name": "Shoalal medical", "Goods / Product Name": "Past Balance Recovery", "Qty": 0.0, "FOC Qty": 0.0, "Sale Rate (Rs.)": 0.0, "Cash Collected (Rs.)": 700.0, "Credit Given (Rs.)": 0.0, "Client Address": "Lautan", "Invoice No.": ""},
        {"Client / Party Name": "Satya medical", "Goods / Product Name": "Past Balance Recovery", "Qty": 0.0, "FOC Qty": 0.0, "Sale Rate (Rs.)": 0.0, "Cash Collected (Rs.)": 900.0, "Credit Given (Rs.)": 0.0, "Client Address": "Lautan", "Invoice No.": ""},
        {"Client / Party Name": "Jay shree gadimai medical", "Goods / Product Name": "Past Balance Recovery", "Qty": 0.0, "FOC Qty": 0.0, "Sale Rate (Rs.)": 0.0, "Cash Collected (Rs.)": 500.0, "Credit Given (Rs.)": 0.0, "Client Address": "Birgunj", "Invoice No.": ""},
        {"Client / Party Name": "Alex medical", "Goods / Product Name": "Past Balance Recovery", "Qty": 0.0, "FOC Qty": 0.0, "Sale Rate (Rs.)": 0.0, "Cash Collected (Rs.)": 500.0, "Credit Given (Rs.)": 0.0, "Client Address": "Birgunj", "Invoice No.": ""},
        {"Client / Party Name": "Om shiv shakti medical", "Goods / Product Name": "Past Balance Recovery", "Qty": 0.0, "FOC Qty": 0.0, "Sale Rate (Rs.)": 0.0, "Cash Collected (Rs.)": 500.0, "Credit Given (Rs.)": 0.0, "Client Address": "Birgunj", "Invoice No.": ""}
    ])

def blank_office():
    return pd.DataFrame([
        {"Expense Details": "MR Nasta", "Paid To / Vendor": "Local Stall", "Payment Mode": "Cash", "Amount (Rs.)": 50.0, "Remarks": "Daily breakfast"},
        {"Expense Details": "FZ Bike Fuel", "Paid To / Vendor": "Fuel Station", "Payment Mode": "Cash", "Amount (Rs.)": 0.0, "Remarks": "Route transit"}
    ])

def blank_staff():
    return pd.DataFrame([
        {"Staff / Personnel Name": "Karan", "Purpose / Details": "Karan Adv", "Payment Type": "Staff Advance", "Amount (Rs.)": 300.0, "Remarks": "Advance handed over"},
        {"Staff / Personnel Name": "Office Remittance", "Purpose / Details": "E-sewa Deposit", "Payment Type": "Remittance / eSewa", "Amount (Rs.)": 1700.0, "Remarks": "Transferred to Head Office"}
    ])

def blank_ledger():
    return pd.DataFrame([
        {"Client / Party Name": "Ali health clinic", "Reference": "Opening Ledger", "Previous Due (Rs.)": 1500.0, "New Credit (Rs.)": 2758.0, "Payment Received (Rs.)": 1500.0, "Returns / Adjustments (Rs.)": 0.0},
        {"Client / Party Name": "Shoalal medical", "Reference": "Opening Ledger", "Previous Due (Rs.)": 700.0, "New Credit (Rs.)": 1500.0, "Payment Received (Rs.)": 700.0, "Returns / Adjustments (Rs.)": 0.0}
    ])

# =========================================================
# SESSION STATE INITIALIZATION
# =========================================================

today = date.today()
if "report_date" not in st.session_state:
    st.session_state.report_date = today

if "report_no" not in st.session_state:
    suffix = uuid.uuid4().hex[:4].upper()
    st.session_state.report_no = f"ALP-{today.strftime('%Y%m%d')}-{suffix}"

defaults = {
    "sales": blank_sales(),
    "office": blank_office(),
    "staff": blank_staff(),
    "ledger": blank_ledger()
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy()

# =========================================================
# REPORT METADATA CONTAINER
# =========================================================

with st.container(border=True):
    st.markdown("#### 📋 Tour & Medical Representative Details")
    c1, c2, c3, c4 = st.columns([1.1, 1.3, 1.3, 1.1])

    with c1:
        report_date = st.date_input("Date (A.D.)", value=st.session_state.report_date)
        st.caption(f"🇳🇵 **Miti (B.S.):** `{nepali_date(report_date)}`")

    with c2:
        staff_name = st.text_input("MR / Staff Name", value="Pritam Gupta")

    with c3:
        route = st.text_input("Route / Area Covered", value="Birgunj To Lautan")

    with c4:
        report_no = st.text_input("Report Reference No.", value=st.session_state.report_no)

# =========================================================
# 1. SALES & CASH COLLECTION ENTRIES
# =========================================================

st.subheader("1. Sales & Cash Collections Grid")
st.caption("Enter product sales or cash collections. You can click any cell to edit or add rows at the bottom.")

sales = st.data_editor(
    st.session_state.sales,
    num_rows="dynamic",
    hide_index=True,
    use_container_width=True,
    key="sales_editor",
    column_config={
        "Client / Party Name": st.column_config.TextColumn("Client / Party Name", required=True),
        "Goods / Product Name": st.column_config.TextColumn("Goods / Product Name"),
        "Qty": st.column_config.NumberColumn("Qty", min_value=0, step=1),
        "FOC Qty": st.column_config.NumberColumn("FOC (Bonus)", min_value=0, step=1),
        "Sale Rate (Rs.)": st.column_config.NumberColumn("Sale Rate (Rs.)", min_value=0.0, format="%.2f"),
        "Cash Collected (Rs.)": st.column_config.NumberColumn("Cash Collected (Rs.)", min_value=0.0, format="%.2f"),
        "Credit Given (Rs.)": st.column_config.NumberColumn("Credit Given (Rs.)", min_value=0.0, format="%.2f"),
        "Client Address": st.column_config.TextColumn("Client Address"),
        "Invoice No.": st.column_config.TextColumn("Invoice / Bill No.")
    }
)

sales = numeric_columns(sales, ["Qty", "FOC Qty", "Sale Rate (Rs.)", "Cash Collected (Rs.)", "Credit Given (Rs.)"])

# Robust Total Sale computation: If Qty*Rate is filled use that, else use Cash + Credit
computed_sale = sales["Qty"] * sales["Sale Rate (Rs.)"]
direct_components = sales["Cash Collected (Rs.)"] + sales["Credit Given (Rs.)"]
sales["Total Sale (Rs.)"] = computed_sale.where(computed_sale > 0, direct_components)

st.session_state.sales = sales.drop(columns=["Total Sale (Rs.)"], errors="ignore")

total_sales = float(sales["Total Sale (Rs.)"].sum())
total_cash = float(sales["Cash Collected (Rs.)"].sum())
total_credit = float(sales["Credit Given (Rs.)"].sum())
total_foc = float(sales["FOC Qty"].sum())
total_qty = float(sales["Qty"].sum())

# Metrics Strip
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total Billed Sales", money(total_sales))
m2.metric("Gross Cash Collected", money(total_cash))
m3.metric("Total Credit Debited", money(total_credit))
m4.metric("Total Qty Sold", f"{total_qty:g} units")
m5.metric("Free Goods (FOC)", f"{total_foc:g} units")

st.divider()

# =========================================================
# 2. OFFICE EXPENSES & 3. STAFF PAYMENTS
# =========================================================

col_exp_1, col_exp_2 = st.columns(2)

with col_exp_1:
    st.subheader("2. Operating / Office Expenses")
    st.caption("Nasta, Fuel, Maintenance, and field costs.")
    
    office = st.data_editor(
        st.session_state.office,
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        key="office_editor",
        column_config={
            "Expense Details": st.column_config.TextColumn("Expense Details"),
            "Paid To / Vendor": st.column_config.TextColumn("Paid To"),
            "Payment Mode": st.column_config.SelectboxColumn("Mode", options=["Cash", "Digital Wallet", "Bank Transfer", "Credit"]),
            "Amount (Rs.)": st.column_config.NumberColumn("Amount (Rs.)", min_value=0.0, format="%.2f"),
            "Remarks": st.column_config.TextColumn("Remarks")
        }
    )
    office = numeric_columns(office, ["Amount (Rs.)"])
    st.session_state.office = office
    office_total = float(office["Amount (Rs.)"].sum())
    st.markdown(f"**Subtotal Office Expenses:** `{money(office_total)}`")

with col_exp_2:
    st.subheader("3. Staff Advances & eSewa Transfers")
    st.caption("MR advance, Karan advance, eSewa remittance to HO.")
    
    staff = st.data_editor(
        st.session_state.staff,
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        key="staff_editor",
        column_config={
            "Staff / Personnel Name": st.column_config.TextColumn("Staff / Purpose"),
            "Purpose / Details": st.column_config.TextColumn("Details"),
            "Payment Type": st.column_config.SelectboxColumn("Payment Type", options=["Staff Advance", "Remittance / eSewa", "Allowance", "Salary", "Other"]),
            "Amount (Rs.)": st.column_config.NumberColumn("Amount (Rs.)", min_value=0.0, format="%.2f"),
            "Remarks": st.column_config.TextColumn("Remarks")
        }
    )
    staff = numeric_columns(staff, ["Amount (Rs.)"])
    st.session_state.staff = staff
    staff_total = float(staff["Amount (Rs.)"].sum())
    st.markdown(f"**Subtotal Staff & Remittances:** `{money(staff_total)}`")

total_expenses = office_total + staff_total
net_cash = total_cash - total_expenses
sales_variance = total_sales - (total_cash + total_credit)

st.divider()

# =========================================================
# CLIENT LEDGER EXPANDER
# =========================================================

with st.expander("📊 Client Ledger & Receivables Reconciliation"):
    st.caption("Track client-wise opening dues, current credit sales, cash receipts, and current balance.")
    
    ledger = st.data_editor(
        st.session_state.ledger,
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        key="ledger_editor",
        column_config={
            "Client / Party Name": st.column_config.TextColumn("Client / Party Name"),
            "Reference": st.column_config.TextColumn("Ref / Area"),
            "Previous Due (Rs.)": st.column_config.NumberColumn(min_value=0.0, format="%.2f"),
            "New Credit (Rs.)": st.column_config.NumberColumn(min_value=0.0, format="%.2f"),
            "Payment Received (Rs.)": st.column_config.NumberColumn(min_value=0.0, format="%.2f"),
            "Returns / Adjustments (Rs.)": st.column_config.NumberColumn(min_value=0.0, format="%.2f")
        }
    )
    
    ledger = numeric_columns(ledger, ["Previous Due (Rs.)", "New Credit (Rs.)", "Payment Received (Rs.)", "Returns / Adjustments (Rs.)"])
    ledger["Current Due (Rs.)"] = (
        ledger["Previous Due (Rs.)"] + ledger["New Credit (Rs.)"]
        - ledger["Payment Received (Rs.)"] - ledger["Returns / Adjustments (Rs.)"]
    )
    st.session_state.ledger = ledger.drop(columns=["Current Due (Rs.)"], errors="ignore")
    
    ledger_outstanding = float(ledger["Current Due (Rs.)"].sum())
    st.dataframe(ledger, use_container_width=True, hide_index=True)

# =========================================================
# 4. EXECUTIVE FINANCIAL CLOSING SUMMARY
# =========================================================

st.subheader("4. Financial Closing Summary")

with st.container(border=True):
    s1, s2, s3 = st.columns(3)
    s1.metric("Total Sales Billed", money(total_sales))
    s2.metric("Credit Given (Debit to Clients)", money(total_credit))
    s3.metric("Gross Cash Collected", money(total_cash))

    s4, s5, s6 = st.columns(3)
    s4.metric("Operating Expenses (Nasta/Fuel)", money(office_total))
    s5.metric("Staff Advance & eSewa", money(staff_total))
    s6.metric("Total Deductions", money(total_expenses))

    s7, s8, s9 = st.columns(3)
    s7.metric("NET CLOSING CASH IN HAND", money(net_cash), delta=f"Collected {money(total_cash)}")
    s8.metric("Sales Variance", money(sales_variance), help="Total Sale minus (Cash + Credit)")
    s9.metric("Total Client Dues Outstanding", money(ledger_outstanding))

# =========================================================
# REPORTLAB PDF GENERATOR (A4 LANDSCAPE)
# =========================================================

def pdf_table(data, widths, font_size=7):
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(ALPINE_PRIMARY)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(ALPINE_BORDER)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(ALPINE_MINT)])
    ]))
    return table

def create_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=8 * mm,
        bottomMargin=8 * mm,
        title="Alpine Herbs Daily Field Report"
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "AHTitle",
        parent=styles["Title"],
        fontSize=15,
        leading=17,
        textColor=colors.HexColor(ALPINE_DARK),
        alignment=1,
        spaceAfter=2
    )

    sec_style = ParagraphStyle(
        "AHSec",
        parent=styles["Heading2"],
        fontSize=9,
        leading=11,
        textColor=colors.HexColor(ALPINE_PRIMARY),
        spaceBefore=6,
        spaceAfter=3
    )

    cell_style = ParagraphStyle(
        "AHCell",
        parent=styles["Normal"],
        fontSize=6.5,
        leading=8,
        textColor=colors.HexColor("#222222")
    )

    story = [
        Paragraph("<b>ALPINE HERBS PVT. LTD.</b>", title_style),
        Paragraph(
            "Birgunj, Nepal &nbsp;|&nbsp; Daily Medical Representative (MR) Report",
            ParagraphStyle("Sub", parent=styles["Normal"], alignment=1, fontSize=8, leading=10, textColor=colors.HexColor("#444"), spaceAfter=6)
        )
    ]

    # Meta Info Table
    info_data = [
        ["English Date", report_date.strftime("%d-%b-%Y"), "Nepali Miti (B.S.)", nepali_date(report_date)],
        ["MR / Personnel", staff_name or "—", "Route / Area", route or "—"],
        ["Reference No.", report_no or "—", "Generated At", datetime.now().strftime("%d-%b-%Y %H:%M")]
    ]
    meta_table = Table(info_data, colWidths=[28*mm, 75*mm, 35*mm, 139*mm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor(ALPINE_MINT)),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor(ALPINE_MINT)),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(ALPINE_BORDER)),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3)
    ]))
    story.append(meta_table)

    # 1. Sales Table (Total Width = 277 mm edge-to-edge)
    story.append(Paragraph("1. SALES ENTRIES & RECOVERIES", sec_style))
    sales_header = ["S.N.", "Client / Party Name", "Goods / Product Name", "Qty", "FOC", "Rate", "Total Sale", "Cash", "Credit", "Address", "Invoice"]
    sales_rows = [sales_header]

    for idx, r in sales.reset_index(drop=True).iterrows():
        sales_rows.append([
            str(idx + 1),
            Paragraph(str(r["Client / Party Name"]), cell_style),
            Paragraph(str(r["Goods / Product Name"]), cell_style),
            f'{r["Qty"]:g}',
            f'{r["FOC Qty"]:g}',
            f'{r["Sale Rate (Rs.)"]:,.1f}',
            f'{r["Total Sale (Rs.)"]:,.1f}',
            f'{r["Cash Collected (Rs.)"]:,.1f}',
            f'{r["Credit Given (Rs.)"]:,.1f}',
            Paragraph(str(r["Client Address"]), cell_style),
            str(r["Invoice No."])
        ])

    story.append(pdf_table(
        sales_rows,
        [8*mm, 45*mm, 42*mm, 11*mm, 10*mm, 18*mm, 23*mm, 22*mm, 22*mm, 52*mm, 24*mm],
        6.5
    ))

    # 2 & 3. Side-by-Side Expenses and Staff Payments
    story.append(Spacer(1, 3))
    story.append(Paragraph("2. EXPENSES & DISBURSEMENTS", sec_style))

    exp_data = [["Expense Details", "Paid To", "Mode", "Amount (Rs.)"]]
    for _, r in office.reset_index(drop=True).iterrows():
        exp_data.append([str(r["Expense Details"]), str(r["Paid To / Vendor"]), str(r["Payment Mode"]), money(r["Amount (Rs.)"])])
    if len(exp_data) == 1:
        exp_data.append(["No expenses logged", "—", "—", money(0)])

    staff_pdf_data = [["Staff / Remittance", "Purpose", "Type", "Amount (Rs.)"]]
    for _, r in staff.reset_index(drop=True).iterrows():
        staff_pdf_data.append([str(r["Staff / Personnel Name"]), str(r["Purpose / Details"]), str(r["Payment Type"]), money(r["Amount (Rs.)"])])
    if len(staff_pdf_data) == 1:
        staff_pdf_data.append(["No staff advances logged", "—", "—", money(0)])

    t_office = pdf_table(exp_data, [45*mm, 40*mm, 25*mm, 26*mm], 6.5)
    t_staff = pdf_table(staff_pdf_data, [45*mm, 40*mm, 28*mm, 28*mm], 6.5)

    side_table = Table([[t_office, t_staff]], colWidths=[137*mm, 140*mm])
    side_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0)
    ]))
    story.append(side_table)

    # 4. Summary Table
    story.append(Spacer(1, 4))
    story.append(Paragraph("3. CLOSING FINANCIAL RECONCILIATION", sec_style))
    sum_data = [
        ["Total Billed Sales", money(total_sales), "Gross Cash Collected", money(total_cash)],
        ["Total Credit Given", money(total_credit), "Total FOC Units", f"{total_foc:g}"],
        ["Office Expenses", money(office_total), "Staff Advance / eSewa", money(staff_total)],
        ["Total Deductions", money(total_expenses), "NET CASH IN HAND", money(net_cash)]
    ]
    t_sum = pdf_table(sum_data, [50*mm, 45*mm, 50*mm, 45*mm], 7.5)
    story.append(t_sum)

    # Signatures
    story.append(Spacer(1, 10))
    sig_data = [
        [
            Paragraph("____________________________<br/><b>Prepared by (MR)</b>", cell_style),
            Paragraph("____________________________<br/><b>Verified by (Accounts)</b>", cell_style),
            Paragraph("____________________________<br/><b>Approved by (Director)</b>", cell_style)
        ]
    ]
    t_sig = Table(sig_data, colWidths=[92*mm, 92*mm, 93*mm])
    t_sig.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))
    story.append(t_sig)

    doc.build(story)
    return buffer.getvalue()

# =========================================================
# EMAIL DISPATCH HELPER
# =========================================================

def email_pdf(pdf_bytes):
    try:
        msg = EmailMessage()
        filename = f"ALPINE_HERBS_Report_{report_no}_{report_date}.pdf"
        msg["Subject"] = f"[{report_no}] Alpine Herbs Daily Report - {staff_name} ({nepali_date(report_date)})"
        msg["From"] = st.secrets.get("smtp_from", "noreply@alpineherbs.com")
        msg["To"] = EMAIL_TO

        msg.set_content(
            f"Dear Management,\n\n"
            f"Please find attached the daily field report for Alpine Herbs Pvt. Ltd.\n\n"
            f"Reference: {report_no}\n"
            f"Date: {report_date} ({nepali_date(report_date)})\n"
            f"MR Name: {staff_name}\n"
            f"Route: {route}\n"
            f"Gross Cash Collected: {money(total_cash)}\n"
            f"Credit Given: {money(total_credit)}\n"
            f"Total Deductions: {money(total_expenses)}\n"
            f"Net Closing Cash to Deposit: {money(net_cash)}\n\n"
            f"Regards,\nField Operations System"
        )

        msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=filename)

        with smtplib.SMTP(st.secrets.get("smtp_host", "smtp.gmail.com"), int(st.secrets.get("smtp_port", 587)), timeout=25) as server:
            server.starttls()
            server.login(st.secrets.get("smtp_user", "your-email@gmail.com"), st.secrets.get("smtp_password", "app-password"))
            server.send_message(msg)

        return True, f"Report successfully dispatched to {EMAIL_TO}!"
    except Exception as exc:
        return False, f"Email delivery failed: {exc}"

# =========================================================
# 5. SUBMIT & EXPORT SECTION
# =========================================================

st.subheader("5. Verification & Submission")

c_sub1, c_sub2, c_sub3 = st.columns([1.5, 1, 1])

with c_sub1:
    if st.button("🚀 SUBMIT & EMAIL OFFICIAL PDF REPORT", type="primary", use_container_width=True):
        with st.spinner("Generating PDF and sending email..."):
            pdf_bytes = create_pdf()
            st.session_state["report_pdf"] = pdf_bytes
            st.session_state["report_filename"] = f"ALPINE_HERBS_{report_no}.pdf"
            ok, msg = email_pdf(pdf_bytes)
            if ok:
                st.balloons()
                st.success(msg)
            else:
                st.error(msg)
                st.info("The PDF was generated. You can download it directly below.")

with c_sub2:
    if "report_pdf" in st.session_state:
        st.download_button(
            "⬇️ DOWNLOAD PDF COPY",
            data=st.session_state["report_pdf"],
            file_name=st.session_state["report_filename"],
            mime="application/pdf",
            use_container_width=True
        )

with c_sub3:
    # Excel export
    excel_buf = BytesIO()
    with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
        sales.to_excel(writer, sheet_name="Sales Grid", index=False)
        office.to_excel(writer, sheet_name="Office Expenses", index=False)
        staff.to_excel(writer, sheet_name="Staff Advances", index=False)
        st.session_state.ledger.to_excel(writer, sheet_name="Ledger", index=False)
        pd.DataFrame([{
            "Ref": report_no, "Date AD": str(report_date), "Miti BS": nepali_date(report_date),
            "MR": staff_name, "Route": route, "Total Sales": total_sales,
            "Cash Collected": total_cash, "Credit Given": total_credit,
            "Total Expenses": total_expenses, "Net Cash": net_cash
        }]).to_excel(writer, sheet_name="Summary", index=False)

    st.download_button(
        "📥 DOWNLOAD EXCEL (.XLSX)",
        data=excel_buf.getvalue(),
        file_name=f"Alpine_Herbs_{report_no}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

st.markdown("---")
st.caption("🌿 ALPINE HERBS PVT. LTD. | Pharmaceutical Field Accounting System. All transactions are logged with audit tag.")
