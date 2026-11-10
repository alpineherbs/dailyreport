import streamlit as st
import pandas as pd
import requests
import datetime
import io

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="ALPINE HERBS | Field Sales & Closing App (Repo A)",
    page_icon="🌿",
    layout="wide"
)

# SPREADSHEET ID & APPS SCRIPT WEBHOOK URL
SHEET_ID = "1cpPYFS9EkajB5tGfMnReIJ71cmB5djz6oaMvvEoqs6A"
WEBHOOK_URL = "YOUR_APPS_SCRIPT_WEBHOOK_URL_HERE"  # Replace with your deployed Google Apps Script Web App URL

# --- STYLING ---
st.markdown("""<style>
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1400px; }
.main-banner {
    background: linear-gradient(135deg, #0D2818 0%, #164E33 100%);
    padding: 14px 20px;
    border-radius: 8px;
    color: white;
    margin-bottom: 1.2rem;
}
.review-card {
    background: #FAFCFA;
    border: 1px solid #D1E5D8;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 1rem;
}
</style>""", unsafe_allow_html=True)

# --- USER CREDENTIALS MAPPING ---
USERS = {
    "Pritam Das": "pritam2026",
    "Manish Das": "manish2026",
    "Admin": "alpine2026"
}

# --- AUTHENTICATION STATE ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("""
    <div style="max-width: 400px; margin: 100px auto; padding: 30px; background: #FAFCFA; border: 1px solid #D1E5D8; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); text-align: center;">
        <h2 style="color: #0D2818; margin-bottom: 5px;">🌿 ALPINE HERBS</h2>
        <p style="color: #4A6354; font-size: 0.88rem; margin-bottom: 20px;">Field Operations Portal (Repo A)</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("🔒 Login", type="primary", use_container_width=True)
            
            if login_btn:
                if username in USERS and USERS[username] == password:
                    st.session_state["authenticated"] = True
                    st.session_state["staff_name"] = username
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
    st.stop()

# --- DYNAMIC CLIENT DIRECTORY LOADER (FROM GOOGLE SHEETS) ---
@st.cache_data(ttl=30)
def load_client_directory():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Clients"
    try:
        df = pd.read_csv(url, dtype=str)
        if not df.empty:
            df.columns = [str(c).strip().lower() for c in df.columns]
            df = df.fillna("")
            clients = df.to_dict("records")
            for c in clients:
                try: 
                    c["dues"] = float(c["dues"]) if c["dues"] != "" else 0.0
                except: 
                    c["dues"] = 0.0
            return clients
    except Exception:
        pass
    return []

if "client_db" not in st.session_state or not st.session_state["client_db"]:
    st.session_state["client_db"] = load_client_directory()

client_pool = st.session_state["client_db"]

