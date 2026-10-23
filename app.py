import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO

st.set_page_config(page_title="WENS Daily Report", page_icon="📊", layout="wide")

# ---------- Styling ----------
st.markdown("""
<style>
.block-container {padding-top: 1.1rem; padding-bottom: 1rem; max-width: 1600px;}
h1, h2, h3 {color: #17365D;}
div[data-testid="stMetric"] {
    background: #F3F7FA; border: 1px solid #D8E3EA;
    padding: 12px 14px; border-radius: 10px;
}
.small-note {color:#52616B; font-size:0.88rem;}
</style>
""", unsafe_allow_html=True)

st.title("WENS | Daily Sales, Cash & Client Ledger")
st.caption("Single-page daily report • Sales • FOC • Expenses • Cash closing • Client ledger")

# ---------- Helpers ----------
def money(value):
    try:
        return f"Rs. {float(value):,.2f}"
    except (ValueError, TypeError):
        return "Rs. 0.00"

def blank_sales():
    return pd.DataFrame([{
        "Client / Party Name": "",
        "Goods / Product Name": "",
        "Qty Sold": 0.0,
        "FOC Qty": 0.0,
        "Sale Rate (Rs.)": 0.0,
        "Cash Collected (Rs.)": 0.0,
        "Credit Given (Rs.)": 0.0,
        "Client Address": "",
        "Invoice / Ref. No.": "",
        "Remarks": "",
    }])

def blank_expenses():
    return pd.DataFrame([{
        "Expense Category": "Fuel / Travel",
        "Description / Purpose": "",
        "Staff Name (if advance)": "",
        "Amount (Rs.)": 0.0,
    }])

def blank_ledger():
    return pd.DataFrame([{
        "Date": date.today(),
        "Client / Party Name": "",
        "Goods / Reference": "",
        "Invoice No.": "",
        "Sale / Debit (Rs.)": 0.0,
        "Payment Received (Rs.)": 0.0,
        "Adjustment / Return (Rs.)": 0.0,
        "Client Address": "",
        "Remarks": "",
    }])

def to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8-sig")

if "sales_data" not in st.session_state:
    st.session_state.sales_data = blank_sales()
if "expense_data" not in st.session_state:
    st.session_state.expense_data = blank_expenses()
if "ledger_data" not in st.session_state:
    st.session_state.ledger_data = blank_ledger()

# ---------- Report header ----------
with st.container(border=True):
    c1, c2, c3, c4 = st.columns([1, 1.25, 1.25, 1])
    with c1:
        report_date = st.date_input("Report date", value=date.today())
    with c2:
        staff_name = st.text_input("MR / Staff name")
    with c3:
        route_area = st.text_input("Route / Area", placeholder="e.g. Birgunj to Lautan")
    with c4:
        report_no = st.text_input("Report number")

# ---------- Sales entry ----------
st.subheader("1. Sales details")
st.caption("Enter one row for each product supplied. Total sale is calculated automatically as quantity sold × sale rate. FOC quantity is tracked separately.")
sales = st.data_editor(
    st.session_state.sales_data,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    key="sales_editor",
    column_config={
        "Client / Party Name": st.column_config.TextColumn(required=False),
        "Goods / Product Name": st.column_config.TextColumn(required=False),
        "Qty Sold": st.column_config.NumberColumn(min_value=0, step=1, format="%.2f"),
        "FOC Qty": st.column_config.NumberColumn(min_value=0, step=1, format="%.2f"),
        "Sale Rate (Rs.)": st.column_config.NumberColumn(min_value=0, step=1, format="%.2f"),
        "Cash Collected (Rs.)": st.column_config.NumberColumn(min_value=0, step=1, format="%.2f"),
        "Credit Given (Rs.)": st.column_config.NumberColumn(min_value=0, step=1, format="%.2f"),
    },
)
sales = sales.copy()
for col in ["Qty Sold", "FOC Qty", "Sale Rate (Rs.)", "Cash Collected (Rs.)", "Credit Given (Rs.)"]:
    sales[col] = pd.to_numeric(sales[col], errors="coerce").fillna(0)
sales["Total Sale (Rs.)"] = sales["Qty Sold"] * sales["Sale Rate (Rs.)"]
st.session_state.sales_data = sales.drop(columns=["Total Sale (Rs.)"], errors="ignore")

