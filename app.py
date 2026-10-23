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
# PAGE CONFIGURATION & BRAND THEME
# =========================================================

st.set_page_config(
    page_title="ALPINE HERBS | Daily Field Report",
    page_icon="🌿",
    layout="wide"
)

ALPINE_DARK = "#0D2818"
ALPINE_PRIMARY = "#164E33"
ALPINE_ACCENT = "#2D7D52"
ALPINE_MINT = "#EAF2EC"
ALPINE_BORDER = "#C8DCCF"

st.markdown(f"""
<style>
.block-container {{
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1550px;
}}
.brand-header {{
    background: linear-gradient(135deg, {ALPINE_DARK} 0%, {ALPINE_PRIMARY} 100%);
    color: white;
    padding: 1.2rem 1.8rem;
    border-radius: 10px;
    margin-bottom: 1.2rem;
}}
.brand-title {{
    font-size: 1.7rem;
    font-weight: 800;
    margin: 0;
    color: #FFFFFF;
}}
.brand-sub {{
    font-size: 0.85rem;
    color: #D3E6DA;
    margin: 0.2rem 0 0 0;
}}
div[data-testid="stMetric"] {{
    background: {ALPINE_MINT} !important;
    border: 1px solid {ALPINE_BORDER} !important;
    border-top: 4px solid {ALPINE_ACCENT} !important;
    padding: 10px 14px !important;
    border-radius: 8px !important;
}}
div.stButton > button[kind="primary"] {{
    background: linear-gradient(180deg, {ALPINE_PRIMARY} 0%, {ALPINE_DARK} 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 700 !important;
    padding: 0.6rem 1.5rem;
    border-radius: 6px;
}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="brand-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div class="brand-title">🌿 ALPINE HERBS PVT. LTD.</div>
            <div class="brand-sub">BIRGUNJ, NEPAL &nbsp;|&nbsp; DAILY MEDICAL REPRESENTATIVE CLOSING</div>
        </div>
        <div style="text-align: right; font-size: 0.85rem; color: #E0EFE5;">
            <strong>Daily Report Form</strong>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def money(val):
    try:
        return f"Rs. {float(val or 0):,.2f}"
    except (TypeError, ValueError):
        return "Rs. 0.00"

def nepali_date(d):
    try:
        import nepali_datetime
        bs = nepali_datetime.date.from_datetime_date(d)
        return f"{bs.year:04d}-{bs.month:02d}-{bs.day:02d} B.S."
    except Exception:
        return "B.S. Date (nepali-datetime missing)"

def numeric_columns(df, columns):
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df

# BLANK SCHEMAS (Starts 100% empty)
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

def generate_new_ref(ad_date):
    suffix = uuid.uuid4().hex[:4].upper()
    return f"ALP-{ad_date.strftime('%Y%m%d')}-{suffix}"

# =========================================================
# SESSION STATE & RESET LOGIC
# =========================================================

if "form_version" not in st.session_state:
    st.session_state.form_version = 1

if "report_date" not in st.session_state:
    st.session_state.report_date = date.today()

if "report_no" not in st.session_state:
    st.session_state.report_no = generate_new_ref(st.session_state.report_date)

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

def reset_all_for_next_entry():
    """Wipes all data to blank and generates a new report code for the next entry."""
    st.session_state.form_version += 1
    st.session_state.report_no = generate_new_ref(st.session_state.report_date)
    st.session_state.sales = blank_sales()
    st.session_state.office = blank_office()
    st.session_state.staff = blank_staff()
    st.session_state.ledger = blank_ledger()
    # Keep MR name and Route so they don't have to re-type it every single day

# =========================================================
# SIDEBAR: CONFIGURATION & CREDENTIALS
# =========================================================

with st.sidebar:
    st.header("⚙️ Report & Mail Settings")
    st.info(f"**Reference Code:**\n`{st.session_state.report_no}`")

    target_email = st.text_input(
        "Send Report To:",
        value=st.secrets.get("smtp_to", "Alpineherbsinfo@gmail.com")
    )

    with st.expander("🔑 Email Server Settings (Fix Connection)"):
        st.caption("If not set in Streamlit Secrets, configure here:")
        smtp_user = st.text_input(
            "Sender Gmail Address:",
            value=st.secrets.get("smtp_user", "")
        )
        smtp_password = st.text_input(
            "Gmail 16-Digit App Password:",
            type="password",
            value=st.secrets.get("smtp_password", ""),
            help="Generate from your Google Account -> Security -> App passwords"
        )
        use_ssl = st.checkbox("Use SSL (Port 465) - Recommended", value=True)

    if st.button("🔄 Clear Form & Start Blank"):
        reset_all_for_next_entry()
        st.rerun()

# =========================================================
# METADATA ENTRY
# =========================================================

with st.container(border=True):
    st.subheader("Report Information")
    c1, c2, c3, c4 = st.columns([1.1, 1.3, 1.3, 1.1])

    with c1:
        report_date = st.date_input("English Date", value=st.session_state.report_date)
        st.session_state.report_date = report_date
        st.caption(f"🇳🇵 Miti: **{nepali_date(report_date)}**")

    with c2:
        staff_name = st.text_input("MR / Staff Name", value=st.session_state.staff_name, placeholder="e.g. Pritam Gupta")
        st.session_state.staff_name = staff_name

    with c3:
        route = st.text_input("Route / Area", value=st.session_state.route, placeholder="e.g. Birgunj To Lautan")
        st.session_state.route = route

    with c4:
        st.text_input("Report Reference No.", value=st.session_state.report_no, disabled=True)

# =========================================================
# 1. SALES ENTRIES
# =========================================================

st.subheader("1. Sales & Cash Collections")
st.caption("Click any empty cell to type. Use the table controls to add or delete rows.")

f_key = st.session_state.form_version

sales = st.data_editor(
    st.session_state.sales,
    num_rows="dynamic",
    hide_index=True,
    use_container_width=True,
    key=f"sales_grid_{f_key}",
    column_config={
        "Client / Party Name": st.column_config.TextColumn("Client / Party Name"),
        "Goods / Product Name": st.column_config.TextColumn("Goods / Product Name"),
        "Qty": st.column_config.NumberColumn("Qty", min_value=0.0, step=1.0),
        "FOC Qty": st.column_config.NumberColumn("FOC (Free)", min_value=0.0, step=1.0),
        "Sale Rate (Rs.)": st.column_config.NumberColumn("Sale Rate (Rs.)", min_value=0.0, format="%.2f"),
        "Cash Collected (Rs.)": st.column_config.NumberColumn("Cash Collected (Rs.)", min_value=0.0, format="%.2f"),
        "Credit Given (Rs.)": st.column_config.NumberColumn("Credit Given (Rs.)", min_value=0.0, format="%.2f"),
        "Client Address": st.column_config.TextColumn("Client Address"),
        "Invoice No.": st.column_config.TextColumn("Invoice No.")
    }
)

sales = numeric_columns(sales, ["Qty", "FOC Qty", "Sale Rate (Rs.)", "Cash Collected (Rs.)", "Credit Given (Rs.)"])

# Calculate row total
calc_sale = sales["Qty"] * sales["Sale Rate (Rs.)"]
direct_cash_credit = sales["Cash Collected (Rs.)"] + sales["Credit Given (Rs.)"]
sales["Total Sale (Rs.)"] = calc_sale.where(calc_sale > 0, direct_cash_credit)

st.session_state.sales = sales.drop(columns=["Total Sale (Rs.)"], errors="ignore")

total_sales = float(sales["Total Sale (Rs.)"].sum())
total_cash = float(sales["Cash Collected (Rs.)"].sum())
total_credit = float(sales["Credit Given (Rs.)"].sum())
total_foc = float(sales["FOC Qty"].sum())
total_qty = float(sales["Qty"].sum())

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total Sales Billed", money(total_sales))
m2.metric("Gross Cash Collected", money(total_cash))
m3.metric("Credit Given (Debit)", money(total_credit))
m4.metric("Total Units Sold", f"{total_qty:g}")
m5.metric("Free (FOC) Units", f"{total_foc:g}")

st.divider()

# =========================================================
# 2. EXPENSES & 3. STAFF ADVANCES
# =========================================================

col_exp1, col_exp2 = st.columns(2)

with col_exp1:
    st.subheader("2. Operating / Office Expenses")
    office = st.data_editor(
        st.session_state.office,
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        key=f"office_grid_{f_key}",
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

with col_exp2:
    st.subheader("3. Staff Advances & eSewa Remittance")
    staff = st.data_editor(
        st.session_state.staff,
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        key=f"staff_grid_{f_key}",
        column_config={
            "Staff / Personnel Name": st.column_config.TextColumn("Staff / Receiver"),
            "Purpose / Details": st.column_config.TextColumn("Purpose"),
            "Payment Type": st.column_config.SelectboxColumn("Type", options=["Staff Advance", "Remittance / eSewa", "Allowance", "Salary", "Other"]),
            "Amount (Rs.)": st.column_config.NumberColumn("Amount (Rs.)", min_value=0.0, format="%.2f"),
            "Remarks": st.column_config.TextColumn("Remarks")
        }
    )
    staff = numeric_columns(staff, ["Amount (Rs.)"])
    st.session_state.staff = staff
    staff_total = float(staff["Amount (Rs.)"].sum())

total_expenses = office_total + staff_total
net_cash = total_cash - total_expenses

# =========================================================
# 4. FINANCIAL CLOSING SUMMARY
# =========================================================

st.subheader("4. Closing Summary")
with st.container(border=True):
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Gross Cash Collected", money(total_cash))
    s2.metric("Total Expenses & Advances", money(total_expenses))
    s3.metric("NET CASH TO HANDOVER", money(net_cash))
    s4.metric("Credit Given", money(total_credit))

# =========================================================
# PDF GENERATION ENGINE
# =========================================================

def create_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=8 * mm,
        bottomMargin=8 * mm,
        title="Alpine Herbs Daily Report"
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("AHTitle", parent=styles["Title"], fontSize=15, leading=17, textColor=colors.HexColor(ALPINE_DARK), alignment=1)
    sec_style = ParagraphStyle("AHSec", parent=styles["Heading2"], fontSize=9, leading=11, textColor=colors.HexColor(ALPINE_PRIMARY), spaceBefore=5, spaceAfter=3)
    cell_style = ParagraphStyle("AHCell", parent=styles["Normal"], fontSize=6.5, leading=8, textColor=colors.HexColor("#222222"))

    story = [
        Paragraph("<b>ALPINE HERBS PVT. LTD.</b>", title_style),
        Paragraph("Birgunj, Nepal &nbsp;|&nbsp; Daily Field Report", ParagraphStyle("Sub", parent=styles["Normal"], alignment=1, fontSize=8, leading=10, textColor=colors.HexColor("#444"), spaceAfter=5))
    ]

    # Meta Table
    info_data = [
        ["English Date", report_date.strftime("%d-%b-%Y"), "Nepali Miti", nepali_date(report_date)],
        ["MR / Personnel", staff_name or "—", "Route / Location", route or "—"],
        ["Reference No.", st.session_state.report_no, "Generated At", datetime.now().strftime("%d-%b-%Y %H:%M")]
    ]
    meta_table = Table(info_data, colWidths=[28*mm, 75*mm, 35*mm, 139*mm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor(ALPINE_MINT)),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor(ALPINE_MINT)),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(ALPINE_BORDER)),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)
    ]))
    story.append(meta_table)

    # Filter out empty rows
    valid_sales = sales[sales["Client / Party Name"].str.strip() != ""]

    story.append(Paragraph("1. SALES ENTRIES & RECOVERIES", sec_style))
    sales_rows = [["S.N.", "Client / Party Name", "Goods / Product Name", "Qty", "FOC", "Rate", "Total Sale", "Cash", "Credit", "Address", "Invoice"]]

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

    t_sales = Table(sales_rows, colWidths=[8*mm, 45*mm, 42*mm, 11*mm, 10*mm, 18*mm, 23*mm, 22*mm, 22*mm, 52*mm, 24*mm], repeatRows=1)
    t_sales.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(ALPINE_PRIMARY)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 6.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(ALPINE_BORDER)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(ALPINE_MINT)])
    ]))
    story.append(t_sales)

    # Expenses Table
    story.append(Paragraph("2. FIELD EXPENSES & REMITTANCES", sec_style))
    exp_rows = [["Type", "Details", "Paid To / Staff", "Mode", "Amount (Rs.)"]]

    valid_office = office[office["Expense Details"].str.strip() != ""]
    valid_staff = staff[staff["Staff / Personnel Name"].str.strip() != ""]

    for _, r in valid_office.iterrows():
        exp_rows.append(["Operating", str(r["Expense Details"]), str(r["Paid To / Vendor"]), str(r["Payment Mode"]), money(r["Amount (Rs.)"])])
    for _, r in valid_staff.iterrows():
        exp_rows.append(["Staff/eSewa", str(r["Purpose / Details"]), str(r["Staff / Personnel Name"]), str(r["Payment Type"]), money(r["Amount (Rs.)"])])

    if len(exp_rows) == 1:
        exp_rows.append(["—", "No expenses or advances logged", "—", "—", "Rs. 0.00"])

    t_exp = Table(exp_rows, colWidths=[25*mm, 90*mm, 70*mm, 45*mm, 47*mm], repeatRows=1)
    t_exp.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(ALPINE_PRIMARY)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 6.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(ALPINE_BORDER))
    ]))
    story.append(t_exp)

    # Summary
    story.append(Paragraph("3. RECONCILIATION SUMMARY", sec_style))
    sum_data = [
        ["Total Billed Sales", money(total_sales), "Gross Cash Collected", money(total_cash)],
        ["Total Credit Given", money(total_credit), "Total Field Expenses", money(total_expenses)],
        ["Total Units Sold", f"{total_qty:g}", "NET CASH IN HAND", money(net_cash)]
    ]
    t_sum = Table(sum_data, colWidths=[50*mm, 45*mm, 50*mm, 45*mm])
    t_sum.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(ALPINE_BORDER)),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(ALPINE_MINT))
    ]))
    story.append(t_sum)

    # Signatures
    story.append(Spacer(1, 10))
    sig_data = [["Prepared by (MR): ____________________", "Checked by (Accounts): ____________________", "Approved by: ____________________"]]
    t_sig = Table(sig_data, colWidths=[92*mm, 92*mm, 93*mm])
    t_sig.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 7), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    story.append(t_sig)

    doc.build(story)
    return buffer.getvalue()

# =========================================================
# EMAIL SUBMISSION ENGINE (SSL PORT 465)
# =========================================================

def send_email_report(pdf_bytes):
    # Retrieve credentials: UI inputs take priority, fallback to secrets
    sender = smtp_user.strip() or st.secrets.get("smtp_user", "")
    password = smtp_password.strip() or st.secrets.get("smtp_password", "")
    host = st.secrets.get("smtp_host", "smtp.gmail.com")

    if not sender or not password:
        return False, "Missing credentials: Please enter your Sender Gmail and App Password in the sidebar."

    try:
        msg = EmailMessage()
        filename = f"ALPINE_HERBS_{st.session_state.report_no}_{report_date}.pdf"
        msg["Subject"] = f"[{st.session_state.report_no}] Daily Report - {staff_name or 'MR'} ({nepali_date(report_date)})"
        msg["From"] = sender
        msg["To"] = target_email

        msg.set_content(
            f"Dear Team,\n\n"
            f"Attached is the daily closing report for Alpine Herbs Pvt. Ltd.\n\n"
            f"Ref: {st.session_state.report_no}\n"
            f"Date: {report_date} ({nepali_date(report_date)})\n"
            f"MR Name: {staff_name}\n"
            f"Route: {route}\n"
            f"Gross Cash Collected: {money(total_cash)}\n"
            f"Credit Given: {money(total_credit)}\n"
            f"Expenses & Advances: {money(total_expenses)}\n"
            f"NET CASH IN HAND: {money(net_cash)}\n\n"
            f"Regards,\nField Operations"
        )

        msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=filename)

        # Connection Logic: Port 465 (SSL) is far more reliable on cloud servers than Port 587
        if use_ssl:
            with smtplib.SMTP_SSL(host, 465, timeout=20) as server:
                server.login(sender, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, 587, timeout=20) as server:
                server.starttls()
                server.login(sender, password)
                server.send_message(msg)

        return True, f"Report successfully emailed to {target_email}!"

    except smtplib.SMTPAuthenticationError:
        return False, "Authentication Error: Google rejected the login. Please check that you are using a 16-digit Google App Password, not your normal password."
    except Exception as e:
        return False, f"Connection Error: {str(e)}"

# =========================================================
# 5. SUBMISSION & PDF SAVE
# =========================================================

st.subheader("5. Submit Report")
st.write("Submitting will generate the official PDF, email it, and clear the screen for the next daily entry.")

c_btn, c_down = st.columns([1.5, 1])

with c_btn:
    if st.button("🚀 SUBMIT, EMAIL & START NEW ENTRY", type="primary", use_container_width=True):
        with st.spinner("Generating PDF and sending email..."):
            pdf_data = create_pdf()
            st.session_state["last_pdf"] = pdf_data
            st.session_state["last_ref"] = st.session_state.report_no
            
            ok, msg = send_email_report(pdf_data)
            
            if ok:
                st.balloons()
                st.success(msg)
                st.info("Form submitted successfully! Resetting to a blank form for your next entry...")
                # Automatically reset to blank
                reset_all_for_next_entry()
                st.rerun()
            else:
                st.error(f"⚠️ {msg}")
                st.warning("The PDF has been generated and saved below so you don't lose your work.")

with c_down:
    if "last_pdf" in st.session_state:
        st.download_button(
            "⬇️ DOWNLOAD GENERATED PDF",
            data=st.session_state["last_pdf"],
            file_name=f"Report_{st.session_state.get('last_ref', 'EOD')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

st.markdown("---")
st.caption("🌿 ALPINE HERBS PVT. LTD. | Daily Field Reporting Portal. PDF format only.")
