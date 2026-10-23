import streamlit as st
import pandas as pd
from datetime import date, datetime
from io import BytesIO
from email.message import EmailMessage
import smtplib

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


# =========================================================
# CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="ALPINE HERBS | Daily Report",
    page_icon="🌿",
    layout="wide"
)

EMAIL_TO = "Alpineherbsinfo@gmail.com"

GREEN = "#234D3C"
LIGHT_GREEN = "#F3F7F3"
BORDER_GREEN = "#D8E4D9"


# =========================================================
# PROFESSIONAL DESIGN
# =========================================================

st.markdown(f"""
<style>
.block-container {{
    padding-top: 1rem;
    padding-bottom: 1.5rem;
    max-width: 1600px;
}}
h1, h2, h3 {{
    color: {GREEN};
}}
div[data-testid="stMetric"] {{
    background: {LIGHT_GREEN};
    border: 1px solid {BORDER_GREEN};
    padding: 7px 10px;
    border-radius: 8px;
}}
div[data-testid="stMetricLabel"] {{
    font-size: 0.76rem;
}}
div[data-testid="stMetricValue"] {{
    font-size: 1.05rem;
}}
div.stButton > button[kind="primary"] {{
    background-color: {GREEN};
    border-color: {GREEN};
    color: white;
    font-weight: bold;
}}
</style>
""", unsafe_allow_html=True)

st.title("🌿 ALPINE HERBS")
st.caption(
    "DAILY FIELD REPORT  |  SALES  |  EXPENSES  |  PERSONNEL  |  CASH CLOSING"
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def money(value):
    try:
        return f"Rs. {float(value or 0):,.2f}"
    except (TypeError, ValueError):
        return "Rs. 0.00"


def nepali_date(d):
    try:
        import nepali_datetime
        bs = nepali_datetime.date.from_datetime_date(d)
        return f"{bs.year:04d}-{bs.month:02d}-{bs.day:02d} BS"
    except Exception:
        return "Unavailable — install nepali-datetime"


def numeric_columns(df, columns):
    df = df.copy()
    for col in columns:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        ).fillna(0)
    return df


def blank_sales():
    return pd.DataFrame([{
        "Client / Party Name": "",
        "Goods / Product Name": "",
        "Qty": 0.0,
        "FOC Qty": 0.0,
        "Sale Rate (Rs.)": 0.0,
        "Cash Collected (Rs.)": 0.0,
        "Credit Given (Rs.)": 0.0,
        "Client Address": "",
        "Invoice No.": ""
    }])


def blank_office():
    return pd.DataFrame([{
        "Expense Details": "",
        "Paid To / Vendor": "",
        "Payment Mode": "Cash",
        "Amount (Rs.)": 0.0,
        "Remarks": ""
    }])


def blank_staff():
    return pd.DataFrame([{
        "Staff / Personnel Name": "",
        "Purpose / Details": "",
        "Payment Type": "Staff Advance",
        "Amount (Rs.)": 0.0,
        "Remarks": ""
    }])


def blank_ledger():
    return pd.DataFrame([{
        "Client / Party Name": "",
        "Reference": "",
        "Previous Due (Rs.)": 0.0,
        "New Credit (Rs.)": 0.0,
        "Payment Received (Rs.)": 0.0,
        "Returns / Adjustments (Rs.)": 0.0
    }])


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "sales": blank_sales(),
    "office": blank_office(),
    "staff": blank_staff(),
    "ledger": blank_ledger()
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy()


# =========================================================
# REPORT INFORMATION
# =========================================================

with st.container(border=True):
    st.subheader("Report Information")

    c1, c2, c3, c4 = st.columns([1, 1.2, 1.3, 1])

    with c1:
        report_date = st.date_input(
            "English Date",
            value=date.today()
        )
        st.caption(f"Miti: *{nepali_date(report_date)}*")

    with c2:
        staff_name = st.text_input("MR / Staff Name")

    with c3:
        route = st.text_input(
            "Route / Area",
            placeholder="Birgunj to Lautan"
        )

    with c4:
        report_no = st.text_input("Report Number")


