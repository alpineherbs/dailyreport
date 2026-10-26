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
# GOOGLE APPS SCRIPT WEB APP LINK FOR SHEET SYNC
# =========================================================
WEB_APP_URL = "YOUR_NEWLY_COPIED_WEB_APP_URL_HERE"

def sync_all_data_to_google_sheet(sales_df, office_df, staff_df, staff_name_val, report_ref, date_val):
    if "YOUR_NEWLY_COPIED_WEB_APP_URL_HERE" in WEB_APP_URL or not WEB_APP_URL.startswith("http"):
        return 0

    synced_count = 0

    # 1. Sync Sales Entries to 'Sales' Tab
    for _, row in sales_df.iterrows():
        c_name = str(row.get("Client / Party Name", "")).strip()
        if c_name and c_name != "nan":
            payload = {
                "target": "sales",
                "date": str(date_val),
                "invoice": str(row.get("Invoice No.", "")),
                "client_name": c_name,
                "address": str(row.get("Client Address", "")),
                "product_name": str(row.get("Goods / Product Name", "")),
                "qty": float(row.get("Qty", 0)),
                "rate": float(row.get("Sale Rate (Rs.)", 0)),
                "cash_collected": float(row.get("Cash Collected (Rs.)", 0)),
                "credit_given": float(row.get("Credit Given (Rs.)", 0)),
                "total_sale": float(row.get("Total Sale (Rs.)", 0)),
                "staff_name": str(staff_name_val),
                "report_no": str(report_ref)
            }
            try:
                res = requests.post(WEB_APP_URL, json=payload, timeout=8)
                if res.status_code == 200:
                    synced_count += 1
            except Exception as e:
                print(f"Sales Sync Error: {e}")

    # 2. Sync Operating Expenses to 'Expenses' Tab
    for _, row in office_df.iterrows():
        details = str(row.get("Expense Details", "")).strip()
        amt = float(row.get("Amount (Rs.)", 0))
        if details and details != "nan" and amt > 0:
            payload = {
                "target": "expenses",
                "date": str(date_val),
                "details": details,
                "paid_to": str(row.get("Paid To / Vendor", "")),
                "mode": str(row.get("Payment Mode", "Cash")),
                "amount": amt,
                "staff_name": str(staff_name_val),
                "report_no": str(report_ref)
            }
            try:
                res = requests.post(WEB_APP_URL, json=payload, timeout=8)
                if res.status_code == 200:
                    synced_count += 1
            except Exception as e:
                print(f"Expense Sync Error: {e}")

    # 3. Sync Staff Advances to 'Staff Advances' Tab
    for _, row in staff_df.iterrows():
        p_name = str(row.get("Staff / Personnel Name", "")).strip()
        amt = float(row.get("Amount (Rs.)", 0))
        if p_name and p_name != "nan" and amt > 0:
            payload = {
                "target": "advances",
                "date": str(date_val),
                "personnel_name": p_name,
                "purpose": str(row.get("Purpose / Details", "")),
                "type": str(row.get("Payment Type", "Staff Advance")),
                "amount": amt,
                "staff_name": str(staff_name_val),
                "report_no": str(report_ref)
            }
            try:
                res = requests.post(WEB_APP_URL, json=payload, timeout=8)
                if res.status_code == 200:
                    synced_count += 1
            except Exception as e:
                print(f"Advances Sync Error: {e}")

    return synced_count

# =========================================================
# PAGE CONFIGURATION & LOGIN
# =========================================================

