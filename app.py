import streamlit as st, pandas as pd, requests, uuid, math
from datetime import date, datetime
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="ALPINE HERBS - Daily Field Closing", page_icon="🌿", layout="wide")

USERS = {
    "Alpine": "AHP@123",
    "Pritam": "Pritam@2024",
    "Admin": "AlpineAdmin@123",
    "Manager": "Alpine@Birgunj"
}

# Silent backend endpoint (No UI exposure)
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzorFkbj5in7NdNAsh_zvSPMZSzM1HmzVTCnoCCUQ_85izF9C1GrC1BB00WvLiRwri5/exec"

CLIENT_DB = [
    {"name": "Naresh Medical", "code": "BAR-001", "area": "Kalaiya", "dues": 3070},
    {"name": "Mahir Health Clinic", "code": "BAR-002", "area": "Jeetpur", "dues": 7105},
    {"name": "Dev Medical", "code": "BAR-003", "area": "Kalaiya", "dues": 2030},
    {"name": "Ashok Medical Hall", "code": "PAR-002", "area": "Naukatola", "dues": 12230},
    {"name": "Ganesh Srestha", "code": "PAR-015", "area": "Birgunj", "dues": 63390},
    {"name": "Roshan Pharmacy", "code": "PAR-032", "area": "Birgunj", "dues": 74290},
    {"name": "Sandip Medical Hall", "code": "PAR-035", "area": "Langada Chouk", "dues": 30195}
]

def clean_str(val, default=""):
    if pd.isna(val) or val is None: return default
    s = str(val).strip()
    return default if s.lower() in ("nan", "none", "null", "undefined", "") else s

def clean_num(val, default=0.0):
    if pd.isna(val) or val is None: return default
    try:
        v = float(val)
        return default if math.isnan(v) or math.isinf(v) else v
    except: return default

def get_nepali_miti(ad_date):
    try:
        import nepali_datetime
        if not isinstance(ad_date, (date, datetime)): ad_date = date.today()
        bs = nepali_datetime.date.from_datetime_date(ad_date)
        return f"{bs.year:04d}-{bs.month:02d}-{bs.day:02d} B.S."
    except:
        return "2083-07-14 B.S."

money = lambda v: f"Rs. {clean_num(v):,.2f}"

# Refined Professional Theme & Header Layout Styling
st.markdown("""<style>
#MainMenu, footer { visibility: hidden; }
header { visibility: visible; }
.block-container { 
    padding-top: 2.2rem !important; 
    padding-bottom: 3rem !important; 
    max-width: 1540px; 
}
input::placeholder { color: #8FA698 !important; opacity: 1 !important; }
.main-header-banner {
    background: linear-gradient(135deg, #0D2818 0%, #164E33 100%);
    padding: 18px 24px;
    border-radius: 10px;
    color: white;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 12px rgba(13, 40, 24, 0.08);
}
.main-header-title {
    font-size: 1.65rem;
    font-weight: 800;
    letter-spacing: 0.5px;
    color: #FFFFFF;
    line-height: 1.2;
}
.main-header-sub {
    font-size: 0.85rem;
    color: #D5EBDD;
    font-weight: 500;
    margin-top: 3px;
}
.g-box { 
    background: #FFFFFF; 
    border: 1px solid #C8DCCF; 
    border-top: 3.5px solid #2D7D52; 
    border-radius: 8px; 
    padding: 14px 16px; 
    height: 100%; 
    box-shadow: 0 2px 6px rgba(0,0,0,0.02);
}
.g-acc { 
    background: #F4FAF6; 
    border: 1px solid #B0D4BE; 
    border-top: 3.5px solid #0D2818; 
    border-radius: 8px; 
    padding: 14px 16px; 
    height: 100%; 
    box-shadow: 0 2px 8px rgba(13, 40, 24, 0.04);
}
.s-row { 
    display: flex; 
    justify-content: space-between; 
    padding: 6px 0; 
    border-bottom: 1px dashed #E2ECE5; 
    font-size: 0.92rem; 
    color: #333333;
}
.s-val { font-weight: 700; color: #0D2818; }
.user-card { 
    background: #F4FAF6; 
    border: 1px solid #D5EBDD; 
    border-left: 4px solid #164E33; 
    padding: 12px; 
    border-radius: 6px; 
    margin-bottom: 12px; 
    font-size: 0.9rem;
    color: #1A3024;
}
</style>""", unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user"] = ""

# --- LOGIN SCREEN ---
if not st.session_state["authenticated"]:
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.1, 1])
    with c2:
        with st.container(border=True):
            st.markdown("""
            <div style="text-align: center; margin-bottom: 1.2rem;">
                <h2 style="color: #0D2818; margin-bottom: 2px; font-weight: 800;">🌿 ALPINE HERBS</h2>
                <p style="color: #2D7D52; font-size: 0.88rem; font-weight: 600; margin: 0;">FIELD OPERATIONS PORTAL</p>
            </div>
            """, unsafe_allow_html=True)
            u = st.text_input("Username", placeholder="Username", label_visibility="collapsed")
            p = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
            st.write("")
            if st.button("🔑 Sign In to Portal", type="primary", use_container_width=True):
                if u.strip() in USERS and USERS[u.strip()] == p.strip():
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = u.strip()
                    st.rerun()
                else: st.error("❌ Invalid Username or Password.")
    st.stop()

