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
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", "your-openai-api-key"))
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = st.secrets.get("SENDER_EMAIL", os.getenv("SENDER_EMAIL", "your-email@gmail.com"))
SENDER_PASSWORD = st.secrets.get("SENDER_PASSWORD", os.getenv("SENDER_PASSWORD", "your-app-password"))
REPORT_RECEIVER_EMAIL = st.secrets.get("REPORT_RECEIVER_EMAIL", os.getenv("REPORT_RECEIVER_EMAIL", "accounts@alpineherbs.com"))

client = OpenAI(api_key=OPENAI_API_KEY)

# ----------------- HELPER: NEPALI DATE & REF CODE -----------------
def get_nepali_date(ad_date: date) -> str:
    if NEPALI_LIB_AVAILABLE:
        try:
            return nepali_datetime.date.from_datetime_date(ad_date).strftime("%Y-%m-%d")
        except Exception:
            pass
    return "2083-07-04"

# ----------------- SESSION STATE -----------------
today_ad = datetime.today().date()
if "ad_date" not in st.session_state:
    st.session_state.ad_date = today_ad

current_bs_date = get_nepali_date(st.session_state.ad_date)

if "reference_no" not in st.session_state:
    unique_suffix = uuid.uuid4().hex[:4].upper()
    date_code = today_ad.strftime("%Y%m%d")
    st.session_state.reference_no = f"ALP-{date_code}-{unique_suffix}"

# Pre-populate sample rows matching the Alpine Herbs XLS format if empty
if "records" not in st.session_state:
    st.session_state.records = [
        {"QTY": 10, "Party Name": "Ali health clinic", "Particulars": "Narayani zyme 100ml", "Free (FOC)": 10, "Cash Collected": 0.0, "Credit Sales": 1724.0, "Sales Rate": 172.4, "Buyer Address": "Birgunj"},
        {"QTY": 10, "Party Name": "Ali health clinic", "Particulars": "Narayani zyme 200ml", "Free (FOC)": 10, "Cash Collected": 0.0, "Credit Sales": 1034.0, "Sales Rate": 103.4, "Buyer Address": "Birgunj"},
        {"QTY": 10, "Party Name": "Shoalal medical", "Particulars": "Provita", "Free (FOC)": 0, "Cash Collected": 0.0, "Credit Sales": 1500.0, "Sales Rate": 150.0, "Buyer Address": "Lautan"},
        {"QTY": 0, "Party Name": "Ali health clinic", "Particulars": "Old Balance Recovery", "Free (FOC)": 0, "Cash Collected": 1500.0, "Credit Sales": 0.0, "Sales Rate": 0.0, "Buyer Address": "Birgunj"},
        {"QTY": 0, "Party Name": "Shoalal medical", "Particulars": "Old Balance Recovery", "Free (FOC)": 0, "Cash Collected": 700.0, "Credit Sales": 0.0, "Sales Rate": 0.0, "Buyer Address": "Lautan"},
        {"QTY": 0, "Party Name": "Satya medical", "Particulars": "Old Balance Recovery", "Free (FOC)": 0, "Cash Collected": 900.0, "Credit Sales": 0.0, "Sales Rate": 0.0, "Buyer Address": "Lautan"},
        {"QTY": 0, "Party Name": "Jay shree gadimai medical", "Particulars": "Old Balance Recovery", "Free (FOC)": 0, "Cash Collected": 500.0, "Credit Sales": 0.0, "Sales Rate": 0.0, "Buyer Address": "Birgunj"},
        {"QTY": 0, "Party Name": "Alex medical", "Particulars": "Old Balance Recovery", "Free (FOC)": 0, "Cash Collected": 500.0, "Credit Sales": 0.0, "Sales Rate": 0.0, "Buyer Address": "Birgunj"},
        {"QTY": 0, "Party Name": "Om shiv shakti medical", "Particulars": "Old Balance Recovery", "Free (FOC)": 0, "Cash Collected": 500.0, "Credit Sales": 0.0, "Sales Rate": 0.0, "Buyer Address": "Birgunj"},
    ]

