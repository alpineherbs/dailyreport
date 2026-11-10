import streamlit as st
import pandas as pd
import requests
import uuid
import math
import io
from datetime import date, datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="ALPINE HERBS - Daily Field Closing", page_icon="🌿", layout="wide")

# --- CENTRAL CONFIGURATION ---
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzorFkbj5in7NdNAsh_zvSPMZSzM1HmzVTCnoCCUQ_85izF9C1GrC1BB00WvLiRwri5/exec"
SHEET_ID = "1cpPYFS9EkajB5tGfMnReIJ71cmB5djz6oaMvvEoqs6A"

USERS = {
    "Alpine": "AHP@123",
    "Pritam": "Pritam@2024",
    "Admin": "AlpineAdmin@123",
    "Manager": "Alpine@Birgunj"
}

# --- CLIENT DIRECTORY ---
CLIENTS_DATA = """name,code,area,district,phone,dues
Aarav Pharma,PAR-001,Birgunj,Parsa,,4500
Ashok Medical Hall,PAR-002,Naukatola,Parsa,,12230
Apex Health Care,BAR-004,Kalaiya,Bara,,3100
Baba Medical Store,PAR-005,Birgunj,Parsa,,8500
Bara Pharma Distributors,BAR-007,Simara,Bara,,15400
Birgunj Health Clinic,PAR-006,Birgunj,Parsa,,9200
Bala Ji Medical Hall,BAR-026,Aarnawa Chouk,Bara,,3195
City Medical Hall,PAR-008,Birgunj,Parsa,,6700
Care & Cure Pharmacy,BAR-009,Jeetpur,Bara,,4300
Chandip Medical Hall,PAR-007,Kathmandu Tol,Parsa,,0
Dev Medical,BAR-003,Kalaiya,Bara,9845227985,1500
Dinamik Pharma,PAR-008,Sano Sugauli,Parsa,,15815
Durga Medical Store,PAR-010,Birgunj,Parsa,,11500
Dinanath Medical Hall,PAR-034,Harpur,Parsa,,1740
Everest Health Clinic,BAR-014,Kalaiya,Bara,,2635
Everest Pharmacy,PAR-009,Birwa Chouk,Parsa,,0
Fatepur Health Clinic,PAR-010,Fatepur,Parsa,,0
Friends Medical Hall,PAR-012,Birgunj,Parsa,,3400
Ganesh Srestha,PAR-012,Birgunj,Parsa,,63390
Gupta Medical Store,BAR-016,Kalaiya,Bara,,7800
Hariom Medical,BAR-005,Kolvi,Bara,9811229323,2300
Himal Health Clinic,PAR-017,Naukatola,Parsa,,4100
Ideal Pharmacy,PAR-018,Birgunj,Parsa,,6900
Janta Medical Hall,BAR-019,Jeetpur,Bara,,8300
Jeevan Raksha Clinic,PAR-020,Birgunj,Parsa,,12800
Kalaiya Medical Centre,BAR-021,Kalaiya,Bara,,9400
Krishna Pharmacy,PAR-022,Langada Chouk,Parsa,,14100
Laxmi Medical Store,PAR-023,Birgunj,Parsa,,18500
Mahir Health Clinic,BAR-002,Jeetpur,Bara,9807100296,8165
Naresh Medical,BAR-001,Kalaiya,Bara,9807267001,3100
Nimash Medical,BAR-016,Simara,Bara,9845120836,4620
Roshan Pharmacy,PAR-025,Birgunj,Parsa,,74290
Sandip Medical Hall,PAR-027,Langada Chouk,Parsa,,30195
Sanjeevani Clinic,BAR-009,Simara,Bara,9845130209,2195
Universal Health Clinic,PAR-038,Birgunj,Parsa,,15700
Zenith Health Care,PAR-042,Birgunj,Parsa,,7300"""

if "client_db" not in st.session_state:
    st.session_state["client_db"] = pd.read_csv(io.StringIO(CLIENTS_DATA.strip()), dtype=str).fillna("").to_dict("records")
    for c in st.session_state["client_db"]:
        try: c["dues"] = float(c["dues"]) if c["dues"] != "" else 0.0
        except: c["dues"] = 0.0

