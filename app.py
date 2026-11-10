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
WEBHOOK_URL = "YOUR_APPS_SCRIPT_WEBHOOK_URL_HERE"  # Replace with your deployed Apps Script URL

# --- STYLING ---
st.markdown("""<style>
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px; }
.main-banner {
    background: linear-gradient(135deg, #0D2818 0%, #164E33 100%);
    padding: 16px 20px;
    border-radius: 8px;
    color: white;
    margin-bottom: 1.2rem;
}
</style>""", unsafe_allow_html=True)

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

# Initialize Session State for Dynamic Client Database
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

# --- SIDEBAR METADATA ---
with st.sidebar:
    st.markdown("### 📋 Submission Details")
    staff_name = st.text_input("MR / Sales Executive Name", "Pritam Das")
    report_no = st.text_input("Report Reference / ID", f"REP-{datetime.date.today().strftime('%Y%m%d')}")
    date_ad = st.date_input("Date (AD)", datetime.date.today())
    bs_date = st.text_input("Nepali Miti (YYYY-MM-DD)", "2083-07-20")

    st.divider()
    if st.button("🔄 Refresh Client List from Sheet", use_container_width=True):
        st.cache_data.clear()
        st.session_state["client_db"] = load_client_directory()
        st.success("Client directory reloaded successfully!")
        st.rerun()

# --- INITIALIZE TRANSACTION LISTS IN SESSION STATE ---
for key in ["sales_entries", "collection_entries", "return_entries", "expense_entries", "advance_entries"]:
    if key not in st.session_state:
        st.session_state[key] = []

# Helper for Client Selection Dropdown
def get_client_selectbox_options(pool):
    sorted_pool = sorted(pool, key=lambda x: x.get("name", "").lower())
    return [f"{c.get('name')}  [{c.get('code', 'N/A')}] — 📍 {c.get('area', 'Birgunj')}" for c in sorted_pool]

client_options = get_client_selectbox_options(client_pool)

# --- DEFINE TABS FIRST ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    f"🛒 Sales ({len(st.session_state['sales_entries'])})",
    f"💵 Collections ({len(st.session_state['collection_entries'])})",
    f"🔄 Returns ({len(st.session_state['return_entries'])})",
    f"💸 Expenses ({len(st.session_state['expense_entries'])})",
    f"👤 Advances ({len(st.session_state['advance_entries'])})",
    "🚀 Review & Submit"
])

