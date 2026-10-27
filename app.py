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
# 1. USER AUTHENTICATION & GOOGLE SHEET WEBHOOK
# =========================================================
USERS = {
    "Alpine": "AHP@123",
    "Pritam": "Pritam@2024",
    "Admin": "AlpineAdmin@123",
    "Manager": "Alpine@Birgunj"
}

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzqcy8A442WqYY8gFjPRojpLeDZw3GhQnyo7Y8PadW6vZ1YW2QvkIceFqxkZuo8166R/exec"

CLIENT_DATABASE = [
    {"code": "BAR-001", "name": "Naresh Medical", "area": "Kalaiya, Bara", "dues": 3070, "phone": "9807267001"},
    {"code": "BAR-002", "name": "Mahir Health Clinic", "area": "Jeetpur, Bara", "dues": 7105, "phone": "9807100296"},
    {"code": "BAR-003", "name": "Dev Medical", "area": "Kalaiya, Bara", "dues": 2030, "phone": "9845227985"},
    {"code": "BAR-004", "name": "Nirajan Pharmacy", "area": "Bakuliya, Bara", "dues": 550, "phone": "9804242586"},
    {"code": "BAR-005", "name": "Hariom Medical", "area": "Kolvi, Bara", "dues": 400, "phone": "9811229323"},
    {"code": "BAR-008", "name": "Rupa Medical", "area": "Simara, Bara", "dues": 4535, "phone": ""},
    {"code": "BAR-009", "name": "Sanjeevani Clinic", "area": "Simara, Bara", "dues": 2195, "phone": "9845130209"},
    {"code": "PAR-002", "name": "Ashok Medical Hall", "area": "Naukatola, Parsa", "dues": 12230, "phone": ""},
    {"code": "PAR-004", "name": "Ali Health Clinic", "area": "Gunjabhawani, Parsa", "dues": 29040, "phone": ""},
    {"code": "PAR-015", "name": "Ganesh Srestha", "area": "Birgunj, Parsa", "dues": 63390, "phone": ""},
    {"code": "PAR-032", "name": "Roshan Pharmacy", "area": "Birgunj, Parsa", "dues": 74290, "phone": ""},
    {"code": "PAR-035", "name": "Sandip Medical Hall", "area": "Langada Chouk, Parsa", "dues": 30195, "phone": ""}
]

# =========================================================
# 2. GOOGLE SHEET BATCH SYNC
# =========================================================
def sync_to_sheets(sales_df, office_df, staff_df, mr_name, rep_ref, rep_date):
    if not str(WEB_APP_URL).startswith("http"):
        st.error("Invalid Google Apps Script Web App URL.")
        return False, 0

    sales_payload = []
    for _, r in sales_df.iterrows():
        qty = float(r.get("Qty", 0.0) or 0.0)
        rate = float(r.get("Rate (Rs.)", 0.0) or 0.0)
        cash = float(r.get("Cash Recd (Rs.)", 0.0) or 0.0)
        manual_credit = float(r.get("Credit Given (Rs.)", 0.0) or 0.0)
        tot = qty * rate
        credit = manual_credit if manual_credit > 0 else max(0.0, tot - cash)
        if tot == 0 and (cash > 0 or credit > 0):
            tot = cash + credit

        pname = str(r.get("Product Name", "")).strip()
        cname = str(r.get("Client Name", "")).strip()
        addr = str(r.get("Address", "Birgunj")).strip()
        inv = str(r.get("Invoice No.", "INV-01")).strip()

        if qty > 0 or cash > 0 or credit > 0 or (pname and pname != "nan") or (cname and cname != "nan"):
            sales_payload.append({
                "invoice": inv if inv else "INV-01",
                "client_name": cname if cname else "Walk-in Party",
                "address": addr if addr else "Birgunj",
                "product_name": pname if pname else "General Stock",
                "qty": qty, "rate": rate, "cash_collected": cash,
                "credit_given": credit, "total_sale": tot
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
                "amount": amt, "remarks": str(r.get("Remarks", "")).strip()
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
                "amount": amt, "remarks": str(r.get("Remarks", "")).strip()
            })

    total_records = len(sales_payload) + len(exp_payload) + len(adv_payload)
    if total_records == 0:
        st.warning("No entries found to sync.")
        return True, 0

    master_payload = {
        "date": str(rep_date), "report_no": str(rep_ref), "staff_name": str(mr_name),
        "sales": sales_payload, "expenses": exp_payload, "advances": adv_payload
    }
    try:
        res = requests.post(WEB_APP_URL, json=master_payload, timeout=25, allow_redirects=True)
        return (True, total_records) if res.status_code == 200 else (False, 0)
    except Exception as e:
        st.error(f"Sync Connection Error: {e}")
        return False, 0

