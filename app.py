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
    if not WEB_APP_URL or not str(WEB_APP_URL).startswith("http"):
        st.error("Google Apps Script URL is empty or invalid.")
        return False, 0

    sales_list = []
    for _, row in sales_df.iterrows():
        c_name = str(row.get("Client / Party Name", "")).strip()
        p_name = str(row.get("Goods / Product Name", "")).strip()
        qty_val = float(row.get("Qty", 0.0) or 0.0)
        rate_val = float(row.get("Sale Rate (Rs.)", 0.0) or 0.0)
        cash_val = float(row.get("Cash Collected (Rs.)", 0.0) or 0.0)
        credit_val = float(row.get("Credit Given (Rs.)", 0.0) or 0.0)
        total_val = float(row.get("Total Sale (Rs.)", 0.0) or 0.0)

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
        amt = float(row.get("Amount (Rs.)", 0.0) or 0.0)
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
        amt = float(row.get("Amount (Rs.)", 0.0) or 0.0)
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
        st.warning("No valid rows found to sync.")
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
                    st.error("Google Script Error: " + str(res_json.get("message", "Unknown error")))
                    return False, 0
            except Exception:
                return True, total_records
        else:
            st.error("Google Server HTTP Status: " + str(response.status_code))
            return False, 0
    except requests.exceptions.RequestException as e:
        st.error("Network Error: " + str(e))
        return False, 0

# =========================================================
# 3. PAGE INITIALIZATION & AUTHENTICATION
# =========================================================
st.set_page_config(page_title="ALPINE HERBS - Operations Portal", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["current_user"] = ""

if not st.session_state["authenticated"]:
    st.title("ALPINE HERBS PVT. LTD.")
    st.subheader("Field Operations & Closing Portal")
    st.divider()

    c_pad1, c_box, c_pad2 = st.columns([1, 1.2, 1])
    with c_box:
        st.markdown("### Staff Sign In")
        login_user = st.text_input("Username / MR Code", placeholder="e.g. Alpine or Pritam")
        login_pass = st.text_input("Password", type="password", placeholder="Enter password")
        st.write("")
        if st.button("Login to Portal", type="primary", use_container_width=True):
            user_clean = login_user.strip()
            pass_clean = login_pass.strip()
            if user_clean in AUTHORIZED_USERS and AUTHORIZED_USERS[user_clean] == pass_clean:
                st.session_state["authenticated"] = True
                st.session_state["current_user"] = user_clean
                st.rerun()
            else:
                st.error("Invalid username or password.")
    st.stop()

# =========================================================
# 4. APP HELPERS & DATA CACHE
# =========================================================
logged_user = st.session_state.get("current_user", "Staff")

def money(val):
    try:
        return "Rs. {:,.2f}".format(float(val or 0.0))
    except Exception:
        return "Rs. 0.00"

def nepali_date(d):
    try:
        import nepali_datetime
        if not isinstance(d, (date, datetime)):
            d = date.today()
        bs = nepali_datetime.date.from_datetime_date(d)
        return "{:04d}-{:02d}-{:02d} B.S.".format(bs.year, bs.month, bs.day)
    except Exception:
        return "Nepali Calendar Active"

def generate_report_no(d):
    if not isinstance(d, (date, datetime)):
        d = date.today()
    return "ALP-" + d.strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:4].upper()

def init_sales():
    return pd.DataFrame([
        {"Invoice No.": "INV-01", "Client / Party Name": "", "Client Address": "Birgunj", "Goods / Product Name": "", "Qty": 0.0, "Sale Rate (Rs.)": 0.0, "Cash Collected (Rs.)": 0.0},
        {"Invoice No.": "INV-02", "Client / Party Name": "", "Client Address": "Birgunj", "Goods / Product Name": "", "Qty": 0.0, "Sale Rate (Rs.)": 0.0, "Cash Collected (Rs.)": 0.0}
    ])

def init_office():
    return pd.DataFrame([
        {"Expense Details": "", "Paid To / Vendor": "Vendor", "Payment Mode": "Cash", "Amount (Rs.)": 0.0, "Remarks": ""}
    ])

def init_staff():
    return pd.DataFrame([
        {"Staff / Personnel Name": "", "Purpose / Details": "Tour Advance", "Payment Type": "Staff Advance", "Amount (Rs.)": 0.0, "Remarks": ""}
    ])

if "sales_data" not in st.session_state:
    st.session_state["sales_data"] = init_sales()
if "office_data" not in st.session_state:
    st.session_state["office_data"] = init_office()
if "staff_data" not in st.session_state:
    st.session_state["staff_data"] = init_staff()
if "report_date" not in st.session_state:
    st.session_state["report_date"] = date.today()
if "report_no" not in st.session_state:
    st.session_state["report_no"] = generate_report_no(date.today())

def reset_all_fields():
    st.session_state["report_no"] = generate_report_no(st.session_state.get("report_date", date.today()))
    st.session_state["sales_data"] = init_sales()
    st.session_state["office_data"] = init_office()
    st.session_state["staff_data"] = init_staff()
    if "submitted_pdf" in st.session_state:
        del st.session_state["submitted_pdf"]

# =========================================================
# 5. TOP HEADER & METADATA
# =========================================================
st.title("ALPINE HERBS PVT. LTD.")
st.caption("Birgunj, Nepal | Medical Representative Daily Field Operations | Logged: " + logged_user)

c1, c2, c3, c4 = st.columns([1.1, 1.3, 1.4, 1.1])
with c1:
    selected_date = st.date_input("Date (A.D.)", value=st.session_state.get("report_date", date.today()))
    st.session_state["report_date"] = selected_date
    st.caption("Nepali Miti: " + nepali_date(selected_date))
with c2:
    staff_name = st.text_input("MR / Representative Name", value=st.session_state.get("saved_mr_name", logged_user if logged_user != "Alpine" else "Pritam Gupta"))
    st.session_state["saved_mr_name"] = staff_name
with c3:
    route = st.text_input("Territory / Route Covered", placeholder="e.g. Birgunj - Lautan - Kalaiya")
with c4:
    st.text_input("Report Reference No.", value=st.session_state.get("report_no", ""), disabled=True)

st.write("")

# =========================================================
# 6. REAL-TIME DATA COMPUTATION
# =========================================================
sales_df = st.session_state["sales_data"].copy()
for col in ["Qty", "Sale Rate (Rs.)", "Cash Collected (Rs.)"]:
    sales_df[col] = pd.to_numeric(sales_df[col], errors="coerce").fillna(0.0)

computed_total = sales_df["Qty"] * sales_df["Sale Rate (Rs.)"]
sales_df["Total Sale (Rs.)"] = computed_total
sales_df["Credit Given (Rs.)"] = (computed_total - sales_df["Cash Collected (Rs.)"]).clip(lower=0.0)

office_df = st.session_state["office_data"].copy()
office_df["Amount (Rs.)"] = pd.to_numeric(office_df["Amount (Rs.)"], errors="coerce").fillna(0.0)

staff_df = st.session_state["staff_data"].copy()
staff_df["Amount (Rs.)"] = pd.to_numeric(staff_df["Amount (Rs.)"], errors="coerce").fillna(0.0)

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
st.subheader("Financial Summary (Live Updates)")
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Total Sales Billed", m
