import streamlit as st, pandas as pd, requests, uuid, math
from datetime import date, datetime
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="ALPINE HERBS - Daily Field Closing", page_icon="🌿", layout="wide")

USERS = {
    "Alpine": "AHP@123",
    "Pritam": "Pritam@2024",
    "Admin": "AlpineAdmin@123",
    "Manager": "Alpine@Birgunj"
}

# Silent backend endpoint (No UI exposure)
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzorFkbj5in7NdNAsh_zvSPMZSzM1HmzVTCnoCCUQ_85izF9C1GrC1BB00WvLiRwri5/exec"

CLIENT_DB = [
    {"name": "Naresh Medical", "code": "BAR-001", "area": "Kalaiya", "dues": 3070},
    {"name": "Mahir Health Clinic", "code": "BAR-002", "area": "Jeetpur", "dues": 7105},
    {"name": "Dev Medical", "code": "BAR-003", "area": "Kalaiya", "dues": 2030},
    {"name": "Ashok Medical Hall", "code": "PAR-002", "area": "Naukatola", "dues": 12230},
    {"name": "Ganesh Srestha", "code": "PAR-015", "area": "Birgunj", "dues": 63390},
    {"name": "Roshan Pharmacy", "code": "PAR-032", "area": "Birgunj", "dues": 74290},
    {"name": "Sandip Medical Hall", "code": "PAR-035", "area": "Langada Chouk", "dues": 30195}
]

def clean_str(val, default=""):
    if pd.isna(val) or val is None: return default
    s = str(val).strip()