# =========================================================
# 3. PAGE INITIALIZATION WITH 🌿 ICON & BRANDING
# =========================================================
st.set_page_config(page_title="ALPINE HERBS - Daily Field Closing", page_icon="🌿", layout="wide")

st.markdown("""
<style>
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem; padding-bottom: 2.5rem; max-width: 1520px; }
input::placeholder { color: #8FA698 !important; opacity: 1 !important; font-style: normal !important; }
.brand-nav { background: linear-gradient(135deg, #0D2818 0%, #164E33 100%); padding: 14px 20px; border-radius: 8px; color: white; display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
.brand-logo-text { font-size: 1.55rem; font-weight: 800; letter-spacing: 0.5px; color: #FFFFFF; }
.green-box-title { font-size: 0.78rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.8px; color: #164E33; margin-bottom: 8px; }
.green-card { background: #F4FAF6; border: 1.5px solid #2D7D52; border-radius: 8px; padding: 14px; height: 100%; box-shadow: 0 2px 4px rgba(0,0,0,0.03); }
.green-card-accent { background: #E7F5ED; border: 2px solid #164E33; border-radius: 8px; padding: 14px; height: 100%; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }
.stat-row { display: flex; justify-content: space-between; align-items: center; padding: 5px 0; border-bottom: 1px dashed #C8DEC2; font-size: 0.9rem; }
.stat-val { font-weight: 700; color: #0D2818; }
.stat-val-bold { font-weight: 800; font-size: 1.25rem; color: #0D2818; }
.credit-badge-strip { background: #FFF8E7; border-left: 4px solid #D97706; padding: 8px 14px; border-radius: 4px; font-size: 0.85rem; color: #92400E; margin-top: 10px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

ALPINE_ICON = """<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#68D391" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle; margin-right:8px;"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>"""

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user"] = ""

if not st.session_state["authenticated"]:
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    c_pad1, c_box, c_pad2 = st.columns([1, 1.1, 1])
    with c_box:
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <div style="display:inline-block;">{ALPINE_ICON}</div>
            <div style="font-size: 1.7rem; font-weight: 800; color: #0D2818;">ALPINE HERBS</div>
            <div style="font-size: 0.85rem; color: #2D7D52; font-weight: 600;">MEDICAL FIELD OPERATIONS PORTAL</div>
        </div>
        """, unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("##### Staff Sign In")
            u_in = st.text_input("Username", placeholder="Username", label_visibility="collapsed")
            p_in = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
            st.write("")
            if st.button("Sign In to Portal", type="primary", use_container_width=True):
                u_c = u_in.strip()
                p_c = p_in.strip()
                if u_c in USERS and USERS[u_c] == p_c:
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = u_c
                    st.rerun()
                else:
                    st.error("Invalid Username or Password.")
    st.stop()

# =========================================================
# 4. PORTAL HEADER & METADATA
# =========================================================
cur_user = st.session_state.get("user", "Staff")

def money(val):
    return "Rs. {:,.2f}".format(float(val or 0.0))

def get_rep_no():
    return "ALP-" + datetime.now().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:4].upper()

if "rep_no" not in st.session_state:
    st.session_state["rep_no"] = get_rep_no()

# Initial Grid Templates (NOW INCLUDING EXPLICIT CREDIT COLUMNS)
INIT_SALES = pd.DataFrame([
    {"Invoice No.": "INV-01", "Client Name": "", "Address": "Birgunj", "Product Name": "", "Qty": 0.0, "Rate (Rs.)": 0.0, "Cash Recd (Rs.)": 0.0, "Credit Given (Rs.)": 0.0, "Credit Remarks": ""},
    {"Invoice No.": "INV-02", "Client Name": "", "Address": "Birgunj", "Product Name": "", "Qty": 0.0, "Rate (Rs.)": 0.0, "Cash Recd (Rs.)": 0.0, "Credit Given (Rs.)": 0.0, "Credit Remarks": ""},
    {"Invoice No.": "INV-03", "Client Name": "", "Address": "Birgunj", "Product Name": "", "Qty": 0.0, "Rate (Rs.)": 0.0, "Cash Recd (Rs.)": 0.0, "Credit Given (Rs.)": 0.0, "Credit Remarks": ""}
])

INIT_OFFICE = pd.DataFrame([{"Details": "", "Paid To": "Vendor", "Mode": "Cash", "Amount (Rs.)": 0.0, "Remarks": ""}])
INIT_STAFF = pd.DataFrame([{"Staff Name": "", "Purpose": "Tour Advance", "Category": "Staff Advance", "Amount (Rs.)": 0.0, "Remarks": ""}])

st.markdown(f"""
<div class="brand-nav">
    <div style="display: flex; align-items: center;">
        {ALPINE_ICON}
        <div>
            <div class="brand-logo-text">ALPINE HERBS PVT. LTD.</div>
            <div style="font-size: 0.78rem; color: #D5EBDD;">BIRGUNJ, NEPAL &nbsp;|&nbsp; DAILY TOUR CLOSING & LEDGER AUDIT</div>
        </div>
    </div>
    <div style="text-align: right; font-size: 0.8rem; color: #E7F6ED;">
        <div>Officer: <strong>{cur_user}</strong></div>
        <div>ISO GMP Standard</div>
    </div>
</div>
""", unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns([1.2, 1.4, 1.4, 1.2])
with m1:
    rep_date = st.date_input("Date (A.D.)", value=date.today())
with m2:
    mr_name = st.text_input("MR / Representative Name", value=cur_user if cur_user != "Alpine" else "Pritam Gupta")
with m3:
    route_name = st.text_input("Territory / Route", placeholder="e.g. Birgunj - Kalaiya - Simara")
with m4:
    st.text_input("Report Reference", value=st.session_state["rep_no"], disabled=True)

st.write("")

# =========================================================
# 5. DATA GRIDS (WITH VISIBLE CREDIT & PARTY DUES)
# =========================================================
t1, t2, t3 = st.tabs(["🛒 1. Sales & Collections Grid", "🏢 2. Operating Expenses", "👥 3. Staff Advances"])

with t1:
    st.caption("Press Tab to jump between columns, Enter to move down. You can enter Cash Received and/or Credit Given directly.")
    edited_sales = st.data_editor(INIT_SALES, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_s")

with t2:
    st.caption("Record route fuel, food, logistics, and local operational costs.")
    edited_office = st.data_editor(INIT_OFFICE, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_o")

with t3:
    st.caption("Record field allowances, per-diem, and tour advances given to personnel.")
    edited_staff = st.data_editor(INIT_STAFF, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_st")

# =========================================================
# 6. MATHEMATICAL RECONCILIATION
# =========================================================
s_qty = pd.to_numeric(edited_sales["Qty"], errors="coerce").fillna(0.0)
s_rate = pd.to_numeric(edited_sales["Rate (Rs.)"], errors="coerce"
