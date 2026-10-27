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
# 1. USER ACCESS & GOOGLE SHEET WEBHOOK
# =========================================================
USERS = {
    "Alpine": "AHP@123",
    "Pritam": "Pritam@2024",
    "Admin": "AlpineAdmin@123",
    "Manager": "Alpine@Birgunj"
}

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzqcy8A442WqYY8gFjPRojpLeDZw3GhQnyo7Y8PadW6vZ1YW2QvkIceFqxkZuo8166R/exec"

# =========================================================
# 2. CLIENT MASTER DATABASE (BARA & PARSA LEDGER)
# =========================================================
CLIENT_DATABASE = [
    {"code": "BAR-001", "name": "Naresh Medical", "area": "Kalaiya, Bara", "dues": 3070, "phone": "9807267001"},
    {"code": "BAR-002", "name": "Mahir Health Clinic", "area": "Jeetpur, Bara", "dues": 7105, "phone": "9807100296"},
    {"code": "BAR-003", "name": "Dev Medical", "area": "Kalaiya, Bara", "dues": 2030, "phone": "9845227985"},
    {"code": "BAR-004", "name": "Nirajan Pharmacy", "area": "Bakuliya, Bara", "dues": 550, "phone": "9804242586"},
    {"code": "BAR-005", "name": "Hariom Medical", "area": "Kolvi, Bara", "dues": 400, "phone": "9811229323"},
    {"code": "BAR-006", "name": "S.K.S Pharma", "area": "Parsauni, Bara", "dues": 1175, "phone": ""},
    {"code": "BAR-008", "name": "Rupa Medical", "area": "Simara, Bara", "dues": 4535, "phone": ""},
    {"code": "BAR-009", "name": "Sanjeevani Clinic", "area": "Simara, Bara", "dues": 2195, "phone": "9845130209"},
    {"code": "BAR-011", "name": "Alex Medical Surgical", "area": "Bagrampur, Bara", "dues": 4745, "phone": ""},
    {"code": "BAR-012", "name": "Kaliyani Medical", "area": "Kolvi, Bara", "dues": 2025, "phone": ""},
    {"code": "BAR-015", "name": "Roman Surgical", "area": "Khopawa, Bara", "dues": 1660, "phone": "9821231370"},
    {"code": "BAR-016", "name": "Nimash Medical", "area": "Simara, Bara", "dues": 4620, "phone": "9845120836"},
    {"code": "BAR-017", "name": "Advance Poli Clinic", "area": "Raghunathpur, Bara", "dues": 6510, "phone": "9809153231"},
    {"code": "BAR-018", "name": "Pritvi Medical", "area": "Jaitapur, Bara", "dues": 3070, "phone": ""},
    {"code": "PAR-002", "name": "Ashok Medical Hall", "area": "Naukatola, Parsa", "dues": 12230, "phone": ""},
    {"code": "PAR-003", "name": "Alex Medical Hall", "area": "Bagrampur, Parsa", "dues": 18000, "phone": ""},
    {"code": "PAR-004", "name": "Ali Health Clinic", "area": "Gunjabhawani, Parsa", "dues": 29040, "phone": ""},
    {"code": "PAR-005", "name": "Alina Health Clinic", "area": "Kalaiya, Parsa", "dues": 8250, "phone": ""},
    {"code": "PAR-006", "name": "Sudama Surgical", "area": "Neutan, Parsa", "dues": 20200, "phone": ""},
    {"code": "PAR-007", "name": "B.s Health Clinic", "area": "Paterwa, Parsa", "dues": 24665, "phone": ""},
    {"code": "PAR-008", "name": "Pandey Medical Hall", "area": "Badanihar, Parsa", "dues": 7065, "phone": ""},
    {"code": "PAR-009", "name": "Bhawani Medical Hall", "area": "Bharatwa, Parsa", "dues": 9950, "phone": ""},
    {"code": "PAR-011", "name": "Dinamik Pharma", "area": "Sano Sugauli, Parsa", "dues": 15815, "phone": ""},
    {"code": "PAR-015", "name": "Ganesh Srestha", "area": "Birgunj, Parsa", "dues": 63390, "phone": ""},
    {"code": "PAR-016", "name": "Hariom medical Hall", "area": "Kolbi, Parsa", "dues": 2300, "phone": ""},
    {"code": "PAR-017", "name": "Harnaiya Aashirvad Medical", "area": "Harnaiya, Parsa", "dues": 4565, "phone": ""},
    {"code": "PAR-019", "name": "Kaliyani Medical Hall", "area": "Kolbi, Parsa", "dues": 15580, "phone": ""},
    {"code": "PAR-031", "name": "Rihansh Medical Hall", "area": "Birgunj, Parsa", "dues": 1740, "phone": ""},
    {"code": "PAR-032", "name": "Roshan Pharmacy", "area": "Birgunj, Parsa", "dues": 74290, "phone": ""},
    {"code": "PAR-033", "name": "Rupa Medical Hall", "area": "Simra, Parsa", "dues": 5515, "phone": ""},
    {"code": "PAR-035", "name": "Sandip Medical Hall", "area": "Langada Chouk, Parsa", "dues": 30195, "phone": ""},
    {"code": "PAR-036", "name": "Sanniya Medical Hall", "area": "Jeetpur, Parsa", "dues": 3460, "phone": ""},
    {"code": "PAR-037", "name": "Sohil Medical Hall", "area": "Pokhariya, Parsa", "dues": 11600, "phone": ""},
    {"code": "PAR-038", "name": "Shohalal Medical Hall", "area": "Gunjabhawani, Parsa", "dues": 7175, "phone": ""},
    {"code": "PAR-040", "name": "Tarkeshwar Medical Hall", "area": "Nagwa, Parsa", "dues": 8885, "phone": ""},
    {"code": "PAR-052", "name": "Mahir Health Clinic", "area": "Jeetpur, Parsa", "dues": 8165, "phone": ""},
    {"code": "PAR-056", "name": "OM Shivsakti Pharmacy", "area": "Kalaiya, Parsa", "dues": 3680, "phone": ""},
    {"code": "REC-001", "name": "Aarabh Pharmacy (Bad Debt)", "area": "Nijagar", "dues": 36725, "phone": "9855019764"},
    {"code": "REC-002", "name": "Aarabh Pharmacy Narayani", "area": "Nijagar", "dues": 25915, "phone": "9855019764"}
]

