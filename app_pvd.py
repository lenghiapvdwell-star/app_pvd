import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import time
import plotly.express as px
import os

# --- 1. CONFIGURATION & STYLE (GIỮ NGUYÊN) ---
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

# --- 2. LOGO & TITLES (GIỮ NGUYÊN) ---
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

# --- 3. CATEGORIES & HOLIDAYS (GIỮ NGUYÊN) ---
COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
DEFAULT_RIGS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]
HOLIDAYS_2026 = [
    date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), 
    date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), 
    date(2026,5,1), date(2026,9,2)
]

# --- 4. DATA CONNECTION (TỐI ƯU HÓA) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data_cached(wks_name):
    try:
        df = conn.read(worksheet=wks_name, ttl="0s") # Ép buộc đọc dữ liệu mới nhất
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

# --- 5. CALCULATION ENGINE (GIỮ NGUYÊN LOGIC CỦA ANH) ---
def apply_logic(df, curr_m, curr_y, rigs):
    df_calc = df.copy()
    rigs_up = [r.upper() for r in rigs]
    date_cols = [c for c in df_calc.columns if "/" in str(c) and "(" in str(c)]
    
    name_col = next((c for c in ['Full Name', 'Họ và Tên'] if c in df_calc.columns), 'Full Name')
    prev_col = next((c for c in ['Previous Bal', 'Tồn cũ'] if c in df_calc.columns), 'Previous Bal')
    total_col = next((c for c in ['Total CA', 'Tổng CA'] if c in df_calc.columns), 'Total CA')

    for idx, row in df_calc.iterrows():
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
        pb = pd.to_numeric(row.get(prev_col, 0), errors='coerce')
        df_calc.at[idx, total_col] = round(float(pb if not pd.isna(pb) else 0.0) + accrued, 1)
    return df_calc

def push_balances_to_future(start_date, start_df, rigs):
    current_df = start_df.copy()
    current_date = start_date
    name_col = 'Full Name'
    total_col = 'Total CA'
    for i in range(1, 13 - current_date.month + 1):
        next_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)
        if next_date.year > current_date.year: break
        next_sheet = next_date.strftime("%m_%Y")
        try:
            time.sleep(1)
            next_df = get_data_cached(next_sheet)
            if next_df.empty: continue
            balances = current_df.set_index(name_col)[total_col].to_dict()
            for idx, row in next_df.iterrows():
                name = row.get(name_col)
                if name in balances: next_df.at[idx, 'Previous Bal'] = balances[name]
            next_df = apply_logic(next_df, next_date.month, next_date.year, rigs)
            conn.update(worksheet=next_sheet, data=next_df)
            current_df = next_df; current_date = next_date
        except: break

# --- 7. INITIALIZATION (NÂNG CẤP AUTO-FILL) ---
if "GIANS" not in st.session_state: st.session_state.GIANS = load_config_rigs()
if "NAMES" not in st.session_state: st.session_state.NAMES = load_config_names()
if "store" not in st.session_state: st.session_state.store = {}

col_date1, col_date2, col_date3 = st.columns([3, 2, 3])
with col_date2: 
    wd = st.date_input("📅 SELECT MONTH:", value=date.today())

sheet_name = wd.strftime("%m_%Y")
curr_m, curr_y = wd.month, wd.year
days_in_m = calendar.monthrange(curr_y, curr_m)[1]
DAYS_EN = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
DATE_COLS = [f"{d:02d}/{wd.strftime('%b')} ({DAYS_EN[date(curr_y,curr_m,d).weekday()]})" for d in range(1, days_in_m+1)]

