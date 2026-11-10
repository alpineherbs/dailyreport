import streamlit as st
import pandas as pd
import requests
import datetime
import io

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Alpine Herbs | Field Operations & Closing",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# SPREADSHEET ID & APPS SCRIPT WEBHOOK URL
SHEET_ID = "1cpPYFS9EkajB5tGfMnReIJ71cmB5djz6oaMvvEoqs6A"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxG9ENtvINZxBhDVQyAkPiHojvQxPrRa7oV9tKrqR0NbWT7MEtMUN4Oj2y3JI75Kn7m/exec"  # Replace with your deployed Google Apps Script URL

# --- PROFESSIONAL STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    #MainMenu, footer, header { visibility: hidden; }
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 3rem;
        max-width: 1350px;
    }
    
    /* Top Brand Header */
    .brand-header {
        background: linear-gradient(135deg, #092013 0%, #164E33 60%, #1e6b46 100%);
        padding: 20px 24px;
        border-radius: 12px;
        color: #FFFFFF;
        box-shadow: 0 4px 16px rgba(9, 32, 19, 0.12);
        margin-bottom: 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .brand-title {
        font-size: 1.45rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .brand-subtitle {
        font-size: 0.85rem;
        color: #C3E2D0;
        margin-top: 4px;
    }
    .status-badge {
        background: rgba(255, 255, 255, 0.15);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        border: 1px solid rgba(255, 255, 255, 0.25);
    }

    /* Content Cards */
    .card-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .card-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #0F172A;
        margin-bottom: 14px;
    }
    
    /* Dynamic Product Item Rows */
    .product-row-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 10px;
    }
    
    /* Metric Highlights */
    .stat-card {
        background: #F8FAF9;
        border-left: 4px solid #164E33;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
    .stat-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        color: #475569;
    }
    .stat-val {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0F172A;
    }
</style>
""", unsafe_allow_html=True)

# --- DYNAMIC CLIENT DIRECTORY LOADER ---
@st.cache_data(ttl=60)
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

def get_client_selectbox_options(pool):
    if not pool:
        return ["Direct Walk-in / Retail [RET-001] — 📍 Birgunj"]
    sorted_pool = sorted(pool, key=lambda x: str(x.get("name", "")).lower())
    return [f"{c.get('name')}  [{c.get('code', 'N/A')}] — 📍 {c.get('area', 'Local')}" for c in sorted_pool]

client_options = get_client_selectbox_options(client_pool)

# --- INITIALIZE STATE VARIABLES ---
for key in ["sales_entries", "collection_entries", "return_entries", "expense_entries", "advance_entries"]:
    if key not in st.session_state:
        st.session_state[key] = []

# Persistent Dynamic Product Lines for the active invoice
if "invoice_lines" not in st.session_state:
    st.session_state["invoice_lines"] = [
        {"id": 1, "product_name": "", "qty": 1.0, "foc": 0.0, "rate": 0.0}
    ]
if "line_counter" not in st.session_state:
    st.session_state["line_counter"] = 1

# --- TOP NAVIGATION & HEADER ---
st.markdown("""
<div class="brand-header">
    <div>
        <div class="brand-title">🌿 ALPINE HERBS PVT. LTD.</div>
        <div class="brand-subtitle">Field Sales, Collections & Daily Operations Portal | Birgunj, Nepal</div>
    </div>
    <div class="status-badge">⚡ System Online</div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR: EXECUTIVE & CLOSING METADATA ---
with st.sidebar:
    st.markdown("#### 👤 Executive Details")
    staff_name = st.text_input("Sales Executive (MR)", value="Pritam Das")
    report_no = st.text_input("Closing Reference #", f"REP-{datetime.date.today().strftime('%Y%m%d')}")
    
    st.markdown("#### 📅 Operations Date")
    date_ad = st.date_input("Gregorian Date (AD)", datetime.date.today())
    bs_date = st.text_input("Nepali Miti (BS)", "2081-08-15")

    st.markdown("---")
    if st.button("🔄 Reload Client Directory", use_container_width=True):
        st.cache_data.clear()
        st.session_state["client_db"] = load_client_directory()
        st.success("Client database refreshed!")
        st.rerun()

    st.markdown("---")
    # Quick running totals indicator
    active_sales = sum(s["total_sale"] for s in st.session_state["sales_entries"])
    active_cols = sum(c["amount"] for c in st.session_state["collection_entries"])
    st.caption("Session Queue")
    st.markdown(f"**Sales Queued:** Rs. {active_sales:,.2f}")
    st.markdown(f"**Collections:** Rs. {active_cols:,.2f}")

# --- TABS CONFIGURATION ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    f"🛒 Sales Invoice ({len(st.session_state['sales_entries'])})",
    f"💵 Collections ({len(st.session_state['collection_entries'])})",
    f"🔄 Returns ({len(st.session_state['return_entries'])})",
    f"💸 Expenses ({len(st.session_state['expense_entries'])})",
    f"👤 Advances ({len(st.session_state['advance_entries'])})",
    "🚀 Review & Daily Submission"
])