if "form_id" not in st.session_state:
    st.session_state["form_id"] = 0

def clean_str(val, default=""):
    if pd.isna(val) or val is None: return default
    s = str(val).strip()
    return default if s.lower() in ("nan", "none", "null", "undefined", "") else s

def clean_num(val, default=0.0):
    if pd.isna(val) or val is None: return default
    try:
        s = str(val).replace("Rs.", "").replace("Rs", "").replace(",", "").strip()
        v = float(s)
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

def resolve_client(raw_val, default_area="Birgunj"):
    s = clean_str(raw_val)
    if not s or s.lower() == "other / walk-in":
        return "Walk-in Party", "WALK-IN", default_area
    if "— 📍" in s:
        s = s.split("— 📍")[0].strip()
    if "[" in s and s.endswith("]"):
        parts = s.rsplit("[", 1)
        cname, ccode = parts[0].strip(), parts[1].replace("]", "").strip()
        for item in st.session_state["client_db"]:
            if item["code"].lower() == ccode.lower():
                return cname, ccode, item.get("area", default_area)
        return cname, ccode, default_area
    for item in st.session_state["client_db"]:
        if item["name"].lower() == s.lower():
            return item["name"], item["code"], item.get("area", default_area)
    return s, "WALK-IN", default_area

# --- STYLING ---
st.markdown("""<style>
#MainMenu, footer { visibility: hidden; }
header { visibility: visible; }
.block-container { padding-top: 1.8rem !important; padding-bottom: 2.5rem !important; max-width: 1540px; }
.login-box {
    background: #FFFFFF;
    border: 1px solid #C8DCCF;
    border-top: 5px solid #164E33;
    border-radius: 10px;
    padding: 24px 28px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.06);
    margin-top: 2rem;
}
.main-header-banner {
    background: linear-gradient(135deg, #0D2818 0%, #164E33 100%);
    padding: 16px 22px;
    border-radius: 8px;
    color: white;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 12px rgba(13, 40, 24, 0.08);
}
.g-box { background: #FFFFFF; border: 1px solid #C8DCCF; border-top: 3.5px solid #2D7D52; border-radius: 8px; padding: 14px 16px; height: 100%; box-shadow: 0 2px 6px rgba(0,0,0,0.02); }
.g-acc { background: #F4FAF6; border: 1px solid #B0D4BE; border-top: 3.5px solid #0D2818; border-radius: 8px; padding: 14px 16px; height: 100%; box-shadow: 0 2px 8px rgba(13, 40, 24, 0.04); }
.s-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px dashed #E2ECE5; font-size: 0.92rem; color: #333333; }
.s-val { font-weight: 700; color: #0D2818; }
.user-card { background: #F4FAF6; border: 1px solid #D5EBDD; border-left: 4px solid #164E33; padding: 12px; border-radius: 6px; margin-bottom: 12px; font-size: 0.9rem; color: #1A3024; }
</style>""", unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user"] = ""

# --- LOGIN ---
if not st.session_state["authenticated"]:
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("""
        <div class="login-box">
            <div style="text-align: center; margin-bottom: 1.2rem;">
                <h2 style="color: #0D2818; margin: 0; font-weight: 800;">🌿 ALPINE HERBS</h2>
                <div style="color: #2D7D52; font-size: 0.86rem; font-weight: 700; margin-top: 2px;">FIELD OPERATIONS PORTAL</div>
                <div style="color: #738C7D; font-size: 0.78rem; margin-top: 3px;">Birgunj, Nepal | Sign In to Begin Daily Closing</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            u = st.text_input("Username", placeholder="e.g. Alpine")
            p = st.text_input("Password", type="password", placeholder="••••••••")
            st.write("")
            submit_btn = st.form_submit_button("🔑 Sign In to Portal", type="primary", use_container_width=True)

            if submit_btn:
                if u.strip() in USERS and USERS[u.strip()] == p.strip():
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = u.strip()
                    st.rerun()
                else:
                    st.error("❌ Invalid Username or Password.")

        st.caption("ℹ️ Accounts: `Alpine` / `Pritam` / `Admin` | Head Office: Birgunj")
    st.stop()

cur_user = st.session_state.get("user", "Staff")

if "rep_no" not in st.session_state:
    st.session_state["rep_no"] = f"ALP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

# --- SIDEBAR ---
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
    st.markdown("#### 📋 Client Dues Directory")
    sq = st.text_input("Search Chemist / Town / Code", placeholder="Type name or town...").strip().lower()
    matches = [c for c in st.session_state["client_db"] if sq in c['name'].lower() or sq in c['area'].lower() or sq in c['code'].lower()] if sq else st.session_state["client_db"]
    for item in matches[:5]:
        phone_txt = f" | 📞 {item['phone']}" if item.get('phone') else ""
        st.markdown(f"**{item['name']}** (`{item['code']}`)\n📍 {item['area']}{phone_txt}\n💰 Dues: **Rs. {item['dues']:,}**")
        st.write("---")

INIT_SALES = pd.DataFrame({
    "Invoice No.": ["INV-01", "INV-02", "INV-03"],
    "Client Name": ["", "", ""],
    "Address": ["Birgunj", "Birgunj", "Birgunj"],
    "Product Name": ["", "", ""],
    "Qty": [0.0, 0.0, 0.0],
    "FOC Qty": [0.0, 0.0, 0.0],
    "Rate (Rs.)": [0.0, 0.0, 0.0],
    "Cash Recd (Rs.)": [0.0, 0.0, 0.0],
    "Credit Given (Rs.)": [0.0, 0.0, 0.0]
})

INIT_COLLECTIONS = pd.DataFrame({
    "Receipt No.": ["REC-01", "REC-02"],
    "Client Name": ["", ""],
    "Payment Mode": ["Cash", "Cash"],
    "Amount Collected (Rs.)": [0.0, 0.0],
    "Remarks / Ref": ["Old Dues Collection", "Old Dues Collection"]
})

INIT_RETURNS = pd.DataFrame({
    "Client Name": [""],
    "Product Name": [""],
    "Return Qty": [0.0],
    "Rate (Rs.)": [0.0],
    "Total Return (Rs.)": [0.0],
    "Reason": ["Near Expiry / Breakage"]
})

INIT_OFFICE = pd.DataFrame({
    "Details": [""],
    "Paid To": ["Vendor"],
    "Mode": ["Cash"],
    "Amount (Rs.)": [0.0],
    "Remarks": [""]
})

INIT_STAFF = pd.DataFrame({
    "Staff Name": [""],
    "Purpose": ["Tour Advance"],
    "Category": ["Staff Advance"],
    "Amount (Rs.)": [0.0],
    "Remarks": [""]
})

st.markdown("""
<div class="main-header-banner">
    <div style="font-size: 1.55rem; font-weight: 800; color: #FFFFFF;">🌿 ALPINE HERBS PVT. LTD.</div>
    <div style="font-size: 0.85rem; color: #D5EBDD; font-weight: 500; margin-top: 2px;">BIRGUNJ, NEPAL &nbsp;|&nbsp; DAILY FIELD CLOSING & AUDIT REPORT</div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns([1.1, 1.1, 1.3, 1.3, 1.1])
with c1:
    rep_date = st.date_input("Date (A.D.)", value=date.today())
with c2:
    bs_miti = get_nepali_miti(rep_date)
    st.text_input("Nepali Miti (B.S.)", value=bs_miti, disabled=True)
with c3:
    mr_name = st.text_input("MR Name", value=cur_user if cur_user != "Alpine" else "Pritam Gupta")
with c4:
    unique_areas = sorted(list(set([c["area"] for c in st.session_state["client_db"] if c.get("area")])))
    selected_area = st.selectbox("Route / Territory", ["All Territories (A-Z)"] + unique_areas)
with c5:
    st.text_input("Report Ref", value=st.session_state["rep_no"], disabled=True)

all_clients = sorted(st.session_state["client_db"], key=lambda x: x["name"].lower())
if selected_area != "All Territories (A-Z)":
    area_clients = [c for c in all_clients if c["area"].lower() == selected_area.lower()]
    other_clients = [c for c in all_clients if c["area"].lower() != selected_area.lower()]
    sorted_client_pool = area_clients + other_clients
else:
    sorted_client_pool = all_clients

CLIENT_OPTIONS = [""] + [
    f"{c['name']}  [{c['code']}] — 📍 {c['area']}" for c in sorted_client_pool
] + ["Other / Walk-in"]

client_col_config = {
    "Client Name": st.column_config.SelectboxColumn(
        "Client Name (Type ANY Initial A-Z)",
        help="Type any letter to find chemist. Code & area are auto-entered.",
        width="large",
        options=CLIENT_OPTIONS,
        required=False
    )
}

t1, t2, t3, t4 = st.tabs([
    "🛒 1. Sales & Collections",
    "🏢 2. Operating Expenses",
    "👥 3. Staff Advances & Imprest",
    "🔄 4. Goods Return (Clients)"
])

fid = st.session_state["form_id"]

with t1:
    st.markdown("##### 🛒 Sales Ledger (With FOC Bonus Tracking)")
    ed_s = st.data_editor(INIT_SALES, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"ed_s_{fid}", column_config=client_col_config)
    st.write("")
    st.markdown("##### 💵 Dedicated Cash Collections & Payment Receipts")
    ed_c = st.data_editor(INIT_COLLECTIONS, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"ed_c_{fid}", column_config=client_col_config)

with t2:
    ed_o = st.data_editor(INIT_OFFICE, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"ed_o_{fid}")

with t3:
    ed_st = st.data_editor(INIT_STAFF, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"ed_st_{fid}")

with t4:
    ed_r = st.data_editor(INIT_RETURNS, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"ed_r_{fid}", column_config=client_col_config)

# Math & Calculations
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

st.markdown("### 📊 Financial Closing Summary")
sb1, sb2, sb3 = st.columns(3)
with sb1:
    st.markdown(f"""<div class="g-box"><b>🛒 1. Revenue & Collections</b>
    <div class="s-row"><span>Total Sales Billed:</span><span class="s-val">{money(tot_sales)}</span></div>
    <div class="s-row"><span>Total Cash Collected:</span><span class="s-val" style="color:#164E33;">{money(total_gross_cash)}</span></div>
    <div class="s-row"><span>Credit Given:</span><span class="s-val" style="color:#A04000;">{money(tot_credit)}</span></div></div>""", unsafe_allow_html=True)
with sb2:
    st.markdown(f"""<div class="g-box"><b>🏢 2. Route Disbursements</b>
    <div class="s-row"><span>Operating Expenses:</span><span class="s-val">{money(tot_exp)}</span></div>
    <div class="s-row"><span>Staff Advances:</span><span class="s-val">{money(tot_adv)}</span></div>
    <div class="s-row"><span>Total Outflow:</span><span class="s-val" style="color:#800000;">{money(tot_disbursed)}</span></div></div>""", unsafe_allow_html=True)
with sb3:
    col_net = "#0D2818" if net_cash >= 0 else "#900C3F"
    st.markdown(f"""<div class="g-acc"><b>💰 3. Final Cash Settlement</b>
    <div class="s-row"><span>Total Cash Collected:</span><span class="s-val">{money(total_gross_cash)}</span></div>
    <div class="s-row"><span>Less Total Outflow:</span><span class="s-val">- {money(tot_disbursed)}</span></div>
    <div style="margin-top:8px; display:flex; justify-content:space-between; align-items:center;">
    <span style="font-weight:800;">NET CASH IN HAND:</span><span style="font-weight:800; font-size:1.3rem; color:{col_net};">{money(net_cash)}</span></div></div>""", unsafe_allow_html=True)

# Google Sheets Sync
def sync_to_sheets():
    s_items = []
    for _, r in ed_s.iterrows():
        raw_client = r.get("Client Name")
        cname, ccode, carea = resolve_client(raw_client, clean_str(r.get("Address"), "Birgunj"))
        pname = clean_str(r.get("Product Name"))
        q, f_q, rt = clean_num(r.get("Qty")), clean_num(r.get("FOC Qty")), clean_num(r.get("Rate (Rs.)"))
        c, cm = clean_num(r.get("Cash Recd (Rs.)")), clean_num(r.get("Credit Given (Rs.)"))
        tb = q * rt; cb = cm if cm > 0 else max(0.0, tb - c)
        if tb == 0 and (c > 0 or cb > 0): tb = c + cb
        if cname or pname or q > 0 or f_q > 0 or c > 0 or cb > 0:
            s_items.append({
                "invoice": clean_str(r.get("Invoice No."), "INV-01"),
                "client_name": cname or "Walk-in Party",
                "client_code": ccode, "address": carea,
                "product_name": pname or "General Stock",
                "qty": q, "foc_qty": f_q, "rate": rt,
                "cash_collected": c, "credit_given": cb, "total_sale": tb
            })

    c_items = []
    for _, r in ed_c.iterrows():
        raw_client = r.get("Client Name")
        cname, ccode, _ = resolve_client(raw_client)
        rec = clean_str(r.get("Receipt No."), "REC-01")
        amt = clean_num(r.get("Amount Collected (Rs.)"))
        if cname or amt > 0:
            c_items.append({
                "receipt_no": rec, "client_name": cname or "Chemist",
                "client_code": ccode, "mode": clean_str(r.get("Payment Mode"), "Cash"),
                "amount": amt, "remarks": clean_str(r.get("Remarks / Ref"), "Old Dues")
            })

    r_items = []
    for _, r in ed_r.iterrows():
        raw_client = r.get("Client Name")
        cname, ccode, _ = resolve_client(raw_client)
        pname = clean_str(r.get("Product Name"))
        rq, r_rt = clean_num(r.get("Return Qty")), clean_num(r.get("Rate (Rs.)"))
        if cname or pname or rq > 0:
            r_items.append({
                "client_name": cname or "Chemist", "client_code": ccode,
                "product_name": pname or "Returned Item", "qty": rq, "rate": r_rt,
                "total": rq * r_rt, "reason": clean_str(r.get("Reason"), "Expiry")
            })

    e_items = []
    for _, r in ed_o.iterrows():
        amt, det = clean_num(r.get("Amount (Rs.)")), clean_str(r.get("Details"))
        if amt > 0 or det:
            e_items.append({
                "details": det or "Route Expense", "paid_to": clean_str(r.get("Paid To"), "Vendor"),
                "mode": clean_str(r.get("Mode"), "Cash"), "amount": amt, "remarks": clean_str(r.get("Remarks"))
            })

    a_items = []
    for _, r in ed_st.iterrows():
        amt, staff = clean_num(r.get("Amount (Rs.)")), clean_str(r.get("Staff Name"))
        if amt > 0 or staff:
            a_items.append({
                "personnel_name": staff or "Staff", "purpose": clean_str(r.get("Purpose"), "Tour Advance"),
                "type": clean_str(r.get("Category"), "Staff Advance"), "amount": amt, "remarks": clean_str(r.get("Remarks"))
            })

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
        data = res.json()
        if data.get("status") == "success":
            st.session_state["sync_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return True, data.get("records_synced", len(s_items) + len(c_items) + len(r_items) + len(e_items) + len(a_items))
        else:
            st.error(f"❌ Google Script Error: {data.get('message')}")
            return False, 0
    except Exception as err:
        st.error(f"❌ Sync Connection Error: {err}")
        return False, 0

b1, b2 = st.columns([3, 1])
with b1:
    if st.button("🚀 CONFIRM & SYNC REPORT TO MASTER", type="primary", use_container_width=True):
        with st.spinner("Syncing to Master Ledger..."):
            ok, count = sync_to_sheets()
            if ok:
                st.balloons()
                st.success(f"✅ Report `{st.session_state['rep_no']}` synchronized successfully! ({count} records written to Google Sheets)")
with b2:
    if st.button("🔄 Reset / Start Blank", use_container_width=True):
        st.session_state["rep_no"] = f"ALP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        st.session_state["form_id"] += 1
        st.rerun()
