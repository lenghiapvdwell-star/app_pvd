import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import time
import plotly.express as px
import os

# --- 1. CONFIGURATION & STYLE ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 1rem;}
    .main-title {
        color: #007BFF !important; 
        font-size: 39px !important; 
        font-weight: bold !important;
        text-align: center !important; 
        margin-bottom: 20px !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO ---
def display_main_logo():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        logo_path = os.path.join(current_dir, f"logo_pvd{ext}")
        if os.path.exists(logo_path):
            col1, col2, col3 = st.columns([4, 2, 4])
            with col2: st.image(logo_path, use_container_width=True)
            return True
    return False

display_main_logo()
st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. CATEGORIES & HOLIDAYS ---
COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
DEFAULT_RIGS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]
HOLIDAYS_2026 = [
    date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), 
    date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), 
    date(2026,5,1), date(2026,9,2)
]

# --- 4. DATA CONNECTION & MANAGEMENT ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300, show_spinner=False)
def get_data_cached(wks_name):
    try:
        df = conn.read(worksheet=wks_name, ttl=0)
        return df if not df.empty else pd.DataFrame()
    except: return pd.DataFrame()

def load_config_names():
    df = get_data_cached("nhansu")
    if not df.empty:
        df.columns = [str(c).strip() for c in df.columns]
        if "999s" in df.columns:
            return [str(n).strip() for n in df["999s"].dropna().tolist() if str(n).strip()]
    return [] 

def save_config_names(name_list):
    try:
        df_save = pd.DataFrame({"999s": name_list})
        conn.update(worksheet="nhansu", data=df_save)
        st.cache_data.clear()
        return True
    except: return False

def load_config_rigs():
    df = get_data_cached("config")
    if not df.empty:
        df.columns = [str(c).strip() for c in df.columns]
        if "GIANS" in df.columns:
            return [str(g).strip().upper() for g in df["GIANS"].dropna().tolist() if str(g).strip()]
    return DEFAULT_RIGS

def save_config_rigs(rig_list):
    try:
        df_save = pd.DataFrame({"GIANS": rig_list})
        conn.update(worksheet="config", data=df_save)
        st.cache_data.clear()
        return True
    except: return False

# --- 5. CALCULATION ENGINE ---
def apply_logic(df, curr_m, curr_y, rigs):
    df_calc = df.copy()
    rigs_up = [r.upper() for r in rigs]
    date_cols = [c for c in df_calc.columns if "/" in c and "(" in c]
    
    name_col = 'Full Name' if 'Full Name' in df_calc.columns else ('Họ và Tên' if 'Họ và Tên' in df_calc.columns else None)
    prev_col = 'Previous Bal' if 'Previous Bal' in df_calc.columns else ('Tồn cũ' if 'Tồn cũ' in df_calc.columns else None)
    total_col = 'Total CA' if 'Total CA' in df_calc.columns else ('Tổng CA' if 'Tổng CA' in df_calc.columns else 'Total CA')

    if not name_col: return df_calc

    for idx, row in df_calc.iterrows():
        if not str(row.get(name_col, '')).strip(): continue
        accrued = 0.0
        for col in date_cols:
            try:
                val = str(row.get(col, "")).strip().upper()
                if not val or val in ["NAN", "NONE", ""]: continue
                
                d_num = int(col[:2])
                target_date = date(curr_y, curr_m, d_num)
                is_we = target_date.weekday() >= 5
                is_ho = target_date in HOLIDAYS_2026
                
                if any(g in val for g in rigs_up):
                    if is_ho: accrued += 2.0
                    elif is_we: accrued += 1.0
                    else: accrued += 0.5
                elif val == "CA":
                    if not is_we and not is_ho: accrued -= 1.0
            except: continue
        
        pb = pd.to_numeric(row.get(prev_col, 0), errors='coerce') if prev_col else 0
        df_calc.at[idx, total_col] = round(float(pb if not pd.isna(pb) else 0.0) + accrued, 1)
    return df_calc

# --- 6. INITIALIZATION ---
if "GIANS" not in st.session_state: st.session_state.GIANS = load_config_rigs()
if "NAMES" not in st.session_state: st.session_state.NAMES = load_config_names()
if "store" not in st.session_state: st.session_state.store = {}

