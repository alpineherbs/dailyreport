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
                # Fallback lookup from database if code missing in string
                matched_c = next((c for c in client_pool if c["name"].lower() == c_name.lower()), {})
                c_code = matched_c.get("code", "PAR-000")

            tot_sale = qty * rate
            credit_given = max(0.0, tot_sale - cash_collected)

            st.session_state["sales_entries"].append({
                "client_code": c_code,  # <--- GUARANTEED CLIENT CODE (e.g., BAR-001)
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