# =========================================================
# 1. SALES ENTRIES
# =========================================================

st.subheader("1. Sales Entries")

st.caption(
    "Enter one row for each client-product transaction. "
    "Use the add-row control for additional entries."
)

sales = st.data_editor(
    st.session_state.sales,
    num_rows="dynamic",
    hide_index=True,
    use_container_width=True,
    key="sales_editor",
    column_config={
        "Client / Party Name":
            st.column_config.TextColumn("Client / Party Name"),
        "Goods / Product Name":
            st.column_config.TextColumn("Goods / Product Name"),
        "Qty":
            st.column_config.NumberColumn("Qty", min_value=0),
        "FOC Qty":
            st.column_config.NumberColumn("FOC Qty", min_value=0),
        "Sale Rate (Rs.)":
            st.column_config.NumberColumn(
                "Sale Rate (Rs.)", min_value=0
            ),
        "Cash Collected (Rs.)":
            st.column_config.NumberColumn(
                "Cash Collected (Rs.)", min_value=0
            ),
        "Credit Given (Rs.)":
            st.column_config.NumberColumn(
                "Credit Given (Rs.)", min_value=0
            ),
        "Client Address":
            st.column_config.TextColumn("Client Address"),
        "Invoice No.":
            st.column_config.TextColumn("Invoice No.")
    }
)

sales = numeric_columns(
    sales,
    [
        "Qty",
        "FOC Qty",
        "Sale Rate (Rs.)",
        "Cash Collected (Rs.)",
        "Credit Given (Rs.)"
    ]
)

sales["Total Sale (Rs.)"] = (
    sales["Qty"] * sales["Sale Rate (Rs.)"]
)

st.session_state.sales = sales.drop(
    columns=["Total Sale (Rs.)"], errors="ignore"
)

total_sales = float(sales["Total Sale (Rs.)"].sum())
total_cash = float(sales["Cash Collected (Rs.)"].sum())
total_credit = float(sales["Credit Given (Rs.)"].sum())
total_foc = float(sales["FOC Qty"].sum())


# Compact metrics
m1, m2, m3, m4 = st.columns([1, 1, 1, 0.75])

m1.metric("Total Sales", money(total_sales))
m2.metric("Cash Collected", money(total_cash))
m3.metric("Credit Given", money(total_credit))
m4.metric("FOC Qty", f"{total_foc:,.2f}")


# =========================================================
# 2. OFFICE EXPENSES
# =========================================================

st.subheader("2. Office Expenses")

st.caption(
    "Record fuel, travel, lodging, food, maintenance, "
    "loading/unloading, stationery and other operating costs."
)

office = st.data_editor(
    st.session_state.office,
    num_rows="dynamic",
    hide_index=True,
    use_container_width=True,
    key="office_editor",
    column_config={
        "Expense Details":
            st.column_config.TextColumn("Expense Details"),
        "Paid To / Vendor":
            st.column_config.TextColumn("Paid To / Vendor"),
        "Payment Mode":
            st.column_config.SelectboxColumn(
                "Payment Mode",
                options=[
                    "Cash",
                    "Bank Transfer",
                    "Digital Wallet",
                    "Credit"
                ]
            ),
        "Amount (Rs.)":
            st.column_config.NumberColumn(
                "Amount (Rs.)", min_value=0
            ),
        "Remarks":
            st.column_config.TextColumn("Remarks")
    }
)

office = numeric_columns(office, ["Amount (Rs.)"])
st.session_state.office = office

office_total = float(office["Amount (Rs.)"].sum())


# =========================================================
# 3. STAFF / PERSONNEL
# =========================================================

st.subheader("3. Staff / Personnel")

st.caption(
    "Staff advances, allowances, salaries and reimbursements "
    "are recorded separately from office expenses."
)