st.set_page_config(page_title="ALPINE HERBS | Daily Field Report", page_icon="🌿", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🌿 ALPINE HERBS PVT. LTD.")
    st.subheader("Field Operations Portal (Repository A)")
    st.divider()

    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        st.markdown("### 🔐 Staff Login")
        login_user = st.text_input("Username", placeholder="Username", key="auth_user")
        login_pass = st.text_input("Password", type="password", placeholder="Password", key="auth_pass")
        st.write("")
        if st.button("🔑 Login to Portal", type="primary", use_container_width=True):
            if login_user.strip() == "Alpine" and login_pass.strip() == "AHP@123":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Invalid Username or Password")
else:
    # BRAND STYLING
    st.markdown("""
    <style>
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1550px; }
    .brand-header { background: linear-gradient(135deg, #0D2818 0%, #164E33 100%); color: white; padding: 1.2rem 1.8rem; border-radius: 10px; margin-bottom: 1.2rem; }
    .brand-title { font-size: 1.7rem; font-weight: 800; color: #FFFFFF; }
    .brand-sub { font-size: 0.85rem; color: #D3E6DA; }
    h3, h2, h1 { color: #164E33 !important; font-weight: 700; }
    div[data-testid="stMetric"] { background: #EAF2EC !important; border: 1px solid #C8DCCF !important; border-top: 4px solid #2D7D52 !important; padding: 10px 14px !important; border-radius: 8px !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="brand-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div class="brand-title">🌿 ALPINE HERBS PVT. LTD.</div>
                <div class="brand-sub">BIRGUNJ, NEPAL &nbsp;|&nbsp; MEDICAL REPRESENTATIVE DAILY FIELD CLOSING</div>
            </div>
            <div style="text-align: right; font-size: 0.8rem; color: #E0EFE5;">
                <div><strong>ISO GMP Standard</strong></div>
                <div>Field Operations Portal (Repository A)</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    def money(value):
        try: return f"Rs. {float(value or 0):,.2f}"
        except: return "Rs. 0.00"

    def nepali_date(d):
        try:
            import nepali_datetime
            if not isinstance(d, (date, datetime)): d = date.today()
            bs = nepali_datetime.date.from_datetime_date(d)
            return f"{bs.year:04d}-{bs.month:02d}-{bs.day:02d} B.S."
        except: return "2083-07-04 B.S."

    def generate_report_no(d):
        if not isinstance(d, (date, datetime)): d = date.today()
        return f"ALP-{d.strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

    def blank_sales():
        return pd.DataFrame([{"Client / Party Name": "", "Goods / Product Name": "", "Qty": 0.0, "FOC Qty": 0.0, "Sale Rate (Rs.)": 0.0, "Cash Collected (Rs.)": 0.0, "Credit Given (Rs.)": 0.0, "Client Address": "", "Invoice No.": ""}])

    def blank_office():
        return pd.DataFrame([{"Expense Details": "", "Paid To / Vendor": "", "Payment Mode": "Cash", "Amount (Rs.)": 0.0, "Remarks": ""}])

    def blank_staff():
        return pd.DataFrame([{"Staff / Personnel Name": "", "Purpose / Details": "", "Payment Type": "Staff Advance", "Amount (Rs.)": 0.0, "Remarks": ""}])

    def numeric_columns(df, columns):
        df = df.copy()
        for col in columns:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        return df

    if "form_id" not in st.session_state: st.session_state["form_id"] = 1
    if "sales_base" not in st.session_state: st.session_state["sales_base"] = blank_sales()
    if "office_base" not in st.session_state: st.session_state["office_base"] = blank_office()
    if "staff_base" not in st.session_state: st.session_state["staff_base"] = blank_staff()
    if "previous_dues" not in st.session_state: st.session_state["previous_dues"] = {}
    if "report_date" not in st.session_state: st.session_state["report_date"] = date.today()
    if "report_no" not in st.session_state: st.session_state["report_no"] = generate_report_no(date.today())

    def reset_form_to_blank():
        st.session_state["form_id"] += 1
        st.session_state["report_no"] = generate_report_no(st.session_state.get("report_date", date.today()))
        st.session_state["sales_base"] = blank_sales()
        st.session_state["office_base"] = blank_office()
        st.session_state["staff_base"] = blank_staff()

    st.markdown("#### 📋 Tour & Medical Representative Details")
    c1, c2, c3, c4 = st.columns([1.1, 1.3, 1.3, 1.1])
    with c1:
        selected_date = st.date_input("Date (A.D.)", value=st.session_state.get("report_date", date.today()))
        st.session_state["report_date"] = selected_date
        st.caption(f"🇳🇵 **Miti (B.S.):** `{nepali_date(selected_date)}`")
    with c2: staff_name = st.text_input("MR / Staff Name", placeholder="e.g. Pritam Gupta")
    with c3: route = st.text_input("Route / Area Covered", placeholder="e.g. Birgunj To Lautan")
    with c4: st.text_input("Report Reference No.", value=st.session_state.get("report_no", ""), disabled=True)

    st.divider()

    with st.form("daily_report_form"):
        st.subheader("1. Sales & Cash Collections Grid")
        current_form_id = st.session_state["form_id"]
        raw_sales = st.data_editor(st.session_state["sales_base"], num_rows="dynamic", hide_index=True, use_container_width=True, key=f"sales_editor_{current_form_id}")
        sales = numeric_columns(raw_sales, ["Qty", "FOC Qty", "Sale Rate (Rs.)", "Cash Collected (Rs.)", "Credit Given (Rs.)"])
        computed_bill = sales["Qty"] * sales["Sale Rate (Rs.)"]
        sales["Credit Given (Rs.)"] = (computed_bill - sales["Cash Collected (Rs.)"]).clip(lower=0.0)
        sales["Total Sale (Rs.)"] = computed_bill.where(computed_bill > 0, sales["Cash Collected (Rs.)"] + sales["Credit Given (Rs.)"])

        total_sales = float(sales["Total Sale (Rs.)"].sum())
        total_cash = float(sales["Cash Collected (Rs.)"].sum())
        total_credit = float(sales["Credit Given (Rs.)"].sum())

        col_exp_1, col_exp_2 = st.columns(2)
        with col_exp_1:
            st.subheader("2. Operating / Office Expenses")
            raw_office = st.data_editor(st.session_state["office_base"], num_rows="dynamic", hide_index=True, use_container_width=True, key=f"office_editor_{current_form_id}")
            office = numeric_columns(raw_office, ["Amount (Rs.)"])
            office_total = float(office["Amount (Rs.)"].sum())

        with col_exp_2:
            st.subheader("3. Staff Advances")
            raw_staff = st.data_editor(st.session_state["staff_base"], num_rows="dynamic", hide_index=True, use_container_width=True, key=f"staff_editor_{current_form_id}")
            staff = numeric_columns(raw_staff, ["Amount (Rs.)"])
            staff_total = float(staff["Amount (Rs.)"].sum())

        total_expenses = office_total + staff_total
        net_cash = total_cash - total_expenses

        valid_sales = sales[sales["Client / Party Name"].astype(str).str.strip() != ""]

        st.divider()
        st.markdown("##### 📊 Financial Closing Summary")

        st.markdown("""
        <style>
        .compact-metric-container { display: flex; gap: 10px; margin-bottom: 15px; }
        .compact-metric-card { background: #EAF2EC; border: 1px solid #C8DCCF; border-top: 3px solid #2D7D52; padding: 8px 12px; border-radius: 6px; flex: 1; text-align: left; }
        .compact-label { font-size: 0.68rem; font-weight: 700; color: #164E33; text-transform: uppercase; letter-spacing: 0.5px; }
        .compact-value { font-size: 0.95rem; font-weight: 700; color: #0D2818; margin-top: 2px; }
        </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="compact-metric-container">
            <div class="compact-metric-card">
                <div class="compact-label">Total Sales Billed</div>
                <div class="compact-value">{money(total_sales)}</div>
            </div>
            <div class="compact-metric-card">
                <div class="compact-label">Credit Given</div>
                <div class="compact-value">{money(total_credit)}</div>
            </div>
            <div class="compact-metric-card">
                <div class="compact-label">Gross Cash Collected</div>
                <div class="compact-value">{money(total_cash)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="compact-metric-container">
            <div class="compact-metric-card">
                <div class="compact-label">Operating Expenses</div>
                <div class="compact-value">{money(office_total)}</div>
            </div>
            <div class="compact-metric-card">
                <div class="compact-label">Staff Advances</div>
                <div class="compact-value">{money(staff_total)}</div>
            </div>
            <div class="compact-metric-card" style="border-top-color: #0D2818; background: #D3E6DA;">
                <div class="compact-label">Net Cash In Hand</div>
                <div class="compact-value" style="color: #0D2818;">{money(net_cash)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        def create_pdf():
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
            styles = getSampleStyleSheet()
            story = [Paragraph("<b>ALPINE HERBS PVT. LTD.</b>", styles["Title"])]
            doc.build(story)
            return buffer.getvalue()

        st.divider()
        submitted = st.form_submit_button("🚀 FINAL GENERATE & SYNC TO MASTER", use_container_width=True)

        if submitted:
            with st.spinner("Syncing Sales, Expenses, and Staff Advances..."):
                pdf_bytes = create_pdf()
                current_locked_ref = st.session_state.get('report_no', 'ALP')
                synced_count = sync_all_data_to_google_sheet(valid_sales, office, staff, staff_name, current_locked_ref, selected_date)
                st.session_state["submitted_pdf"] = pdf_bytes
                st.balloons()
                st.success(f"✅ Report `{current_locked_ref}` synced! ({synced_count} records posted across Sales, Expenses, and Staff Advances tabs)")
                reset_form_to_blank()

    with st.sidebar:
        st.header("⚙️ Controls")
        if st.button("🔒 Logout", use_container_width=True):
            st.session_state["authenticated"] = False
            st.rerun()

    if "submitted_pdf" in st.session_state:
        st.download_button(
            "⬇️ DOWNLOAD FINAL SUBMITTED PDF",
            data=st.session_state["submitted_pdf"],
            file_name=st.session_state.get("submitted_filename", "ALPINE_HERBS_REPORT.pdf"),
            mime="application/pdf",
            use_container_width=True
        )
