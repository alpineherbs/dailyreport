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