if "expenses" not in st.session_state:
    st.session_state.expenses = [
        {"Category": "Nasta (Food)", "Particulars": "MR Nasta", "Amount": 50.0},
        {"Category": "Staff Advance", "Particulars": "Karan Advance", "Amount": 300.0},
        {"Category": "eSewa Deposit", "Particulars": "Online Remittance to Office", "Amount": 1700.0},
        {"Category": "Fuel", "Particulars": "FZ Bike Fuel", "Amount": 0.0},
    ]

# ----------------- AI PARSER ENGINE -----------------
def parse_field_entry_with_ai(natural_text: str):
    system_prompt = """
    You are an AI assistant for ALPINE HERBS PVT. LTD. (Nepal).
    Extract sales, collections, and expenses from the user's input into JSON:
    {
      "records": [
        {"QTY": int, "Party Name": str, "Particulars": str, "Free (FOC)": int, "Cash Collected": float, "Credit Sales": float, "Sales Rate": float, "Buyer Address": str}
      ],
      "expenses": [
        {"Category": "Nasta (Food)" | "Fuel" | "Staff Advance" | "eSewa Deposit" | "Maintenance" | "Office Nasta" | "Extra", "Particulars": str, "Amount": float}
      ]
    }
    Always output strict JSON.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": natural_text}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

# ----------------- EMAIL DISPATCH -----------------
def send_eod_email(subject: str, html_body: str):
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
        return True, "Report successfully sent to management!"
    except Exception as e:
        return False, str(e)

# ----------------- STREAMLIT UI -----------------
st.set_page_config(page_title="Alpine Herbs - Daily MR Report", layout="wide")

# Company Header
st.markdown("""
<div style='text-align: center; border-bottom: 2px solid #2e7d32; padding-bottom: 10px; margin-bottom: 20px;'>
    <h2 style='color: #1b5e20; margin: 0;'>ALPINE HERBS PVT. LTD.</h2>
    <p style='margin: 0; color: #555; font-size: 14px;'>Birgunj, Nepal | Daily Sales, Collection & Expense Ledger</p>
