import streamlit as st, pandas as pd, requests, uuid
from datetime import date, datetime
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="ALPINE HERBS - Daily Field Closing", page_icon="🌿", layout="wide")

USERS = {"Alpine": "AHP@123", "Pritam": "Pritam@2024", "Admin": "AlpineAdmin@123", "Manager": "Alpine@Birgunj"}
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzqcy8A442WqYY8gFjPRojpLeDZw3GhQnyo7Y8PadW6vZ1YW2QvkIceFqxkZuo8166R/exec"

CLIENT_DATABASE = [
    {"code": "BAR-001", "name": "Naresh Medical", "area": "Kalaiya, Bara", "dues": 3070},
    {"code": "BAR-002", "name": "Mahir Health Clinic", "area": "Jeetpur, Bara", "dues": 7105},
    {"code": "BAR-003", "name": "Dev Medical", "area": "Kalaiya, Bara", "dues": 2030},
    {"code": "BAR-004", "name": "Nirajan Pharmacy", "area": "Bakuliya, Bara", "dues": 550},
    {"code": "BAR-005", "name": "Hariom Medical", "area": "Kolvi, Bara", "dues": 400},
    {"code": "PAR-002", "name": "Ashok Medical Hall", "area": "Naukatola, Parsa", "dues": 12230},
    {"code": "PAR-004", "name": "Ali Health Clinic", "area": "Gunjabhawani, Parsa", "dues": 29040},
    {"code": "PAR-015", "name": "Ganesh Srestha", "area": "Birgunj, Parsa", "dues": 63390},
    {"code": "PAR-032", "name": "Roshan Pharmacy", "area": "Birgunj, Parsa", "dues": 74290},
    {"code": "PAR-035", "name": "Sandip Medical Hall", "area": "Langada Chouk, Parsa", "dues": 30195}
]