# Header
st.markdown("""
<div class="main-banner">
    <h2 style="margin:0; font-size:1.5rem;">🌿 ALPINE HERBS PVT. LTD. — FIELD OPERATIONS</h2>
    <div style="font-size:0.85rem; color:#D3E6DA; margin-top:2px;">
        Daily Sales, Collections, & Closing Submission Portal (Repo A) &nbsp;|&nbsp; Birgunj, Nepal
    </div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR METADATA & LOGOUT ---
with st.sidebar:
    st.markdown("### 📋 Submission Details")
    staff_name = st.text_input("MR / Sales Executive Name", st.session_state.get("staff_name", "Pritam Das"))
    report_no = st.text_input("Report Reference / ID", f"REP-{datetime.date.today().strftime('%Y%m%d')}")
    date_ad = st.date_input("Date (AD)", datetime.date.today())
    bs_date = st.text_input("Nepali Miti (YYYY-MM-DD)", "2083-07-20")

    st.divider()
    if st.button("🔄 Refresh Client List from Sheet", use_container_width=True):
        st.cache_data.clear()
        st.session_state["client_db"] = load_client_directory()
        st.success("Client directory reloaded successfully!")
        st.rerun()

    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

# --- INITIALIZE TRANSACTION LISTS IN SESSION STATE ---
for key in ["sales_entries", "collection_entries", "return_entries", "expense_entries", "advance_entries"]:
    if key not in st.session_state:
        st.session_state[key] = []

def get_client_selectbox_options(pool):
    sorted_pool = sorted(pool, key=lambda x: x.get("name", "").lower())
    return [f"{c.get('name')}  [{c.get('code', 'N/A')}] — 📍 {c.get('area', 'Birgunj')}" for c in sorted_pool]

client_options = get_client_selectbox_options(client_pool)

# --- DEFINE TABS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    f"🛒 Sales ({len(st.session_state['sales_entries'])})",
    f"💵 Collections ({len(st.session_state['collection_entries'])})",
    f"🔄 Returns ({len(st.session_state['return_entries'])})",
    f"💸 Expenses ({len(st.session_state['expense_entries'])})",
    f"👤 Advances ({len(st.session_state['advance_entries'])})",
    "🚀 Review & Submit"
])

# --- TAB 1: MULTI-PRODUCT SALES ENTRY ---
with tab1:
    st.markdown("##### 🛒 Record Product Sale / Invoice (Multi-Product Supported)")
    with st.form("sales_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            sel_client_str = st.selectbox("Select Chemist / Client", client_options if client_options else ["No Clients Found [PAR-000]"])
            invoice_no = st.text_input("Invoice Number", f"INV-{datetime.datetime.now().strftime('%H%M%S')}")
        with col2:
            cash_collected = st.number_input("Cash Collected on Delivery (Rs.)", min_value=0.0, value=0.0, step=10.0)

        st.markdown("---")
        st.markdown("**Add Products to this Invoice:**")
        
        if "temp_cart" not in st.session_state:
            st.session_state["temp_cart"] = []

        col_p1, col_p2, col_p3, col_p4 = st.columns([2, 1, 1, 1])
        with col_p1:
            p_name = st.text_input("Product Name", key="cart_prod")
        with col_p2:
            p_qty = st.number_input("Qty", min_value=0.0, value=1.0, step=1.0, key="cart_qty")
        with col_p3:
            p_foc = st.number_input("FOC", min_value=0.0, value=0.0, step=1.0, key="cart_foc")
        with col_p4:
            p_rate = st.number_input("Rate (Rs.)", min_value=0.0, value=0.0, step=10.0, key="cart_rate")

        add_to_cart = st.form_submit_button("➕ Add Product Item to Invoice")
        if add_to_cart and p_name.strip():
            st.session_state["temp_cart"].append({
                "product_name": p_name.strip(),
                "qty": p_qty,
                "foc_qty": p_foc,
                "rate": p_rate,
                "total": p_qty * p_rate
            })
            st.success(f"Added {p_name} to current invoice cart!")

    if st.session_state["temp_cart"]:
        st.markdown("**Current Invoice Items:**")
        cart_df = pd.DataFrame(st.session_state["temp_cart"])
        st.dataframe(cart_df, use_container_width=True, hide_index=True)
        
        if st.button("🗑️ Clear Current Invoice Cart"):
            st.session_state["temp_cart"] = []
            st.rerun()

        if st.button("💾 Finalize & Save Invoice to Sales Entries", type="primary"):
            selected_str = sel_client_str.strip()
            if "[" in selected_str and "]" in selected_str:
                parts = selected_str.split("[")
                c_name = parts[0].strip()
                c_code = parts[1].replace("]", "").split("—")[0].strip()
            else:
                c_name = selected_str
                matched_c = next((c for c in client_pool if c["name"].lower() == c_name.lower()), {})
                c_code = matched_c.get("code", "PAR-000")

            tot_invoice_amt = sum(item["total"] for item in st.session_state["temp_cart"])
            credit_given = max(0.0, tot_invoice_amt - cash_collected)

            for item in st.session_state["temp_cart"]:
                st.session_state["sales_entries"].append({
                    "client_code": c_code,
                    "client_name": c_name,
                    "invoice": invoice_no,
                    "product_name": item["product_name"],
                    "qty": item["qty"],
                    "foc_qty": item["foc_qty"],
                    "rate": item["rate"],
                    "cash_collected": cash_collected / len(st.session_state["temp_cart"]),
                    "credit_given": credit_given / len(st.session_state["temp_cart"]),
                    "total_sale": item["total"]
                })
            
            st.session_state["temp_cart"] = []
            st.success(f"Invoice {invoice_no} saved successfully for {c_name} [{c_code}]!")
            st.rerun()

    if st.session_state["sales_entries"]:
        st.markdown("---")
        st.markdown("##### 📋 Recorded Sales Entries for Today")
        st.dataframe(pd.DataFrame(st.session_state["sales_entries"]), use_container_width=True, hide_index=True)
        if st.button("🗑️ Clear All Sales Entries"):
            st.session_state["sales_entries"] = []
            st.rerun()

# --- TAB 2: COLLECTIONS ---
with tab2:
    st.markdown("##### 💵 Record Dues Collection / Payment Receipt")
    with st.form("col_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            sel_client_col = st.selectbox("Select Chemist / Client", client_options if client_options else ["No Clients Found [PAR-000]"], key="col_cli")
            receipt_no = st.text_input("Receipt / Ref No.", f"REC-{datetime.datetime.now().strftime('%H%M%S')}")
        with col2:
            amount = st.number_input("Amount Collected (Rs.)", min_value=0.0, value=0.0, step=100.0)
            mode = st.selectbox("Payment Mode", ["Cash", "Bank Transfer / QR", "Cheque"])
            remarks = st.text_input("Remarks / Notes", "Old Dues Clearance")
        
        if st.form_submit_button("➕ Add Collection Entry", type="primary"):
            selected_str = sel_client_col.strip()
            if "[" in selected_str and "]" in selected_str:
                parts = selected_str.split("[")
                c_name = parts[0].strip()
                c_code = parts[1].replace("]", "").split("—")[0].strip()
            else:
                c_name = selected_str
                matched_c = next((c for c in client_pool if c["name"].lower() == c_name.lower()), {})
                c_code = matched_c.get("code", "PAR-000")

            st.session_state["collection_entries"].append({
                "client_code": c_code,
                "client_name": c_name,
                "receipt_no": receipt_no,
                "amount": amount,
                "mode": mode,
                "remarks": remarks
            })
            st.success(f"Added collection of Rs. {amount:,.2f} from {c_name} [{c_code}]!")

    if st.session_state["collection_entries"]:
        st.markdown("---")
        st.dataframe(pd.DataFrame(st.session_state["collection_entries"]), use_container_width=True, hide_index=True)
        if st.button("🗑️ Clear Collection Entries"):
            st.session_state["collection_entries"] = []
            st.rerun()

# --- TAB 3: RETURNS ---
with tab3:
    st.markdown("##### 🔄 Record Goods Return / Damage / Expiry")
    with st.form("ret_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            sel_client_ret = st.selectbox("Select Chemist / Client", client_options if client_options else ["No Clients Found [PAR-0