total_sales = float(sales["Total Sale (Rs.)"].sum())
total_cash = float(sales["Cash Collected (Rs.)"].sum())
total_credit = float(sales["Credit Given (Rs.)"].sum())
total_foc = float(sales["FOC Qty"].sum())
sales_view = sales.copy()
sales_view.insert(0, "S.N.", range(1, len(sales_view) + 1))
st.dataframe(
    sales_view[["S.N.", "Client / Party Name", "Goods / Product Name", "Qty Sold", "FOC Qty",
                "Sale Rate (Rs.)", "Total Sale (Rs.)", "Cash Collected (Rs.)",
                "Credit Given (Rs.)", "Client Address", "Invoice / Ref. No.", "Remarks"]],
    use_container_width=True, hide_index=True
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total sales", money(total_sales))
m2.metric("Cash collected", money(total_cash))
m3.metric("Credit given", money(total_credit))
m4.metric("FOC quantity", f"{total_foc:,.2f}")

# ---------- Expenses and cash closing ----------
st.subheader("2. Expenses, staff advances & cash closing")
expense_categories = [
    "Fuel / Travel", "Staff Advance", "Loading / Unloading", "Maintenance",
    "Food / Refreshment", "Phone / Internet", "Office Expense", "Other"
]
expenses = st.data_editor(
    st.session_state.expense_data,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    key="expenses_editor",
    column_config={
        "Expense Category": st.column_config.SelectboxColumn(options=expense_categories, required=True),
        "Description / Purpose": st.column_config.TextColumn(),
        "Staff Name (if advance)": st.column_config.TextColumn(),
        "Amount (Rs.)": st.column_config.NumberColumn(min_value=0, step=100, format="%.2f"),
    },
)
expenses = expenses.copy()
expenses["Amount (Rs.)"] = pd.to_numeric(expenses["Amount (Rs.)"], errors="coerce").fillna(0)
st.session_state.expense_data = expenses
total_expenses = float(expenses["Amount (Rs.)"].sum())
net_cash = total_cash - total_expenses

e1, e2, e3 = st.columns(3)
e1.metric("Total expenses / advances", money(total_expenses))
e2.metric("Net cash remaining", money(net_cash))
e3.metric("Sales reconciliation difference", money(total_sales - total_cash - total_credit))

st.caption("Reconciliation assumes the cash and credit fields refer to the same day's sales. Collections against old dues should be recorded separately in the client ledger.")

# ---------- Client ledger ----------
st.subheader("3. Client ledger & outstanding balance")
st.caption("Use one row per invoice, payment or adjustment. A sale is a debit; later receipts reduce the balance. Keep client names spelled consistently.")
ledger = st.data_editor(
    st.session_state.ledger_data,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    key="ledger_editor",
    column_config={
        "Date": st.column_config.DateColumn(format="DD-MMM-YYYY"),
        "Client / Party Name": st.column_config.TextColumn(required=False),
        "Sale / Debit (Rs.)": st.column_config.NumberColumn(min_value=0, step=100, format="%.2f"),
        "Payment Received (Rs.)": st.column_config.NumberColumn(min_value=0, step=100, format="%.2f"),
        "Adjustment / Return (Rs.)": st.column_config.NumberColumn(min_value=0, step=100, format="%.2f"),
    },
)
ledger = ledger.copy()
for col in ["Sale / Debit (Rs.)", "Payment Received (Rs.)", "Adjustment / Return (Rs.)"]:
    ledger[col] = pd.to_numeric(ledger[col], errors="coerce").fillna(0)
ledger["Date"] = pd.to_datetime(ledger["Date"], errors="coerce")
ledger["Net Movement (Rs.)"] = ledger["Sale / Debit (Rs.)"] - ledger["Payment Received (Rs.)"] - ledger["Adjustment / Return (Rs.)"]
ledger["Client Outstanding (Rs.)"] = ledger.groupby("Client / Party Name", dropna=False)["Net Movement (Rs.)"].cumsum()
st.session_state.ledger_data = ledger.drop(columns=["Net Movement (Rs.)", "Client Outstanding (Rs.)"], errors="ignore")

ledger_view = ledger.copy()
ledger_view["Date"] = ledger_view["Date"].dt.strftime("%d-%b-%Y")
st.dataframe(ledger_view, use_container_width=True, hide_index=True)

valid_ledger = ledger[ledger["Client / Party Name"].fillna("").astype(str).str.strip() != ""]
if not valid_ledger.empty:
    client_summary = (
        valid_ledger.groupby("Client / Party Name", as_index=False)
        .agg(
            Total_Sales=("Sale / Debit (Rs.)", "sum"),
            Payments=("Payment Received (Rs.)", "sum"),
            Adjustments=("Adjustment / Return (Rs.)", "sum"),
        )
    )
    client_summary["Outstanding (Rs.)"] = client_summary["Total_Sales"] - client_summary["Payments"] - client_summary["Adjustments"]
    st.markdown("*Outstanding by client*")
    st.dataframe(client_summary.rename(columns={
        "Total_Sales": "Ledger sales (Rs.)",
        "Payments": "Payments received (Rs.)",
        "Adjustments": "Adjustments / returns (Rs.)",
    }), use_container_width=True, hide_index=True)

# ---------- Export ----------
st.subheader("4. Export today's report")
header_df = pd.DataFrame([{
    "Report Date": report_date.isoformat(),
    "MR / Staff Name": staff_name,
    "Route / Area": route_area,
    "Report No.": report_no,
    "Total Sales (Rs.)": total_sales,
    "Total Cash Collected (Rs.)": total_cash,
    "Total Credit Given (Rs.)": total_credit,
    "Total FOC Qty": total_foc,
    "Total Expenses / Advances (Rs.)": total_expenses,
    "Net Cash Remaining (Rs.)": net_cash,
}])

def make_excel():
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        header_df.to_excel(writer, sheet_name="Daily Summary", index=False)
        sales_view.to_excel(writer, sheet_name="Sales Details", index=False)
        expenses.to_excel(writer, sheet_name="Expenses", index=False)
        ledger_view.to_excel(writer, sheet_name="Client Ledger", index=False)
        if not valid_ledger.empty:
            client_summary.to_excel(writer, sheet_name="Outstanding by Client", index=False)
    return output.getvalue()

x1, x2 = st.columns(2)
with x1:
    st.download_button(
        "Download full report (Excel)",
        data=make_excel(),
        file_name=f"WENS_Daily_Report_{report_date.isoformat()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
with x2:
    st.download_button(
        "Download sales data (CSV)",
        data=to_csv_bytes(sales_view),
        file_name=f"WENS_Sales_{report_date.isoformat()}.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.markdown("---")
st.markdown(
    '<p class="small-note">Template note: this is a single-page Streamlit app. Data is held in the current Streamlit session; add a database (for example SQLite or PostgreSQL) before using it as a permanent multi-user accounting system. VAT, old-due collections, returns, and staff-advance settlement should follow your accountant’s approved process.</p>',
    unsafe_allow_html=True,
)