staff = st.data_editor(
    st.session_state.staff,
    num_rows="dynamic",
    hide_index=True,
    use_container_width=True,
    key="staff_editor",
    column_config={
        "Staff / Personnel Name":
            st.column_config.TextColumn("Staff / Personnel Name"),
        "Purpose / Details":
            st.column_config.TextColumn("Purpose / Details"),
        "Payment Type":
            st.column_config.SelectboxColumn(
                "Payment Type",
                options=[
                    "Staff Advance",
                    "Allowance",
                    "Salary",
                    "Reimbursement",
                    "Other"
                ]
            ),
        "Amount (Rs.)":
            st.column_config.NumberColumn(
                "Amount (Rs.)", min_value=0
            ),
        "Remarks":
            st.column_config.TextColumn("Remarks")
    }
)

staff = numeric_columns(staff, ["Amount (Rs.)"])
st.session_state.staff = staff

staff_total = float(staff["Amount (Rs.)"].sum())

total_expenses = office_total + staff_total

net_cash = total_cash - total_expenses

reconciliation = total_sales - total_cash - total_credit


# =========================================================
# OPTIONAL CLIENT LEDGER
# =========================================================

with st.expander("Client Ledger & Outstanding Balances"):

    st.caption(
        "Optional tracking for opening dues, new credit sales, "
        "payments and returns. Use consistent client names."
    )

    ledger = st.data_editor(
        st.session_state.ledger,
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        key="ledger_editor",
        column_config={
            "Client / Party Name":
                st.column_config.TextColumn("Client / Party Name"),
            "Reference":
                st.column_config.TextColumn("Reference"),
            "Previous Due (Rs.)":
                st.column_config.NumberColumn(min_value=0),
            "New Credit (Rs.)":
                st.column_config.NumberColumn(min_value=0),
            "Payment Received (Rs.)":
                st.column_config.NumberColumn(min_value=0),
            "Returns / Adjustments (Rs.)":
                st.column_config.NumberColumn(min_value=0)
        }
    )

    ledger = numeric_columns(
        ledger,
        [
            "Previous Due (Rs.)",
            "New Credit (Rs.)",
            "Payment Received (Rs.)",
            "Returns / Adjustments (Rs.)"
        ]
    )

    ledger["Outstanding (Rs.)"] = (
        ledger["Previous Due (Rs.)"]
        + ledger["New Credit (Rs.)"]
        - ledger["Payment Received (Rs.)"]
        - ledger["Returns / Adjustments (Rs.)"]
    )

    st.session_state.ledger = ledger.drop(
        columns=["Outstanding (Rs.)"], errors="ignore"
    )

    st.dataframe(
        ledger,
        use_container_width=True,
        hide_index=True
    )


# Calculate ledger total outside the expander as well
ledger = numeric_columns(
    st.session_state.ledger,
    [
        "Previous Due (Rs.)",
        "New Credit (Rs.)",
        "Payment Received (Rs.)",
        "Returns / Adjustments (Rs.)"
    ]
)

ledger["Outstanding (Rs.)"] = (
    ledger["Previous Due (Rs.)"]
    + ledger["New Credit (Rs.)"]
    - ledger["Payment Received (Rs.)"]
    - ledger["Returns / Adjustments (Rs.)"]
)

ledger_outstanding = float(
    ledger["Outstanding (Rs.)"].sum()
)


# =========================================================
# 4. FINAL REPORT SUMMARY
# =========================================================

st.subheader("4. Final Report Summary")

with st.container(border=True):

    a1, a2, a3 = st.columns(3)

    a1.metric("Total Sales", money(total_sales))
    a2.metric("Total Cash Collected", money(total_cash))
    a3.metric("Total Credit Given", money(total_credit))

    b1, b2, b3 = st.columns(3)

    b1.metric("Office Expenses", money(office_total))
    b2.metric("Personnel Payments", money(staff_total))
    b3.metric("Total Expenses", money(total_expenses))

    c1, c2, c3 = st.columns(3)

    c1.metric("NET CASH REMAINING", money(net_cash))
    c2.metric("Sales Reconciliation", money(reconciliation))
    c3.metric("Client Outstanding", money(ledger_outstanding))

