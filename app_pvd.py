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
DEFAULT_RIGS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD", "DIALOG MALAYSIA"]
HOLIDAYS_2026 = [
    date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), 
    date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), 
    date(2026,5,1), date(2026,9,2)
]

# --- 4. DATA CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data_fresh(wks_name):
    try:
        return conn.read(worksheet=wks_name, ttl="0s")
    except: return pd.DataFrame()

@st.cache_data(ttl=300)
def load_config_names():
    df = get_data_fresh("nhansu")
    if not df.empty and "999s" in df.columns:
        return [str(n).strip() for n in df["999s"].dropna().tolist() if str(n).strip()]
    return [] 

@st.cache_data(ttl=300)
def load_config_rigs():
    df = get_data_fresh("config")
    if not df.empty and "GIANS" in df.columns:
        return [str(g).strip().upper() for g in df["GIANS"].dropna().tolist() if str(g).strip()]
    return DEFAULT_RIGS

# --- 5. LOGIC TÍNH TOÁN ---
def apply_logic(df, curr_m, curr_y, rigs):
    df_calc = df.copy()
    rigs_up = [r.upper() for r in rigs]
    date_cols = [c for c in df_calc.columns if "/" in str(c)]
    
    name_col = next((c for c in ['Full Name', 'Họ và Tên'] if c in df_calc.columns), None)
    prev_col = next((c for c in ['Previous Bal', 'Tồn cũ'] if c in df_calc.columns), 'Previous Bal')
    total_col = next((c for c in ['Total CA', 'Tổng CA'] if c in df_calc.columns), 'Total CA')

    if not name_col: return df_calc

    for idx, row in df_calc.iterrows():
        if not str(row.get(name_col, '')).strip(): continue
        accrued = 0.0
        for col in date_cols:
            try:
                val = str(row.get(col, "")).strip().upper()
                if val in ["", "NAN", "NONE", "0", "0.0"]: continue
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
        pb = pd.to_numeric(row.get(prev_col, 0), errors='coerce')
        df_calc.at[idx, total_col] = round(float(pb if not pd.isna(pb) else 0.0) + accrued, 1)
    return df_calc

# --- 6. KHỞI TẠO & AUTO-FILL ---
if "GIANS" not in st.session_state: st.session_state.GIANS = load_config_rigs()
if "NAMES" not in st.session_state: st.session_state.NAMES = load_config_names()

col_date1, col_date2, col_date3 = st.columns([3, 2, 3])
with col_date2: 
    wd = st.date_input("📅 SELECT MONTH:", value=date.today())

sheet_name = wd.strftime("%m_%Y")
curr_m, curr_y = wd.month, wd.year
days_in_m = calendar.monthrange(curr_y, curr_m)[1]
DAYS_EN = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
DATE_COLS = [f"{d:02d}/{wd.strftime('%b')} ({DAYS_EN[date(curr_y,curr_m,d).weekday()]})" for d in range(1, days_in_m+1)]

df_raw = get_data_fresh(sheet_name)

if df_raw.empty:
    df_raw = pd.DataFrame({'No.': range(1, len(st.session_state.NAMES)+1), 'Full Name': st.session_state.NAMES})
    df_raw['Company'] = 'PVDWS'; df_raw['Title'] = 'Casing crew'; df_raw['Previous Bal'] = 0.0
    for c in DATE_COLS: df_raw[c] = ""
    prev_m_str = (wd.replace(day=1) - timedelta(days=1)).strftime("%m_%Y")
    df_prev = get_data_fresh(prev_m_str)
    if not df_prev.empty:
        name_c_p = next((c for c in ['Full Name', 'Họ và Tên'] if c in df_prev.columns), df_prev.columns[1])
        total_c_p = next((c for c in ['Total CA', 'Tổng CA'] if c in df_prev.columns), 'Total CA')
        bal_map = df_prev.set_index(name_c_p)[total_c_p].to_dict()
        df_raw['Previous Bal'] = df_raw['Full Name'].map(bal_map).fillna(0.0)

# FIX LỖI TYPEERROR: Ép kiểu dữ liệu các cột ngày về chuỗi để tránh xung đột
for col in DATE_COLS:
    if col in df_raw.columns:
        df_raw[col] = df_raw[col].astype(object)

