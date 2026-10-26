import requests

WEB_APP_URL = "YOUR_COPIED_GOOGLE_APPS_SCRIPT_WEB_APP_URL_HERE"

def push_sales_to_google_sheet(sales_df, staff_name_val, report_ref, date_val):
    success_count = 0
    for _, row in sales_df.iterrows():
        c_name = str(row.get("Client / Party Name", "")).strip()
        if c_name:
            payload = {
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
                response = requests.post(WEB_APP_URL, json=payload, timeout=10)
                if response.status_code == 200:
                    success_count += 1
            except Exception as e:
                print(f"Sync error: {e}")
    return success_count
