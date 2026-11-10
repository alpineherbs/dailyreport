# --- 1. EXPANDED A-TO-Z MASTER CHEMIST DIRECTORY ---
MASTER_CLIENT_DB = [
    {"name": "Aarav Pharma", "code": "PAR-001", "area": "Birgunj", "dues": 4500},
    {"name": "Ashok Medical Hall", "code": "PAR-002", "area": "Naukatola", "dues": 12230},
    {"name": "Apex Health Care", "code": "BAR-004", "area": "Kalaiya", "dues": 3100},
    {"name": "Baba Medical Store", "code": "PAR-005", "area": "Birgunj", "dues": 8500},
    {"name": "Bara Pharma Distributors", "code": "BAR-007", "area": "Simara", "dues": 15400},
    {"name": "Birgunj Health Clinic", "code": "PAR-006", "area": "Birgunj", "dues": 9200},
    {"name": "City Medical Hall", "code": "PAR-008", "area": "Birgunj", "dues": 6700},
    {"name": "Care & Cure Pharmacy", "code": "BAR-009", "area": "Jeetpur", "dues": 4300},
    {"name": "Dev Medical", "code": "BAR-003", "area": "Kalaiya", "dues": 2030},
    {"name": "Durga Medical Store", "code": "PAR-010", "area": "Birgunj", "dues": 11500},
    {"name": "Everest Pharmacy", "code": "PAR-011", "area": "Pokhariya", "dues": 5200},
    {"name": "Friends Medical Hall", "code": "PAR-012", "area": "Birgunj", "dues": 3400},
    {"name": "Ganesh Srestha", "code": "PAR-015", "area": "Birgunj", "dues": 63390},
    {"name": "Gupta Medical Store", "code": "BAR-016", "area": "Kalaiya", "dues": 7800},
    {"name": "Himal Health Clinic", "code": "PAR-017", "area": "Naukatola", "dues": 4100},
    {"name": "Ideal Pharmacy", "code": "PAR-018", "area": "Birgunj", "dues": 6900},
    {"name": "Janta Medical Hall", "code": "BAR-019", "area": "Jeetpur", "dues": 8300},
    {"name": "Jeevan Raksha Clinic", "code": "PAR-020", "area": "Birgunj", "dues": 12800},
    {"name": "Kalaiya Medical Centre", "code": "BAR-021", "area": "Kalaiya", "dues": 9400},
    {"name": "Krishna Pharmacy", "code": "PAR-022", "area": "Langada Chouk", "dues": 14100},
    {"name": "Laxmi Medical Store", "code": "PAR-023", "area": "Birgunj", "dues": 18500},
    {"name": "Maa Durga Pharma", "code": "BAR-024", "area": "Simara", "dues": 6200},
    {"name": "Mahir Health Clinic", "code": "BAR-002", "area": "Jeetpur", "dues": 7105},
    {"name": "Naresh Medical", "code": "BAR-001", "area": "Kalaiya", "dues": 3070},
    {"name": "Nepal Health Care", "code": "PAR-025", "area": "Birgunj", "dues": 21400},
    {"name": "Om Sai Medical", "code": "PAR-026", "area": "Birgunj", "dues": 5600},
    {"name": "Parsa Medical Store", "code": "PAR-027", "area": "Birgunj", "dues": 33200},
    {"name": "Prakash Pharmacy", "code": "BAR-028", "area": "Kalaiya", "dues": 4800},
    {"name": "Quality Health Pharma", "code": "PAR-029", "area": "Birgunj", "dues": 11300},
    {"name": "Radhey Medical", "code": "BAR-033", "area": "Simara", "dues": 7500},
    {"name": "Roshan Pharmacy", "code": "PAR-032", "area": "Birgunj", "dues": 74290},
    {"name": "Sandip Medical Hall", "code": "PAR-035", "area": "Langada Chouk", "dues": 30195},
    {"name": "Shiva Medical Store", "code": "PAR-036", "area": "Pokhariya", "dues": 8900},
    {"name": "Tirupati Medical Hall", "code": "PAR-037", "area": "Naukatola", "dues": 6400},
    {"name": "Universal Health Clinic", "code": "PAR-038", "area": "Birgunj", "dues": 15700},
    {"name": "Verma Medical Store", "code": "BAR-039", "area": "Jeetpur", "dues": 9100},
    {"name": "Welfare Pharmacy", "code": "PAR-040", "area": "Birgunj", "dues": 4600},
    {"name": "Yadav Medical Hall", "code": "BAR-041", "area": "Kalaiya", "dues": 11200},
    {"name": "Zenith Health Care", "code": "PAR-042", "area": "Birgunj", "dues": 7300}
]

# --- 2. OPTIONAL LIVE GOOGLE SHEETS SYNC FOR CLIENTS ---
SHEET_ID = "1cpPYFS9EkajB5tGfMnReIJ71cmB5djz6oaMvvEoqs6A"

@st.cache_data(ttl=120)
def load_live_clients():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Clients"
        df = pd.read_csv(url, dtype=str)
        if not df.empty and "name" in [c.lower() for c in df.columns]:
            df.columns = [c.strip().lower() for c in df.columns]
            live_list = []
            for _, r in df.iterrows():
                if pd.notna(r.get("name")):
                    live_list.append({
                        "name": str(r.get("name")).strip(),
                        "code": str(r.get("code", "PAR-999")).strip().upper(),
                        "area": str(r.get("area", "Birgunj")).strip(),
                        "dues": float(r.get("dues", 0.0) or 0.0)
                    })
            if live_list:
                return live_list
    except Exception:
        pass
    return MASTER_CLIENT_DB

if "client_db" not in st.session_state:
    st.session_state["client_db"] = load_live_clients()

if "form_id" not in st.session_state:
    st.session_state["form_id"] = 0

# --- 3. SMART CLIENT RESOLVER ---
def resolve_client(raw_val, default_area="Birgunj"):
    s = clean_str(raw_val)
    if not s or s.lower() == "other / walk-in":
        return "Walk-in Party", "WALK-IN", default_area

    # If formatted as: "Naresh Medical  [BAR-001] — 📍 Kalaiya"
    if "— 📍" in s:
        s = s.split("— 📍")[0].strip()

    if "[" in s and s.endswith("]"):
        parts = s.rsplit("[", 1)
        cname = parts[0].strip()
        ccode = parts[1].replace("]", "").strip()
        for item in st.session_state["client_db"]:
            if item["code"].lower() == ccode.lower():
                return cname, ccode, item.get("area", default_area)
        return cname, ccode, default_area

    # Fallback exact or partial name match
    for item in st.session_state["client_db"]:
        if item["name"].lower() == s.lower():
            return item["name"], item["code"], item.get("area", default_area)

    return s, "WALK-IN", default_area