# Khối xử lý dữ liệu chính
if sheet_name not in st.session_state.store:
    with st.spinner("Đang đồng bộ dữ liệu..."):
        df_raw = get_data_cached(sheet_name)
        
        # Tạo sheet mới nếu chưa có
        if df_raw.empty:
            df_raw = pd.DataFrame({'No.': range(1, len(st.session_state.NAMES)+1), 'Full Name': st.session_state.NAMES})
            df_raw['Company'] = 'PVDWS'; df_raw['Title'] = 'Casing crew'; df_raw['Previous Bal'] = 0.0
            df_raw['Total CA'] = 0.0
            for c in DATE_COLS: df_raw[c] = ""
        
        # --- THUẬT TOÁN AUTO-FILL ---
        now = datetime.now()
        if sheet_name == now.strftime("%m_%Y"):
            has_changes = False
            today_num = now.day
            
            # 1. Lấy dữ liệu ngày cuối tháng trước cho ngày 01
            col_01 = DATE_COLS[0]
            if str(df_raw.at[0, col_01]).strip() in ["", "nan", "None"]:
                prev_date = wd.replace(day=1) - timedelta(days=1)
                prev_df = get_data_cached(prev_date.strftime("%m_%Y"))
                if not prev_df.empty:
                    last_day_col = [c for c in prev_df.columns if "/" in str(c)][-1]
                    last_map = prev_df.set_index('Full Name')[last_day_col].to_dict()
                    df_raw[col_01] = df_raw['Full Name'].map(last_map).fillna("")
                    has_changes = True

            # 2. Tự động điền tiếp sức (Forward Fill) cho đến ngày hôm nay
            for d in range(2, today_num + 1):
                prev_col = DATE_COLS[d-2]
                curr_col = DATE_COLS[d-1]
                # Chỉ điền nếu ô hiện tại trống
                mask = (df_raw[curr_col].astype(str).str.strip().isin(["", "nan", "None"]))
                if mask.any():
                    df_raw.loc[mask, curr_col] = df_raw.loc[mask, prev_col]
                    has_changes = True
            
            if has_changes:
                df_raw = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)
                conn.update(worksheet=sheet_name, data=df_raw)

        st.session_state.store[sheet_name] = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)

# --- 8. OPERATIONS (GIỮ NGUYÊN GIAO DIỆN) ---
t1, t2 = st.tabs(["🚀 OPERATIONS", "📊 SUMMARY CHARTS"])

with t1:
    db = st.session_state.store[sheet_name]
    rigs_up = [r.upper() for r in st.session_state.GIANS]

    # Style (Giữ nguyên màu đỏ ngày lễ)
    def highlight_holidays(s):
        res = ['' for _ in s]
        try:
            d_num = int(s.name[:2])
            target_date = date(curr_y, curr_m, d_num)
            if target_date in HOLIDAYS_2026:
                for i, val in enumerate(s):
                    if any(g in str(val).upper() for g in rigs_up):
                        res[i] = 'background-color: #FF4B4B; color: white; font-weight: bold'
        except: pass
        return res

    c1, c2, c3 = st.columns([2, 2, 4])
    if c1.button("📤 SAVE & UPDATE YEARLY", type="primary", use_container_width=True):
        with st.spinner("Đang lưu..."):
            db = apply_logic(db, curr_m, curr_y, st.session_state.GIANS)
            conn.update(worksheet=sheet_name, data=db)
            push_balances_to_future(wd, db, st.session_state.GIANS)
            st.cache_data.clear(); st.session_state.store.clear(); st.success("Updated!"); st.rerun()

    with c3:
        buf = io.BytesIO()
        db.to_excel(buf, index=False)
        st.download_button("📥 EXPORT EXCEL", buf.getvalue(), f"PVD_{sheet_name}.xlsx", use_container_width=True)

    # QUICK INPUT (Giữ nguyên)
    with st.expander("🛠️ QUICK INPUT TOOL"):
        names_sel = st.multiselect("Personnel:", st.session_state.NAMES)
        dr = st.date_input("Date range:", value=(date(curr_y, curr_m, 1), date(curr_y, curr_m, 5)))
        r1, r2, r3, r4 = st.columns(4)
        stt = r1.selectbox("Status:", ["Offshore", "CA", "WS", "Holiday", "AL", "SL", "Clear"])
        rig = r2.selectbox("Rig Name:", st.session_state.GIANS) if stt == "Offshore" else stt
        co = r3.selectbox("Company:", ["Keep Current"] + COMPANIES)
        ti = r4.selectbox("Title:", ["Keep Current"] + TITLES)
        
        if st.button("✅ APPLY", use_container_width=True):
            if names_sel and len(dr) == 2:
                for n in names_sel:
                    idx = db.index[db['Full Name'] == n].tolist()[0]
                    if co != "Keep Current": db.at[idx, 'Company'] = co
                    if ti != "Keep Current": db.at[idx, 'Title'] = ti
                    sd, ed = dr
                    while sd <= ed:
                        if sd.month == curr_m:
                            col = [c for c in db.columns if c.startswith(f"{sd.day:02d}/")][0]
                            db.at[idx, col] = "" if stt == "Clear" else str(rig)
                        sd += timedelta(days=1)
                st.session_state.store[sheet_name] = apply_logic(db, curr_m, curr_y, st.session_state.GIANS)
                st.rerun()

    # DATA EDITOR (Giữ nguyên)
    col_config = {
        "No.": st.column_config.NumberColumn("No.", width="min", pinned=True),
        "Full Name": st.column_config.TextColumn("Full Name", width="medium", pinned=True),
        "Previous Bal": st.column_config.NumberColumn("Prev Bal", format="%.1f"),
        "Total CA": st.column_config.NumberColumn("Total CA", format="%.1f"),
    }
    status_options = st.session_state.GIANS + ["CA", "WS", "Lễ", "AL", "SL", ""]
    for c in [col for col in db.columns if "/" in str(col)]:
        col_config[c] = st.column_config.SelectboxColumn(c, options=status_options)

    ed_db = st.data_editor(db.style.apply(highlight_holidays, axis=0), use_container_width=True, height=600, hide_index=True, column_config=col_config)
    
    if not ed_db.equals(db):
        st.session_state.store[sheet_name] = apply_logic(ed_db, curr_m, curr_y, st.session_state.GIANS)
        st.rerun()

