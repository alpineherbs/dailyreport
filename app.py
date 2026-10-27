import streamlit as st
import pandas as pd
from datetime import date, datetime
from io import BytesIO
import uuid
import requests

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# =========================================================
# 1. USER AUTHENTICATION & ACCESS CONTROL (EDIT USERS HERE)
# =========================================================
AUTHORIZED_USERS = {
    "Alpine": "AHP@123",
    "Pritam": "Pritam@2024",
    "Admin": "AlpineAdmin@123",
    "Manager": "Alpine@Birgunj"
}

# =========================================================
# 2. GOOGLE APPS SCRIPT WEB APP LINK
# =========================================================
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzqcy8A442WqYY8gFjPRojpLeDZw3GhQnyo7Y8PadW6vZ1YW2QvkIceFqxkZuo8166R/exec"

def sync_all_data_to_google_sheet(sales_df, office_df, staff_df, staff_name_val, report_ref, date_val):
    if not WEB_APP_URL or not WEB_APP_URL.startswith("http"):
        st.error("❌ Google Apps Script URL is empty or invalid.")
        return False, 0

    sales_list = []
    for _, row in sales_df.iterrows():
        c_name = str(row.get("Client / Party Name", "")).strip()
        p_name = str(row.get("Goods / Product Name", "")).strip()
        qty_val = float(row.get("Qty", 0))
        rate_val = float(row.get("Sale Rate (Rs.)", 0))
        cash_val = float(row.get("Cash Collected (Rs.)", 0))
        credit_val = float(row.get("Credit Given (Rs.)", 0))
        total_val = float(row.get("Total Sale (Rs.)", 0))

        if qty_val > 0 or cash_val > 0 or credit_val > 0 or total_val > 0 or (p_name and p_name != "nan"):
            sales_list.append({
                "invoice": str(row.get("Invoice No.", "INV-01")),
                "client_name": c_name if c_name and c_name != "nan" else "Walk-in Party",
                "address": str(row.get("Client Address", "Birgunj")),
                "product_name": p_name if p_name and p_name != "nan" else "General Stock",
                "qty": qty_val,
                "rate": rate_val,
                "cash_collected": cash_val,
                "credit_given": credit_val,
                "total_sale": total_val
            })

    office_list = []
    for _, row in office_df.iterrows():
        details = str(row.get("Expense Details", "")).strip()
        amt = float(row.get("Amount (Rs.)", 0))
        if details and details != "nan" and amt > 0:
            office_list.append({
                "details": details,
                "paid_to": str(row.get("Paid To / Vendor", "Vendor")),
                "mode": str(row.get("Payment Mode", "Cash")),
                "amount": amt,
                "remarks": str(row.get("Remarks", ""))
            })

    staff_list = []
    for _, row in staff_df.iterrows():
        p_name = str(row.get("Staff / Personnel Name", "")).strip()
        amt = float(row.get("Amount (Rs.)", 0))
        if p_name and p_name != "nan" and amt > 0:
            staff_list.append({
                "personnel_name": p_name,
                "purpose": str(row.get("Purpose / Details", "Advance")),
                "type": str(row.get("Payment Type", "Staff Advance")),
                "amount": amt,
                "remarks": str(row.get("Remarks", ""))
            })

    total_records = len(sales_list) + len(office_list) + len(staff_list)
    if total_records == 0:
        st.warning("⚠️ No valid rows found to sync.")
        return True, 0

    master_payload = {
        "date": str(date_val),
        "report_no": str(report_ref),
        "staff_name": str(staff_name_val if staff_name_val else "Field MR"),
        "sales": sales_list,
        "expenses": office_list,
        "advances": staff_list
    }

    try:
        response = requests.post(WEB_APP_URL, json=master_payload, timeout=25, allow_redirects=True)
        if response.status_code == 200:
            try:
                res_json = response.json()
                if res_json.get("status") == "success":
                    return True, res_json.get("records_synced", total_records)
                else:
                    st.error(f"⚠️ Google Script Error: {res_json.get('message')}")
                    return False, 0
            except Exception:
                return True, total_records
        else:
            st.error(f"❌ Google Server HTTP {response.status_code}")
            return False, 0
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Network Error: {e}")
        return False, 0

