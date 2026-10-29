import streamlit as st, pandas as pd, requests, uuid, math
from datetime import date, datetime
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="ALPINE HERBS - Daily Field Closing", page_icon="🌿", layout="wide")

USERS = {"Alpine": "AHP@123", "Pritam": "Pritam@2024", "Admin": "AlpineAdmin@123", "Manager": "Alpine@Birgunj"}
DEFAULT_WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzqcy8A442WqYY8gFjPRojpLeDZw3GhQnyo7Y8PadW6vZ1YW2QvkIceFqxkZuo8166R/exec"

CLIENT_DB = [
    {"name": "Naresh Medical", "code": "BAR-001", "area": "Kalaiya", "dues": 3070},
    {"name": "Mahir Health Clinic", "code": "BAR-002", "area": "Jeetpur", "dues": 7105},
    {"name": "Dev Medical", "code": "BAR-003", "area": "Kalaiya", "dues": 2030},
    {"name": "Ashok Medical Hall", "code": "PAR-002", "area": "Naukatola", "dues": 12230},
    {"name": "Ganesh Srestha", "code": "PAR-015", "area": "Birgunj", "dues": 63390},
    {"name": "Roshan Pharmacy", "code": "PAR-032", "area": "Birgunj", "dues": 74290},
    {"name": "Sandip Medical Hall", "code": "PAR-035", "area": "Langada Chouk", "dues": 30195}
]

# DATA SANITIZERS (PREVENTS "NAN" FROM EVER APPEARING IN GOOGLE SHEETS)
def clean_str(val, default=""):
    if pd.isna(val) or val is None: return default
    s = str(val).strip()
    return default if s.lower() in ("nan", "none", "null", "undefined", "") else s

def clean_num(val, default=0.0):
    if pd.isna(val) or val is None: return default
    try:
        v = float(val)
        return default if math.isnan(v) or math.isinf(v) else v
    except: return default

money = lambda v: f"Rs. {clean_num(v):,.2f}"