</div>
""", unsafe_allow_html=True)

# Sidebar: Metadata & Info
with st.sidebar:
    st.header("📌 Tour Details")
    st.info(f"**Reference No:** `{st.session_state.reference_no}`")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        miti_bs = st.text_input("Date (B.S. Miti)", value=current_bs_date)
    with col_d2:
        date_ad = st.date_input("Date (A.D.)", value=st.session_state.ad_date)
        
    mr_name = st.text_input("MR Name", value="Pritam Gupta")
    mr_address = st.text_input("Address / HQ", value="Birgunj")
    tour_route = st.text_input("Tour Location / Route", value="Birgunj To Lautan")
    verifier_name = st.text_input("Verifying Person", value="Accounts Manager")
    report_email = st.text_input("Email Report To", value=REPORT_RECEIVER_EMAIL)

# 1. AI Quick Voice / Text Parser
with st.expander("🎙️ AI Quick Voice / Text Entry (Click to expand)"):
    ai_text = st.text_area("Type or dictate with your phone's microphone:", height=70, 
                           placeholder="e.g. Sold 10 Provita to Shoalal medical on credit 1500. Collected 500 from Alex medical. Spent 50 on Nasta.")
    if st.button("➕ Parse and Insert Rows"):
        if ai_text.strip():
            with st.spinner("AI parsing..."):
                try:
                    res = parse_field_entry_with_ai(ai_text)
                    if "records" in res and res["records"]:
                        st.session_state.records.extend(res["records"])
                    if "expenses" in res and res["expenses"]:
                        st.session_state.expenses.extend(res["expenses"])
                    st.success("Entries added to the table below!")
                except Exception as ex:
                    st.error(f"Error parsing entry: {ex}")

# 2. Interactive Excel-Style Entry Grids
st.subheader("1. Sales & Cash Collection Ledger")
st.caption("You can click, type, edit rows, or add new rows directly in this grid like Excel.")

records_df = pd.DataFrame(st.session_state.records)
edited_records_df = st.data_editor(
    records_df, 
    num_rows="dynamic", 
    use_container_width=True,
    column_config={
        "QTY": st.column_config.NumberColumn("QTY", min_value=0, step=1),
        "Party Name": st.column_config.TextColumn("Party Name", required=True),
        "Particulars": st.column_config.TextColumn("Particulars (Product / Dues)"),
        "Free (FOC)": st.column_config.NumberColumn("Free (FOC)", min_value=0, step=1),
        "Cash Collected": st.column_config.NumberColumn("Cash Collected (Rs.)", format="%.2f"),
        "Credit Sales": st.column_config.NumberColumn("Credit Sales / Debit (Rs.)", format="%.2f"),
        "Sales Rate": st.column_config.NumberColumn("Sales Rate", format="%.2f"),
        "Buyer Address": st.column_config.TextColumn("Buyer Address"),
    }
)

# Keep session state updated with table edits
st.session_state.records = edited_records_df.to_dict('records')

st.subheader("2. Field Expenses & Remittances")
expenses_df = pd.DataFrame(st.session_state.expenses)
edited_expenses_df = st.data_editor(
    expenses_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Category": st.column_config.SelectboxColumn("Expense Category", options=["Nasta (Food)", "Fuel", "Staff Advance", "eSewa Deposit", "Office Nasta", "Maintenance", "Extra"]),
        "Particulars": st.column_config.TextColumn("Details / Remarks"),
        "Amount": st.column_config.NumberColumn("Amount (Rs.)", min_value=0.0, format="%.2f")
    }
)
st.session_state.expenses = edited_expenses_df.to_dict('records')

st.divider()

# ----------------- REAL-TIME TOTALS & RECONCILIATION -----------------
total_qty = edited_records_df["QTY"].sum() if not edited_records_df.empty and "QTY" in edited_records_df else 0
total_foc = edited_records_df["Free (FOC)"].sum() if not edited_records_df.empty and "Free (FOC)" in edited_records_df else 0
total_cash_collected = edited_records_df["Cash Collected"].sum() if not edited_records_df.empty and "Cash Collected" in edited_records_df else 0.0
total_credit_sales = edited_records_df["Credit Sales"].sum() if not edited_records_df.empty and "Credit Sales" in edited_records_df else 0.0

total_expenses = edited_expenses_df["Amount"].sum() if not edited_expenses_df.empty and "Amount" in edited_expenses_df else 0.0
net_cash_in_hand = total_cash_collected - total_expenses

st.subheader("3. Daily Financial Summary")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total QTY Sold", f"{int(total_qty)}")
m2.metric("Total FOC Given", f"{int(total_foc)}")
m3.metric("Total Credit (Debit)", f"Rs. {total_credit_sales:,.2f}")
m4.metric("Gross Cash Collected", f"Rs. {total_cash_collected:,.2f}")
m5.metric("Net Cash in Hand", f"Rs. {net_cash_in_hand:,.2f}", delta=f"Less Rs. {total_expenses:,.2f} exp")

st.divider()

# ----------------- 4. FINAL SUBMIT SECTION -----------------
st.subheader("4. Final Verification & Submission")
st.write(f"Clicking final submit will lock reference **{st.session_state.reference_no}** and send the report to **{report_email}**.")

col_sub1, col_sub2 = st.columns([2, 1])

with col_sub1:
    if st.button("🚀 Final Submit & Email Report", type="primary", use_container_width=True):
        email_subject = f"[{st.session_state.reference_no}] Daily Report - {mr_name} - Miti: {miti_bs}"
        
        # HTML formatting matches company letterhead
        html_report = f"""
        <div style="font-family: Arial, sans-serif; font-size: 13px; color: #222;">
            <div style="text-align: center; border-bottom: 2px solid #1b5e20; padding-bottom: 8px;">
                <h2 style="color: #1b5e20; margin: 0;">ALPINE HERBS PVT. LTD.</h2>
                <p style="margin: 2px; color: #555;">Birgunj, Nepal | Daily Field Report</p>
            </div>

            <table style="width: 100%; border-collapse: collapse; margin-top: 15px; background-color: #f9f9f9;">
                <tr>
                    <td style="padding: 6px; border: 1px solid #ddd;"><strong>Ref Code:</strong> {st.session_state.reference_no}</td>
                    <td style="padding: 6px; border: 1px solid #ddd;"><strong>Date (Miti B.S.):</strong> {miti_bs}</td>
                    <td style="padding: 6px; border: 1px solid #ddd;"><strong>Date (A.D.):</strong> {date_ad}</td>
                </tr>
                <tr>
                    <td style="padding: 6px; border: 1px solid #ddd;"><strong>MR Name:</strong> {mr_name}</td>
                    <td style="padding: 6px; border: 1px solid #ddd;"><strong>Address:</strong> {mr_address}</td>
                    <td style="padding: 6px; border: 1px solid #ddd;"><strong>Location:</strong> {tour_route}</td>
                </tr>
                <tr>
                    <td colspan="3" style="padding: 6px; border: 1px solid #ddd;"><strong>Verified By:</strong> {verifier_name}</td>
                </tr>
            </table>

            <h3 style="color: #1b5e20; margin-top: 20px;">Financial Ledger Reconciliation</h3>
            <table style="width: 60%; border-collapse: collapse; margin-bottom: 15px;">
                <tr style="background-color: #f2f2f2;">
                    <td style="padding: 6px; border: 1px solid #ddd;">Total Credit Sales (Debit to Parties)</td>
                    <td style="padding: 6px; border: 1px solid #ddd; text-align: right;"><strong>Rs. {total_credit_sales:,.2f}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 6px; border: 1px solid #ddd;">Total Cash Collected</td>
                    <td style="padding: 6px; border: 1px solid #ddd; text-align: right; color: green;"><strong>Rs. {total_cash_collected:,.2f}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 6px; border: 1px solid #ddd;">Less: Field Expenses & Remittances</td>
                    <td style="padding: 6px; border: 1px solid #ddd; text-align: right; color: red;">- Rs. {total_expenses:,.2f}</td>
                </tr>
                <tr style="background-color: #d4edda;">
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>CLOSING CASH TO DEPOSIT / HANDOVER</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: right;"><strong>Rs. {net_cash_in_hand:,.2f}</strong></td>
                </tr>
            </table>

            <h4>1. Sales & Cash Collection Breakdown</h4>
            {edited_records_df.to_html(index=False)}

            <h4>2. Field Expenses (Nasta, Fuel, Advance, eSewa)</h4>
            {edited_expenses_df.to_html(index=False)}

            <br/>
            <p style="font-size: 11px; color: #888;">Generated automatically via Alpine Herbs Field AI Agent. Unique System Tag: {st.session_state.reference_no}</p>
        </div>
        """
        
        with st.spinner("Submitting final report and sending email..."):
            success, msg = send_eod_email(email_subject, html_report)
            if success:
                st.balloons()
                st.success(f"Report `{st.session_state.reference_no}` verified and sent to {report_email}!")
            else:
                st.error(f"Failed to send email: {msg}")

with col_sub2:
    # Download as CSV directly
    csv_export = edited_records_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV Ledger",
        data=csv_export,
        file_name=f"Daily_Report_{miti_bs}_{mr_name}.csv",
        mime='text/csv',
        use_container_width=True
    )
