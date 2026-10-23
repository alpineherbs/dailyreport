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

# Try importing nepali_datetime for automatic BS conversion
try:
    import nepali_datetime
    NEPALI_LIB_AVAILABLE = True
except ImportError:
    NEPALI_LIB_AVAILABLE = False

# ----------------- CONFIGURATION & SECRETS -----------------
# Picks up keys from Streamlit Secrets or Environment Variables
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", "your-openai-api-key"))
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = st.secrets.get("SENDER_EMAIL", os.getenv("SENDER_EMAIL", "your-email@gmail.com"))
SENDER_PASSWORD = st.secrets.get("SENDER_PASSWORD", os.getenv("SENDER_PASSWORD", "your-app-password"))
REPORT_RECEIVER_EMAIL = st.secrets.get("REPORT_RECEIVER_EMAIL", os.getenv("REPORT_RECEIVER_EMAIL", "accounts@yourcompany.com"))

client = OpenAI(api_key=OPENAI_API_KEY)

# ----------------- DATE & REFERENCE NO HELPERS -----------------
def get_nepali_date(ad_date: date) -> str:
    """Converts Gregorian (AD) date to Nepali Bikram Sambat (BS / Miti)."""
    if NEPALI_LIB_AVAILABLE:
        try:
            bs_date = nepali_datetime.date.from_datetime_date(ad_date)
            return bs_date.strftime("%Y-%m-%d")
        except Exception:
            return "BS Conversion Error"
    return "nepali-datetime library missing"

# ----------------- INITIALIZE SESSION STATE -----------------
if "sales" not in st.session_state:
    st.session_state.sales = []        # Client, Product, Qty, Total Amount, Cash, Credit
if "collections" not in st.session_state:
    st.session_state.collections = []  # Client, Amount Collected against past dues
if "expenses" not in st.session_state:
    st.session_state.expenses = []     # Category (Fuel/Food/Maintenance/Extra), Amount, Note

# Automatically lock today's date & generate sticky reference number
today_ad = datetime.today().date()
if "ad_date" not in st.session_state:
    st.session_state.ad_date = today_ad

if "reference_no" not in st.session_state:
    # Generates a permanent unique ID tagged to date: e.g., REF-20261023-A7F2
    unique_suffix = uuid.uuid4().hex[:4].upper()
    date_code = today_ad.strftime("%Y%m%d")
    st.session_state.reference_no = f"REF-{date_code}-{unique_suffix}"

current_bs_date = get_nepali_date(st.session_state.ad_date)