col_date1, col_date2, col_date3 = st.columns([3, 2, 3])
with col_date2: wd = st.date_input("📅 SELECT MONTH:", value=date.today())

sheet_name = wd.strftime("%m_%Y")
curr_m, curr_y = wd.month, wd.year
days_in_m = calendar.monthrange(curr_y, curr_m)[1]

# Cột ngày hiển thị tiếng Anh
DAYS_EN = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
DATE_COLS = [f"{d:02d}/{wd.strftime('%b')} ({DAYS_EN[date(curr_y,curr_m,d).weekday()]})" for d in range(1, days_in_m+1)]

if sheet_name not in st.session_state.store:
    with st.spinner(f"Loading data..."):
        df_raw = get_data_cached(sheet_name)
        
        # Ánh xạ tên cột Việt -> Anh để đồng nhất xử lý
        mapping = {'STT': 'No.', 'Họ và Tên': 'Full Name', 'Công ty': 'Company', 'Chức danh': 'Title', 'Tồn cũ': 'Previous Bal', 'Tổng CA': 'Total CA'}
        if not df_raw.empty:
            df_raw = df_raw.rename(columns=mapping)
            # Sửa lỗi KeyError: Tìm cột ngày thực tế trong Sheet
            actual_cols = df_raw.columns.tolist()
            
            # Logic nối dữ liệu tự động
            now = datetime.now()
            if sheet_name == now.strftime("%m_%Y"):
                target_day = min(now.day, days_in_m)
                for d in range(2, target_day + 1):
                    p_prefix = f"{(d-1):02d}/"
                    c_prefix = f"{d:02d}/"
                    p_col = next((c for c in actual_cols if c.startswith(p_prefix)), None)
                    c_col = next((c for c in actual_cols if c.startswith(c_prefix)), None)
                    
                    if p_col and c_col:
                        mask = (df_raw[c_col].isna() | (df_raw[c_col].astype(str).str.strip().isin(["","None","nan"]))) & \
                               (df_raw[p_col].notna() & (~df_raw[p_col].astype(str).str.strip().isin(["","None","nan"])))
                        df_raw.loc[mask, c_col] = df_raw.loc[mask, p_col]

        else:
            df_raw = pd.DataFrame({'No.': range(1, len(st.session_state.NAMES)+1), 'Full Name': st.session_state.NAMES})
            df_raw['Company'] = 'PVDWS'; df_raw['Title'] = 'Casing crew'; df_raw['Previous Bal'] = 0.0
            for c in DATE_COLS: df_raw[c] = ""
        
        st.session_state.store[sheet_name] = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)

# --- 7. MAIN UI ---
t1, t2 = st.tabs(["🚀 OPERATIONS", "📊 CHARTS"])

with t1:
    db = st.session_state.store[sheet_name]
    
    # Identify dynamic date columns
    actual_date_cols = [c for c in db.columns if "/" in c and "(" in c]
    
    c1, c2, c3 = st.columns([2, 2, 4])
    if c1.button("📤 SAVE TO DATABASE", type="primary", use_container_width=True):
        conn.update(worksheet=sheet_name, data=db)
        st.success("Data saved successfully!")
        st.cache_data.clear(); st.rerun()

    with c3:
        buf = io.BytesIO()
        db.to_excel(buf, index=False)
        st.download_button("📥 EXCEL", buf.getvalue(), f"PVD_{sheet_name}.xlsx", use_container_width=True)

    # Editor
    col_config = {
        "No.": st.column_config.NumberColumn(width="min", pinned=True),
        "Full Name": st.column_config.TextColumn(width="medium", pinned=True),
        "Total CA": st.column_config.NumberColumn(format="%.1f", disabled=True)
    }
    
    ed_db = st.data_editor(db, use_container_width=True, height=600, hide_index=True, column_config=col_config)
    
    if not ed_db.equals(db):
        st.session_state.store[sheet_name] = apply_logic(ed_db, curr_m, curr_y, st.session_state.GIANS)
        st.rerun()

# --- 9. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ SETTINGS")
    if st.button("🔄 REFRESH SYSTEM", use_container_width=True):
        st.cache_data.clear(); st.session_state.clear(); st.rerun()