st.markdown("""<style>
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem; max-width: 1520px; }
input::placeholder { color: #8FA698 !important; opacity: 1 !important; }
.g-box { background: #F4FAF6; border: 1.5px solid #2D7D52; border-radius: 8px; padding: 12px; height: 100%; }
.g-acc { background: #E7F5ED; border: 2px solid #164E33; border-radius: 8px; padding: 12px; height: 100%; }
.s-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dashed #C8DEC2; font-size: 0.9rem; }
.s-val { font-weight: 700; color: #0D2818; }
.user-card { background: #EAF5EE; border-left: 4px solid #164E33; padding: 10px; border-radius: 4px; margin-bottom: 12px; }
</style>""", unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user"] = ""

if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align:center; color:#0D2818; margin-top:2rem;'>🌿 ALPINE HERBS PVT. LTD.</h2><p style='text-align:center; color:#2D7D52;'>FIELD OPERATIONS PORTAL</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.1, 1])
    with c2:
        with st.container(border=True):
            st.markdown("##### Staff Sign In")
            u = st.text_input("Username", placeholder="Username", label_visibility="collapsed")
            p = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
            if st.button("Sign In to Portal", type="primary", use_container_width=True):
                if u.strip() in USERS and USERS[u.strip()] == p.strip():
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = u.strip()
                    st.rerun()
                else: st.error("Invalid Username or Password.")
    st.stop()

cur_user = st.session_state.get("user", "Staff")
money = lambda v: f"Rs. {float(v or 0):,.2f}"

if "rep_no" not in st.session_state:
    st.session_state["rep_no"] = f"ALP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

INIT_SALES = pd.DataFrame([
    {"Invoice No.": "INV-01", "Client Name": "", "Address": "Birgunj", "Product Name": "", "Qty": 0.0, "Rate (Rs.)": 0.0, "Cash Recd (Rs.)": 0.0, "Credit Given (Rs.)": 0.0},
    {"Invoice No.": "INV-02", "Client Name": "", "Address": "Birgunj", "Product Name": "", "Qty": 0.0, "Rate (Rs.)": 0.0, "Cash Recd (Rs.)": 0.0, "Credit Given (Rs.)": 0.0},
    {"Invoice No.": "INV-03", "Client Name": "", "Address": "Birgunj", "Product Name": "", "Qty": 0.0, "Rate (Rs.)": 0.0, "Cash Recd (Rs.)": 0.0, "Credit Given (Rs.)": 0.0}
])
INIT_OFFICE = pd.DataFrame([{"Details": "", "Paid To": "Vendor", "Mode": "Cash", "Amount (Rs.)": 0.0, "Remarks": ""}])
INIT_STAFF = pd.DataFrame([{"Staff Name": "", "Purpose": "Tour Advance", "Category": "Staff Advance", "Amount (Rs.)": 0.0, "Remarks": ""}])

# SIDEBAR: USER INFO, LOGOUT & LIVE TEST
with st.sidebar:
    st.markdown("### 👤 User Session")
    st.markdown(f"""<div class="user-card">
    <b>Officer:</b> {cur_user}<br>
    <b>Branch:</b> Birgunj, Nepal<br>
    <b>Status:</b> 🟢 Active Online<br>
    <b>Ref:</b> <code>{st.session_state['rep_no']}</code>
    </div>""", unsafe_allow_html=True)
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("🔒 Logout", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state["user"] = ""
            st.rerun()
    with col_s2:
        if st.button("🧪 Ping Sheet", use_container_width=True, help="Test live connection to Google Sheet"):
            try:
                test_res = requests.get(WEB_APP_URL, timeout=8)
                if test_res.status_code == 200: st.success("🟢 Sheet Connected!")
                else: st.error(f"HTTP {test_res.status_code}")
            except Exception as e: st.error(f"Offline: {e}")

    st.divider()
    st.markdown("### 📋 Client Dues Lookup")
    sq = st.text_input("Search Chemist or Town", placeholder="Search chemist or town").strip().lower()
    matches = [c for c in CLIENT_DATABASE if sq in c['name'].lower() or sq in c['area'].lower()] if sq else CLIENT_DATABASE[:6]
    for item in matches[:8]:
        st.markdown(f"**{item['name']}** (`{item['code']}`)\n{item['area']} | Due: **Rs. {item['dues']:,}**")
        st.write("---")

st.markdown(f"""<div style="background:linear-gradient(135deg, #0D2818, #164E33); padding:12px 18px; border-radius:8px; color:white; display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
<div><span style="font-size:1.5rem; font-weight:800;">🌿 ALPINE HERBS PVT. LTD.</span><br><span style="font-size:0.8rem; color:#D5EBDD;">BIRGUNJ, NEPAL | DAILY TOUR CLOSING</span></div>
<div style="text-align:right; font-size:0.82rem;">Officer: <b>{cur_user}</b><br>ISO GMP Standard</div></div>""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns([1.2, 1.4, 1.4, 1.2])
with c1: rep_date = st.date_input("Date (A.D.)", value=date.today())
with c2: mr_name = st.text_input("MR Name", value=cur_user if cur_user != "Alpine" else "Pritam Gupta")
with c3: route_name = st.text_input("Route / Territory", placeholder="e.g. Birgunj - Kalaiya - Simara")
with c4: st.text_input("Report Ref", value=st.session_state["rep_no"], disabled=True)

t1, t2, t3 = st.tabs(["🛒 1. Sales & Credit Ledger", "🏢 2. Operating Expenses", "👥 3. Staff Advances"])
with t1:
    st.caption("Press Tab to jump between cells, Enter to move down. Credit auto-calculates if left at 0.")
    ed_s = st.data_editor(INIT_SALES, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_s")
with t2:
    st.caption("Record route fuel, food, logistics, and local operational costs.")
    ed_o = st.data_editor(INIT_OFFICE, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_o")
with t3:
    st.caption("Record field allowances, per-diem, and tour advances given to personnel.")
    ed_st = st.data_editor(INIT_STAFF, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_st")

s_qty = pd.to_numeric(ed_s["Qty"], errors="coerce").fillna(0.0)
s_rate = pd.to_numeric(ed_s["Rate (Rs.)"], errors="coerce").fillna(0.0)
s_cash = pd.to_numeric(ed_s["Cash Recd (Rs.)"], errors="coerce").fillna(0.0)
s_c_man = pd.to_numeric(ed_s["Credit Given (Rs.)"], errors="coerce").fillna(0.0)

s_bill = s_qty * s_rate
s_cred = s_c_man.where(s_c_man > 0, (s_bill - s_cash).clip(lower=0.0))
s_tot = s_bill.where(s_bill > 0, s_cash + s_cred)

tot_sales, tot_cash, tot_credit = float(s_tot.sum()), float(s_cash.sum()), float(s_cred.sum())
tot_exp = float(pd.to_numeric(ed_o["Amount (Rs.)"], errors="coerce").fillna(0.0).sum())
tot_adv = float(pd.to_numeric(ed_st["Amount (Rs.)"], errors="coerce").fillna(0.0).sum())
tot_disbursed = tot_exp + tot_adv
net_cash = tot_cash - tot_disbursed

with t1:
    st.info(f"📋 Live Credit & Sales Tracker: Billed: {money(tot_sales)} | Cash Recd: {money(tot_cash)} | Credit Given (Udharo): {money(tot_credit)}")

st.markdown("### 📊 Financial Closing Summary")
sb1, sb2, sb3 = st.columns(3)
with sb1:
    st.markdown(f"""<div class="g-box"><b style="color:#164E33;">🛒 1. Sales & Revenue Position</b>
    <div class="s-row"><span>Total Gross Billed:</span><span class="s-val">{money(tot_sales)}</span></div>
    <div class="s-row"><span>Cash Collected:</span><span class="s-val" style="color:#164E33;">{money(tot_cash)}</span></div>
    <div class="s-row" style="border:none;"><span>Credit Given:</span><span class="s-val" style="color:#A04000;">{money(tot_credit)}</span></div></div>""", unsafe_allow_html=True)
with sb2:
    st.markdown(f"""<div class="g-box"><b style="color:#164E33;">🏢 2. Route Disbursements</b>
    <div class="s-row"><span>Operating Expenses:</span><span class="s-val">{money(tot_exp)}</span></div>
    <div class="s-row"><span>Staff Advances:</span><span class="s-val">{money(tot_adv)}</span></div>
    <div class="s-row" style="border:none;"><span>Total Outflow:</span><span class="s-val" style="color:#800000;">{money(tot_disbursed)}</span></div></div>""", unsafe_allow_html=True)
with sb3:
    col_net = "#0D2818" if net_cash >= 0 else "#900C3F"
    st.markdown(f"""<div class="g-acc"><b style="color:#0D2818;">💰 3. Final Cash Settlement</b>
    <div class="s-row"><span>Cash Collected:</span><span class="s-val">{money(tot_cash)}</span></div>
    <div class="s-row"><span>Less Outflow:</span><span class="s-val">- {money(tot_disbursed)}</span></div>
    <div style="margin-top:6px; display:flex; justify-content:space-between; align-items:center;">
    <span style="font-weight:800;">NET IN HAND:</span><span style="font-weight:800; font-size:1.2rem; color:{col_net};">{money(net_cash)}</span></div></div>""", unsafe_allow_html=True)

if net_cash < 0: st.warning("⚠️ Warning: Disbursements exceed cash collected. Net Cash is negative.")

def sync_to_sheets():
    s_items = []
    for _, r in ed_s.iterrows():
        q, rt, c, cm = float(r.get("Qty", 0) or 0), float(r.get("Rate (Rs.)", 0) or 0), float(r.get("Cash Recd (Rs.)", 0) or 0), float(r.get("Credit Given (Rs.)", 0) or 0)
        tb = q * rt; cb = cm if cm > 0 else max(0.0, tb - c)
        if tb == 0: tb = c + cb
        pname, cname = str(r.get("Product Name", "")).strip(), str(r.get("Client Name", "")).strip()
        if q > 0 or c > 0 or cb > 0 or pname or cname:
            s_items.append({"invoice": str(r.get("Invoice No.", "INV-01")), "client_name": cname or "Walk-in Party", "address": str(r.get("Address", "Birgunj")), "product_name": pname or "General Stock", "qty": q, "rate": rt, "cash_collected": c, "credit_given": cb, "total_sale": tb})

    e_items = [{"details": str(r.get("Details", "")), "paid_to": str(r.get("Paid To", "Vendor")), "mode": str(r.get("Mode", "Cash")), "amount": float(r.get("Amount (Rs.)", 0) or 0), "remarks": str(r.get("Remarks", ""))} for _, r in ed_o.iterrows() if float(r.get("Amount (Rs.)", 0) or 0) > 0 or str(r.get("Details", "")).strip()]
    a_items = [{"personnel_name": str(r.get("Staff Name", "")), "purpose": str(r.get("Purpose", "Advance")), "type": str(r.get("Category", "Staff Advance")), "amount": float(r.get("Amount (Rs.)", 0) or 0), "remarks": str(r.get("Remarks", ""))} for _, r in ed_st.iterrows() if float(r.get("Amount (Rs.)", 0) or 0) > 0 or str(r.get("Staff Name", "")).strip()]

    if not (s_items or e_items or a_items):
        st.warning("No entries to sync."); return False, 0

    payload = {"date": str(rep_date), "report_no": str(st.session_state["rep_no"]), "staff_name": str(mr_name), "sales": s_items, "expenses": e_items, "advances": a_items}
    try:
        res = requests.post(WEB_APP_URL, json=payload, timeout=25, allow_redirects=True)
        if res.status_code == 200:
            st.session_state["last_sync_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return (True, len(s_items) + len(e_items) + len(a_items))
        else:
            st.error(f"Google responded with HTTP {res.status_code}. Check Apps Script permissions.")
            return (False, 0)
    except Exception as err:
        st.error(f"Sync Connection Error: {err}"); return False, 0

def make_pdf():
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=10*mm, rightMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"<b>ALPINE HERBS PVT. LTD. - DAILY FIELD CLOSING VOUCHER</b>", styles["Heading1"]),
        Paragraph(f"<b>Ref:</b> {st.session_state['rep_no']} | <b>Date:</b> {rep_date} | <b>MR:</b> {mr_name} | <b>Route:</b> {route_name or 'Birgunj'}", styles["Normal"]),
        Spacer(1, 3*mm)
    ]
    s_rows = [["Inv #", "Client Name", "Address", "Product", "Qty", "Rate", "Cash Recd", "Credit Given", "Total"]]
    for _, r in ed_s.iterrows():
        q, rt, c,