# ==========================================
# TAB 1: DYNAMIC MULTI-PRODUCT SALES INVOICE
# ==========================================
with tab1:
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🧾 New Invoice Details</div>', unsafe_allow_html=True)

    col_c1, col_c2 = st.columns([3, 2])
    with col_c1:
        sel_client_str = st.selectbox("Select Chemist / Stockist", client_options, key="sales_cli_sel")
    with col_c2:
        invoice_no = st.text_input("Invoice Number", f"INV-{datetime.datetime.now().strftime('%H%M%S')}")

    st.markdown("<hr style='margin: 15px 0; border: 0; border-top: 1px solid #EDF2F7;'>", unsafe_allow_html=True)
    st.markdown("##### 📦 Product Line Items")
    st.caption("Click **➕ Add Item Line** to add as many products as needed. Calculations update in real time.")

    # Render dynamic product input lines
    lines_to_delete = []
    invoice_gross_total = 0.0

    # Header labels for table-like look
    col_h1, col_h2, col_h3, col_h4, col_h5, col_h6 = st.columns([3.5, 1.2, 1.2, 1.5, 1.5, 0.6])
    col_h1.caption("**Product / Formulation Name**")
    col_h2.caption("**Billed Qty**")
    col_h3.caption("**FOC / Free**")
    col_h4.caption("**Rate (Rs.)**")
    col_h5.caption("**Line Total**")
    col_h6.caption("**Action**")

    for idx, line in enumerate(st.session_state["invoice_lines"]):
        line_id = line["id"]
        c1, c2, c3, c4, c5, c6 = st.columns([3.5, 1.2, 1.2, 1.5, 1.5, 0.6])
        
        with c1:
            line["product_name"] = st.text_input(
                "Product", 
                value=line["product_name"], 
                key=f"prod_name_{line_id}", 
                placeholder="e.g. Liv-Alpine Syrup 200ml", 
                label_visibility="collapsed"
            )
        with c2:
            line["qty"] = st.number_input(
                "Qty", 
                min_value=1.0, 
                value=float(line["qty"]), 
                step=1.0, 
                key=f"qty_{line_id}", 
                label_visibility="collapsed"
            )
        with c3:
            line["foc"] = st.number_input(
                "FOC", 
                min_value=0.0, 
                value=float(line["foc"]), 
                step=1.0, 
                key=f"foc_{line_id}", 
                label_visibility="collapsed"
            )
        with c4:
            line["rate"] = st.number_input(
                "Rate", 
                min_value=0.0, 
                value=float(line["rate"]), 
                step=10.0, 
                key=f"rate_{line_id}", 
                label_visibility="collapsed"
            )
        
        line_subtotal = float(line["qty"]) * float(line["rate"])
        invoice_gross_total += line_subtotal
        
        with c5:
            st.markdown(f"<div style='padding-top: 8px; font-weight: 600; color: #164E33;'>Rs. {line_subtotal:,.2f}</div>", unsafe_allow_html=True)
            
        with c6:
            if len(st.session_state["invoice_lines"]) > 1:
                if st.button("✕", key=f"del_{line_id}", help="Remove this line item"):
                    lines_to_delete.append(idx)

    # Process deletions if triggered
    if lines_to_delete:
        for d in sorted(lines_to_delete, reverse=True):
            st.session_state["invoice_lines"].pop(d)
        st.rerun()

    # Add line button
    col_btn, _ = st.columns([2, 5])
    with col_btn:
        if st.button("➕ Add Item Line", use_container_width=True):
            st.session_state["line_counter"] += 1
            st.session_state["invoice_lines"].append({
                "id": st.session_state["line_counter"],
                "product_name": "",
                "qty": 1.0,
                "foc": 0.0,
                "rate": 0.0
            })
            st.rerun()

    st.markdown("<hr style='margin: 18px 0; border: 0; border-top: 1px solid #EDF2F7;'>", unsafe_allow_html=True)

    # Payment settlement for this invoice
    st.markdown("##### 💳 Settlement on Delivery")
    col_p1, col_p2, col_p3 = st.columns(3)
    
    with col_p1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Total Invoice Value</div>
            <div class="stat-val" style="color:#164E33;">Rs. {invoice_gross_total:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_p2:
        cash_received = st.number_input(
            "Cash Received Today (Rs.)", 
            min_value=0.0, 
            value=0.0, 
            step=50.0,
            help="Any instant cash given by client upon taking goods delivery"
        )
        
    with col_p3:
        credit_balance = max(0.0, invoice_gross_total - cash_received)
        st.markdown(f"""
        <div class="stat-card" style="border-left-color: {'#C53030' if credit_balance > 0 else '#2E7D32'};">
            <div class="stat-label">Added to Dues / Credit</div>
            <div class="stat-val" style="color: {'#C53030' if credit_balance > 0 else '#2E7D32'};">
                Rs. {credit_balance:,.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)

    col_save, col_clear = st.columns([3, 1])
    with col_save:
        if st.button("💾 Finalize & Save Complete Invoice", type="primary", use_container_width=True):
            valid_items = [item for item in st.session_state["invoice_lines"] if item["product_name"].strip() != ""]
            if not valid_items:
                st.error("Please provide at least one product name before saving.")
            else:
                # Client identification parsing
                selected_str = sel_client_str.strip()
                if "[" in selected_str and "]" in selected_str:
                    c_name = selected_str.split("[")[0].strip()
                    c_code = selected_str.split("[")[1].split("]")[0].strip()
                else:
                    c_name = selected_str
                    c_code = "PAR-000"

                num_items = len(valid_items)
                cash_split = cash_received / num_items if num_items else 0.0
                credit_split = credit_balance / num_items if num_items else 0.0

                for item in valid_items:
                    line_amt = float(item["qty"]) * float(item["rate"])
                    st.session_state["sales_entries"].append({
                        "client_code": c_code,
                        "client_name": c_name,
                        "invoice": invoice_no,
                        "product_name": item["product_name"].strip(),
                        "qty": float(item["qty"]),
                        "foc_qty": float(item["foc"]),
                        "rate": float(item["rate"]),
                        "cash_collected": cash_split,
                        "credit_given": credit_split,
                        "total_sale": line_amt
                    })

                # Reset line items for fresh invoice
                st.session_state["line_counter"] += 1
                st.session_state["invoice_lines"] = [
                    {"id": st.session_state["line_counter"], "product_name": "", "qty": 1.0, "foc": 0.0, "rate": 0.0}
                ]
                st.success(f"Invoice #{invoice_no} ({num_items} items) successfully recorded!")
                st.rerun()

    with col_clear:
        if st.button("Reset Form", use_container_width=True):
            st.session_state["invoice_lines"] = [
                {"id": 1, "product_name": "", "qty": 1.0, "foc": 0.0, "rate": 0.0}
            ]
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # Active sales table
    if st.session_state["sales_entries"]:
        st.markdown("##### 📋 Recorded Invoices in Current Session")
        sales_df = pd.DataFrame(st.session_state["sales_entries"])
        st.dataframe(sales_df, use_container_width=True, hide_index=True)
        if st.button("🗑️ Clear Sales Entries", key="clr_sales"):
            st.session_state["sales_entries"] = []
            st.rerun()


# ==========================================
# TAB 2: COLLECTIONS
# ==========================================
with tab2:
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">💵 Record Dues Collection / Receipt</div>', unsafe_allow_html=True)

    with st.form("collection_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            sel_client_col = st.selectbox("Select Chemist / Client", client_options, key="col_cli")
            receipt_no = st.text_input("Receipt / Cheque / Ref No.", f"REC-{datetime.datetime.now().strftime('%H%M%S')}")
            mode = st.selectbox("Payment Instrument", ["Cash", "Fonepay / Bank QR", "Cheque Transfer"])
        with col2:
            amount = st.number_input("Collection Amount (Rs.)", min_value=0.0, value=0.0, step=100.0)
            remarks = st.text_input("Transaction Note", "Against Outstanding Ledger Balance")

        if st.form_submit_button("➕ Record Collection", type="primary", use_container_width=True):
            if amount > 0:
                selected_str = sel_client_col.strip()
                if "[" in selected_str and "]" in selected_str:
                    c_name = selected_str.split("[")[0].strip()
                    c_code = selected_str.split("[")[1].split("]")[0].strip()
                else:
                    c_name = selected_str
                    c_code = "PAR-000"

                st.session_state["collection_entries"].append({
                    "client_code": c_code,
                    "client_name": c_name,
                    "receipt_no": receipt_no,
                    "amount": amount,
                    "mode": mode,
                    "remarks": remarks
                })
                st.success(f"Recorded Rs. {amount:,.2f} from {c_name}!")
                st.rerun()
            else:
                st.warning("Please specify an amount greater than 0.")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state["collection_entries"]:
        st.dataframe(pd.DataFrame(st.session_state["collection_entries"]), use_container_width=True, hide_index=True)
        if st.button("🗑️ Clear Collections", key="clr_cols"):
            st.session_state["collection_entries"] = []
            st.rerun()


# ==========================================
# TAB 3: RETURNS
# ==========================================
with tab3:
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🔄 Record Goods Return / Near Expiry</div>', unsafe_allow_html=True)

    with st.form("return_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            sel_client_ret = st.selectbox("Select Chemist / Client", client_options, key="ret_cli")
            product_name = st.text_input("Returned Item Name", placeholder="Product formulation")
        with col2:
            c_r1, c_r2 = st.columns(2)
            qty = c_r1.number_input("Units Returned", min_value=1.0, value=1.0, step=1.0)
            rate = c_r2.number_input("Credit Rate (Rs.)", min_value=0.0, value=0.0, step=10.0)
            reason = st.selectbox("Reason", ["Near Expiry", "Breakage / Leakage", "Excess Stock Correction"])

        if st.form_submit_button("➕ Record Return", type="primary", use_container_width=True):
            if product_name.strip():
                selected_str = sel_client_ret.strip()
                if "[" in selected_str and "]" in selected_str:
                    c_name = selected_str.split("[")[0].strip()
                    c_code = selected_str.split("[")[1].split("]")[0].strip()
                else:
                    c_name = selected_str
                    c_code = "PAR-000"

                st.session_state["return_entries"].append({
                    "client_code": c_code,
                    "client_name": c_name,
                    "product_name": product_name.strip(),
                    "qty": qty,
                    "rate": rate,
                    "total": qty * rate,
                    "reason": reason
                })
                st.success(f"Recorded return for {c_name}!")
                st.rerun()
            else:
                st.warning("Please enter a product name.")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state["return_entries"]:
        st.dataframe(pd.DataFrame(st.session_state["return_entries"]), use_container_width=True, hide_index=True)
        if st.button("🗑️ Clear Returns", key="clr_rets"):
            st.session_state["return_entries"] = []
            st.rerun()


# ==========================================
# TAB 4: EXPENSES
# ==========================================
with tab4:
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">💸 Daily Field Expenses</div>', unsafe_allow_html=True)

    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            details = st.selectbox("Expense Category", ["Fuel / Petrol", "Bus / Auto Fare", "Food & Meals", "Printing & Stationery", "Doctor Samples Postage", "Other"])
            paid_to = st.text_input("Paid To / Vendor", placeholder="e.g. Birgunj Petroleum")
        with col2:
            amount = st.number_input("Amount (Rs.)", min_value=0.0, value=0.0, step=50.0)
            remarks = st.text_input("Notes", placeholder="Route / travel details")

        if st.form_submit_button("➕ Add Expense", type="primary", use_container_width=True):
            if amount > 0:
                st.session_state["expense_entries"].append({
                    "details": details,
                    "paid_to": paid_to,
                    "amount": amount,
                    "remarks": remarks
                })
                st.success("Expense logged.")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state["expense_entries"]:
        st.dataframe(pd.DataFrame(st.session_state["expense_entries"]), use_container_width=True, hide_index=True)
        if st.button("🗑️ Clear Expenses", key="clr_exps"):
            st.session_state["expense_entries"] = []
            st.rerun()


# ==========================================
# TAB 5: ADVANCES
# ==========================================
with tab5:
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">👤 Staff Advances & Adjustments</div>', unsafe_allow_html=True)

    with st.form("advance_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            personnel_name = st.text_input("Staff / MR Name", staff_name)
            purpose = st.text_input("Purpose", "Emergency field / travel advance")
        with col2:
            amount = st.number_input("Amount (Rs.)", min_value=0.0, value=0.0, step=100.0)
            remarks = st.text_input("Authorization / Remarks", "Approved")

        if st.form_submit_button("➕ Add Staff Advance", type="primary", use_container_width=True):
            if amount > 0:
                st.session_state["advance_entries"].append({
                    "personnel_name": personnel_name,
                    "purpose": purpose,
                    "amount": amount,
                    "remarks": remarks
                })
                st.success("Staff advance logged.")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state["advance_entries"]:
        st.dataframe(pd.DataFrame(st.session_state["advance_entries"]), use_container_width=True, hide_index=True)
        if st.button("🗑️ Clear Advances", key="clr_advs"):
            st.session_state["advance_entries"] = []
            st.rerun()


# ==========================================
# TAB 6: REVIEW & DAILY SUBMISSION
# ==========================================
with tab6:
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">📊 Executive Financial Summary</div>', unsafe_allow_html=True)

    # Compute key accounting figures
    total_sales_val = sum(s["total_sale"] for s in st.session_state["sales_entries"])
    total_sales_cash = sum(s["cash_collected"] for s in st.session_state["sales_entries"])
    total_dues_col = sum(c["amount"] for c in st.session_state["collection_entries"])
    total_ret_val = sum(r["total"] for r in st.session_state["return_entries"])
    total_exp_val = sum(e["amount"] for e in st.session_state["expense_entries"])
    total_adv_val = sum(a["amount"] for a in st.session_state["advance_entries"])

    # Net physical cash that must be in the MR's pocket to hand over
    net_cash_in_hand = (total_sales_cash + total_dues_col) - (total_exp_val + total_adv_val)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Gross Billed Sales", f"Rs. {total_sales_val:,.2f}")
    m2.metric("Total Cash Collected", f"Rs. {(total_sales_cash + total_dues_col):,.2f}")
    m3.metric("Goods Returns", f"Rs. {total_ret_val:,.2f}")
    m4.metric("Field Expenses", f"Rs. {total_exp_val:,.2f}")
    m5.metric("Net Cash on Hand", f"Rs. {net_cash_in_hand:,.2f}", delta=f"{net_cash_in_hand:,.2f}")

    st.markdown("<hr style='margin: 16px 0; border: 0; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

    # Clean expandable sections for each journal
    with st.expander(f"🛒 Sales Entries Details ({len(st.session_state['sales_entries'])} records)", expanded=True):
        if st.session_state["sales_entries"]:
            st.dataframe(pd.DataFrame(st.session_state["sales_entries"]), use_container_width=True, hide_index=True)
        else:
            st.caption("No sales items queued.")

    with st.expander(f"💵 Dues Collections ({len(st.session_state['collection_entries'])} records)"):
        if st.session_state["collection_entries"]:
            st.dataframe(pd.DataFrame(st.session_state["collection_entries"]), use_container_width=True, hide_index=True)
        else:
            st.caption("No collections recorded.")

    with st.expander(f"🔄 Returns, Expenses & Advances ({len(st.session_state['return_entries']) + len(st.session_state['expense_entries']) + len(st.session_state['advance_entries'])} records)"):
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            st.markdown("**Expenses**")
            if st.session_state["expense_entries"]:
                st.dataframe(pd.DataFrame(st.session_state["expense_entries"]), use_container_width=True, hide_index=True)
            else:
                st.caption("No expenses recorded.")
        with r_col2:
            st.markdown("**Returns**")
            if st.session_state["return_entries"]:
                st.dataframe(pd.DataFrame(st.session_state["return_entries"]), use_container_width=True, hide_index=True)
            else:
                st.caption("No returns recorded.")

    st.markdown('</div>', unsafe_allow_html=True)

    # Submission Block
    submit_col1, submit_col2 = st.columns([3, 1])
    with submit_col1:
        if st.button("🚀 Push Official Daily Closing to Google Sheets", type="primary", use_container_width=True):
            if WEBHOOK_URL == "YOUR_APPS_SCRIPT_WEBHOOK_URL_HERE":
                st.error("⚠️ Setup Required: Please set your deployed Google Apps Script URL in the `WEBHOOK_URL` variable at the top of the file.")
            else:
                payload = {
                    "date": str(date_ad),
                    "bs_date": bs_date,
                    "report_no": report_no,
                    "staff_name": staff_name,
                    "sales": st.session_state["sales_entries"],
                    "collections": st.session_state["collection_entries"],
                    "returns": st.session_state["return_entries"],
                    "expenses": st.session_state["expense_entries"],
                    "advances": st.session_state["advance_entries"],
                    "net_cash": net_cash_in_hand
                }

                with st.spinner("Pushing closing data to central spreadsheet..."):
                    try:
                        res = requests.post(WEBHOOK_URL, json=payload, timeout=20)
                        res_data = res.json()
                        if res_data.get("status") == "success":
                            st.success(f"Closing synchronized successfully! Total rows affected: {res_data.get('records_synced', 'All')}")
                            
                            # Build PDF Receipt in memory
                            try:
                                from reportlab.lib.pagesizes import letter
                                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                                from reportlab.lib import colors

                                pdf_buf = io.BytesIO()
                                doc = SimpleDocTemplate(pdf_buf, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
                                story = []
                                styles = getSampleStyleSheet()

                                title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=15, textColor=colors.HexColor('#092013'))
                                sub_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#475569'), spaceAfter=14)

                                story.append(Paragraph("ALPINE HERBS PVT. LTD. — DAILY CLOSING SUMMARY", title_style))
                                story.append(Paragraph(f"<b>Report Ref:</b> {report_no} | <b>Executive:</b> {staff_name} | <b>Date:</b> {date_ad} ({bs_date})", sub_style))
                                
                                summary_tbl = [
                                    ["Head / Transaction Type", "Items Count", "Subtotal (Rs.)"],
                                    ["Gross Product Sales", str(len(st.session_state["sales_entries"])), f"{total_sales_val:,.2f}"],
                                    ["Direct Cash On Delivery", "-", f"{total_sales_cash:,.2f}"],
                                    ["Ledger Dues Collections", str(len(st.session_state["collection_entries"])), f"{total_dues_col:,.2f}"],
                                    ["Goods Returns & Damages", str(len(st.session_state["return_entries"])), f"{total_ret_val:,.2f}"],
                                    ["Daily Field Expenses", str(len(st.session_state["expense_entries"])), f"{total_exp_val:,.2f}"],
                                    ["Staff Cash Advances", str(len(st.session_state["advance_entries"])), f"{total_adv_val:,.2f}"],
                                    ["Net Cash to Deposit", "-", f"{net_cash_in_hand:,.2f}"]
                                ]
                                
                                t = Table(summary_tbl, colWidths=[240, 100, 150])
                                t.setStyle(TableStyle([
                                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#164E33')),
                                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                                    ('FONTSIZE', (0,0), (-1,-1), 9),
                                    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
                                    ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#F1F5F9')),
                                    ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
                                ]))
                                story.append(t)
                                doc.build(story)

                                st.download_button(
                                    label="📥 Download Closing Voucher (PDF)",
                                    data=pdf_buf.getvalue(),
                                    file_name=f"Alpine_Closing_{report_no}.pdf",
                                    mime="application/pdf",
                                    type="secondary"
                                )
                            except Exception:
                                pass

                            # Clear recorded entries
                            for key in ["sales_entries", "collection_entries", "return_entries", "expense_entries", "advance_entries"]:
                                st.session_state[key] = []
                                
                        else:
                            st.error(f"Error from server: {res_data.get('message', 'Failed to save')}")
                    except Exception as ex:
                        st.error(f"Transmission failed: {str(ex)}")

    with submit_col2:
        if st.button("Reset Entire Form", use_container_width=True):
            for key in ["sales_entries", "collection_entries", "return_entries", "expense_entries", "advance_entries"]:
                st.session_state[key] = []
            st.rerun()
