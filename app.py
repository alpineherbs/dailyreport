import streamlit as st
import pandas as pd
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, date
import uuid
import os
from openai import OpenAI

try:
    import nepali_datetime
    NEPALI_LIB_AVAILABLE = True
except ImportError:
    NEPALI_LIB_AVAILABLE = False

# ----------------- CREDENTIALS & SECRETS -----------------
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", "your-openai-api-key"))
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = st.secrets.get("SENDER_EMAIL", os.getenv("SENDER_EMAIL", "your-email@gmail.com"))
SENDER_PASSWORD = st.secrets.get("SENDER_PASSWORD", os.getenv("SENDER_PASSWORD", "your-app-password"))
REPORT_RECEIVER_EMAIL = st.secrets.get("REPORT_RECEIVER_EMAIL", os.getenv("REPORT_RECEIVER_EMAIL", "accounts@alpineherbs.com"))

client = OpenAI(api_key=OPENAI_API_KEY)

# ----------------- SESSION STATE -----------------
if "sales" not in st.session_state:
    st.session_state.sales = []        # Qty, Party Name, Particulars, Free, Cash, Credit
if "collections" not in st.session_state:
    st.session_state.collections = []  # Party Name, Cash Collected
if "expenses" not in st.session_state:
    st.session_state.expenses = []     # Category (Nasta, Fuel, Advance, eSewa, Misc), Amount, Note

today_ad = datetime.today().date()
if "ad_date" not in st.session_state:
    st.session_state.ad_date = today_ad

if "reference_no" not in st.session_state:
    unique_suffix = uuid.uuid4().hex[:4].upper()
    st.session_state.reference_no = f"ALP-{today_ad.strftime('%Y%m%d')}-{unique_suffix}"

def get_nepali_date(ad_date: date) -> str:
    if NEPALI_LIB_AVAILABLE:
        try:
            return nepali_datetime.date.from_datetime_date(ad_date).strftime("%Y-%m-%d")
        except Exception:
            pass
    return "2083-07-04"

current_bs_date = get_nepali_date(st.session_state.ad_date)