now = datetime.now()
if sheet_name == now.strftime("%m_%Y"):
    changed = False
    today_num = now.day
    name_col = next((c for c in ['Full Name', 'Họ và Tên'] if c in df_raw.columns), 'Full Name')

    # Bước 1: Ngày 01
    val_d1 = str(df_raw.at[0, DATE_COLS[0]]).strip().upper()
    if val_d1 in ["", "NAN", "NONE"]:
        prev_m_str = (wd.replace(day=1) - timedelta(days=1)).strftime("%m_%Y")
        df_p = get_data_fresh(prev_m_str)
        if not df_p.empty:
            last_col = [c for c in df_p.columns if "/" in str(c)][-1]
            name_c_p = next((c for c in ['Full Name', 'Họ và Tên'] if c in df_p.columns), df_p.columns[1])
            st_map = df_p.set_index(name_c_p)[last_col].to_dict()
            df_raw[DATE_COLS[0]] = df_raw[name_col].map(st_map).fillna("")
            changed = True
    
    # Bước 2: Điền tiếp nối
    for d in range(1, today_num):
        curr_c, next_c = DATE_COLS[d-1], DATE_COLS[d]
        def is_really_empty(val):
            return str(val).strip().upper() in ["", "NAN", "NONE"]

        mask = (df_raw[next_c].apply(is_really_empty)) & (~df_raw[curr_c].apply(is_really_empty))
        if mask.any():
            # Sử dụng .values để gán mảng, tránh xung đột index và dtype
            df_raw.loc[mask, next_c] = df_raw.loc[mask, curr_c].values
            changed = True
    
    if changed:
        df_raw = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)
        conn.update(worksheet=sheet_name, data=df_raw)

current_df = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)

# --- 7. TABS OPERATIONS ---
t1, t2 = st.tabs(["🚀 OPERATIONS", "📊 SUMMARY CHARTS"])

with t1:
    db = current_df
    rigs_up = [r.upper() for r in st.session_state.GIANS]

    def highlight_holidays(s):
        res = ['' for _ in s]
        try:
            d_num = int(s.name[:2])
            if date(curr_y, curr_m, d_num) in HOLIDAYS_2026:
                for i, v in enumerate(s):
                    if any(g in str(v).upper() for g in rigs_up):
                        res[i] = 'background-color: #FF4B4B; color: white; font-weight: bold'
        except: pass
        return res

    # --- 1. SẮP XẾP THỨ TỰ CỘT ---
    name_col = next((c for c in ['Full Name', 'Họ và Tên'] if c in db.columns), 'Full Name')
    total_col = next((c for c in ['Total CA', 'Tổng CA'] if c in db.columns), 'Total CA')
    prev_col = next((c for c in ['Previous Bal', 'Tồn cũ'] if c in db.columns), 'Previous Bal')
    
    # Thứ tự mong muốn: No -> Name -> Company -> Title -> Prev Bal -> Total CA -> Dates
    fixed_cols = ['No.', name_col, 'Company', 'Title', prev_col, total_col]
    date_cols = [c for c in db.columns if "/" in str(c)]
    
    # Lọc lấy những cột thực tế có trong dataframe
    existing_fixed = [c for c in fixed_cols if c in db.columns]
    new_column_order = existing_fixed + date_cols
    db = db[new_column_order]

    # --- 2. CÁC NÚT BẤM THAO TÁC ---
    c1, c2, c3 = st.columns([2, 2, 4])
    if c1.button("📤 SAVE TO DATABASE", type="primary", use_container_width=True):
        conn.update(worksheet=sheet_name, data=db)
        st.cache_data.clear()
        st.success("Data saved successfully!")
        st.rerun()

    with c2:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            db.to_excel(writer, index=False, sheet_name=sheet_name)
        st.download_button(label="📥 EXPORT EXCEL", data=output.getvalue(), 
                         file_name=f"PVD_Report_{sheet_name}.xlsx", 
                         mime="application/vnd.ms-excel", use_container_width=True)

    # --- 3. QUICK INPUT TOOL ---
    with st.expander("🛠️ QUICK INPUT TOOL"):
        names_sel = st.multiselect("Personnel:", st.session_state.NAMES)
        dr = st.date_input("Date range:", value=(date(curr_y, curr_m, 1), date(curr_y, curr_m, 1)))
        
        r1, r2, r3, r4 = st.columns(4)
        stt = r1.selectbox("Status:", ["Offshore", "CA", "WS", "Holiday", "AL", "SL", "Clear"])
        rig = r2.selectbox("Rig/Detail:", st.session_state.GIANS) if stt == "Offshore" else stt
        comp_sel = r3.selectbox("Company:", [""] + COMPANIES)
        title_sel = r4.selectbox("Title:", [""] + TITLES)
        
        if st.button("✅ APPLY CHANGES", use_container_width=True):
            if names_sel and len(dr) == 2:
                for n in names_sel:
                    idx_list = db.index[db[name_col] == n].tolist()
                    if idx_list:
                        idx = idx_list[0]
                        if comp_sel: db.at[idx, 'Company'] = comp_sel
                        if title_sel: db.at[idx, 'Title'] = title_sel
                        
                        sd, ed = dr
                        while sd <= ed:
                            if sd.month == curr_m:
                                col_target = [c for c in db.columns if c.startswith(f"{sd.day:02d}/")]
                                if col_target:
                                    db.at[idx, col_target[0]] = "" if stt == "Clear" else str(rig)
                            sd += timedelta(days=1)
                
                db = apply_logic(db, curr_m, curr_y, st.session_state.GIANS)
                conn.update(worksheet=sheet_name, data=db)
                st.rerun()

    # --- 4. DATA EDITOR (BẢNG HIỂN THỊ CHÍNH) ---
    col_config = {
        "No.": st.column_config.NumberColumn("No.", width="small", pinned=True),
        name_col: st.column_config.TextColumn(name_col, width="medium", pinned=True),
        "Company": st.column_config.TextColumn("Company", width="small", pinned=True),
        "Title": st.column_config.TextColumn("Title", width="small", pinned=True),
        prev_col: st.column_config.NumberColumn("Prev Bal", format="%.1f", width="small", pinned=True),
        total_col: st.column_config.NumberColumn("Total CA", format="%.1f", width="small", pinned=True)
    }
    
    status_options = st.session_state.GIANS + ["CA", "WS", "Lễ", "AL", "SL", ""]
    for c in date_cols:
        col_config[c] = st.column_config.SelectboxColumn(c, options=status_options, width="small")

    ed_db = st.data_editor(
        db.style.apply(highlight_holidays, axis=0), 
        use_container_width=True, 
        height=550, 
        hide_index=True, 
        column_config=col_config
    )
    
    if not ed_db.equals(db):
        conn.update(worksheet=sheet_name, data=ed_db)
        st.rerun()