# =========================================================
# 3. GOOGLE SHEET SYNC (TRANSMITS EDITED DATA DIRECTLY)
# =========================================================
def sync_to_sheets(sales_df, office_df, staff_df, mr_name, rep_ref, rep_date):
    if not WEB_APP_URL.startswith("http"):
        st.error("Google Web App URL is invalid.")
        return False, 0

    sales_payload = []
    for _, r in sales_df.iterrows():
        qty = float(r.get("Qty", 0.0) or 0.0)
        rate = float(r.get("Rate (Rs.)", 0.0) or 0.0)
        cash = float(r.get("Cash Recd (Rs.)", 0.0) or 0.0)
        tot = qty * rate
        credit = max(0.0, tot - cash)
        pname = str(r.get("Product Name", "")).strip()
        cname = str(r.get("Client Name", "")).strip()
        addr = str(r.get("Address", "Birgunj")).strip()
        inv = str(r.get("Invoice No.", "INV-01")).strip()

        if qty > 0 or cash > 0 or (pname and pname != "nan") or (cname and cname != "nan"):
            sales_payload.append({
                "invoice": inv if inv else "INV-01",
                "client_name": cname if cname else "Walk-in Party",
                "address": addr if addr else "Birgunj",
                "product_name": pname if pname else "General Stock",
                "qty": qty,
                "rate": rate,
                "cash_collected": cash,
                "credit_given": credit,
                "total_sale": tot
            })

    exp_payload = []
    for _, r in office_df.iterrows():
        amt = float(r.get("Amount (Rs.)", 0.0) or 0.0)
        det = str(r.get("Details", "")).strip()
        if amt > 0 or (det and det != "nan"):
            exp_payload.append({
                "details": det if det else "Route Expense",
                "paid_to": str(r.get("Paid To", "Vendor")).strip() or "Vendor",
                "mode": str(r.get("Mode", "Cash")).strip() or "Cash",
                "amount": amt,
                "remarks": str(r.get("Remarks", "")).strip()
            })

    adv_payload = []
    for _, r in staff_df.iterrows():
        amt = float(r.get("Amount (Rs.)", 0.0) or 0.0)
        staff = str(r.get("Staff Name", "")).strip()
        if amt > 0 or (staff and staff != "nan"):
            adv_payload.append({
                "personnel_name": staff if staff else "Staff",
                "purpose": str(r.get("Purpose", "Tour Advance")).strip() or "Tour Advance",
                "type": str(r.get("Category", "Staff Advance")).strip() or "Staff Advance",
                "amount": amt,
                "remarks": str(r.get("Remarks", "")).strip()
            })

    total_records = len(sales_payload) + len(exp_payload) + len(adv_payload)
    if total_records == 0:
        st.warning("No entries found to sync.")
        return True, 0

    master_payload = {
        "date": str(rep_date),
        "report_no": str(rep_ref),
        "staff_name": str(mr_name),
        "sales": sales_payload,
        "expenses": exp_payload,
        "advances": adv_payload
    }

    try:
        res = requests.post(WEB_APP_URL, json=master_payload, timeout=25, allow_redirects=True)
        return (True, total_records) if res.status_code == 200 else (False, 0)
    except Exception as e:
        st.error(f"Sync Connection Error: {e}")
        return False, 0