# ----------------- AI PARSER ENGINE -----------------
def parse_alpine_entry(text: str):
    """
    Parses pharmaceutical sales, party collections, and MR field expenses.
    Handles Free schemes, Credit sales, Cash recoveries, and Nasta/Fuel/eSewa deductions.
    """
    system_prompt = """
    You are an AI data assistant for ALPINE HERBS PVT.LTD (Pharma division).
    Convert the field agent's notes into JSON with three lists:
    1. 'sales': [
         {"qty": int, "party_name": str, "particulars": str, "free": int, "cash": float, "credit": float}
       ]
       - 'qty': quantity supplied
       - 'particulars': medicine / product name
       - 'free': free scheme quantity (bonus)
       - 'cash': upfront cash paid for this bill
       - 'credit': billed on credit (debit to party)
    2. 'collections': [
         {"party_name": str, "cash_collected": float, "note": str}
       ]
       - Cash recovered from clinics/medical stores against past dues.
    3. 'expenses': [
         {"category": "Nasta" | "Fuel" | "Advance" | "eSewa" | "Maintenance" | "Extra", "amount": float, "particulars": str}
       ]

    Output ONLY a valid JSON object.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

# ----------------- EMAIL DISPATCH ENGINE -----------------
def send_alpine_report(subject: str, html_body: str):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = REPORT_RECEIVER_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, REPORT_RECEIVER_EMAIL, msg.as_string())
        server.quit()
        return True, "Report successfully sent to Accounts & Management!"
    except Exception as e:
        return False, str(e)

# ----------------- STREAMLIT UI -----------------
st.set_page_config(page_title="Alpine Herbs - MR Daily Report", layout="wide")

# Header
st.markdown("<h2 style='text-align: center; color: #1e7e34;'>ALPINE HERBS PVT. LTD.</h2>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align: center; color: #555;'>Birgunj, Nepal | Daily Medical Representative (MR) Report</h5>", unsafe_allow_html=True)
st.write("")

# Metadata Sidebar
with st.sidebar:
    st.header("📋 Tour & MR Details")
    st.info(f"**Ref No:** `{st.session_state.reference_no}`")
    mr_name = st.text_input("MR Name", value="Pritam Gupta")
    headquarters = st.text_input("Address / HQ", value="Birgunj")
    tour_location = st.text_input("Tour Location / Route", value="Birgunj To Lautan")
    
    st.divider()
    miti_bs = st.text_input("Date (B.S. Miti)", value=current_bs_date)
    date_ad = st.date_input("Date (A.D.)", value=st.session_state.ad_date)
    verifier_name = st.text_input("Verified By (Supervisor)", value="Accounts Section")

# 1. Quick Data Input
st.subheader("1. AI Fast Log")
st.caption("Paste raw notes or speak into your microphone. The AI will extract Sales, Collections, and Expenses automatically.")

sample_entry = """Sold 10 Narayani zyme 100ml with 10 free to Ali health clinic on credit 1724.
Sold 10 Narayani zyme 200ml with 10 free to Ali health clinic on credit 1034.
Sold 10 Provita to Shoalal medical on credit 1500.
Collected cash: Ali health clinic 1500, Shoalal medical 700, Satya medical 900, Jay shree gadimai 500, Alex medical 500, Om shiv shakti 500.
Expenses: Nasta 50, Karan advance 300, E-sewa deposit 1700."""

user_text = st.text_area("Enter Day's Notes:", height=110, placeholder=sample_entry)

col_b1, col_b2 = st.columns([1, 4])
with col_b1:
    if st.button("⚡ Parse & Record", type="secondary", use_container_width=True):
        if user_text.strip():
            with st.spinner("AI parsing pharma entries..."):
                try:
                    data = parse_alpine_entry(user_text)
                    if "sales" in data:
                        st.session_state.sales.extend(data["sales"])
                    if "collections" in data:
                        st.session_state.collections.extend(data["collections"])
                    if "expenses" in data:
                        st.session_state.expenses.extend(data["expenses"])
                    st.success("Entries added to today's ledger!")
                except Exception as e:
                    st.error(f"Error parsing text: {e}")
        else:
            st.warning("Please enter transaction details.")
with col_b2:
    if st.button("🗑️ Clear Today's Records"):
        st.session_state.sales = []
        st.session_state.collections = []
        st.session_state.expenses = []
        st.experimental_rerun()

st.divider()

# 2. Accumulated DataFrames & Financials
sales_df = pd.DataFrame(st.session_state.sales)
collections_df = pd.DataFrame(st.session_state.collections)
expenses_df = pd.DataFrame(st.session_state.expenses)

# Numeric conversions
total_credit_sales = sales_df["credit"].sum() if not sales_df.empty and "credit" in sales_df else 0.0
sales_cash = sales_df["cash"].sum() if not sales_df.empty and "cash" in sales_df else 0.0
recovered_cash = collections_df["cash_collected"].sum() if not collections_df.empty and "cash_collected" in collections_df else 0.0

total_gross_cash = sales_cash + recovered_cash
total_expenses = expenses_df["amount"].sum() if not expenses_df.empty and "amount" in expenses_df else 0.0
net_cash_balance = total_gross_cash - total_expenses

# KPI Tiles
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Credit Sales (Debit)", f"Rs. {total_credit_sales:,.2f}")
kpi2.metric("Total Cash Collected", f"Rs. {total_gross_cash:,.2f}")
kpi3.metric("Expenses & Deposits", f"Rs. {total_expenses:,.2f}")
kpi4.metric("Net Cash in Hand", f"Rs. {net_cash_balance:,.2f}")

# Breakdown Tables
t1, t2, t3 = st.tabs(["📦 Product Sales & Free Schemes", "💵 Party Cash Collections", "⛽ Field Expenses & eSewa"])
with t1:
    st.dataframe(sales_df, use_container_width=True)
with t2:
    st.dataframe(collections_df, use_container_width=True)
with t3:
    st.dataframe(expenses_df, use_container_width=True)

st.divider()

# 3. Final Submission
st.subheader("3. Verification & Submit")

if st.button("🚀 Final Submit & Email Daily Report", type="primary", use_container_width=True):
    subject_line = f"[{st.session_state.reference_no}] Daily MR Report - {mr_name} - Miti: {miti_bs}"
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; font-size: 14px; color: #222;">
      <div style="border-bottom: 2px solid #1e7e34; padding-bottom: 8px; margin-bottom: 12px;">
        <h2 style="color: #1e7e34; margin: 0;">ALPINE HERBS PVT. LTD.</h2>
        <p style="margin: 2px 0; color: #555;">Birgunj, Nepal | Medical Representative Daily Report</p>
      </div>

      <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px; background-color: #f8f9fa;">
        <tr>
          <td style="padding: 6px; border: 1px solid #ddd;"><strong>Ref No:</strong> {st.session_state.reference_no}</td>
          <td style="padding: 6px; border: 1px solid #ddd;"><strong>Miti (B.S.):</strong> {miti_bs}</td>
          <td style="padding: 6px; border: 1px solid #ddd;"><strong>Date (A.D.):</strong> {date_ad}</td>
        </tr>
        <tr>
          <td style="padding: 6px; border: 1px solid #ddd;"><strong>MR Name:</strong> {mr_name}</td>
          <td style="padding: 6px; border: 1px solid #ddd;"><strong>Address:</strong> {headquarters}</td>
          <td style="padding: 6px; border: 1px solid #ddd;"><strong>Route:</strong> {tour_location}</td>
        </tr>
        <tr>
          <td colspan="3" style="padding: 6px; border: 1px solid #ddd;"><strong>Verified By:</strong> {verifier_name}</td>
        </tr>
      </table>

      <h3 style="color: #333; margin-bottom: 5px;">Daily Cash & Credit Summary</h3>
      <table style="width: 60%; border-collapse: collapse; margin-bottom: 15px;">
        <tr style="background: #e9ecef;"><td style="padding: 6px; border: 1px solid #ddd;">Total Credit Sales (Debit to Party)</td><td style="padding: 6px; border: 1px solid #ddd; text-align: right;"><strong>Rs. {total_credit_sales:,.2f}</strong></td></tr>
        <tr><td style="padding: 6px; border: 1px solid #ddd;">Total Cash Collections</td><td style="padding: 6px; border: 1px solid #ddd; text-align: right; color: green;"><strong>Rs. {total_gross_cash:,.2f}</strong></td></tr>
        <tr><td style="padding: 6px; border: 1px solid #ddd;">Less: Field Expenses & eSewa Transferred</td><td style="padding: 6px; border: 1px solid #ddd; text-align: right; color: red;">- Rs. {total_expenses:,.2f}</td></tr>
        <tr style="background: #d4edda;"><td style="padding: 6px; border: 1px solid #ddd;"><strong>Closing Cash in Hand to Handover</strong></td><td style="padding: 6px; border: 1px solid #ddd; text-align: right;"><strong>Rs. {net_cash_balance:,.2f}</strong></td></tr>
      </table>

      <h4>1. Product Sales & Free Schemes</h4>
      {sales_df.to_html(index=False) if not sales_df.empty else "<p>No direct sales logged.</p>"}

      <h4>2. Party Cash Collections</h4>
      {collections_df.to_html(index=False) if not collections_df.empty else "<p>No cash collections logged.</p>"}

      <h4>3. Field Expenses (Nasta, Fuel, Advance, eSewa)</h4>
      {expenses_df.to_html(index=False) if not expenses_df.empty else "<p>No expenses logged.</p>"}

      <br/>
      <p style="font-size: 11px; color: #888;">Generated automatically via Alpine Herbs Field AI Agent. Unique Tag: {st.session_state.reference_no}</p>
    </div>
    """

    with st.spinner("Dispatching verified report via email..."):
        success, err = send_alpine_report(subject_line, html_content)
        if success:
            st.balloons()
            st.success(f"Report `{st.session_state.reference_no}` has been emailed to {REPORT_RECEIVER_EMAIL}!")
        else:
            st.error(f"Email failed: {err}")
