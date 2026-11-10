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
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyxbrlC6Ayn-ShWWBLGXGNBd9wnqc3m4lXRyfE6U6Fsbtnbea5R3_JBvq0ggKitR5pD/exec"

USERS = {
    "Alpine": "AHP@123",
    "Pritam": "Pritam@2024",
    "Admin": "AlpineAdmin@123",
    "Manager": "Alpine@Birgunj"
}

# --- SYNTAX-SAFE CLIENT DIRECTORY (BARA & PARSA) ---
CLIENTS_DATA = """name,code,area,district,phone,dues
Naresh Medical,BAR-001,Kalaiya,Bara,9807267001,3100
Mahir Health Clinic,BAR-002,Jeetpur,Bara,9807100296,8165
Dev Medical,BAR-003,Kalaiya,Bara,9845227985,1500
Nirajan Pharmacy,BAR-004,Bakuliya,Bara,9804242586,550
Hariom Medical,BAR-005,Kolvi,Bara,9811229323,2300
S.K.S Pharma,BAR-006,Parsauni,Bara,,1175
Aayan First Aid Center,BAR-007,Simara,Bara,,2060
Rupa Medical Hall,BAR-008,Simara,Bara,,5515
Sanjeevani Clinic,BAR-009,Simara,Bara,9845130209,2195
Ale Health Clinic,BAR-010,Ganj Bhawanipur,Bara,,1645
Alex Medical Hall,BAR-011,Bagrampur,Bara,,18000
Kaliyani Medical Hall,BAR-012,Kolvi,Bara,,15580
Shohalal Medical Hall,BAR-013,Ganj Bhawanipur,Bara,9814286651,7175
Everest Health Clinic,BAR-014,Kalaiya,Bara,,2635
Roman Surgical,BAR-015,Khopawa,Bara,9821231370,1660
Nimash Medical,BAR-016,Simara,Bara,9845120836,4620
Advance Poli Clinic,BAR-017,Raghunathpur,Bara,9809153231,4310
Prithvi Medical Hall,BAR-018,Jaitapur,Bara,,6745
Safe Life Hospital,BAR-019,Benauli,Bara,,740
Alina Health Clinic,BAR-020,Kalaiya,Bara,,8250
Hargendra Pande Medical,BAR-021,Rautahar,Bara,,500
Jungbahadur Medical,BAR-022,Bagrampur,Bara,,200
Aarabh Pharmacy,BAR-023,Nijgadh,Bara,9855019764,36725
Aarabh Pharmacy (Narayani),BAR-024,Nijgadh,Bara,9855019764,25915
Sanniya Medical Hall,BAR-025,Jeetpur,Bara,,3460
Bala Ji Medical Hall,BAR-026,Aarnawa Chouk,Bara,,3195
Sapna Health Clinic,BAR-027,Bariyarpur,Bara,,1365
Gudi Pharmacy,BAR-028,Bariyarpur,Bara,,0
OM Shivsakti Pharmacy,BAR-029,Kalaiya,Bara,,3680
Aditi Pharmacy,PAR-001,Manwa Bazar,Parsa,,500
Ashok Medical Hall,PAR-002,Naukatola,Parsa,,12230
Sudama Surgical,PAR-003,Neutan,Parsa,,20200
B.S Health Clinic,PAR-004,Paterwa,Parsa,,24665
Pandey Medical Hall,PAR-005,Badanihar,Parsa,,7065
Bhawani Medical Hall,PAR-006,Bharatwa,Parsa,,9950
Chandip Medical Hall,PAR-007,Kathmandu Tol,Parsa,,0
Dinamik Pharma,PAR-008,Sano Sugauli,Parsa,,15815
Everest Pharmacy,PAR-009,Birwa Chouk,Parsa,,0
Fatepur Health Clinic,PAR-010,Fatepur,Parsa,,0
Gadi Mai Medical Hall,PAR-011,Pachgawa,Parsa,,0
Ganesh Srestha,PAR-012,Birgunj,Parsa,,63390
Harnaiya Aashirvad Medical,PAR-013,Harnaiya,Parsa,,4565
Madhav Medical Hall,PAR-014,Pachgawa,Parsa,,0
Nawal Kishor Medical Hall,PAR-015,Pachgawa,Parsa,,0
Nausad Medical Hall,PAR-016,Rangapur,Parsa,,0
Kohinoor Medical Hall,PAR-017,Milan Chouk,Parsa,,0
Sibil Medical Hall,PAR-018,Milan Chouk,Parsa,,0
Noor Tamana Health Clinic,PAR-019,Derbana,Parsa,,0
Aftab Medical Hall,PAR-020,Derbana,Parsa,,0
Pandey Medical Hall (Murli),PAR-021,Murli,Parsa,,700
Puja Medical Hall,PAR-022,Fatepur,Parsa,,1030
Raina Health Clinic,PAR-023,Veda Tol,Parsa,,3672
Rihansh Medical Hall,PAR-024,Birgunj,Parsa,,1740
Roshan Pharmacy,PAR-025,Birgunj,Parsa,,74290
Samir Medical Hall,PAR-026,Pachgawa,Parsa,,0
Sandip Medical Hall,PAR-027,Langada Chouk,Parsa,,30195
Sohil Medical Hall,PAR-028,Pokhariya,Parsa,,11600
Tarai Medical Hall,PAR-029,Manwa Bazar,Parsa,,235
Tarkeshwar Medical Hall,PAR-030,Nagwa,Parsa,,8885
Jitendra Health Clinic,PAR-031,Mahuwan,Parsa,,4565
Anshari Medical Hall,PAR-032,Derbana,Parsa,,0
Jay Shree Gadhi Mai Medical,PAR-033,Lautan,Parsa,,1575
Dinanath Medical Hall,PAR-034,Harpur,Parsa,,1740
Shahu Pharmacy,PAR-035,Dokaila,Parsa,,0
G.K.S Pharmacy,PAR-036,Narahi Bazar,Parsa,,0
Bagmorcha Mai Medical,PAR-037,Bagmorcha,Parsa,,0
Pushpa Medical Hall,PAR-038,Kathariya,Parsa,,105
Satiya Health Clinic,PAR-039,Lautan,Parsa,,0
Anil Medical Hall,PAR-040,Gadwal,Parsa,,0
Harnaiya City Hospital,PAR-041,Harnaiya,Parsa,,0"""

