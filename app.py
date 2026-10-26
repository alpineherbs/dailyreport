# =========================================================
    # COMPACT FINANCIAL CLOSING SUMMARY
    # =========================================================
    st.divider()
    st.markdown("##### 📊 Financial Closing Summary")

    st.markdown("""
    <style>
    .compact-metric-container {
        display: flex;
        gap: 10px;
        margin-bottom: 15px;
    }
    .compact-metric-card {
        background: #EAF2EC;
        border: 1px solid #C8DCCF;
        border-top: 3px solid #2D7D52;
        padding: 8px 12px;
        border-radius: 6px;
        flex: 1;
        text-align: left;
    }
    .compact-label {
        font-size: 0.68rem;
        font-weight: 700;
        color: #164E33;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .compact-value {
        font-size: 0.95rem;
        font-weight: 700;
        color: #0D2818;
        margin-top: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Row 1: Sales & Collections
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

    # Row 2: Deductions & Net Closing
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