cur_user = st.session_state.get("user", "Staff")

if "rep_no" not in st.session_state:
    st.session_state["rep_no"] = f"ALP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

# --- SIDEBAR (CLEAN SESSION & CLIENT DIRECTORY ONLY) ---
with st.sidebar:
    st.markdown("#### Active Session")
    st.markdown(f"""<div class="user-card">
    <b>User:</b> {cur_user}<br>
    <b>Territory:</b> Birgunj Sector<br>
    <b>Ref No:</b> <code>{st.session_state['rep_no']}</code>
    </div>""", unsafe_allow_html=True)

    if st.button("🔒 Sign Out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["user"] = ""
        st.rerun()

    st.divider()
    st.markdown("#### 📋 Client Dues Lookup")
    sq = st.text_input("Search Chemist / Town", placeholder="e.g. Naresh, Kalaiya").strip().lower()
    matches = [c for c in CLIENT_DB if sq in c['name'].lower() or sq in c['area'].lower()] if sq else CLIENT_DB
    for item in matches[:6]:
        st.markdown(f"**{item['name']}** (`{item['code']}`)\n{item['area']} | Due: **Rs. {item['dues']:,}**")
        st.write("---")

# Initial DataFrames
INIT_SALES = pd.DataFrame([
    {"Invoice No.": "INV-01", "Client Name": "", "Address": "Birgunj", "Product Name": "", "Qty": 0.0, "FOC Qty": 0.0, "Rate (Rs.)": 0.0, "Cash Recd (Rs.)": 0.0, "Credit Given (Rs.)": 0.0},
    {"Invoice No.": "INV-02", "Client Name": "", "Address": "Birgunj", "Product Name": "", "Qty": 0.0, "FOC Qty": 0.0, "Rate (Rs.)": 0.0, "Cash Recd (Rs.)": 0.0, "Credit Given (Rs.)": 0.0},
    {"Invoice No.": "INV-03", "Client Name": "", "Address": "Birgunj", "Product Name": "", "Qty": 0.0, "FOC Qty": 0.0, "Rate (Rs.)": 0.0, "Cash Recd (Rs.)": 0.0, "Credit Given (Rs.)": 0.0}
])

INIT_COLLECTIONS = pd.DataFrame([
    {"Receipt No.": "REC-01", "Client Name": "", "Payment Mode": "Cash", "Amount Collected (Rs.)": 0.0, "Remarks / Ref": "Old Dues Collection"},
    {"Receipt No.": "REC-02", "Client Name": "", "Payment Mode": "Cash", "Amount Collected (Rs.)": 0.0, "Remarks / Ref": "Old Dues Collection"}
])

INIT_RETURNS = pd.DataFrame([
    {"Client Name": "", "Product Name": "", "Return Qty": 0.0, "Rate (Rs.)": 0.0, "Total Return (Rs.)": 0.0, "Reason": "Near Expiry / Breakage"}
])

INIT_OFFICE = pd.DataFrame([{"Details": "", "Paid To": "Vendor", "Mode": "Cash", "Amount (Rs.)": 0.0, "Remarks": ""}])
INIT_STAFF = pd.DataFrame([{"Staff Name": "", "Purpose": "Tour Advance", "Category": "Staff Advance", "Amount (Rs.)": 0.0, "Remarks": ""}])

# Professional Main Header (Full Banner, No Clipped Margin)
st.markdown("""
<div class="main-header-banner">
    <div>
        <div class="main-header-title">🌿 ALPINE HERBS PVT. LTD.</div>
        <div class="main-header-sub">BIRGUNJ, NEPAL &nbsp;|&nbsp; DAILY FIELD CLOSING & AUDIT REPORT</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Tour Metadata Inputs
c1, c2, c3, c4, c5 = st.columns([1.1, 1.1, 1.3, 1.3, 1.1])
with c1:
    rep_date = st.date_input("Date (A.D.)", value=date.today())
with c2:
    bs_miti = get_nepali_miti(rep_date)
    st.text_input("Nepali Miti (B.S.)", value=bs_miti, disabled=True)
with c3:
    mr_name = st.text_input("MR Name", value=cur_user if cur_user != "Alpine" else "Pritam Gupta")
with c4:
    route_name = st.text_input("Route / Territory", placeholder="e.g. Birgunj - Kalaiya - Simara")
with c5:
    st.text_input("Report Ref", value=st.session_state["rep_no"], disabled=True)

# Data Entry Tabs
t1, t2, t3, t4 = st.tabs([
    "🛒 1. Sales & Collections",
    "🏢 2. Operating Expenses",
    "👥 3. Staff Advances & Imprest",
    "🔄 4. Goods Return (Clients)"
])

with t1:
    st.markdown("##### 🛒 Sales Ledger (With FOC Bonus Tracking)")
    st.caption("FOC Qty tracks promotional items and does not inflate billed totals. Empty rows are skipped.")
    ed_s = st.data_editor(INIT_SALES, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_s")

    st.write("")
    st.markdown("##### 💵 Dedicated Cash Collections & Payment Receipts")
    st.caption("Record direct payments and dues recovered from clients with receipt numbers.")
    ed_c = st.data_editor(INIT_COLLECTIONS, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_c")

with t2:
    st.caption("Record route fuel, food, logistics, and operational vendor costs.")
    ed_o = st.data_editor(INIT_OFFICE, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_o")

with t3:
    st.caption("Record daily allowances, per-diem, and tour advances given to personnel.")
    ed_st = st.data_editor(INIT_STAFF, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_st")

with t4:
    st.markdown("##### 🔄 Goods Return Ledger (Client Product Returns)")
    st.caption("Record stock returned by clients due to expiry, damage, or slow turnover.")
    ed_r = st.data_editor(INIT_RETURNS, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_r")

# Financial Calculations
s_qty = ed_s["Qty"].apply(clean_num)
s_rate = ed_s["Rate (Rs.)"].apply(clean_num)
s_cash = ed_s["Cash Recd (Rs.)"].apply(clean_num)
s_c_man = ed_s["Credit Given (Rs.)"].apply(clean_num)
s_bill = s_qty * s_rate
s_cred = s_c_man.where(s_c_man > 0, (s_bill - s_cash).clip(lower=0.0))
s_tot = s_bill.where(s_bill > 0, s_cash + s_cred)

tot_sales = float(s_tot.sum())
tot_sales_cash = float(s_cash.sum())
tot_credit = float(s_cred.sum())

col_amt = ed_c["Amount Collected (Rs.)"].apply(clean_num)
tot_receipt_cash = float(col_amt.sum())
total_gross_cash = tot_sales_cash + tot_receipt_cash

ret_q = ed_r["Return Qty"].apply(clean_num)
ret_rt = ed_r["Rate (Rs.)"].apply(clean_num)
tot_returns = float((ret_q * ret_rt).sum())

tot_exp = float(ed_o["Amount (Rs.)"].apply(clean_num).sum())
tot_adv = float(ed_st["Amount (Rs.)"].apply(clean_num).sum())
tot_disbursed = tot_exp + tot_adv
net_cash = total_gross_cash - tot_disbursed

with t1:
    st.info(f"📋 Live Cash Breakdown: Direct Sales Cash: {money(tot_sales_cash)} + Dues Receipts: {money(tot_receipt_cash)} = Total Cash: {money(total_gross_cash)} | Credit Given: {money(tot_credit)}")

# Corporate Financial Summary Cards (Bottom of Form)
st.markdown("### 📊 Financial Closing Summary")
sb1, sb2, sb3 = st.columns(3)
with sb1:
    st.markdown(f"""<div class="g-box"><b style="color:#164E33; text-transform:uppercase; letter-spacing:0.5px;">🛒 1. Revenue & Collections</b>
    <div class="s-row"><span>Total Sales Billed:</span><span class="s-val">{money(tot_sales)}</span></div>
    <div class="s-row"><span>Direct Sales Cash:</span><span class="s-val">{money(tot_sales_cash)}</span></div>
    <div class="s-row"><span>Receipt Dues Collected:</span><span class="s-val">{money(tot_receipt_cash)}</span></div>
    <div class="s-row"><span>Total Cash Collected:</span><span class="s-val" style="color:#164E33;">{money(total_gross_cash)}</span></div>
    <div class="s-row"><span>Credit Given:</span><span class="s-val" style="color:#A04000;">{money(tot_credit)}</span></div>
    <div class="s-row" style="border:none;"><span>Goods Return Total:</span><span class="s-val" style="color:#6B46C1;">{money(tot_returns)}</span></div></div>""", unsafe_allow_html=True)
with sb2:
    st.markdown(f"""<div class="g-box"><b style="color:#164E33; text-transform:uppercase; letter-spacing:0.5px;">🏢 2. Route Disbursements</b>
    <div class="s-row"><span>Operating Expenses:</span><span class="s-val">{money(tot_exp)}</span></div>
    <div class="s-row"><span>Staff Advances:</span><span class="s-val">{money(tot_adv)}</span></div>
    <div class="s-row" style="border:none;"><span>Total Outflow:</span><span class="s-val" style="color:#800000;">{money(tot_disbursed)}</span></div></div>""", unsafe_allow_html=True)
with sb3:
    col_net = "#0D2818" if net_cash >= 0 else "#900C3F"
    st.markdown(f"""<div class="g-acc"><b style="color:#0D2818; text-transform:uppercase; letter-spacing:0.5px;">💰 3. Final Cash Settlement</b>
    <div class="s-row"><span>Total Cash Collected:</span><span class="s-val">{money(total_gross_cash)}</span></div>
    <div class="s-row"><span>Less Total Outflow:</span><span class="s-val">- {money(tot_disbursed)}</span></div>
    <div style="margin-top:8px; display:flex; justify-content:space-between; align-items:center;">
    <span style="font-weight:800; font-size:0.95rem;">NET CASH IN HAND:</span><span style="font-weight:800; font-size:1.3rem; color:{col_net};">{money(net_cash)}</span></div></div>""", unsafe_allow_html=True)

if net_cash < 0: st.warning("⚠️ Warning: Route disbursements exceed total cash collected today. Net Cash is negative.")

# Background Synchronization Function
def sync_to_sheets():
    s_items = []
    for _, r in ed_s.iterrows():
        cname, pname = clean_str(r.get("Client Name")), clean_str(r.get("Product Name"))
        q, f_q, rt = clean_num(r.get("Qty")), clean_num(r.get("FOC Qty")), clean_num(r.get("Rate (Rs.)"))
        c, cm = clean_num(r.get("Cash Recd (Rs.)")), clean_num(r.get("Credit Given (Rs.)"))
        tb = q * rt
        cb = cm if cm > 0 else max(0.0, tb - c)
        if tb == 0 and (c > 0 or cb > 0): tb = c + cb
        if cname or pname or q > 0 or f_q > 0 or c > 0 or cb > 0:
            s_items.append({
                "invoice": clean_str(r.get("Invoice No."), "INV-01"), "client_name": cname or "Walk-in Party",
                "address": clean_str(r.get("Address"), "Birgunj"), "product_name": pname or "General Stock",
                "qty": q, "foc_qty": f_q, "rate": rt, "cash_collected": c, "credit_given": cb, "total_sale": tb
            })

    c_items = []
    for _, r in ed_c.iterrows():
        cname, rec = clean_str(r.get("Client Name")), clean_str(r.get("Receipt No."), "REC-01")
        amt = clean_num(r.get("Amount Collected (Rs.)"))
        if cname or amt > 0:
            c_items.append({
                "receipt_no": rec, "client_name": cname or "Chemist",
                "mode": clean_str(r.get("Payment Mode"), "Cash"), "amount": amt,
                "remarks": clean_str(r.get("Remarks / Ref"), "Old Dues")
            })

    r_items = []
    for _, r in ed_r.iterrows():
        cname, pname = clean_str(r.get("Client Name")), clean_str(r.get("Product Name"))
        rq, r_rt = clean_num(r.get("Return Qty")), clean_num(r.get("Rate (Rs.)"))
        if cname or pname or rq > 0:
            r_items.append({
                "client_name": cname or "Chemist", "product_name": pname or "Returned Item",
                "qty": rq, "rate": r_rt, "total": rq * r_rt, "reason": clean_str(r.get("Reason"), "Expiry / Breakage")
            })

    e_items = []
    for _, r in ed_o.iterrows():
        amt, det = clean_num(r.get("Amount (Rs.)")), clean_str(r.get("Details"))
        if amt > 0 or det:
            e_items.append({"details": det or "Route Expense", "paid_to": clean_str(r.get("Paid To"), "Vendor"), "mode": clean_str(r.get("Mode"), "Cash"), "amount": amt, "remarks": clean_str(r.get("Remarks"))})

    a_items = []
    for _, r in ed_st.iterrows():
        amt, staff = clean_num(r.get("Amount (Rs.)")), clean_str(r.get("Staff Name"))
        if amt > 0 or staff:
            a_items.append({"personnel_name": staff or "Staff", "purpose": clean_str(r.get("Purpose"), "Tour Advance"), "type": clean_str(r.get("Category"), "Staff Advance"), "amount": amt, "remarks": clean_str(r.get("Remarks"))})

    if not (s_items or c_items or r_items or e_items or a_items):
        st.warning("⚠️ No valid entries to sync. Please fill in records first.")
        return False, 0

    payload = {
        "date": str(rep_date), "bs_date": str(bs_miti), "report_no": str(st.session_state["rep_no"]),
        "staff_name": clean_str(mr_name, "MR Staff"), "sales": s_items,
        "collections": c_items, "returns": r_items,
        "expenses": e_items, "advances": a_items
    }

    try:
        res = requests.post(WEB_APP_URL, json=payload, timeout=25, allow_redirects=True)
        raw_text = res.text.strip()
        if "<!DOCTYPE html" in raw_text or "accounts.google.com" in raw_text:
            st.error("❌ Google Permission Error: Access restricted. Set 'Who has access' to 'Anyone' in Apps Script.")
            return False, 0
        try:
            data = res.json()
            if data.get("status") == "success":
                st.session_state["sync_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return True, data.get("records_synced", len(s_items) + len(c_items) + len(r_items) + len(e_items) + len(a_items))
            else:
                st.error(f"❌ Google Script Error: {data.get('message', raw_text)}")
                return False, 0
        except Exception:
            if "success" in raw_text.lower():
                return True, len(s_items) + len(c_items) + len(r_items) + len(e_items) + len(a_items)
            st.error(f"❌ Unexpected Google Response: {raw_text[:200]}")
            return False, 0
    except Exception as err:
        st.error(f"❌ Sync Connection Error: {err}")
        return False, 0

# Multi-Section PDF Generator
def make_pdf():
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=10*mm, rightMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm)
    styles = getSampleStyleSheet()
    t_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#164E33")), 
        ('TEXTCOLOR', (0,0), (-1,0), colors.white), 
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey), 
        ('FONTSIZE', (0,0), (-1,-1), 8)
    ])

    story = [
        Paragraph(f"<b>ALPINE HERBS PVT. LTD. - DAILY FIELD CLOSING VOUCHER</b>", styles["Heading1"]),
        Paragraph(f"<b>Ref:</b> {st.session_state['rep_no']} | <b>Date:</b> {rep_date} ({bs_miti}) | <b>MR:</b> {mr_name} | <b>Route:</b> {route_name or 'Birgunj'}", styles["Normal"]),
        Spacer(1, 3*mm)
    ]
    
    # 1. Sales Table
    s_rows = [["Inv #", "Client Name", "Address", "Product", "Qty", "FOC", "Rate", "Cash Recd", "Credit", "Total"]]
    for _, r in ed_s.iterrows():
        cname, pname = clean_str(r.get("Client Name")), clean_str(r.get("Product Name"))
        q, f_q, rt = clean_num(r.get("Qty")), clean_num(r.get("FOC Qty")), clean_num(r.get("Rate (Rs.)"))
        c, cm = clean_num(r.get("Cash Recd (Rs.)")), clean_num(r.get("Credit Given (Rs.)"))
        tb = q * rt; cb = cm if cm > 0 else max(0.0, tb - c)
        if tb == 0 and (c > 0 or cb > 0): tb = c + cb
        if cname or pname or q > 0 or f_q > 0 or c > 0 or cb > 0:
            s_rows.append([clean_str(r.get("Invoice No."), "INV-01"), cname or "Walk-in Party", clean_str(r.get("Address"), "Birgunj"), pname or "General Stock", str(q), str(f_q), money(rt), money(c), money(cb), money(tb)])
    if len(s_rows) > 1:
        story.append(Paragraph("<b>1. Sales & Invoicing Ledger</b>", styles["Heading2"]))
        t_s = Table(s_rows, colWidths=[18*mm, 48*mm, 24*mm, 46*mm, 14*mm, 14*mm, 26*mm, 26*mm, 26*mm, 26*mm], style=t_style)
        story.extend([t_s, Spacer(1, 3*mm)])

    # 2. Cash Collections Table
    c_rows = [["Receipt #", "Client / Chemist Name", "Payment Mode", "Amount Collected", "Remarks / Ref"]]
    for _, r in ed_c.iterrows():
        cname, amt = clean_str(r.get("Client Name")), clean_num(r.get("Amount Collected (Rs.)"))
        if cname or amt > 0:
            c_rows.append([clean_str(r.get("Receipt No."), "REC-01"), cname or "Chemist", clean_str(r.get("Payment Mode"), "Cash"), money(amt), clean_str(r.get("Remarks / Ref"))])
    if len(c_rows) > 1:
        story.append(Paragraph("<b>2. Cash Collections & Payment Receipts</b>", styles["Heading2"]))
        t_c = Table(c_rows, colWidths=[30*mm, 85*mm, 45*mm, 45*mm, 63*mm], style=t_style)
        story.extend([t_c, Spacer(1, 3*mm)])

    # 3. Goods Return Table
    r_rows = [["Client Name", "Product Name", "Return Qty", "Rate", "Total Value", "Reason / Batch"]]
    for _, r in ed_r.iterrows():
        cname, pname = clean_str(r.get("Client Name")), clean_str(r.get("Product Name"))
        rq, r_rt = clean_num(r.get("Return Qty")), clean_num(r.get("Rate (Rs.)"))
        if cname or pname or rq > 0:
            r_rows.append([cname or "Chemist", pname or "Returned Item", str(rq), money(r_rt), money(rq * r_rt), clean_str(r.get("Reason"))])
    if len(r_rows) > 1:
        story.append(Paragraph("<b>3. Goods Return Ledger</b>", styles["Heading2"]))
        t_r = Table(r_rows, colWidths=[65*mm, 75*mm, 25*mm, 30*mm, 35*mm, 38*mm], style=t_style)
        story.extend([t_r, Spacer(1, 3*mm)])

    # 4. Expenses Summary
    e_rows = [["Details / Particulars", "Paid To / Vendor", "Mode", "Amount", "Remarks"]]
    for _, r in ed_o.iterrows():
        amt, det = clean_num(r.get("Amount (Rs.)")), clean_str(r.get("Details"))
        if amt > 0 or det:
            e_rows.append([det or "Route Expense", clean_str(r.get("Paid To"), "Vendor"), clean_str(r.get("Mode"), "Cash"), money(amt), clean_str(r.get("Remarks"))])
    if len(e_rows) > 1:
        story.append(Paragraph("<b>4. Route Operating Expenses</b>", styles["Heading2"]))
        t_e = Table(e_rows, colWidths=[90*mm, 55*mm, 35*mm, 35*mm, 53*mm], style=t_style)
        story.extend([t_e, Spacer(1, 3*mm)])

    # 5. Grand Reconciliation Table
    story.append(Paragraph("<b>5. Grand Financial Settlement</b>", styles["Heading2"]))
    sum_rows = [
        ["Total Billed", "Total Cash Recd", "Credit Given", "Goods Return", "Total Outflow", "NET CASH IN HAND"],
        [money(tot_sales), money(total_gross_cash), money(tot_credit), money(tot_returns), money(tot_disbursed), money(net_cash)]
    ]
    t_sum = Table(sum_rows, colWidths=[45*mm, 45*mm, 45*mm, 45*mm, 45*mm, 43*mm], style=[
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0D2818")), 
        ('TEXTCOLOR', (0,0), (-1,0), colors.white), 
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey), 
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#EAF5EE")), 
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ])
    story.extend([t_sum, Spacer(1, 5*mm)])
    story.append(Table([
        ["\n____________________", "\n____________________", "\n____________________"], 
        ["Medical Representative", "Area Sales Manager", "Head Office Audit"]
    ], colWidths=[89*mm]*3, style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    doc.build(story)
    return buf.getvalue()

# Form Submission Controls
st.write("")
b1, b2 = st.columns([3, 1])
with b1:
    if st.button("🚀 CONFIRM & SYNC REPORT TO MASTER", type="primary", use_container_width=True):
        with st.spinner("Syncing to Master Ledger..."):
            ok, count = sync_to_sheets()
            if ok:
                st.session_state["pdf"] = make_pdf()
                sync_t = st.session_state.get("sync_time", "")
                st.balloons()
                st.success(f"✅ Report `{st.session_state['rep_no']}` synchronized successfully! ({count} records written to Google Sheets at {sync_t})")
with b2:
    if st.button("🔄 Reset / Start Blank", use_container_width=True):
        st.session_state["rep_no"] = f"ALP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        for k in ["ed_s", "ed_c", "ed_r", "ed_o", "ed_st", "pdf"]: st.session_state.pop(k, None)
        st.rerun()

if "pdf" in st.session_state:
    st.write("")
    st.download_button("⬇️ DOWNLOAD OFFICIAL SIGN-OFF PDF AUDIT VOUCHER", data=st.session_state["pdf"], file_name=f"{st.session_state['rep_no']}.pdf", mime="application/pdf", use_container_width=True)