st.caption(
    "Net cash remaining = cash collected entered above "
    "minus office expenses and personnel payments. "
    "The reconciliation assumes cash and credit correspond "
    "to today's sales, not collections against previous dues."
)


# =========================================================
# PDF TABLE HELPER
# =========================================================

def pdf_table(data, widths, font_size=7):

    table = Table(
        data,
        colWidths=widths,
        repeatRows=1,
        hAlign="LEFT"
    )

    table.setStyle(TableStyle([
        (
            "BACKGROUND",
            (0, 0), (-1, 0),
            colors.HexColor(GREEN)
        ),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        (
            "GRID",
            (0, 0), (-1, -1),
            0.4,
            colors.HexColor(BORDER_GREEN)
        ),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        (
            "ROWBACKGROUNDS",
            (0, 1), (-1, -1),
            [colors.white, colors.HexColor(LIGHT_GREEN)]
        )
    ]))

    return table


# =========================================================
# PDF GENERATION
# =========================================================

def create_pdf():

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=9 * mm,
        bottomMargin=9 * mm,
        title="ALPINE HERBS Daily Report"
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "AHtitle",
        parent=styles["Title"],
        fontSize=17,
        textColor=colors.HexColor(GREEN),
        alignment=1,
        spaceAfter=3
    )

    section_style = ParagraphStyle(
        "AHsection",
        parent=styles["Heading2"],
        fontSize=10,
        textColor=colors.HexColor(GREEN),
        spaceBefore=7,
        spaceAfter=4
    )

    story = [
        Paragraph("ALPINE HERBS", title_style),
        Paragraph(
            "DAILY FIELD REPORT",
            ParagraphStyle(
                "AHsubtitle",
                parent=styles["Normal"],
                alignment=1,
                fontSize=9,
                spaceAfter=8
            )
        )
    ]

    # Report details
    info = [
        [
            "English Date",
            report_date.strftime("%d-%b-%Y"),
            "Nepali Miti",
            nepali_date(report_date)
        ],
        [
            "MR / Staff",
            staff_name or "—",
            "Route / Area",
            route or "—"
        ],
        [
            "Report Number",
            report_no or "—",
            "Generated At",
            datetime.now().strftime("%d-%b-%Y %H:%M")
        ]
    ]

    info_table = Table(
        info,
        colWidths=[30*mm, 65*mm, 30*mm, 80*mm]
    )

    info_table.setStyle(TableStyle([
        (
            "BACKGROUND",
            (0, 0), (0, -1),
            colors.HexColor("#E7EFE8")
        ),
        (
            "BACKGROUND",
            (2, 0), (2, -1),
            colors.HexColor("#E7EFE8")
        ),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        (
            "GRID",
            (0, 0), (-1, -1),
            0.4,
            colors.HexColor(BORDER_GREEN)
        ),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5)
    ]))

    story.extend([
        info_table,
        Paragraph("1. SALES ENTRIES", section_style)
    ])

    # Sales table
    sales_data = [[
        "S.N.", "Client / Party", "Goods / Product", "Qty",
        "FOC", "Rate", "Total Sale", "Cash", "Credit",
        "Address", "Invoice"
    ]]

    for i, row in sales.reset_index(drop=True).iterrows():

        sales_data.append([
            str(i + 1),
            str(row["Client / Party Name"]),
            str(row["Goods / Product Name"]),
            f'{row["Qty"]:g}',
            f'{row["FOC Qty"]:g}',
            f'{row["Sale Rate (Rs.)"]:,.2f}',
            f'{row["Total Sale (Rs.)"]:,.2f}',
            f'{row["Cash Collected (Rs.)"]:,.2f}',
            f'{row["Credit Given (Rs.)"]:,.2f}',
            str(row["Client Address"]),
            str(row["Invoice No."])
        ])

    story.append(pdf_table(
        sales_data,
        [
            9*mm, 30*mm, 32*mm, 11*mm, 10*mm,
            17*mm, 20*mm, 18*mm, 18*mm, 39*mm, 18*mm
        ],
        6
    ))

    story.append(Paragraph("2. OFFICE EXPENSES", section_style))

    expense_data = [[
        "S.N.", "Expense Details", "Paid To / Vendor",
        "Payment Mode", "Amount (Rs.)", "Remarks"
    ]]

    for i, row in office.reset_index(drop=True).iterrows():

        expense_data.append([
            str(i + 1),
            str(row["Expense Details"]),
            str(row["Paid To / Vendor"]),
            str(row["Payment Mode"]),
            money(row["Amount (Rs.)"]),
            str(row["Remarks"])
        ])

    if len(expense_data) == 1:
        expense_data.append([
            "—", "No expenses entered", "—", "—", money(0), "—"
        ])

    story.append(pdf_table(
        expense_data,
        [10*mm, 60*mm, 45*mm, 28*mm, 28*mm, 55*mm],
        7
    ))

    story.append(Paragraph("3. STAFF / PERSONNEL", section_style))

    staff_data = [[
        "S.N.", "Staff Name", "Purpose / Details",
        "Payment Type", "Amount (Rs.)", "Remarks"
    ]]

    for i, row in staff.reset_index(drop=True).iterrows():

        staff_data.append([
            str(i + 1),
            str(row["Staff / Personnel Name"]),
            str(row["Purpose / Details"]),
            str(row["Payment Type"]),
            money(row["Amount (Rs.)"]),
            str(row["Remarks"])
        ])

    if len(staff_data) == 1:
        staff_data.append([
            "—", "No personnel payments entered",
            "—", "—", money(0), "—"
        ])

    story.append(pdf_table(
        staff_data,
        [10*mm, 45*mm, 60*mm, 32*mm, 28*mm, 50*mm],
        7
    ))

    story.append(Paragraph("4. FINAL REPORT SUMMARY", section_style))

    summary_data = [
        ["Summary", "Amount", "Summary", "Amount"],
        ["Total Sales", money(total_sales),
         "Total Cash Collected", money(total_cash)],
        ["Total Credit Given", money(total_credit),
         "Total FOC Quantity", f"{total_foc:,.2f}"],
        ["Office Expenses", money(office_total),
         "Personnel Payments", money(staff_total)],
        ["Total Expenses", money(total_expenses),
         "NET CASH REMAINING", money(net_cash)],
        ["Sales Reconciliation", money(reconciliation),
         "Client Outstanding", money(ledger_outstanding)]
    ]

    story.append(pdf_table(
        summary_data,
        [45*mm, 40*mm, 50*mm, 40*mm],
        8
    ))

    story.append(Spacer(1, 12))

    story.append(Paragraph(
        "Prepared by: ________"
        "&nbsp;&nbsp;&nbsp;&nbsp; Checked by: ________"
        "&nbsp;&nbsp;&nbsp;&nbsp; Approved by: ________",
        styles["Normal"]
    ))

    doc.build(story)

    return buffer.getvalue()