with t2:
    st.subheader(f"📊 Personnel Statistics {curr_y}")
    sel_name = st.selectbox("🔍 Select Personnel:", st.session_state.NAMES)
    month_order = [f"Month {i}" for i in range(1, 13)]
    
    if sel_name:
        yearly_data = []
        for m in range(1, 13):
            m_sheet = f"{m:02d}_{curr_y}"
            m_df = get_data_fresh(m_sheet)
            if not m_df.empty:
                n_c = next((c for c in ['Full Name', 'Họ và Tên'] if c in m_df.columns), m_df.columns[1])
                if sel_name in m_df[n_c].values:
                    p_row = m_df[m_df[n_c] == sel_name].iloc[0]
                    counts = {"Offshore": 0, "CA": 0, "Workshop": 0, "Holiday": 0, "AL (Phép)": 0, "SL (Ốm)": 0}
                    for c in m_df.columns:
                        if "/" in str(c):
                            val = str(p_row[c]).strip().upper()
                            if val in ["", "NAN", "NONE"]: continue
                            if any(g in val for g in rigs_up): counts["Offshore"] += 1
                            elif val == "CA": counts["CA"] += 1
                            elif val == "WS": counts["Workshop"] += 1
                            elif val in ["AL", "NP", "P"]: counts["AL (Phép)"] += 1
                            elif val in ["SL", "ỐM", "O"]: counts["SL (Ốm)"] += 1
                            elif val in ["LỄ", "HOLIDAY"]: counts["Holiday"] += 1
                    for k, v in counts.items():
                        if v > 0: yearly_data.append({"Month": f"Month {m}", "Type": k, "Days": v})
        
        if yearly_data:
            df_chart = pd.DataFrame(yearly_data)
            fig = px.bar(df_chart, x="Month", y="Days", color="Type", barmode="stack", text="Days",
                         color_discrete_map={"AL (Phép)": "#2ecc71", "SL (Ốm)": "#e74c3c"},
                         category_orders={"Month": month_order}, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            pv = df_chart.pivot_table(index='Type', columns='Month', values='Days', aggfunc='sum', fill_value=0)
            st.table(pv)

with st.sidebar:
    st.header("⚙️ SETTINGS")
    with st.expander("🏗️ Rigs"):
        ng = st.text_input("➕ Add Rig:").upper().strip()
        if st.button("Add Rig") and ng:
            st.session_state.GIANS.append(ng); conn.update(worksheet="config", data=pd.DataFrame({"GIANS": st.session_state.GIANS})); st.rerun()
    with st.expander("👤 Personnel"):
        new_per = st.text_input("➕ Add Name:").strip()
        if st.button("Add Name") and new_per:
            st.session_state.NAMES.append(new_per); conn.update(worksheet="nhansu", data=pd.DataFrame({"999s": st.session_state.NAMES})); st.rerun()
    if st.button("🔄 REFRESH SYSTEM"):
        st.cache_data.clear(); st.session_state.clear(); st.rerun()
