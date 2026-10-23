import streamlit as st
import pandas as pd
from datetime import date, datetime
from io import BytesIO
from email.message import EmailMessage
import smtplib
import ssl
import uuid

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="ALPINE HERBS | Daily Field Report",
    page_icon="🌿",
    layout="wide"
)

EMAIL_TO = st.secrets.get("smtp_to", "Alpineherbsinfo@gmail.com")
REQUIRED_APP_PASSCODE = str(st.secrets.get("app_passcode", "12345678"))

# =========================================================
# BRAND STYLING
# =========================================================

st.markdown("""
<style>
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1550px;
}
.brand-header {
    background: linear-gradient(135deg, #0D2818 0%, #164E33 100%);
    color: white;
    padding: 1.2rem 1.8rem;
    border-radius: 10px;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 12px rgba(13, 40, 24, 0.12);
}
.brand-title {
    font-size: 1.7rem;
    font-weight: 800;
    letter-spacing: 0.5px;
    margin: 0;
    color: #FFFFFF;
}
.brand-sub {
    font-size: 0.85rem;
    color: #D3E6DA;
    margin: 0.2rem 0 0 0;
    letter-spacing: 1px;
    font-weight: 500;
}
h3, h2, h1 {
    color: #164E33 !important;
    font-weight: 700;
}
div[data-testid="stMetric"] {
    background: #EAF2EC !important;
    border: 1px solid #C8DCCF !important;
    border-top: 4px solid #2D7D52 !important;
    padding: 10px 14px !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
div[data-testid="stMetricLabel"] {
    font-size: 0.76rem !important;
    font-weight: 600 !important;
    color: #164E33 !important;
    text-transform: uppercase;
}
div[data-testid="stMetricValue"] {
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    color: #0D2818 !important;
}
div.stButton > button[kind="primary"] {
    background: linear-gradient(180deg, #164E33 0%, #0D2818 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px;
    padding: 0.55rem 1.2rem;
    border-radius: 6px;
    box-shadow: 0 2px 6px rgba(22, 78, 51, 0.25);
}
div.stButton > button[kind="primary"]:hover {
    background: #2D7D52 !important;
    box-shadow: 0 4px 10px rgba(45, 125, 82, 0.35);
}
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
        if not isinstance(d, (date, datetime)):
            d = date.today()
        bs = nepali_datetime.date.from_datetime_date(d)
        return f"{bs.year:04d}-{bs.month:02d}-{bs.day:02d} B.S."
    except Exception:
        return "2083-07-04 B.S."

def generate_report_no(d):
    if not isinstance(d, (date, datetime)):
        d = date.today()
    suffix = uuid.uuid4().hex[:4].upper()
    return f"ALP-{d.strftime('%Y%m%d')}-{suffix}"

# Blank templates (Fresh empty tables)
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

def numeric_columns(df, columns):
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df

# =========================================================
# PERSISTENT SESSION STATE (Prevents input resets)
# =========================================================

if "form_id" not in st.session_state:
    st.session_state["form_id"] = 1

# Base tables are initialized once and NOT overwritten on every keystroke
if "sales_base" not in st.session_state:
    st.session_state["sales_base"] = blank_sales()

if "office_base" not in st.session_state:
    st.session_state["office_base"] = blank_office()

if "staff_base" not in st.session_state:
    st.session_state["staff_base"] = blank_staff()

if "ledger_base" not in st.session_state:
    st.session_state["ledger_base"] = blank_ledger()

if "report_date" not in st.session_state:
    st.session_state["report_date"] = date.today()

if "report_no" not in st.session_state:
    st.session_state["report_no"] = generate_report_no(date.today())

def reset_form_to_blank():
    """Advances form ID so Streamlit loads a fresh empty table without cached entries."""
    st.session_state["form_id"] += 1
    st.session_state["report_no"] = generate_report_no(st.session_state.get("report_date", date.today()))
    st.session_state["sales_base"] = blank_sales()
    st.session_state["office_base"] = blank_office()
    st.session_state["staff_base"] = blank_staff()
    st.session_state["ledger_base"] = blank_ledger()

# =========================================================
# SIDEBAR: CREDENTIALS & CONTROLS
# =========================================================

with st.sidebar:
    st.header("📧 Email Credentials")
    st.caption("Enter your Gmail details to dispatch reports:")

    user_email = st.text_input(
        "Your Sender Gmail:",
        placeholder="example@gmail.com",
        help="The Gmail address used to send the report."
    )

    user_password = st.text_input(
        "Your 16-Digit App Password:",
        type="password",
        placeholder="Enter App Password",
        help="Google App Password generated from your Google Account -> Security -> App passwords."
    )

    company_recipient = st.text_input(
        "Send Report To:",
        value="Alpineherbsinfo@gmail.com",
        help="Destination email for daily reports."
    )

    st.divider()
    st.info(f"**Report ID:** `{st.session_state.get('report_no', 'ALP')}`")

    if st.button("🔄 Clear Form & Start Fresh"):
        reset_form_to_blank()
        st.rerun()

# =========================================================
# REPORT METADATA
# =========================================================

st.markdown("#### 📋 Tour & Medical Representative Details")
c1, c2, c3, c4 = st.columns([1.1, 1.3, 1.3, 1.1])

with c1:
    selected_date = st.date_input("Date (A.D.)", value=st.session_state.get("report_date", date.today()))
    st.session_state["report_date"] = selected_date
    st.caption(f"🇳🇵 **Miti (B.S.):** `{nepali_date(selected_date)}`")

with c2:
    staff_name = st.text_input("MR / Staff Name", placeholder="e.g. Pritam Gupta")

with c3:
    route = st.text_input("Route / Area Covered", placeholder="e.g. Birgunj To Lautan")

with c4:
    st.text_input("Report Reference No.", value=st.session_state.get("report_no", ""), disabled=True)

st.divider()

# =========================================================
# 1. SALES ENTRIES (Continuous Tab / Enter Flow)
# =========================================================

st.subheader("1. Sales & Cash Collections Grid")
st.caption("Type values and use Tab or Enter. Edits will stay continuously without resetting.")

sales_column_config = {
    "Client / Party Name": st.column_config.TextColumn("Client / Party Name"),
    "Goods / Product Name": st.column_config.TextColumn("Goods / Product Name"),
    "Qty": st.column_config.NumberColumn("Qty", min_value=0.0, step=1.0),
    "FOC Qty": st.column_config.NumberColumn("FOC (Bonus)", min_value=0.0, step=1.0),
    "Sale Rate (Rs.)": st.column_config.NumberColumn("Sale Rate (Rs.)", min_value=0.0, format="%.2f"),
    "Cash Collected (Rs.)": st.column_config.NumberColumn("Cash Collected (Rs.)", min_value=0.0, format="%.2f"),
    "Credit Given (Rs.)": st.column_config.NumberColumn("Credit Given (Rs.)", min_value=0.0, format="%.2f"),
    "Client Address": st.column_config.TextColumn("Client Address"),
    "Invoice No.": st.column_config.TextColumn("Invoice / Bill No.")
}

current_form_id = st.session_state["form_id"]

# Notice: Data source is passed from sales_base without re-writing sales_base on every rerun
raw_sales = st.data_editor(
    st.session_state["sales_base"],
    num_rows="dynamic",
    hide_index=True,
    use_container_width=True,
    key=f"sales_editor_stable_{current_form_id}",
    column_config=sales_column_config
)

sales = numeric_columns(raw_sales, ["Qty", "FOC Qty", "Sale Rate (Rs.)", "Cash Collected (Rs.)", "Credit Given (Rs.)"])

# Robust Sales Math
computed_sale = sales["Qty"] * sales["Sale Rate (Rs.)"]
direct_components = sales["Cash Collected (Rs.)"] + sales["Credit Given (Rs.)"]
sales["Total Sale (Rs.)"] = computed_sale.where(computed_sale > 0, direct_components)

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
    office_column_config = {
        "Expense Details": st.column_config.TextColumn("Expense Details"),
        "Paid To / Vendor": st.column_config.TextColumn("Paid To"),
        "Payment Mode": st.column_config.SelectboxColumn("Mode", options=["Cash", "Digital Wallet", "Bank Transfer", "Credit"]),
        "Amount (Rs.)": st.column_config.NumberColumn("Amount (Rs.)", min_value=0.0, format="%.2f"),
        "Remarks": st.column_config.TextColumn("Remarks")
    }

    raw_office = st.data_editor(
        st.session_state["office_base"],
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        key=f"office_editor_stable_{current_form_id}",
        column_config=office_column_config
    )
    office = numeric_columns(raw_office, ["Amount (Rs.)"])
    office_total = float(office["Amount (Rs.)"].sum())
    st.markdown(f"**Subtotal Office Expenses:** `{money(office_total)}`")

with col_exp_2:
    st.subheader("3. Staff Advances & eSewa Transfers")
    staff_column_config = {
        "Staff / Personnel Name": st.column_config.TextColumn("Staff / Purpose"),
        "Purpose / Details": st.column_config.TextColumn("Details"),
        "Payment Type": st.column_config.SelectboxColumn("Payment Type", options=["Staff Advance", "Remittance / eSewa", "Allowance", "Salary", "Other"]),
        "Amount (Rs.)": st.column_config.NumberColumn("Amount (Rs.)", min_value=0.0, format="%.2f"),
        "Remarks": st.column_config.TextColumn("Remarks")
    }

    raw_staff = st.data_editor(
        st.session_state["staff_base"],
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        key=f"staff_editor_stable_{current_form_id}",
        column_config=staff_column_config
    )
    staff = numeric_columns(raw_staff, ["Amount (Rs.)"])
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

    ledger_column_config = {
        "Client / Party Name": st.column_config.TextColumn("Client / Party Name"),
        "Reference": st.column_config.TextColumn("Ref / Area"),
        "Previous Due (Rs.)": st.column_config.NumberColumn(min_value=0.0, format="%.2f"),
        "New Credit (Rs.)": st.column_config.NumberColumn(min_value=0.0, format="%.2f"),
        "Payment Received (Rs.)": st.column_config.NumberColumn(min_value=0.0, format="%.2f"),
        "Returns / Adjustments (Rs.)": st.column_config.NumberColumn(min_value=0.0, format="%.2f")
    }

    raw_ledger = st.data_editor(
        st.session_state["ledger_base"],
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        key=f"ledger_editor_stable_{current_form_id}",
        column_config=ledger_column_config
    )

    ledger = numeric_columns(raw_ledger, ["Previous Due (Rs.)", "New Credit (Rs.)", "Payment Received (Rs.)", "Returns / Adjustments (Rs.)"])
    ledger["Current Due (Rs.)"] = (
        ledger["Previous Due (Rs.)"] + ledger["New Credit (Rs.)"]
        - ledger["Payment Received (Rs.)"] - ledger["Returns / Adjustments (Rs.)"]
    )
    ledger_outstanding = float(ledger["Current Due (Rs.)"].sum())
    st.dataframe(ledger, use_container_width=True, hide_index=True)

# =========================================================
# 4. EXECUTIVE FINANCIAL CLOSING SUMMARY
# =========================================================

st.subheader("4. Financial Closing Summary")

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
# REPORTLAB PDF GENERATOR
# =========================================================

def pdf_table(data, widths, font_size=7):
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#164E33")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C8DCCF")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EAF2EC")])
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
        "AHTitle", parent=styles["Title"], fontSize=15, leading=17,
        textColor=colors.HexColor("#0D2818"), alignment=1, spaceAfter=2
    )
    sec_style = ParagraphStyle(
        "AHSec", parent=styles["Heading2"], fontSize=9, leading=11,
        textColor=colors.HexColor("#164E33"), spaceBefore=6, spaceAfter=3
    )
    cell_style = ParagraphStyle(
        "AHCell", parent=styles["Normal"], fontSize=6.5, leading=8,
        textColor=colors.HexColor("#222222")
    )

    story = [
        Paragraph("<b>ALPINE HERBS PVT. LTD.</b>", title_style),
        Paragraph(
            "Birgunj, Nepal &nbsp;|&nbsp; Daily Medical Representative (MR) Report",
            ParagraphStyle("Sub", parent=styles["Normal"], alignment=1, fontSize=8, leading=10, textColor=colors.HexColor("#444"), spaceAfter=6)
        )
    ]

    current_report_no = st.session_state.get("report_no", "ALP-REPORT")
    current_staff = staff_name.strip() if staff_name else "—"
    current_route = route.strip() if route else "—"

    info_data = [
        ["English Date", selected_date.strftime("%d-%b-%Y"), "Nepali Miti (B.S.)", nepali_date(selected_date)],
        ["MR / Personnel", current_staff, "Route / Area", current_route],
        ["Reference No.", current_report_no, "Generated At", datetime.now().strftime("%d-%b-%Y %H:%M")]
    ]
    meta_table = Table(info_data, colWidths=[28*mm, 75*mm, 35*mm, 139*mm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF2EC")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#EAF2EC")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C8DCCF")),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3)
    ]))
    story.append(meta_table)

    valid_sales = sales[sales["Client / Party Name"].astype(str).str.strip() != ""]

    story.append(Paragraph("1. SALES ENTRIES & RECOVERIES", sec_style))
    sales_header = ["S.N.", "Client / Party Name", "Goods / Product Name", "Qty", "FOC", "Rate", "Total Sale", "Cash", "Credit", "Address", "Invoice"]
    sales_rows = [sales_header]

    if valid_sales.empty:
        sales_rows.append(["—", "No sales or recoveries logged", "—", "0", "0", "0.00", "0.00", "0.00", "0.00", "—", "—"])
    else:
        for idx, r in valid_sales.reset_index(drop=True).iterrows():
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

    story.append(Spacer(1, 3))
    story.append(Paragraph("2. EXPENSES & DISBURSEMENTS", sec_style))

    valid_office = office[office["Expense Details"].astype(str).str.strip() != ""]
    valid_staff = staff[staff["Staff / Personnel Name"].astype(str).str.strip() != ""]

    exp_data = [["Expense Details", "Paid To", "Mode", "Amount (Rs.)"]]
    for _, r in valid_office.reset_index(drop=True).iterrows():
        exp_data.append([str(r["Expense Details"]), str(r["Paid To / Vendor"]), str(r["Payment Mode"]), money(r["Amount (Rs.)"])])
    if len(exp_data) == 1:
        exp_data.append(["No office expenses logged", "—", "—", money(0)])

    staff_pdf_data = [["Staff / Remittance", "Purpose", "Type", "Amount (Rs.)"]]
    for _, r in valid_staff.reset_index(drop=True).iterrows():
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
# RFC-COMPLIANT EMAIL FUNCTION (Double-EHLO Handshake)
# =========================================================

def email_pdf(pdf_bytes, sender, password, recipient):
    report_ref = st.session_state.get("report_no", "ALP-REPORT")
    staff_disp = staff_name.strip() if staff_name else "MR"
    route_disp = route.strip() if route else "—"

    clean_sender = sender.strip()
    clean_password = password.strip().replace(" ", "")
    clean_recipient = recipient.strip()

    if not clean_sender or not clean_password:
        return False, "Missing Credentials: Enter your Sender Gmail and App Password in the sidebar."

    msg = EmailMessage()
    filename = f"ALPINE_HERBS_Report_{report_ref}_{selected_date}.pdf"
    msg["Subject"] = f"[{report_ref}] Alpine Herbs Daily Report - {staff_disp} ({nepali_date(selected_date)})"
    msg["From"] = clean_sender
    msg["To"] = clean_recipient

    msg.set_content(
        f"Dear Management,\n\n"
        f"Attached is the daily field report for Alpine Herbs Pvt. Ltd.\n\n"
        f"Reference Code: {report_ref}\n"
        f"Date: {selected_date} ({nepali_date(selected_date)})\n"
        f"MR Name: {staff_disp}\n"
        f"Route: {route_disp}\n"
        f"Gross Cash Collected: {money(total_cash)}\n"
        f"Credit Given: {money(total_credit)}\n"
        f"Total Deductions: {money(total_expenses)}\n"
        f"Net Closing Cash to Deposit: {money(net_cash)}\n\n"
        f"Regards,\nField Operations System"
    )

    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=filename)

    context = ssl.create_default_context()

    # Protocol 1: Port 587 with required double-EHLO handshake
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()  # CRITICAL: Prevents Gmail from dropping connection
        server.login(clean_sender, clean_password)
        server.send_message(msg)
        server.quit()
        return True, f"Official PDF successfully emailed to {clean_recipient}!"
    except smtplib.SMTPAuthenticationError:
        return False, "Google Authentication Error: Gmail rejected the password. Please check your 16-character App Password."
    except Exception:
        # Protocol 2: Fallback to Port 465 SSL
        try:
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=30)
            server.login(clean_sender, clean_password)
            server.send_message(msg)
            server.quit()
            return True, f"Official PDF successfully emailed to {clean_recipient}!"
        except smtplib.SMTPAuthenticationError:
            return False, "Google Authentication Error: Gmail rejected the password. Please check your 16-character App Password."
        except Exception as err:
            return False, f"Connection Failed: {err}"

# =========================================================
# 5. SUBMIT & EXPORT
# =========================================================

st.subheader("5. Verification & Submission")

c_pin, c_sub1, c_sub2 = st.columns([1.2, 1.4, 1])

with c_pin:
    entered_pin = st.text_input(
        "Enter 8-Digit App Passcode:",
        type="password",
        max_chars=8,
        placeholder="8-digit passcode",
        help="Enter the 8-digit authorization passcode to submit."
    )

with c_sub1:
    st.write("")
    st.write("")
    if st.button("🚀 SUBMIT & EMAIL OFFICIAL PDF REPORT", type="primary", use_container_width=True):
        if str(entered_pin).strip() != REQUIRED_APP_PASSCODE:
            st.error("❌ Incorrect 8-Digit App Passcode. Enter the valid authorization code (default: 12345678).")
        elif not user_email.strip() or not user_password.strip():
            st.error("⚠️ Enter your Sender Gmail and App Password in the left sidebar before submitting.")
        else:
            with st.spinner("Generating PDF and sending email..."):
                pdf_bytes = create_pdf()
                st.session_state["report_pdf"] = pdf_bytes
                st.session_state["report_filename"] = f"ALPINE_HERBS_{st.session_state.get('report_no', 'REPORT')}.pdf"

                ok, msg = email_pdf(pdf_bytes, user_email, user_password, company_recipient)

                if ok:
                    st.balloons()
                    st.success(msg)
                    st.info("Report submitted! Resetting form for next entry...")
                    reset_form_to_blank()
                    st.rerun()
                else:
                    st.error(msg)
                    st.warning("⚠️ The email could not be sent. You can still download your generated PDF copy below.")

with c_sub2:
    st.write("")
    st.write("")
    if st.session_state.get("report_pdf") is not None:
        st.download_button(
            "⬇️ DOWNLOAD PDF COPY",
            data=st.session_state["report_pdf"],
            file_name=st.session_state.get("report_filename", "ALPINE_HERBS_REPORT.pdf"),
            mime="application/pdf",
            use_container_width=True
        )

st.markdown("---")
st.caption("🌿 ALPINE HERBS PVT. LTD. | Pharmaceutical Field Accounting System.")