# =========================================================
# 4. AUTHENTICATION
# =========================================================
st.set_page_config(page_title="ALPINE HERBS - Operations Portal", layout="wide")

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
# 5. TEMPLATES & PERSISTENT SESSION
# =========================================================
cur_user = st.session_state.get("user", "Staff")

def money(val):
    return "Rs. {:,.2f}".format(float(val or 0.0))

def get_rep_no():
    return "ALP-" + datetime.now().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:4].upper()

if "rep_no" not in st.session_state:
    st.session_state["rep_no"] = get_rep_no()

# Initial Templates (Clean, unchanging base data)
INIT_SALES = pd.DataFrame([
    {"Invoice No.": "INV-01", "Client Name": "", "Address": "Birgunj", "Product Name": "", "Qty": 0.0, "Rate (Rs.)": 0.0, "Cash Recd (Rs.)": 0.0},
    {"Invoice No.": "INV-02", "Client Name": "", "Address": "Birgunj", "Product Name": "", "Qty": 0.0, "Rate (Rs.)": 0.0, "Cash Recd (Rs.)": 0.0},
    {"Invoice No.": "INV-03", "Client Name": "", "Address": "Birgunj", "Product Name": "", "Qty": 0.0, "Rate (Rs.)": 0.0, "Cash Recd (Rs.)": 0.0}
])

INIT_OFFICE = pd.DataFrame([
    {"Details": "", "Paid To": "Vendor", "Mode": "Cash", "Amount (Rs.)": 0.0, "Remarks": ""}
])

INIT_STAFF = pd.DataFrame([
    {"Staff Name": "", "Purpose": "Tour Advance", "Category": "Staff Advance", "Amount (Rs.)": 0.0, "Remarks": ""}
])

# =========================================================
# 6. HEADER & METADATA
# =========================================================
st.title("ALPINE HERBS PVT. LTD.")
st.caption(f"Birgunj, Nepal | Field Operations Portal | Logged as: {cur_user}")

c1, c2, c3, c4 = st.columns([1.2, 1.5, 1.5, 1.2])
with c1:
    rep_date = st.date_input("Date", value=date.today())
with c2:
    mr_name = st.text_input("MR Name", value=cur_user if cur_user != "Alpine" else "Pritam Gupta")
with c3:
    route_name = st.text_input("Route / Territory", placeholder="e.g. Birgunj - Kalaiya")
with c4:
    st.text_input("Report Ref", value=st.session_state["rep_no"], disabled=True)

# Top Summary Container (Receives live updates)
summary_placeholder = st.container()

