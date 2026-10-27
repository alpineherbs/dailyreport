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
from reportlab.lib.styles import getSampleStyleSheet

# =========================================================
# 1. CREDENTIALS & GOOGLE WEBHOOK URL
# =========================================================
USERS = {
    "Alpine": "AHP@123",
    "Pritam": "Pritam@2024",
    "Admin": "AlpineAdmin@123",
    "Manager": "Alpine@Birgunj"
}

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzqcy8A442WqYY8gFjPRojpLeDZw3GhQnyo7Y8PadW6vZ1YW2QvkIceFqxkZuo8166R/exec"

# =========================================================
# 2. GOOGLE SHEET SYNC (BATCH TRANSMISSION)
# =========================================================
def sync_to_sheets(s_df, o_df, st_df, mr_name, rep_ref, rep_date):
    if not WEB_APP_URL.startswith("http"):
        st.error("Google Web App URL is invalid.")
        return False, 0

    sales_items = []
    for _, r in s_df.iterrows():
        qty = float(r.get("Qty", 0.0) or 0.0)
        rate = float(r.get("Rate (Rs.)", 0.0) or 0.0)
        cash = float(r.get("Cash Recd (Rs.)", 0.0) or 0.0)
        credit = float(r.get("Credit Bal (Rs.)", 0.0) or 0.0)
        tot = float(r.get("Total Sale (Rs.)", 0.0) or (qty * rate))
        pname = str(r.get("Product Name", "")).strip()
        cname = str(r.get("Client Name", "")).strip()
        if qty > 0 or cash > 0 or credit > 0 or tot > 0 or pname:
            sales_items.append({
                "invoice": str(r.get("Invoice No.", "INV-01")),
                "client_name": cname if cname else "Walk-in Party",
                "address": str(r.get("Address", "Birgunj")),
                "product_name": pname if pname else "General Stock",
                "qty": qty, "rate": rate, "cash_collected": cash,
                "credit_given": credit, "total_sale": tot
            })

    exp_items = []
    for _, r in o_df.iterrows():
        amt = float(r.get("Amount (Rs.)", 0.0) or 0.0)
        det = str(r.get("Details", "")).strip()
        if amt > 0 and det:
            exp_items.append({
                "details": det, "paid_to": str(r.get("Paid To", "Vendor")),
                "mode": str(r.get("Mode", "Cash")), "amount": amt,
                "remarks": str(r.get("Remarks", ""))
            })

    adv_items = []
    for _, r in st_df.iterrows():
        amt = float(r.get("Amount (Rs.)", 0.0) or 0.0)
        staff = str(r.get("Staff Name", "")).strip()
        if amt > 0 and staff:
            adv_items.append({
                "personnel_name": staff, "purpose": str(r.get("Purpose", "Advance")),
                "type": str(r.get("Category", "Staff Advance")), "amount": amt,
                "remarks": str(r.get("Remarks", ""))
            })

    total_count = len(sales_items) + len(exp_items) + len(adv_items)
    if total_count == 0:
        st.warning("No entries found to sync.")
        return True, 0

    payload = {
        "date": str(rep_date), "report_no": str(rep_ref), "staff_name": str(mr_name),
        "sales": sales_items, "expenses": exp_items, "advances": adv_items
    }
    try:
        res = requests.post(WEB_APP_URL, json=payload, timeout=25, allow_redirects=True)
        return (True, total_count) if res.status_code == 200 else (False, 0)
    except Exception as e:
        st.error(f"Sync Connection Error: {e}")
        return False, 0