# =========================================================
# 3. PAGE INITIALIZATION & AUTHENTICATION
# =========================================================
st.set_page_config(page_title="ALPINE HERBS | Daily Operations Portal", page_icon="🌿", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["current_user"] = ""

if not st.session_state["authenticated"]:
    st.markdown("""
    <div style="text-align: center; margin-top: 3rem; margin-bottom: 2rem;">
        <h1 style="color: #0D2818; font-weight: 800; font-size: 2.3rem; margin-bottom: 0;">🌿 ALPINE HERBS PVT. LTD.</h1>
        <p style="color: #164E33; font-size: 1rem; font-weight: 600; letter-spacing: 0.5px;">
            PHARMACEUTICAL FIELD CLOSING & AUDIT SYSTEM (ISO GMP COMPLIANT)
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_l1, col_l2, col_l3 = st.columns([1, 1.1, 1])
    with col_l2:
        with st.container(border=True):
            st.markdown("#### 🔐 Staff Sign In")
            login_user = st.text_input("Username / MR Code", placeholder="e.g. Alpine or Pritam")
            login_pass = st.text_input("Password", type="password", placeholder="Enter password")
            st.write("")
            if st.button("🔑 Login to Portal", type="primary", use_container_width=True):
                user_clean = login_user.strip()
                pass_clean = login_pass.strip()
                if user_clean in AUTHORIZED_USERS and AUTHORIZED_USERS[user_clean] == pass_clean:
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"] = user_clean
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password.")
    st.stop()

# =========================================================
# 4. APP STYLING & HELPERS
# =========================================================
st.markdown("""
<style>
.block-container { padding-top: 1.2rem; padding-bottom: 2.5rem; max-width: 1560px; }
.brand-header { background: linear-gradient(135deg, #0D2818 0%, #164E33 100%); color: white; padding: 1.2rem 1.8rem; border-radius: 10px; margin-bottom: 1.2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.06); }
.brand-title { font-size: 1.65rem; font-weight: 800; color: #FFFFFF; letter-spacing: 0.5px; }
.brand-sub { font-size: 0.85rem; color: #D3E6DA; font-weight: 500; }
h3, h2, h1 { color: #164E33 !important; font-weight: 700; }
div[data-testid="stMetric"] { background: #FFFFFF !important; border: 1px solid #D5E4DB !important; border-top: 4px solid #164E33 !important; padding: 12px 16px !important; border-radius: 8px !important; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
div[data-testid="stMetricLabel"] { font-size: 0.75rem !important; font-weight: 700 !important; color: #164E33 !important; text-transform: uppercase; }
div[data-testid="stMetricValue"] { font-size: 1.25rem !important; font-weight: 800 !important; color: #0D2818 !important; }
.helper-tag { background: #EBF5F0; border-left: 3px solid #2D7D52; padding: 8px 12px; font-size: 0.82rem; color: #164E33; border-radius: 4px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

logged_user = st.session_state.get("current_user", "Staff")

def money(value):
    try: return f"Rs. {float(value or 0):,.2f}"
    except: return "Rs. 0.00"

def nepali_date(d):
    try:
        import nepali_datetime
        if not isinstance(d, (date, datetime)): d = date.today()
        bs = nepali_datetime.date.from_datetime_date(d)
        return f"{bs.year:04d}-{bs.month:02d}-{bs.day:02d} B.S."
    except Exception:
        return "Nepali Calendar Active"

def generate_report_no(d):
    if not isinstance(d, (date, datetime)): d = date.today()
    return f"ALP-{d.strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

# Master Table Data Structures
def init_sales():
    return pd.DataFrame([
        {"Invoice No.": "INV-01", "Client / Party Name": "", "Client Address": "Birgunj", "Goods / Product Name": "", "Qty": 0.0, "Sale Rate (Rs.)": 0.0, "Cash Collected (Rs.)": 0.0},
        {"Invoice No.": "INV-02", "Client / Party Name": "", "Client Address": "Birgunj", "Goods / Product Name": "", "Qty": 0.0, "Sale Rate (Rs.)": 0.0, "Cash Collected (Rs.)": 0.0},
    ])

def init_office():
    return pd.DataFrame([
        {"Expense Details": "", "Paid To / Vendor": "", "Payment Mode": "Cash", "Amount (Rs.)": 0.0, "Remarks": ""}
    ])

def init_staff():
    return pd.DataFrame([
        {"Staff / Personnel Name": "", "Purpose / Details": "", "Payment Type": "Staff Advance", "Amount (Rs.)": 0.0, "Remarks": ""}
    ])

if "sales_data" not in st.session_state: st.session_state["sales_data"] = init_sales()
if "office_data" not in st.session_state: st.session_state["office_data"] = init_office()
if "staff_data" not in st.session_state: st.session_state["staff_data"] = init_staff()
if "report_date" not in st.session_state: st.session_state["report_date"] = date.today()
if "report_no" not in st.session_state: st.session_state["report_no"] = generate_report_no(date.today())

def reset_all_fields():
    st.session_state["report_no"] = generate_report_no(st.session_state.get("report_date", date.today()))
    st.session_state["sales_data"] = init_sales()
    st.session_state["office_data"] = init_office()
    st.session_state["staff_data"] = init_staff()
    if "submitted_pdf" in st.session_state: del st.session_state["submitted_pdf"]

# =========================================================
# 5. TOP HEADER
# =========================================================
st.markdown(f"""
<div class="brand-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div class="brand-title">🌿 ALPINE HERBS PVT. LTD.</div>
            <div class="brand-sub">BIRGUNJ, NEPAL &nbsp;|&nbsp; MEDICAL REPRESENTATIVE DAILY FIELD CLOSING</div>
        </div>
        <div style="text-align: right; font-size: 0.82rem; color: #E0EFE5;">
            <div>Logged as: <strong>{logged_user}</strong></div>
            <div>ISO 9001:2015 & GMP Certified</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Tour Metadata Row
c1, c2, c3, c4 = st.columns([1.1, 1.3, 1.4, 1.1])
with c1:
    selected_date = st.date_input("Date (A.D.)", value=st.session_state.get("report_date", date.today()))
    st.session_state["report_date"] = selected_date
    st.caption(f"🇳🇵 **Nepali Miti:** `{nepali_date(selected_date)}`")
with c2:
    staff_name = st.text_input("MR / Representative Name", value=st.session_state.get("saved_mr_name", logged_user if logged_user != "Alpine" else "Pritam Gupta"))
    st.session_state["saved_mr_name"] = staff_name
with c3:
    route = st.text_input("Territory / Route Covered", placeholder="e.g. Birgunj — Lautan — Kalaiya")
with c4:
    st.text_input("Report Reference No.", value=st.session_state.get("report_no", ""), disabled=True)

st.write("")

# =========================================================
# 6. REAL-TIME DATA COMPUTATION (RUNS ON EVERY KEYSTROKE)
# =========================================================
# Numeric validation
sales_df = st.session_state["sales_data"].copy()
for col in ["Qty", "Sale Rate (Rs.)", "Cash Collected (Rs.)"]:
    sales_df[col] = pd.to_numeric(sales_df[col], errors="coerce").fillna(0.0)

# Compute Real-Time Values
computed_total = sales_df["Qty"] * sales_df["Sale Rate (Rs.)"]
sales_df["Total Sale (Rs.)"] = computed_total
sales_df["Credit Given (Rs.)"] = (computed_total - sales_df["Cash Collected (Rs.)"]).clip(lower=0.0)

# Office & Staff calculations
office_df = st.session_state["office_data"].copy()
office_df["Amount (Rs.)"] = pd.to_numeric(office_df["Amount (Rs.)"], errors="coerce").fillna(0.0)

staff_df = st.session_state["staff_data"].copy()
staff_df["Amount (Rs.)"] = pd.to_numeric(staff_df["Amount (Rs.)"], errors="coerce").fillna(0.0)

# Financial Aggregates
total_sales_billed = float(sales_df["Total Sale (Rs.)"].sum())
total_cash_collected = float(sales_df["Cash Collected (Rs.)"].sum())
total_credit_given = float(sales_df["Credit Given (Rs.)"].sum())
total_office_exp = float(office_df["Amount (Rs.)"].sum())
total_staff_adv = float(staff_df["Amount (Rs.)"].sum())
total_expenses_all = total_office_exp + total_staff_adv
net_cash_in_hand = total_cash_collected - total_expenses_all

# =========================================================
# 7. LIVE REAL-TIME FINANCIAL SUMMARY BAR
# =========================================================
st.markdown("##### 📊 Live Real-Time Financial Summary *(Updates dynamically)*")
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Total Sales Billed", money(total_sales_billed))
m2.metric("Gross Cash Collected", money(total_cash_collected))
m3.metric("Credit Given", money(total_credit_given))
m4.metric("Operating Expenses", money(total_office_exp))
m5.metric("Staff Advances", money(total_staff_adv))
m6.metric(
    "Net Cash In Hand", 
    money(net_cash_in_hand), 
    delta=f"{money(net_cash_in_hand)} Balance", 
    delta_color="normal" if net_cash_in_hand >= 0 else "inverse"
)

if net_cash_in_hand < 0:
    st.warning("⚠️ **Notice:** Total disbursements (expenses + advances) exceed cash collected today. Net Cash is negative.")

st.divider()

# =========================================================
# 8. DATA ENTRY TABS (OPTIMIZED WITH TAB & ENTER NAVIGATION)
# =========================================================
tab_sales, tab_expenses, tab_advances = st.tabs([
    "🛒 1. Sales & Collections Ledger",
    "🏢 2. Operating / Office Expenses",
    "👥 3. Staff Advances & Tour Imprest"
])

# --- TAB 1: SALES LEDGER ---
with tab_sales:
    st.markdown('<div class="helper-tag">💡 <b>Fast Navigation:</b> Press <b>Tab</b> to jump horizontally across columns; press <b>Enter</b> to save and move down a row. Computed columns are locked automatically.</div>', unsafe_allow_html=True)
    
    # Configure columns for smooth Excel-like keyboard flow
    sales_column_config = {
        "Invoice No.": st.column_config.TextColumn("Invoice #", width="small", default="INV-01", required=True),
        "Client / Party Name": st.column_config.TextColumn("Chemist / Party Name", width="medium", required=True),
        "Client Address": st.column_config.TextColumn("Town / Address", width="small", default="Birgunj"),
        "Goods / Product Name": st.column_config.TextColumn("Product Description", width="medium", required=True),
        "Qty": st.column_config.NumberColumn("Qty", min_value=0.0, step=1.0, default=0.0, width="small"),
        "Sale Rate (Rs.)": st.column_config.NumberColumn("Rate (Rs.)", min_value=0.0, step=10.0, default=0.0, format="Rs. %.2f", width="small"),
        "Cash Collected (Rs.)": st.column_config.NumberColumn("Cash Recd (Rs.)", min_value=0.0, step=50.0, default=0.0, format="Rs. %.2f", width="small"),
        "Total Sale (Rs.)": st.column_config.NumberColumn("Total Billed", disabled=True, format="Rs. %.2f", width="small"),
        "Credit Given (Rs.)": st.column_config.NumberColumn("Credit Bal", disabled=True, format="Rs. %.2f", width="small")
    }

    # Display editor with automated columns
    edited_sales = st.data_editor(
        sales_df,
        column_config=sales_column_config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="sales_editor"
    )
    # Save back edits
    st.session_state["sales_data"] = edited_sales[["Invoice No.", "Client / Party Name", "Client Address", "Goods / Product Name", "Qty", "Sale Rate (Rs.)", "Cash Collected (Rs.)"]]

# --- TAB 2: OFFICE EXPENSES ---
with tab_expenses:
    st.markdown('<div class="helper-tag">💡 Record all daily fuel, food, logistics, and local operational costs incurred on this tour.</div>', unsafe_allow_html=True)
    
    office_column_config = {
        "Expense Details": st.column_config.TextColumn("Expense Particulars", width="large", required=True),
        "Paid To / Vendor": st.column_config.TextColumn("Paid To / Vendor Name", width="medium", default="Vendor"),
        "Payment Mode": st.column_config.SelectboxColumn("Payment Mode", width="small", options=["Cash", "eSewa", "Khalti", "Bank Transfer"], default="Cash", required=True),
        "Amount (Rs.)": st.column_config.NumberColumn("Amount (Rs.)", min_value=0.0, step=20.0, default=0.0, format="Rs. %.2f", width="small", required=True),
        "Remarks": st.column_config.TextColumn("Remarks / Station", width="medium")
    }

    edited_office = st.data_editor(
        office_df[["Expense Details", "Paid To / Vendor", "Payment Mode", "Amount (Rs.)", "Remarks"]],
        column_config=office_column_config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="office_editor"
    )
    st.session_state["office_data"] = edited_office

# --- TAB 3: STAFF ADVANCES ---
with tab_advances:
    st.markdown('<div class="helper-tag">💡 Record per-diem allowances, field advances, or emergency funds given to personnel.</div>', unsafe_allow_html=True)
    
    staff_column_config = {
        "Staff / Personnel Name": st.column_config.TextColumn("Personnel Name", width="medium", required=True),
        "Purpose / Details": st.column_config.TextColumn("Advance Purpose / Station", width="large", default="Tour Advance"),
        "Payment Type": st.column_config.SelectboxColumn("Category", width="medium", options=["Staff Advance", "TA/DA Allowance", "Emergency Medical", "Other"], default="Staff Advance"),
        "Amount (Rs.)": st.column_config.NumberColumn("Amount (Rs.)", min_value=0.0, step=100.0, default=0.0, format="Rs. %.2f", width="small", required=True),
        "Remarks": st.column_config.TextColumn("Remarks", width="medium")
    }

    edited_staff = st.data_editor(
        staff_df[["Staff / Personnel Name", "Purpose / Details", "Payment Type", "Amount (Rs.)", "Remarks"]],
        column_config=staff_column_config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="staff_editor"
    )
    st.session_state["staff_data"] = edited_staff

# =========================================================
# 9. PROFESSIONAL PDF VOUCHER BUILDER
# =========================================================
def generate_corporate_pdf(rep_no, dt, name, rt, s_df, o_df, st_df, t_sales, t_cash, t_credit, t_exp, t_adv, net_c):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        leftMargin=10*mm, rightMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm
    )
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(name="TitleStyle", parent=styles["Heading1"], fontSize=15, leading=18, textColor=colors.HexColor("#0D2818"), spaceAfter=2)
    meta_style = ParagraphStyle(name="MetaStyle", parent=styles["Normal"], fontSize=8.5, leading=11, textColor=colors.HexColor("#333333"))
    table_header_style = ParagraphStyle(name="THStyle", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.white, fontName="Helvetica-Bold", alignment=1)
    table_cell_style = ParagraphStyle(name="TCCStyle", parent=styles["Normal"], fontSize=7.5, leading=9)

    story = [
        Paragraph("<b>ALPINE HERBS PVT. LTD. &nbsp;|&nbsp; DAILY FIELD CLOSING VOUCHER</b>", title_style),
        Paragraph(f"<b>Report Ref:</b> {rep_no} &nbsp;|&nbsp; <b>Date:</b> {dt} ({nepali_date(dt)}) &nbsp;|&nbsp; <b>MR / Representative:</b> {name} &nbsp;|&nbsp; <b>Route:</b> {rt or 'Birgunj Sector'}", meta_style),
        Spacer(1, 3*mm)
    ]

    # Executive Summary Box
    summary_matrix = [
        ["Total Sales Billed", "Credit Given", "Gross Cash Collected", "Office Expenses", "Staff Advances", "Net Cash in Hand"],
        [money(t_sales), money(t_credit), money(t_cash), money(t_exp), money(t_adv), money(net_c)]
    ]
    sum_table = Table(summary_matrix, colWidths=[46*mm]*6)
    sum_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#164E33")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#B0C4B7")),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F5FAF7")),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (5,1