if "client_db" not in st.session_state:
    st.session_state["client_db"] = pd.read_csv(io.StringIO(CLIENTS_DATA.strip()), dtype=str).fillna("").to_dict("records")
    for c in st.session_state["client_db"]:
        try: c["dues"] = float(c["dues"]) if c["dues"] != "" else 0.0
        except: c["dues"] = 0.0

if "form_id" not in st.session_state:
    st.session_state["form_id"] = 0

# --- HELPERS ---
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
.block-container { padding-top: 2.2rem !important; padding-bottom: 3rem !important; max-width: 1540px; }
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
.main-header-title { font-size: 1.65rem; font-weight: 800; letter-spacing: 0.5px; color: #FFFFFF; line-height: 1.2; }
.main-header-sub { font-size: 0.85rem; color: #D5EBDD; font-weight: 500; margin-top: 3px; }
.g-box { background: #FFFFFF; border: 1px solid #C8DCCF; border-top: 3.5px solid #2D7D52; border-radius: 8px; padding: 14px 16px; height: 100%; box-shadow: 0 2px 6px rgba(0,0,0,0.02); }
.g-acc { background: #F4FAF6; border: 1px solid #B0D4BE; border-top: 3.5px solid #0D2818; border-radius: 8px; padding: 14px 16px; height: 100%; box-shadow: 0 2px 8px rgba(13, 40, 24, 0.04); }
.s-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px dashed #E2ECE5; font-size: 0.92rem; color: #333333; }
.s-val { font-weight: 700; color: #0D2818; }
.user-card { background: #F4FAF6; border: 1px solid #D5EBDD; border-left: 4px solid #164E33; padding: 12px; border-radius: 6px; margin-bottom: 12px; font-size: 0.9rem; color: #1A3024; }
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
    st.markdown("#### 📋 Client Dues Lookup")
    sq = st.text_input("Search Chemist / Town", placeholder="Type name or town...").strip().lower()
    matches = [c for c in st.session_state["client_db"] if sq in c['name'].lower() or sq in c['area'].lower() or sq in c['code'].lower()] if sq else st.session_state["client_db"]
    for item in matches[:5]:
        phone_txt = f" | 📞 {item['phone']}" if item.get('phone') else ""
        st.markdown(f"**{item['name']}** (`{item['code']}`)\n📍 {item['area']}{phone_txt}\n💰 Dues: **Rs. {item['dues']:,}**")
        st.write("---")

    with st.expander("➕ Register New Chemist"):
        with st.form("new_chem_form", clear_on_submit=True):
            n_name = st.text_input("Chemist Name*")
            n_code = st.text_input("Code*", value=f"PAR-{len(st.session_state['client_db'])+10:03d}")
            n_area = st.text_input("Town / Area*", value="Birgunj")
            n_phone = st.text_input("Mobile No.")
            n_due  = st.number_input("Opening Due (Rs.)", min_value=0.0, value=0.0, step=500.0)
            if st.form_submit_button("Save Chemist"):
                if n_name.strip():
                    st.session_state["client_db"].append({
                        "name": n_name.strip(), "code": n_code.strip().upper(),
                        "area": n_area.strip(), "district": "Parsa",
                        "phone": n_phone.strip(), "dues": n_due
                    })
                    st.success(f"✅ Registered {n_name} ({n_code})")
                    st.rerun()

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

# Main Header Banner
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
    unique_areas = sorted(list(set([c["area"] for c in st.session_state["client_db"] if c.get("area")])))
    selected_area = st.selectbox("Route / Territory", ["All Territories (A-Z)"] + unique_areas)
with c5:
    st.text_input("Report Ref", value=st.session_state["rep_no"], disabled=True)

# Build Complete A-Z Client Recommendations
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
        help="Type any letter to find chemist. Code is auto-entered.",
        width="large",
        options=CLIENT_OPTIONS,
        required=False
    )
}

# Entry Tabs
t1, t2, t3, t4 = st.tabs([
    "🛒 1. Sales & Collections",
    "🏢 2. Operating Expenses",
    "👥 3. Staff Advances & Imprest",
    "🔄 4. Goods Return (Clients)"
])

fid = st.session_state["form_id"]

with t1:
    st.markdown("##### 🛒 Sales Ledger (With FOC Bonus Tracking)")
    st.caption("💡 Click on 'Client Name' and type any letter to select chemists. Codes are auto-entered.")
    ed_s = st.data_editor(
        INIT_SALES,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key=f"ed_s_{fid}",
        column_config=client_col_config
    )

    st.write("")
    st.markdown("##### 💵 Dedicated Cash Collections & Payment Receipts")
    st.caption("Record direct payments and dues recovered from clients with receipt numbers.")
    ed_c = st.data_editor(
        INIT_COLLECTIONS,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key=f"ed_c_{fid}",
        column_config=client_col_config
    )

with t2:
    st.caption("Record route fuel, food, logistics, and operational vendor costs.")
    ed_o = st.data_editor(INIT_OFFICE, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"ed_o_{fid}")

with t3:
    st.caption("Record daily allowances, per-diem, and tour advances given to personnel.")
    ed_st = st.data_editor(INIT_STAFF, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"ed_st_{fid}")

with t4:
    st.markdown("##### 🔄 Goods Return Ledger (Client Product Returns)")
    st.caption("Record stock returned by clients due to expiry, damage, or slow turnover.")
    ed_r = st.data_editor(
        INIT_RETURNS,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key=f"ed_r_{fid}",
        column_config=client_col_config
    )

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

# Corporate Financial Summary Cards
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
        raw_client = r.get("Client Name")
        cname, ccode, carea = resolve_client(raw_client, clean_str(r.get("Address"), "Birgunj"))
        pname = clean_str(r.get("Product Name"))
        q, f_q, rt = clean_num(r.get("Qty")), clean_num(r.get("FOC Qty")), clean_num(r.get("Rate (Rs.)"))
        c, cm = clean_num(r.get("Cash Recd (Rs.)")), clean_num(r.get("Credit Given (Rs.)"))
        tb = q * rt
        cb = cm if cm > 0 else max(0.0, tb - c)
        if tb == 0 and (c > 0 or cb > 0): tb = c + cb
        if cname or pname or q > 0 or f_q > 0 or c > 0 or cb > 0:
            s_items.append({
                "invoice": clean_str(r.get("Invoice No."), "INV-01"),
                "client_name": cname or "Walk-in Party",
                "client_code": ccode,
                "address": carea,
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
                "receipt_no": rec,
                "client_name": cname or "Chemist",
                "client_code": ccode,
                "mode": clean_str(r.get("Payment Mode"), "Cash"),
                "amount": amt,
                "remarks": clean_str(r.get("Remarks / Ref"), "Old Dues")
            })

    r_items = []
    for _, r in ed_r.iterrows():
        raw_client = r.get("Client Name")
        cname, ccode, _ = resolve_client(raw_client)
        pname = clean_str(r.get("Product Name"))
        rq, r_rt = clean_num(r.get("Return Qty")), clean_num(r.get("Rate (Rs.)"))
        if cname or pname or rq > 0:
            r_items.append({
                "client_name": cname or "Chemist",
                "client_code": ccode,
                "product_name": pname or "Returned Item",
                "qty": rq, "rate": r_rt, "total": rq * r_rt,
                "reason": clean_str(r.get("Reason"), "Expiry / Breakage")
            })

    e_items = []
    for _, r in ed_o.iterrows():
        amt, det = clean_num(r.get("Amount (Rs.)")), clean_str(r.get("Details"))
        if amt > 0 or det:
            e_items.append({
                "details": det or "Route Expense",
                "paid_to": clean_str(r.get("Paid To"), "Vendor"),
                "mode": clean_str(r.get("Mode"), "Cash"),
                "amount": amt,
                "remarks": clean_str(r.get("Remarks"))
            })

    a_items = []
    for _, r in ed_st.iterrows():
        amt, staff = clean_num(r.get("Amount (Rs.)")), clean_str(r.get("Staff Name"))
        if amt > 0 or staff:
            a_items.append({
                "personnel_name": staff or "Staff",
                "purpose": clean_str(r.get("Purpose"), "Tour Advance"),
                "type": clean_str(r.get("Category"), "Staff Advance"),
                "amount": amt,
                "remarks": clean_str(r.get("Remarks"))
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
        raw_text = res.text.strip()
        if "<!DOCTYPE html" in raw_text or "accounts.google.com" in raw_text:
            st.error("❌ Google Permission Error: Set 'Who has access' to 'Anyone' in Apps Script.")
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
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=10*mm, rightMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm)
    styles = getSampleStyleSheet()
    t_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#164E33")), 
        ('TEXTCOLOR', (0,0), (-1,0), colors.white), 
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey), 
        ('FONTSIZE', (0,0), (-1,-1), 8)
    ])

    story = [
        Paragraph("<b>ALPINE HERBS PVT. LTD. - DAILY FIELD CLOSING VOUCHER</b>", styles["Heading1"]),
        Paragraph(f"<b>Ref:</b> {st.session_state['rep_no']} | <b>Date:</b> {rep_date} ({bs_miti}) | <b>MR:</b> {mr_name} | <b>Route:</b> {selected_area}", styles["Normal"]),
        Spacer(1, 3*mm)
    ]
    
    # 1. Sales Table
    s_rows = [["Inv #", "Client Name [Code]", "Address", "Product", "Qty", "FOC", "Rate", "Cash Recd", "Credit", "Total"]]
    for _, r in ed_s.iterrows():
        cname, ccode, carea = resolve_client(r.get("Client Name"), clean_str(r.get("Address"), "Birgunj"))
        pname = clean_str(r.get("Product Name"))
        q, f_q, rt = clean_num(r.get("Qty")), clean_num(r.get("FOC Qty")), clean_num(r.get("Rate (Rs.)"))
        c, cm = clean_num(r.get("Cash Recd (Rs.)")), clean_num(r.get("Credit Given (Rs.)"))
        tb = q * rt; cb = cm if cm > 0 else max(0.0, tb - c)
        if tb == 0 and (c > 0 or cb > 0): tb = c + cb
        if cname or pname or q > 0 or f_q > 0 or c > 0 or cb > 0:
            display_client = f"{cname} [{ccode}]" if ccode and ccode != "WALK-IN" else cname
            s_rows.append([clean_str(r.get("Invoice No."), "INV-01"), display_client or "Walk-in Party", carea, pname or "General Stock", str(q), str(f_q), money(rt), money(c), money(cb), money(tb)])
    if len(s_rows) > 1:
        story.append(Paragraph("<b>1. Sales & Invoicing Ledger</b>", styles["Heading2"]))
        t_s = Table(s_rows, colWidths=[18*mm, 48*mm, 24*mm, 46*mm, 14*mm, 14*mm, 26*mm, 26*mm, 26*mm, 26*mm], style=t_style)
        story.extend([t_s, Spacer(1, 3*mm)])

    # 2. Cash Collections Table
    c_rows = [["Receipt #", "Client / Chemist [Code]", "Payment Mode", "Amount Collected", "Remarks / Ref"]]
    for _, r in ed_c.iterrows():
        cname, ccode, _ = resolve_client(r.get("Client Name"))
        amt = clean_num(r.get("Amount Collected (Rs.)"))
        if cname or amt > 0:
            display_client = f"{cname} [{ccode}]" if ccode and ccode != "WALK-IN" else cname
            c_rows.append([clean_str(r.get("Receipt No."), "REC-01"), display_client or "Chemist", clean_str(r.get("Payment Mode"), "Cash"), money(amt), clean_str(r.get("Remarks / Ref"))])
    if len(c_rows) > 1:
        story.append(Paragraph("<b>2. Cash Collections & Payment Receipts</b>", styles["Heading2"]))
        t_c = Table(c_rows, colWidths=[30*mm, 85*mm, 45*mm, 45*mm, 63*mm], style=t_style)
        story.extend([t_c, Spacer(1, 3*mm)])

    # 3. Goods Return Table
    r_rows = [["Client Name [Code]", "Product Name", "Return Qty", "Rate", "Total Value", "Reason / Batch"]]
    for _, r in ed_r.iterrows():
        cname, ccode, _ = resolve_client(r.get("Client Name"))
        pname = clean_str(r.get("Product Name"))
        rq, r_rt = clean_num(r.get("Return Qty")), clean_num(r.get("Rate (Rs.)"))
        if cname or pname or rq > 0:
            display_client = f"{cname} [{ccode}]" if ccode and ccode != "WALK-IN" else cname
            r_rows.append([display_client or "Chemist", pname or "Returned Item", str(rq), money(r_rt), money(rq * r_rt), clean_str(r.get("Reason"))])
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

    # 5. Staff Advances Table
    a_rows = [["Staff / Personnel", "Purpose / Type", "Amount", "Remarks"]]
    for _, r in ed_st.iterrows():
        amt, staff = clean_num(r.get("Amount (Rs.)")), clean_str(r.get("Staff Name"))
        if amt > 0 or staff:
            a_rows.append([staff or "Staff", f"{clean_str(r.get('Category'))} - {clean_str(r.get('Purpose'))}", money(amt), clean_str(r.get("Remarks"))])
    if len(a_rows) > 1:
        story.append(Paragraph("<b>5. Staff Advances & Imprest</b>", styles["Heading2"]))
        t_a = Table(a_rows, colWidths=[65*mm, 80*mm, 45*mm, 78*mm], style=t_style)
        story.extend([t_a, Spacer(1, 3*mm)])

    # 6. Grand Reconciliation Table
    story.append(Paragraph("<b>6. Grand Financial Settlement</b>", styles["Heading2"]))
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

# Form Controls
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
        st.session_state["form_id"] += 1
        st.session_state.pop("pdf", None)
        st.rerun()

if "pdf" in st.session_state:
    st.write("")
    st.download_button("⬇️ DOWNLOAD OFFICIAL SIGN-OFF PDF AUDIT VOUCHER", data=st.session_state["pdf"], file_name=f"{st.session_state['rep_no']}.pdf", mime="application/pdf", use_container_width=True)
