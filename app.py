import streamlit as st
import pandas as pd
from datetime import date, datetime
from io import BytesIO
from email.message import EmailMessage
import smtplib
import uuid

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# =========================================================
# CONFIGURATION & BRAND THEMING
# =========================================================

st.set_page_config(
    page_title="ALPINE HERBS | Daily Field Report",
    page_icon="🌿",
    layout="wide"
)

EMAIL_TO = st.secrets.get("smtp_to", "Alpineherbsinfo@gmail.com")

# Default 8-Digit App Passcode (Can be overridden in Streamlit Secrets: app_passcode = "87654321")
REQUIRED_APP_PASSCODE = str(st.secrets.get("app_passcode", "12345678"))

# Clean CSS with exact Alpine brand colors
st.markdown("""
<style>
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1550px;
}
.brand-header {
    background: linear-gradient(135deg, #0D2818 0%, #164E33 100%);
    color: white;
    padding: 1.2rem 1.8rem;
    border-radius: 10px;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 12px rgba(13, 40, 24, 0.12);
}
.brand-title {
    font-size: 1.7rem;
    font-weight: 800;
    letter-spacing: 0.5px;
    margin: 0;
    color: #FFFFFF;
}
.brand-sub {
    font-size: 0.85rem;
    color: #D3E6DA;
    margin: 0.2rem 0 0 0;
    letter-spacing: 1px;
    font-weight: 500;
}
h3, h2, h1 {
    color: #164E33 !important;
    font-weight: 700;
}
div[data-testid="stMetric"] {
    background: #EAF2EC !important;
    border: 1px solid #C8DCCF !important;
    border-top: 4px solid #2D7D52 !important;
    padding: 10px 14px !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
div[data-testid="stMetricLabel"] {
    font-size: 0.76rem !important;
    font-weight: 600 !important;
    color: #164E33 !important;
    text-transform: uppercase;
}
div[data-testid="stMetricValue"] {
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    color: #0D2818 !important;
}
div.stButton > button[kind="primary"] {
    background: linear-gradient(180deg, #164E33 0%, #0D2818 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px;
    padding: 0.55rem 1.2rem;
    border-radius: 6px;
    box-shadow: 0 2px 6px rgba(22, 78, 51, 0.25);
}
div.stButton > button[kind="primary"]:hover {
    background: #2D7D52 !important;
    box-shadow: 0 4px 10px rgba(45, 125, 82, 0.35);
}
</style>
""", unsafe_allow_html=True)

# App Banner
st.markdown("""
<div class="brand-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div class="brand-title">🌿 ALPINE HERBS PVT. LTD.</div>
            <div class="brand-sub">BIRGUNJ, NEPAL &nbsp;|&nbsp; MEDICAL REPRESENTATIVE DAILY FIELD CLOSING</div>
        </div>
        <div style="text-align: right; font-size: 0.8rem; color: #E0EFE5; line-height: 1.4;">
            <div><strong>ISO GMP Standard</strong></div>
            <div>Field Operations Portal</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