# =========================================================
# EMAIL PDF
# =========================================================

def email_pdf(pdf_bytes):

    try:

        # These values must be configured in Streamlit secrets.
        msg = EmailMessage()

        filename = (
            "ALPINE_HERBS_Daily_Report_"
            f"{report_date.strftime('%Y-%m-%d')}.pdf"
        )

        msg["Subject"] = (
            "ALPINE HERBS Daily Report - "
            f"{report_date.strftime('%Y-%m-%d')} - "
            f"{staff_name or 'Staff'}"
        )

        msg["From"] = st.secrets["smtp_from"]
        msg["To"] = EMAIL_TO

        msg.set_content(
            "Dear Alpine Herbs Team,\n\n"
            "Please find the attached daily field report.\n\n"
            f"English Date: {report_date}\n"
            f"Nepali Miti: {nepali_date(report_date)}\n"
            f"MR / Staff: {staff_name}\n"
            f"Route: {route}\n"
            f"Total Sales: {money(total_sales)}\n"
            f"Cash Collected: {money(total_cash)}\n"
            f"Credit Given: {money(total_credit)}\n"
            f"Net Cash Remaining: {money(net_cash)}\n\n"
            "Regards,\nALPINE HERBS"
        )

        msg.add_attachment(
            pdf_bytes,
            maintype="application",
            subtype="pdf",
            filename=filename
        )

        with smtplib.SMTP(
            st.secrets["smtp_host"],
            int(st.secrets["smtp_port"]),
            timeout=30
        ) as server:

            server.starttls()

            server.login(
                st.secrets["smtp_user"],
                st.secrets["smtp_password"]
            )

            server.send_message(msg)

        return True, f"PDF emailed to {EMAIL_TO}."

    except Exception as exc:

        return False, (
            "Email could not be sent. Check your SMTP settings. "
            f"Details: {exc}"
        )