# =========================================================
# 3. AUTHENTICATION SCREEN
# =========================================================
st.set_page_config(page_title="ALPINE HERBS - Daily Portal", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user"] = ""

if not st.session_state["authenticated"]:
    st.title("ALPINE HERBS PVT. LTD.")
    st.subheader("Medical Representative Daily Reporting Portal")
    st.divider()
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        u_in = st.text_input("Username", placeholder="e.g. Alpine or Pritam")
        p_in = st.text_input("Password", type="password")
        if st.button("Login", type="primary", use_container_width=True):
            if u_in.strip() in USERS and USERS[u_in.strip()] == p_in.strip():
                st.session_state["authenticated"] = True
                st.session_state["user"] = u_in.strip()
                st.rerun()
            else:
                st.error("Invalid username or password.")
    st.stop()

# =========================================================
# 4. APP STATE & MASTER DATA
# =========================================================
cur_user = st.session_state.get("user", "Staff")

def money(val):
    return f"Rs. {float(val or 0):,.2f}"

def get_rep_no():
    return f"ALP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

if "sales_df" not in st.session_state:
    st.session_state["sales_df"] = pd.DataFrame([
        {"Invoice No.": "INV-01", "Client Name": "", "Address": "Birgunj", "Product Name": "", "Qty": 0.0, "Rate (Rs.)": 0.0, "Cash Recd (Rs.)": 0.0},
        {"Invoice No.": "INV-02", "Client Name": "", "Address": "Birgunj", "Product Name": "", "Qty": 0.0, "Rate (Rs.)": 0.0, "Cash Recd (Rs.)": 0.0}
    ])
if "office_df" not in st.session_state:
    st.session_state["office_df"] = pd.DataFrame([{"Details": "", "Paid To": "Vendor", "Mode": "Cash", "Amount (Rs.)": 0.0, "Remarks": ""}])
if "staff_df" not in st.session_state:
    st.session_state["staff_df"] = pd.DataFrame([{"Staff Name": "", "Purpose": "Tour Advance", "Category": "Staff Advance", "Amount (Rs.)": 0.0, "Remarks": ""}])
if "rep_no" not in st.session_state:
    st.session_state["rep_no"] = get_rep_no()

# =========================================================
# 5. HEADER & LIVE FINANCIAL SUMMARY
# =========================================================
st.title("ALPINE HERBS PVT. LTD.")
st.caption(f"Birgunj, Nepal | Daily Field Operations | Logged: {cur_user}")

c1, c2, c3, c4 = st.columns([1.2, 1.5, 1.5, 1.2])
with c1:
    rep_date = st.date_input("Date", value=date.today())
with c2:
    mr_name = st.text_input("MR Name", value=cur_user if cur_user != "Alpine" else "Pritam Gupta")
with c3:
    route_name = st.text_input("Route / Territory", placeholder="e.g. Birgunj - Lautan")
with c4:
    st.text_input("Report Ref", value=st.session_state["rep_no"], disabled=True)

# LIVE MATH (Runs on every Tab / Enter keystroke)
s_work = st.session_state["sales_df"].copy()
for col in ["Qty", "Rate (Rs.)", "Cash Recd (Rs.)"]:
    s_work[col] = pd.to_numeric(s_work[col], errors="coerce").fillna(0.0)

s_work["Total Sale (Rs.)"] = s_work["Qty"] * s_work["Rate (Rs.)"]
s_work["Credit Bal (Rs.)"] = (s_work["Total Sale (Rs.)"] - s_work["Cash Recd (Rs.)"]).clip(lower=0.0)

o_work = st.session_state["office_df"].copy()
o_work["Amount (Rs.)"] = pd.to_numeric(o_work["Amount (Rs.)"], errors="coerce").fillna(0.0)

st_work = st.session_state["staff_df"].copy()
st_work["Amount (Rs.)"] = pd.to_numeric(st_work["Amount (Rs.)"], errors="coerce").fillna(0.0)

tot_sales = float(s_work["Total Sale (Rs.)"].sum())
tot_cash = float(s_work["Cash Recd (Rs.)"].sum())
tot_credit = float(s_work["Credit Bal (Rs.)"].sum())
tot_exp = float(o_work["Amount (Rs.)"].sum())
tot_adv = float(st_work["Amount (Rs.)"].sum())
net_cash = tot_cash - (tot_exp + tot_adv)

# REAL-TIME METRICS BAR
st.write("##### Real-Time Closing Summary")
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Total Sales", money(tot_sales))
k2.metric("Gross Cash", money(tot_cash))
k3.metric("Credit Given", money(tot_credit))
k4.metric("Expenses", money(tot_exp))
k5.metric("Advances", money(tot_adv))
k6.metric("Net In Hand", money(net_cash))

st.divider()

# =========================================================
# 6. EXCEL-STYLE DATA GRIDS (TAB & ENTER KEYBOARD NAVIGATION)
# =========================================================
t1, t2, t3 = st.tabs(["1. Sales & Collections", "2. Office Expenses", "3. Staff Advances"])

with t1:
    st.caption("Press Tab to jump between columns, Enter to move down. Total & Credit calculate automatically.")
    cfg_s = {
        "Total Sale (Rs.)": st.column_config.NumberColumn("Total Billed", disabled=True, format="Rs. %.2f"),
        "Credit Bal (Rs.)": st.column_config.NumberColumn("Credit Bal", disabled=True, format="Rs. %.2f")
    }
    ed_s = st.data_editor(s_work, column_config=cfg_s, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_s")
    st.session_state["sales_df"] = ed_s[["Invoice No.", "Client Name", "Address", "Product Name", "Qty", "Rate (Rs.)", "Cash Recd (Rs.)"]]

with t2:
    ed_o = st.data_editor(o_work, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_o")
    st.session_state["office_df"] = ed_o

with t3:
    ed_st = st.data_editor(st_work, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_st")
    st.session_state["staff_df"] = ed_st

# =========================================================
# 7. PDF BUILDER
# =========================================================
def make_pdf():
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=10*mm, rightMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("<b>ALPINE HERBS PVT. LTD. - DAILY FIELD CLOSING REPORT</b>", styles["Heading1"]),
        Paragraph(f"<b>Ref:</b> {st.session_state['rep_no']} | <b>Date:</b> {rep_date} | <b>Staff:</b> {mr_name} | <b>Route:</b> {route_name}", styles["Normal"]),
        Spacer(1, 4*mm),
        Table([
            ["Total Sales Billed", "Credit Given", "Gross Cash Collected", "Total Expenses", "Net Cash In Hand"],
            [money(tot_sales), money(tot_credit), money(tot_cash), money(tot_exp + tot_adv), money(net_cash)]
        ], colWidths=[55*mm]*5, style=[
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#164E33")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
        ]),
        Spacer(1, 6*mm),
        Table([
            ["\n____________________", "\n____________________", "\n____________________"],
            ["Medical Representative (MR)", "Area Sales Manager", "Audit / Accounts"]
        ], colWidths=[92*mm]*3, style=[('ALIGN', (0,0), (-1,-1), 'CENTER')])
    ]
    doc.build(story)
    return buf.getvalue()

# =========================================================
# 8. SUBMIT & ACTIONS
# =========================================================
st.write("")
b1, b2 = st.columns([3, 1])
with b1:
    if st.button("CONFIRM & SYNC REPORT TO MASTER", type="primary", use_container_width=True):
        with st.spinner("Syncing to Google Sheets..."):
            ok, count = sync_to_sheets(s_work, o_work, st_work, mr_name, st.session_state["rep_no"], rep_date)
            if ok:
                st.session_state["pdf"] = make_pdf()
                st.success(f"Report {st.session_state['rep_no']} synced successfully ({count} rows logged)!")

with b2:
    if st.button("Reset Form", use_container_width=True):
        st.session_state["rep_no"] = get_rep_no()
        st.session_state["sales_df"] = s_work.iloc[0:0]
        if "pdf" in st.session_state:
            del st.session_state["pdf"]
        st.rerun()

if "pdf" in st.session_state:
    st.write("")
    st.download_button(
        "DOWNLOAD SIGNED PDF VOUCHER",
        data=st.session_state["pdf"],
        file_name=f"{st.session_state['rep_no']}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

with st.sidebar:
    st.write(f"Logged in as: **{cur_user}**")
    if st.button("Sign Out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()