st.markdown("""<style>
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1rem; max-width: 1520px; }
input::placeholder { color: #8FA698 !important; opacity: 1 !important; }
.g-box { background: #F4FAF6; border: 1.5px solid #2D7D52; border-radius: 8px; padding: 12px; height: 100%; }
.g-acc { background: #E7F5ED; border: 2px solid #164E33; border-radius: 8px; padding: 12px; height: 100%; }
.s-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dashed #C8DEC2; font-size: 0.9rem; }
.s-val { font-weight: 700; color: #0D2818; }
.user-card { background: #EAF5EE; border-left: 4px solid #164E33; padding: 10px; border-radius: 4px; margin-bottom: 12px; }
.b-nav { background: linear-gradient(135deg, #0D2818, #164E33); padding: 12px 18px; border-radius: 8px; color: white; display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
</style>""", unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user"] = ""

if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align:center; color:#0D2818; margin-top:2rem;'>🌿 ALPINE HERBS PVT. LTD.</h2><p style='text-align:center; color:#2D7D52; font-weight:600;'>FIELD CLOSING PORTAL</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.1, 1])
    with c2:
        with st.container(border=True):
            st.markdown("##### 🔐 Staff Sign In")
            u = st.text_input("Username", placeholder="Username", label_visibility="collapsed")
            p = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
            st.write("")
            if st.button("🔑 Sign In to Portal", type="primary", use_container_width=True):
                if u.strip() in USERS and USERS[u.strip()] == p.strip():
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = u.strip()
                    st.rerun()
                else: st.error("❌ Invalid Username or Password.")
    st.stop()

cur_user = st.session_state.get("user", "Staff")

if "rep_no" not in st.session_state:
    st.session_state["rep_no"] = f"ALP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

with st.sidebar:
    st.markdown("### 👤 User Session")
    st.markdown(f"""<div class="user-card">
    <b>Officer:</b> {cur_user}<br>
    <b>Branch:</b> Birgunj, Nepal<br>
    <b>Status:</b> 🟢 Active Online<br>
    <b>Ref No:</b> <code>{st.session_state['rep_no']}</code>
    </div>""", unsafe_allow_html=True)

    if st.button("🔒 Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["user"] = ""
        st.rerun()

    st.divider()
    st.markdown("### 🔗 Google Sheet Connection")
    webhook_url = st.text_input("Webhook URL", value=st.session_state.get("custom_url", DEFAULT_WEB_APP_URL))
    st.session_state["custom_url"] = webhook_url.strip()

    if st.button("🧪 Test Connection", use_container_width=True):
        try:
            t_res = requests.get(webhook_url.strip(), timeout=10, allow_redirects=True)
            if "accounts.google.com" in t_res.text:
                st.error("❌ Auth Error: Google is asking for login. Set 'Who has access' to 'Anyone' in Apps Script.")
            elif t_res.status_code == 200:
                st.success("🟢 Connected! Google Sheet is active.")
            else:
                st.error(f"HTTP {t_res.status_code}")
        except Exception as e:
            st.error(f"Sync Connection Error: {e}")

    st.divider()
    st.markdown("### 📋 Client Dues Lookup")
    sq = st.text_input("Search Chemist / Town", placeholder="e.g. Naresh, Kalaiya").strip().lower()
    matches = [c for c in CLIENT_DB if sq in c['name'].lower() or sq in c['area'].lower()] if sq else CLIENT_DB
    for item in matches[:6]:
        st.markdown(f"**{item['name']}** (`{item['code']}`)\n{item['area']} | Due: **Rs. {item['dues']:,}**")
        st.write("---")

INIT_SALES = pd.DataFrame([
    {"Invoice No.": "INV-01", "Client Name": "", "Address": "Birgunj", "Product Name": "", "Qty": 0.0, "Rate (Rs.)": 0.0, "Cash Recd (Rs.)": 0.0, "Credit Given (Rs.)": 0.0},
    {"Invoice No.": "INV-02", "Client Name": "", "Address": "Birgunj", "Product Name": "", "Qty": 0.0, "Rate (Rs.)": 0.0, "Cash Recd (Rs.)": 0.0, "Credit Given (Rs.)": 0.0},
    {"Invoice No.": "INV-03", "Client Name": "", "Address": "Birgunj", "Product Name": "", "Qty": 0.0, "Rate (Rs.)": 0.0, "Cash Recd (Rs.)": 0.0, "Credit Given (Rs.)": 0.0}
])
INIT_OFFICE = pd.DataFrame([{"Details": "", "Paid To": "Vendor", "Mode": "Cash", "Amount (Rs.)": 0.0, "Remarks": ""}])
INIT_STAFF = pd.DataFrame([{"Staff Name": "", "Purpose": "Tour Advance", "Category": "Staff Advance", "Amount (Rs.)": 0.0, "Remarks": ""}])

st.markdown(f"""<div class="b-nav">
<div><span style="font-size:1.5rem; font-weight:800;">🌿 ALPINE HERBS PVT. LTD.</span><br><span style="font-size:0.8rem; color:#D5EBDD;">BIRGUNJ, NEPAL | DAILY TOUR CLOSING</span></div>
<div style="text-align:right; font-size:0.82rem;">Officer: <b>{cur_user}</b> | ISO GMP Standard</div></div>""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns([1.2, 1.4, 1.4, 1.2])
with c1: rep_date = st.date_input("Date (A.D.)", value=date.today())
with c2: mr_name = st.text_input("MR Name", value=cur_user if cur_user != "Alpine" else "Pritam Gupta")
with c3: route_name = st.text_input("Route / Territory", placeholder="e.g. Birgunj - Kalaiya - Simara")
with c4: st.text_input("Report Ref", value=st.session_state["rep_no"], disabled=True)

t1, t2, t3 = st.tabs(["🛒 1. Sales & Credit Ledger", "🏢 2. Operating Expenses", "👥 3. Staff Advances"])
with t1:
    st.caption("Press Tab to jump across cells, Enter to move down. Empty rows are automatically ignored.")
    ed_s = st.data_editor(INIT_SALES, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_s")
with t2:
    st.caption("Record route fuel, food, logistics, and local operational costs.")
    ed_o = st.data_editor(INIT_OFFICE, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_o")
with t3:
    st.caption("Record field allowances, per-diem, and tour advances given to personnel.")
    ed_st = st.data_editor(INIT_STAFF, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_st")

# CLEAN NUMERIC CALCULATIONS
s_qty = ed_s["Qty"].apply(clean_num)
s_rate = ed_s["Rate (Rs.)"].apply(clean_num)
s_cash = ed_s["Cash Recd (Rs.)"].apply(clean_num)
s_c_man = ed_s["Credit Given (Rs.)"].apply(clean_num)

s_bill = s_qty * s_rate
s_cred = s_c_man.where(s_c_man > 0, (s_bill - s_cash).clip(lower=0.0))
s_tot = s_bill.where(s_bill > 0, s_cash + s_cred)

tot_sales, tot_cash, tot_credit = float(s_tot.sum()), float(s_cash.sum()), float(s_cred.sum())
tot_exp = float(ed_o["Amount (Rs.)"].apply(clean_num).sum())
tot_adv = float(ed_st["Amount (Rs.)"].apply(clean_num).sum())
tot_disbursed = tot_exp + tot_adv
net_cash = tot_cash - tot_disbursed

with t1:
    st.info(f"📋 Live Sales Breakdown: Billed: {money(tot_sales)} | Cash Recd: {money(tot_cash)} | Credit Given (Udharo): {money(tot_credit)}")

# GREEN SUMMARY BOXES (AT THE BOTTOM)
st.markdown("### 📊 Financial Closing Summary")
sb1, sb2, sb3 = st.columns(3)
with sb1:
    st.markdown(f"""<div class="g-box"><b style="color:#164E33; text-transform:uppercase;">🛒 1. Sales & Revenue Position</b>
    <div class="s-row"><span>Total Gross Billed:</span><span class="s-val">{money(tot_sales)}</span></div>
    <div class="s-row"><span>Cash Collected:</span><span class="s-val" style="color:#164E33;">{money(tot_cash)}</span></div>
    <div class="s-row" style="border:none;"><span>Credit Given:</span><span class="s-val" style="color:#A04000;">{money(tot_credit)}</span></div></div>""", unsafe_allow_html=True)
with sb2:
    st.markdown(f"""<div class="g-box"><b style="color:#164E33; text-transform:uppercase;">🏢 2. Route Disbursements</b>
    <div class="s-row"><span>Operating Expenses:</span><span class="s-val">{money(tot_exp)}</span></div>
    <div class="s-row"><span>Staff Advances:</span><span class="s-val">{money(tot_adv)}</span></div>
    <div class="s-row" style="border:none;"><span>Total Outflow:</span><span class="s-val" style="color:#800000;">{money(tot_disbursed)}</span></div></div>""", unsafe_allow_html=True)
with sb3:
    col_net = "#0D2818" if net_cash >= 0 else "#900C3F"
    st.markdown(f"""<div class="g-acc"><b style="color:#0D2818; text-transform:uppercase;">💰 3. Final Cash Settlement</b>
    <div class="s-row"><span>Cash Collected:</span><span class="s-val">{money(tot_cash)}</span></div>
    <div class="s-row"><span>Less Outflow:</span><span class="s-val">- {money(tot_disbursed)}</span></div>
    <div style="margin-top:6px; display:flex; justify-content:space-between; align-items:center;">
    <span style="font-weight:800;">NET IN HAND:</span><span style="font-weight:800; font-size:1.25rem; color:{col_net};">{money(net_cash)}</span></div></div>""", unsafe_allow_html=True)

if net_cash < 0: st.warning("⚠️ Warning: Disbursements exceed cash collected. Net Cash is negative.")

# GOOGLE SHEET SYNC WITH ZERO "NAN" TRANSMISSION
def sync_to_sheets():
    target_url = st.session_state.get("custom_url", DEFAULT_WEB_APP_URL).strip()
    s_items = []
    for _, r in ed_s.iterrows():
        cname = clean_str(r.get("Client Name"))
        pname = clean_str(r.get("Product Name"))
        addr = clean_str(r.get("Address"), "Birgunj")
        inv = clean_str(r.get("Invoice No."), "INV-01")
        q = clean_num(r.get("Qty"))
        rt = clean_num(r.get("Rate (Rs.)"))
        c = clean_num(r.get("Cash Recd (Rs.)"))
        cm = clean_num(r.get("Credit Given (Rs.)"))
        tb = q * rt
        cb = cm if cm > 0 else max(0.0, tb - c)
        if tb == 0 and (c > 0 or cb > 0): tb = c + cb

        # ONLY SYNC IF USER ACTUALLY ENTERED DATA (SKIPS UNUSED ROWS)
        if cname or pname or q > 0 or c > 0 or cb > 0:
            s_items.append({
                "invoice": inv, "client_name": cname or "Walk-in Party",
                "address": addr, "product_name": pname or "General Stock",
                "qty": q, "rate": rt, "cash_collected": c,
                "credit_given": cb, "total_sale": tb
            })

    e_items = []
    for _, r in ed_o.iterrows():
        amt = clean_num(r.get("Amount (Rs.)"))
        det = clean_str(r.get("Details"))
        if amt > 0 or det:
            e_items.append({
                "details": det or "Route Expense",
                "paid_to": clean_str(r.get("Paid To"), "Vendor"),
                "mode": clean_str(r.get("Mode"), "Cash"),
                "amount": amt, "remarks": clean_str(r.get("Remarks"))
            })

    a_items = []
    for _, r in ed_st.iterrows():
        amt = clean_num(r.get("Amount (Rs.)"))
        staff = clean_str(r.get("Staff Name"))
        if amt > 0 or staff:
            a_items.append({
                "personnel_name": staff or "Staff",
                "purpose": clean_str(r.get("Purpose"), "Tour Advance"),
                "type": clean_str(r.get("Category"), "Staff Advance"),
                "amount": amt, "remarks": clean_str(r.get("Remarks"))
            })

    if not (s_items or e_items or a_items):
        st.warning("⚠️ No valid entries to sync. Please fill in records first.")
        return False, 0

    payload = {
        "date": str(rep_date), "report_no": str(st.session_state["rep_no"]),
        "staff_name": clean_str(mr_name, "MR Staff"), "sales": s_items,
        "expenses": e_items, "advances": a_items
    }

    try:
        res = requests.post(target_url, json=payload, timeout=25, allow_redirects=True)
        raw_text = res.text.strip()
        if "<!DOCTYPE html" in raw_text or "accounts.google.com" in raw_text:
            st.error("❌ Google Permission Error: Access restricted. Set 'Who has access' to 'Anyone' in Apps Script.")
            return False, 0
        try:
            data = res.json()
            if data.get("status") == "success":
                st.session_state["sync_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return True, data.get("records_synced", len(s_items) + len(e_items) + len(a_items))
            else:
                st.error(f"❌ Google Script Error: {data.get('message', raw_text)}")
                return False, 0
        except Exception:
            if "success" in raw_text.lower():
                return True, len(s_items) + len(e_items) + len(a_items)
            st.error(f"❌ Unexpected Google Response: {raw_text[:200]}")
            return False, 0
    except Exception as err:
        st.error(f"❌ Sync Connection Error: {err}")
        return False, 0

# MULTI-SECTION PDF BUILDER
def make_pdf():
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=10*mm, rightMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm)
    styles = getSampleStyleSheet()
    t_style = TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#164E33")), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('FONTSIZE', (0,0), (-1,-1), 8)])

    story = [
        Paragraph(f"<b>ALPINE HERBS PVT. LTD. - DAILY FIELD CLOSING VOUCHER</b>", styles["Heading1"]),
        Paragraph(f"<b>Ref:</b> {st.session_state['rep_no']} | <b>Date:</b> {rep_date} | <b>MR:</b> {mr_name} | <b>Route:</b> {route_name or 'Birgunj'}", styles["Normal"]),
        Spacer(1, 3*mm)
    ]
    s_rows = [["Inv #", "Client Name", "Address", "Product", "Qty", "Rate", "Cash Recd", "Credit Given", "Total"]]
    for _, r in ed_s.iterrows():
        cname, pname = clean_str(r.get("Client Name")), clean_str(r.get("Product Name"))
        q, rt, c, cm = clean_num(r.get("Qty")), clean_num(r.get("Rate (Rs.)")), clean_num(r.get("Cash Recd (Rs.)")), clean_num(r.get("Credit Given (Rs.)"))
        tb = q * rt; cb = cm if cm > 0 else max(0.0, tb - c)
        if tb == 0 and (c > 0 or cb > 0): tb = c + cb
        if cname or pname or q > 0 or c > 0 or cb > 0:
            s_rows.append([clean_str(r.get("Invoice No."), "INV-01"), cname or "Walk-in Party", clean_str(r.get("Address"), "Birgunj"), pname or "General Stock", str(q), money(rt), money(c), money(cb), money(tb)])
    if len(s_rows) > 1:
        story.append(Paragraph("<b>1. Sales & Credit Ledger</b>", styles["Heading2"]))
        t_s = Table(s_rows, colWidths=[20*mm, 52*mm, 26*mm, 52*mm, 15*mm, 27*mm, 27*mm, 27*mm, 27*mm], style=t_style)
        story.extend([t_s, Spacer(1, 3*mm)])

    e_rows = [["Details", "Paid To", "Mode", "Amount", "Remarks"]]
    for _, r in ed_o.iterrows():
        amt, det = clean_num(r.get("Amount (Rs.)")), clean_str(r.get("Details"))
        if amt > 0 or det:
            e_rows.append([det or "Route Expense", clean_str(r.get("Paid To"), "Vendor"), clean_str(r.get("Mode"), "Cash"), money(amt), clean_str(r.get("Remarks"))])
    if len(e_rows) > 1:
        story.append(Paragraph("<b>2. Operating Expenses</b>", styles["Heading2"]))
        t_e = Table(e_rows, colWidths=[90*mm, 55*mm, 35*mm, 35*mm, 58*mm], style=t_style)
        story.extend([t_e, Spacer(1, 3*mm)])

    a_rows = [["Staff Name", "Purpose", "Category", "Amount", "Remarks"]]
    for _, r in ed_st.iterrows():
        amt, staff = clean_num(r.get("Amount (Rs.)")), clean_str(r.get("Staff Name"))
        if amt > 0 or staff:
            a_rows.append([staff or "Staff", clean_str(r.get("Purpose"), "Tour Advance"), clean_str(r.get("Category"), "Staff Advance"), money(amt), clean_str(r.get("Remarks"))])
    if len(a_rows) > 1:
        story.append(Paragraph("<b>3. Staff Advances</b>", styles["Heading2"]))
        t_a = Table(a_rows, colWidths=[65*mm, 75*mm, 45*mm, 35*mm, 53*mm], style=t_style)
        story.extend([t_a, Spacer(1, 3*mm)])

    story.append(Paragraph("<b>4. Grand Total Reconciliation</b>", styles["Heading2"]))
    sum_rows = [["Total Sales", "Credit Issued", "Cash Collected", "Total Expenses", "Staff Advances", "NET CASH IN HAND"],
                [money(tot_sales), money(tot_credit), money(tot_cash), money(tot_exp), money(tot_adv), money(net_cash)]]
    t_sum = Table(sum_rows, colWidths=[46*mm]*6, style=[('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0D2818")), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#EAF5EE")), ('ALIGN', (0,0), (-1,-1), 'CENTER')])
    story.extend([t_sum, Spacer(1, 5*mm)])
    story.append(Table([["\n____________________", "\n____________________", "\n____________________"], ["Medical Representative", "Area Sales Manager", "Head Office Audit"]], colWidths=[91*mm]*3, style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    doc.build(story)
    return buf.getvalue()

st.write("")
b1, b2 = st.columns([3, 1])
with b1:
    if st.button("🚀 CONFIRM & SYNC REPORT TO MASTER", type="primary", use_container_width=True):
        with st.spinner("Syncing to Google Sheets..."):
            ok, count = sync_to_sheets()
            if ok:
                st.session_state["pdf"] = make_pdf()
                sync_t = st.session_state.get("sync_time", "")
                st.balloons()
                st.success(f"✅ Report `{st.session_state['rep_no']}` synced! ({count} clean records written to Google Sheets at {sync_t})")
with b2:
    if st.button("🔄 Reset / Start Blank", use_container_width=True):
        st.session_state["rep_no"] = f"ALP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        for k in ["ed_s", "ed_o", "ed_st", "pdf"]: st.session_state.pop(k, None)
        st.rerun()

if "pdf" in st.session_state:
    st.write("")
    st.download_button("⬇️ DOWNLOAD OFFICIAL SIGN-OFF PDF AUDIT VOUCHER", data=st.session_state["pdf"], file_name=f"{st.session_state['rep_no']}.pdf", mime="application/pdf", use_container_width=True)