# =========================================================
# 5. SUBMIT REPORT
# =========================================================

st.subheader("5. Submit Report")

st.write(
    "Generate the PDF, email it to Alpine Herbs, "
    "and download a copy to your device."
)

if st.button(
    "📧 SUBMIT REPORT & EMAIL PDF",
    type="primary",
    use_container_width=True
):

    pdf_bytes = create_pdf()

    filename = (
        "ALPINE_HERBS_Daily_Report_"
        f"{report_date.strftime('%Y-%m-%d')}.pdf"
    )

    st.session_state["report_pdf"] = pdf_bytes
    st.session_state["report_filename"] = filename

    with st.spinner("Sending PDF report..."):
        success, message = email_pdf(pdf_bytes)

    if success:
        st.success(message)
    else:
        st.error(message)
        st.info(
            "Your PDF is still available for download below."
        )


# =========================================================
# DOWNLOAD COPY TO DEVICE
# =========================================================

if "report_pdf" in st.session_state:

    st.download_button(
        "⬇️ DOWNLOAD PDF COPY",
        data=st.session_state["report_pdf"],
        file_name=st.session_state["report_filename"],
        mime="application/pdf",
        use_container_width=True
    )


# =========================================================
# OPTIONAL EXCEL EXPORT
# =========================================================

with st.expander("Download Excel copy"):

    excel_buffer = BytesIO()

    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl"
    ) as writer:

        sales.to_excel(
            writer, sheet_name="Sales", index=False
        )

        office.to_excel(
            writer, sheet_name="Office Expenses", index=False
        )

        staff.to_excel(
            writer, sheet_name="Personnel", index=False
        )

        ledger.to_excel(
            writer, sheet_name="Client Ledger", index=False
        )

        summary = pd.DataFrame([{
            "English Date": str(report_date),
            "Nepali Miti": nepali_date(report_date),
            "MR / Staff": staff_name,
            "Route / Area": route,
            "Report Number": report_no,
            "Total Sales": total_sales,
            "Total Cash Collected": total_cash,
            "Total Credit Given": total_credit,
            "Total FOC Qty": total_foc,
            "Office Expenses": office_total,
            "Personnel Payments": staff_total,
            "Total Expenses": total_expenses,
            "Net Cash Remaining": net_cash,
            "Sales Reconciliation": reconciliation,
            "Client Outstanding": ledger_outstanding
        }])

        summary.to_excel(
            writer, sheet_name="Daily Summary", index=False
        )

    st.download_button(
        "⬇️ DOWNLOAD EXCEL COPY",
        data=excel_buffer.getvalue(),
        file_name=(
            f"ALPINE_HERBS_Report_{report_date}.xlsx"
        ),
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        use_container_width=True
    )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "ALPINE HERBS | Daily Reporting System. "
    "Reports are generated as PDF and Excel files. "
    "Permanent storage requires a database or connected storage service. "
    "Email submission requires valid SMTP credentials in Streamlit secrets."
)
