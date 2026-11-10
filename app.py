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
            # BULLETPROOF CLIENT CODE & NAME EXTRACTION
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
                "client_code": c_code,  # Guarantees code like BAR-001 is sent to Sheet
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