# --- SUMMARY CHARTS & SIDEBAR (GIỮ NGUYÊN) ---
with t2:
    st.subheader(f"📊 Personnel Statistics {curr_y}")
    # ... (Giữ nguyên phần vẽ biểu đồ Plotly của anh) ...
    sel_name = st.selectbox("🔍 Select Personnel:", st.session_state.NAMES)
    if sel_name:
        yearly_data = []
        for m in range(1, 13):
            m_df = get_data_cached(f"{m:02d}_{curr_y}")
            if not m_df.empty and sel_name in m_df['Full Name'].values:
                p_row = m_df[m_df['Full Name'] == sel_name].iloc[0]
                counts = {"Offshore": 0, "CA": 0, "Workshop": 0}
                for c in m_df.columns:
                    if "/" in str(c):
                        val = str(p_row[c]).upper()
                        if any(g in val for g in rigs_up): counts["Offshore"] += 1
                        elif val == "CA": counts["CA"] += 1
                        elif val == "WS": counts["Workshop"] += 1
                for k, v in counts.items():
                    if v > 0: yearly_data.append({"Month": f"Month {m}", "Type": k, "Days": v})
        if yearly_data:
            df_chart = pd.DataFrame(yearly_data)
            fig = px.bar(df_chart, x="Month", y="Days", color="Type", barmode="stack", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

with st.sidebar:
    st.header("⚙️ SETTINGS")
    with st.expander("🏗️ Rigs"):
        ng = st.text_input("➕ Add Rig:").upper().strip()
        if st.button("Add Rig"):
            if ng and ng not in st.session_state.GIANS:
                st.session_state.GIANS.append(ng); save_config_rigs(st.session_state.GIANS); st.rerun()
        dg = st.selectbox("❌ Delete Rig:", st.session_state.GIANS)
        if st.button("Delete Rig"):
            st.session_state.GIANS.remove(dg); save_config_rigs(st.session_state.GIANS); st.rerun()

    with st.expander("👤 Personnel"):
        new_per = st.text_input("➕ Add Name:").strip()
        if st.button("Add Name"):
            if new_per and new_per not in st.session_state.NAMES:
                st.session_state.NAMES.append(new_per); save_config_names(st.session_state.NAMES); st.rerun()
        del_per = st.selectbox("❌ Delete Name:", st.session_state.NAMES)
        if st.button("Delete Name"):
            st.session_state.NAMES.remove(del_per); save_config_names(st.session_state.NAMES); st.rerun()

    if st.button("🔄 REFRESH SYSTEM"):
        st.cache_data.clear(); st.session_state.clear(); st.rerun()
