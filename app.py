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
SHEET_ID = "1cpPYFS9EkajB5tGfMnReIJ71cmB5djz6oaMvvEoqs6A"

USERS = {
    "Alpine": "AHP@123",
    "Pritam": "Pritam@2024",
    "Admin": "AlpineAdmin@123",
    "Manager": "Alpine@Birgunj"
}

# --- SYNTAX-SAFE A-TO-Z CLIENT DIRECTORY ---
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
Gadi Mai Medical Hall,PAR-011,Pachgawa,Parsa,,0
Gudi Pharmacy,BAR-028,Bariyarpur,Bara,,0
Gupta Medical Store,BAR-016,Kalaiya,Bara,,7800
Hariom Medical,BAR-005,Kolvi,Bara,9811229323,2300
Harnaiya Aashirvad Medical,PAR-013,Harnaiya,Parsa,,4565
Himal Health Clinic,PAR-017,Naukatola,Parsa,,4100
Hargendra Pande Medical,BAR-021,Rautahar,Bara,,500
Harnaiya City Hospital,PAR-041,Harnaiya,Parsa,,0
Ideal Pharmacy,PAR-018,Birgunj,Parsa,,6900
Janta Medical Hall,BAR-019,Jeetpur,Bara,,8300
Jeevan Raksha Clinic,PAR-020,Birgunj,Parsa,,12800
Jitendra Health Clinic,PAR-031,Mahuwan,Parsa,,4565
Jungbahadur Medical,BAR-022,Bagrampur,Bara,,200
Kalaiya Medical Centre,BAR-021,Kalaiya,Bara,,9400
Kaliyani Medical Hall,BAR-012,Kolvi,Bara,,15580
Kohinoor Medical Hall,PAR-017,Milan Chouk,Parsa,,0
Krishna Pharmacy,PAR-022,Langada Chouk,Parsa,,14100
Laxmi Medical Store,PAR-023,Birgunj,Parsa,,18500
Mahir Health Clinic,BAR-002,Jeetpur,Bara,9807100296,8165
Madhav Medical Hall,PAR-014,Pachgawa,Parsa,,0
Naresh Medical,BAR-001,Kalaiya,Bara,9807267001,3100
Nimash Medical,BAR-016,Simara,Bara,9845120836,4620
Nirajan Pharmacy,BAR-004,Bakuliya,Bara,9804242586,550
Nawal Kishor Medical Hall,PAR-015,Pachgawa,Parsa,,0
Nausad Medical Hall,PAR-016,Rangapur,Parsa,,0
Noor Tamana Health Clinic,PAR-019,Derbana,Parsa,,0
OM Shivsakti Pharmacy,BAR-029,Kalaiya,Bara,,3680
Om Sai Medical,PAR-026,Birgunj,Parsa,,5600
Prithvi Medical Hall,BAR-018,Jaitapur,Bara,,6745
Pandey Medical Hall,PAR-005,Badanihar,Parsa,,7065
Pandey Medical Hall (Murli),PAR-021,Murli,Parsa,,700
Puja Medical Hall,PAR-022,Fatepur,Parsa,,1030
Pushpa Medical Hall,PAR-038,Kathariya,Parsa,,105
Quality Health Pharma,PAR-029,Birgunj,Parsa,,11300
Roshan Pharmacy,PAR-025,Birgunj,Parsa,,74290
Rupa Medical Hall,BAR-008,Simara,Bara,,5515
Roman Surgical,BAR-015,Khopawa,Bara,9821231370,1660
Raina Health Clinic,PAR-023,Veda Tol,Parsa,,3672
Rihansh Medical Hall,PAR-024,Birgunj,Parsa,,1740
Sandip Medical Hall,PAR-027,Langada Chouk,Parsa,,30195
Sanjeevani Clinic,BAR-009,Simara,Bara,9845130209,2195
Sudama Surgical,PAR-003,Neutan,Parsa,,20200
S.K.S Pharma,BAR-006,Parsauni,Bara,,1175
Shohalal Medical Hall,BAR-013,Ganj Bhawanipur,Bara,9814286651,7175
Sanniya Medical Hall,BAR-025,Jeetpur,Bara,,3460
Sapna Health Clinic,BAR-027,Bariyarpur,Bara,,1365
Samir Medical Hall,PAR-026,Pachgawa,Parsa,,0
Sohil Medical Hall,PAR-028,Pokhariya,Parsa,,11600
Shahu Pharmacy,PAR-035,Dokaila,Parsa,,0
Satiya Health Clinic,PAR-039,Lautan,Parsa,,0
Safe Life Hospital,BAR-019,Benauli,Bara,,740
Tarai Medical Hall,PAR-029,Manwa Bazar,Parsa,,235
Tarkeshwar Medical Hall,PAR-030,Nagwa,Parsa,,8885
Tirupati Medical Hall,PAR-037,Naukatola,Parsa,,6400
Universal Health Clinic,PAR-038,Birgunj,Parsa,,15700
Verma Medical Store,BAR-039,Jeetpur,Bara,,9100
Welfare Pharmacy,PAR-040,Birgunj,Parsa,,4600
Yadav Medical Hall,BAR-041,Kalaiya,Bara,,11200
Zenith Health Care,PAR-042,Birgunj,Parsa,,7300"""

if "client_db" not in st.session_state:
    st.session_state["client_db"] = pd.read_csv(io.StringIO(CLIENTS_DATA.strip()), dtype=str).fillna("").to_dict("records")
    for c in st.session_state["client_db"]:
        try: c["dues"] = float(c["dues"]) if c["dues"] != "" else 0.0
        except: c["dues"] = 0.0

if "form_id" not in st.session_state:
    st.session_state["form_id"] = 0

# --- UTILITIES ---
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

# --- 1. GUARANTEED WORKING LOGIN SCREEN ---
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
                    st.error("❌ Invalid Username or Password. (Default: Alpine / AHP@123)")

        st.caption("ℹ️ Accounts: `Alpine` / `Pritam` / `Admin` | Head Office: Birgunj")
    st.stop()

# --- AUTHENTICATED USER SESSION ---
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
    sq = st.text_input("Search Chemist / Town / Code", placeholder="Type name, town or code...").strip().lower()
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
    {"Rec