# ----------------- AI PARSING ENGINE -----------------
def parse_field_entry(text: str):
    """Uses LLM to classify messy field entries into structured debit/credit and expenses."""
    system_prompt = """
    You are an automated accounting assistant for a field sales rep.
    Extract the transaction details into valid JSON with three lists:
    1. 'sales': [{"client": str, "product": str, "quantity": int/float, "total_amount": float, "cash_paid": float, "credit": float}]
       - 'total_amount': gross sales value.
       - 'cash_paid': money collected at time of sale.
       - 'credit': debit to client account (total_amount - cash_paid).
    2. 'collections': [{"client": str, "amount_collected": float, "notes": str}]
       - Cash collected against past dues/credit.
    3. 'expenses': [{"category": "Fuel" | "Food" | "Maintenance" | "Extra", "amount": float, "note": str}]

    Return ONLY raw JSON. No explanations.
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
def send_summary_email(subject: str, summary_html: str):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = REPORT_RECEIVER_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(summary_html, 'html'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, REPORT_RECEIVER_EMAIL, msg.as_string())
        server.quit()
        return True, "Report successfully sent to management!"
    except Exception as e:
        return False, str(e)

# ----------------- UI / FRONTEND -----------------
st.set_page_config(page_title="Field Sales & Collection Tracker", layout="centered")

st.title("📋 Daily Sales & Cash Collection Agent")

# Sidebar: Tracking Identity & Dates
with st.sidebar:
    st.header("📌 Report Metadata")
    st.info(f"**Reference No:** `{st.session_state.reference_no}`")
    
    st.write(f"📅 **English Date (A.D.):** {st.session_state.ad_date.strftime('%Y-%m-%d')}")
    st.write(f"🇳🇵 **Nepali Date (Miti B.S.):** {current_bs_date}")
    
    st.divider()
    agent_name = st.text_input("Sales / Collection Person", value="Ramesh Sharma")
    verifier_name = st.text_input("Verifying User / Supervisor", value="Suresh Thapa (Accounts)")
    recipient_email = st.text_input("Report Sending To", value=REPORT_RECEIVER_EMAIL)

# 1. Input Section
st.subheader("1. Quick Natural Language Entry")
st.caption("Type or use speech-to-text on your mobile keyboard.")
user_input = st.text_area(
    "Activity Log:", 
    placeholder="e.g. Sold 10 sacks Rice to Sagar Store for 25000, collected 10000 cash, 15000 credit. Collected 4000 old dues from Everest Traders. Spent 400 on petrol and 150 for lunch."
)

if st.button("➕ Process & Add Entry", use_container_width=True):
    if user_input.strip():
        with st.spinner("AI parsing your sales, credit/debit, and expenses..."):
            try:
                parsed_data = parse_field_entry(user_input)
                if "sales" in parsed_data:
                    st.session_state.sales.extend(parsed_data["sales"])
                if "collections" in parsed_data:
                    st.session_state.collections.extend(parsed_data["collections"])
                if "expenses" in parsed_data:
                    st.session_state.expenses.extend(parsed_data["expenses"])
                st.success("Entry recorded successfully!")
            except Exception as e:
                st.error(f"Error parsing entry: {e}")
    else:
        st.warning("Please enter some text first.")

st.divider()

# 2. Accumulated Data & Ledger Calculations
st.subheader("2. Daily Accumulated Ledger")

sales_df = pd.DataFrame(st.session_state.sales)
collections_df = pd.DataFrame(st.session_state.collections)
expenses_df = pd.DataFrame(st.session_state.expenses)

# Calculations
total_sales = sales_df["total_amount"].sum() if not sales_df.empty else 0.0
total_credit = sales_df["credit"].sum() if not sales_df.empty else 0.0
cash_from_sales = sales_df["cash_paid"].sum() if not sales_df.empty else 0.0
old_dues_collected = collections_df["amount_collected"].sum() if not collections_df.empty else 0.0

gross_cash_collected = cash_from_sales + old_dues_collected
total_expenses = expenses_df["amount"].sum() if not expenses_df.empty else 0.0
net_cash_in_hand = gross_cash_collected - total_expenses

# Display KPI summary cards
c1, c2, c3 = st.columns(3)
c1.metric("Total Sales", f"Rs. {total_sales:,.2f}")
c2.metric("Total Credit Given", f"Rs. {total_credit:,.2f}")
c3.metric("Gross Cash Collected", f"Rs. {gross_cash_collected:,.2f}")

c4, c5 = st.columns(2)
c4.metric("Total Expenses", f"Rs. {total_expenses:,.2f}")
c5.metric("Net Cash to Handover", f"Rs. {net_cash_in_hand:,.2f}")

# Detail Tabs
t1, t2, t3 = st.tabs(["📦 Product Sales", "💰 Debt Recovered", "⛽ Expenses (Fuel/Food/Maint)"])
with t1:
    st.dataframe(sales_df if not sales_df.empty else pd.DataFrame([{"Info": "No sales logged yet"}]), use_container_width=True)
with t2:
    st.dataframe(collections_df if not collections_df.empty else pd.DataFrame([{"Info": "No collections logged yet"}]), use_container_width=True)
with t3:
    st.dataframe(expenses_df if not expenses_df.empty else pd.DataFrame([{"Info": "No expenses logged yet"}]), use_container_width=True)

st.divider()

# 3. Final Submission
st.subheader("3. Final Verification & Submit")
st.write(f"This will finalize **{st.session_state.reference_no}** and send it for verification.")

if st.button("🚀 Final Submit & Email Daily Report", type="primary", use_container_width=True):
    email_subject = f"[{st.session_state.reference_no}] EOD Report: {agent_name} | {current_bs_date} (B.S)"
    
    html_report = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.5; color: #333;">
      <h2 style="color: #0b5394; margin-bottom: 5px;">Daily Sales & Cash Collection Closing Report</h2>
      <p style="margin-top: 0; color: #555;">Reference No: <strong>{st.session_state.reference_no}</strong></p>
      
      <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
        <tr style="background-color: #f2f2f2;">
          <td style="padding: 8px; border: 1px solid #ddd;"><strong>English Date (A.D.):</strong> {st.session_state.ad_date.strftime('%Y-%m-%d')}</td>
          <td style="padding: 8px; border: 1px solid #ddd;"><strong>Nepali Date (Miti B.S.):</strong> {current_bs_date}</td>
        </tr>
        <tr>
          <td style="padding: 8px; border: 1px solid #ddd;"><strong>Sales & Collection Rep:</strong> {agent_name}</td>
          <td style="padding: 8px; border: 1px solid #ddd;"><strong>Verifying Officer:</strong> {verifier_name}</td>
        </tr>
      </table>

      <h3>Financial Summary</h3>
      <ul>
        <li><strong>Total Sales:</strong> Rs. {total_sales:,.2f}</li>
        <li><strong>Total Credit / Debit to Clients:</strong> Rs. {total_credit:,.2f}</li>
        <li><strong>Gross Cash Collected:</strong> Rs. {gross_cash_collected:,.2f} (Sales: Rs. {cash_from_sales:,.2f} + Old Dues: Rs. {old_dues_collected:,.2f})</li>
        <li><strong>Total Field Expenses:</strong> Rs. {total_expenses:,.2f}</li>
        <li><strong style="color: #274e13; font-size: 16px;">NET CASH TO HAND OVER: Rs. {net_cash_in_hand:,.2f}</strong></li>
      </ul>

      <hr/>
      <h3>1. Sales & Invoicing Breakdown</h3>
      {sales_df.to_html(index=False) if not sales_df.empty else "<p>No sales today.</p>"}

      <h3>2. Old Debt Collections</h3>
      {collections_df.to_html(index=False) if not collections_df.empty else "<p>No collections today.</p>"}

      <h3>3. Expenses (Fuel, Food, Maintenance, Misc)</h3>
      {expenses_df.to_html(index=False) if not expenses_df.empty else "<p>No expenses recorded.</p>"}
      
      <br/>
      <p style="font-size: 11px; color: #777;">Generated automatically via Field Agent AI System. Tagged with ID {st.session_state.reference_no}.</p>
    </div>
    """
    
    with st.spinner("Submitting final report..."):
        success, msg = send_summary_email(email_subject, html_report)
        if success:
            st.balloons()
            st.success(f"Report `{st.session_state.reference_no}` has been verified and emailed successfully!")
        else:
            st.error(f"Failed to send email: {msg}")