# --- TAB 1: SALES ENTRY ---
with tab1:
    st.markdown("##### 🛒 Record Product Sale / Invoice")
    with st.form("sales_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            sel_client_str = st.selectbox("Select Chemist / Client", client_options if client_options else ["No Clients Found [PAR-000]"])
            invoice_no = st.text_input("Invoice Number", f"INV-{datetime.datetime.now().strftime('%H%M%S')}")
            product_name = st.text_input("Product Name (e.g., ProtoZem Capsule / Turmeric)")
        with col2:
            qty = st.number_input("Quantity", min_value=1.0, value=1.0, step=1.0)
            rate = st.number_input("Rate per Unit (Rs.)", min_value=0.0, value=0.0, step=10.0)
            cash_collected = st.number_input("Cash Collected on Delivery (Rs.)", min_value=0.0, value=0.0, step=10.0)
        
        submitted = st.form_submit_button("➕ Add Sale Entry", type="primary")
        if submitted:
            selected_str = sel_client_str.strip()
            if "[" in selected_str and "]" in selected_str:
                parts = selected_str.split("[")
                c_name = parts[0].strip()
                c_code = parts[1].replace("]", "").split("—")[0].strip()
            else:
                c_name = selected_str
                matched_c = next((c for c in client_pool if c["name"].lower() == c_name.lower()), {})
                c_code = matched_c.get("code", "PAR-000")

            tot_sale = qty * rate
            credit_given = max(0.0, tot_sale - cash_collected)

            st.session_state["sales_entries"].append({
                "client_code": c_code,
                "client_name": c_name,
                "invoice": invoice_no,
                "product_name": product_name,
                "qty": qty,
                "rate": rate,
                "cash_collected": cash_collected,
                "credit_given": credit_given,
                "total_sale": tot_sale
            })
            st.success(f"Added sale for {c_name} [{c_code}]!")

    if st.session_state["sales_entries"]:
        st.markdown("---")
        st.dataframe(pd.DataFrame(st.session_state["sales_entries"]), use_container_width=True, hide_index=True)
        if st.button("🗑️ Clear Sales Entries"):
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
            sel_client_ret = st.selectbox("Select Chemist / Client", client_options if client_options else ["No Clients Found [PAR-000]"], key="ret_cli")
            product_name = st.text_input("Returned Product Name", key="ret_prod")
        with col2:
            qty = st.number_input("Return Quantity", min_value=1.0, value=1.0, step=1.0, key="ret_qty")
            rate = st.number_input("Rate per Unit (Rs.)", min_value=0.0, value=0.0, step=10.0, key="ret_rate")
            reason = st.text_input("Reason for Return", "Expiry / Damage")

        if st.form_submit_button("➕ Add Return Entry", type="primary"):
            selected_str = sel_client_ret.strip()
            if "[" in selected_str and "]" in selected_str:
                parts = selected_str.split("[")
                c_name = parts[0].strip()
                c_code = parts[1].replace("]", "").split("—")[0].strip()
            else:
                c_name = selected_str
                matched_c = next((c for c in client_pool if c["name"].lower() == c_name.lower()), {})
                c_code = matched_c.get("code", "PAR-000")

            tot_ret = qty * rate
            st.session_state["return_entries"].append({
                "client_code": c_code,
                "client_name": c_name,
                "product_name": product_name,
                "qty": qty,
                "rate": rate,
                "total": tot_ret,
                "reason": reason
            })
            st.success(f"Added return entry for {c_name} [{c_code}]!")

    if st.session_state["return_entries"]:
        st.markdown("---")
        st.dataframe(pd.DataFrame(st.session_state["return_entries"]), use_container_width=True, hide_index=True)
        if st.button("🗑️ Clear Return Entries"):
            st.session_state["return_entries"] = []
            st.rerun()

# --- TAB 4: EXPENSES ---
with tab4:
    st.markdown("##### 💸 Field & Travel Expenses")
    with st.form("exp_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            paid_to = st.text_input("Paid To / Vendor", "Fuel Station / Hotel")
            details = st.text_input("Expense Particulars", "Motorcycle Petrol / Lunch")
        with col2:
            amount = st.number_input("Amount (Rs.)", min_value=0.0, value=0.0, step=50.0)
            remarks = st.text_input("Notes", "Field travel")

        if st.form_submit_button("➕ Add Expense", type="primary"):
            st.session_state["expense_entries"].append({
                "paid_to": paid_to, "details": details, "amount": amount, "remarks": remarks
            })
            st.success("Added expense entry!")

    if st.session_state["expense_entries"]:
        st.markdown("---")
        st.dataframe(pd.DataFrame(st.session_state["expense_entries"]), use_container_width=True, hide_index=True)
        if st.button("🗑️ Clear Expenses"):
            st.session_state["expense_entries"] = []
            st.rerun()

# --- TAB 5: STAFF ADVANCES ---
with tab5:
    st.markdown("##### 👤 Staff Advances & Adjustments")
    with st.form("adv_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            personnel_name = st.text_input("Staff Name", staff_name)
            purpose = st.text_input("Purpose", "Field cash advance")
        with col2:
            amount = st.number_input("Advance Amount (Rs.)", min_value=0.0, value=0.0, step=100.0)
            remarks = st.text_input("Advance Remarks", "Approved")

        if st.form_submit_button("➕ Add Advance Entry", type="primary"):
            st.session_state["advance_entries"].append({
                "personnel_name": personnel_name, "purpose": purpose, "amount": amount, "remarks": remarks
            })
            st.success("Added staff advance entry!")

    if st.session_state["advance_entries"]:
        st.markdown("---")
        st.dataframe(pd.DataFrame(st.session_state["advance_entries"]), use_container_width=True, hide_index=True)
        if st.button("🗑️ Clear Advances"):
            st.session_state["advance_entries"] = []
            st.rerun()

# --- TAB 6: REVIEW & SUBMIT ---
with tab6:
    st.markdown("##### 🚀 Final Review & Sync to Google Sheets")
    
    total_sales_amt = sum(s["total_sale"] for s in st.session_state["sales_entries"])
    total_col_amt = sum(c["amount"] for c in st.session_state["collection_entries"])
    total_ret_amt = sum(r["total"] for r in st.session_state["return_entries"])
    total_exp_amt = sum(e["amount"] for e in st.session_state["expense_entries"])
    total_adv_amt = sum(a["amount"] for a in st.session_state["advance_entries"])

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Sales", f"Rs. {total_sales_amt:,.2f}")
    c2.metric("Collections", f"Rs. {total_col_amt:,.2f}")
    c3.metric("Returns", f"Rs. {total_ret_amt:,.2f}")
    c4.metric("Expenses", f"Rs. {total_exp_amt:,.2f}")
    c5.metric("Advances", f"Rs. {total_adv_amt:,.2f}")

    st.write("")
    if st.button("🚀 Push Closing Payload to Google Sheets", type="primary", use_container_width=True):
        payload = {
            "date": str(date_ad),
            "bs_date": bs_date,
            "report_no": report_no,
            "staff_name": staff_name,
            "sales": st.session_state["sales_entries"],
            "collections": st.session_state["collection_entries"],
            "returns": st.session_state["return_entries"],
            "expenses": st.session_state["expense_entries"],
            "advances": st.session_state["advance_entries"]
        }

        with st.spinner("Syncing closing data to Google Sheet master log..."):
            try:
                response = requests.post(WEBHOOK_URL, json=payload, timeout=15)
                res_json = response.json()
                if res_json.get("status") == "success":
                    st.success(f"Successfully synced {res_json.get('records_synced', 0)} records to Google Sheets!")
                    for key in ["sales_entries", "collection_entries", "return_entries", "expense_entries", "advance_entries"]:
                        st.session_state[key] = []
                else:
                    st.error(f"Sync error from script: {res_json.get('message', 'Unknown error')}")
            except Exception as e:
                st.error(f"Connection failed: {str(e)}")