# =========================================================
# 7. EXCEL-STYLE DATA GRIDS (TAB & ENTER FULLY ENABLED)
# =========================================================
t1, t2, t3 = st.tabs(["1. Sales & Collections", "2. Office Expenses", "3. Staff Advances"])

with t1:
    st.caption("Press Tab to jump between columns, Enter to move down rows. Changes reflect at the top in real time.")
    edited_sales = st.data_editor(
        INIT_SALES,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="ed_s"
    )

with t2:
    st.caption("Record daily operational, transport, and vendor costs.")
    edited_office = st.data_editor(
        INIT_OFFICE,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="ed_o"
    )

with t3:
    st.caption("Record field allowances, per-diem, and staff advances.")
    edited_staff = st.data_editor(
        INIT_STAFF,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="ed_st"
    )

# =========================================================
# 8. REAL-TIME TOTALS CALCULATION
# =========================================================
s_qty = pd.to_numeric(edited_sales["Qty"], errors="coerce").fillna(0.0)
s_rate = pd.to_numeric(edited_sales["Rate (Rs.)"], errors="coerce").fillna(0.0)
s_cash = pd.to_numeric(edited_sales["Cash Recd (Rs.)"], errors="coerce").fillna(0.0)
s_totals = s_qty * s_rate
s_credits = (s_totals - s_cash).clip(lower=0.0)

tot_sales = float(s_totals.sum())
tot_cash = float(s_cash.sum())
tot_credit = float(s_credits.sum())

o_amt = pd.to_numeric(edited_office["Amount (Rs.)"], errors="coerce").fillna(0.0)
tot_exp = float(o_amt.sum())

st_amt = pd.to_numeric(edited_staff["Amount (Rs.)"], errors="coerce").fillna(0.0)
tot_adv = float(st_amt.sum())
net_cash = tot_cash - (tot_exp + tot_adv)

# Render Live Metrics into the top container
with summary_placeholder:
    st.write("##### Real-Time Closing Summary (Live)")
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Total Sales", money(tot_sales))
    k2.metric("Gross Cash", money(tot_cash))
    k3.metric("Credit Given", money(tot_credit))
    k4.metric("Expenses", money(tot_exp))
    k5.metric("Advances", money(tot_adv))
    k6.metric("Net In Hand", money(net_cash))
    if net_cash < 0:
        st.warning("Notice: Expenses and advances exceed cash collected today. Net cash is negative.")
    st.divider()

# =========================================================
# 9. PDF GENERATOR
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
# 10. SUBMISSION & CONTROLS
# =========================================================
st.write("")
b1, b2 = st.columns([3, 1])
with b1:
    if st.button("CONFIRM & SYNC REPORT TO MASTER", type="primary", use_container_width=True):
        with st.spinner("Syncing data to Google Sheets..."):
            ok, count = sync_to_sheets(edited_sales, edited_office, edited_staff, mr_name, st.session_state["rep_no"], rep_date)
            if ok:
                st.session_state["pdf"] = make_pdf()
                st.success(f"Report {st.session_state['rep_no']} synced successfully! ({count} records updated in Google Sheets)")

with b2:
    if st.button("Reset Form", use_container_width=True):
        st.session_state["rep_no"] = get_rep_no()
        for k in ["ed_s", "ed_o", "ed_st", "pdf"]:
            if k in st.session_state:
                del st.session_state[k]
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

# =========================================================
# 11. SIDEBAR: CLIENT DUES LOOKUP
# =========================================================
with st.sidebar:
    st.subheader("Client Ledger & Dues Lookup")
    search_q = st.text_input("Search Chemist or Town", placeholder="e.g. Naresh, Simara").strip().lower()
    matches = [c for c in CLIENT_DATABASE if search_q in c['name'].lower() or search_q in c['area'].lower()] if search_q else CLIENT_DATABASE[:8]

    for item in matches[:10]:
        st.markdown(f"**{item['name']}** ({item['code']})")
        st.caption(f"{item['area']} | Due: **Rs. {item['dues']:,}** {('| ' + item['phone']) if item['phone'] else ''}")
        st.write("---")

    st.write(f"Logged in as: **{cur_user}**")
    if st.button("Sign Out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()
