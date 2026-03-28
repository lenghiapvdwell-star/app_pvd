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
        else:
            return [str(n).strip() for n in df.iloc[:, 0].dropna().tolist() if str(n).strip()]
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

    for idx, row in df_calc.iterrows():
        if not str(row.get('Full Name', '')).strip(): continue
        accrued = 0.0
        for col in date_cols:
            try:
                val = str(row.get(col, "")).strip().upper()
                if not val or val == "NAN" or val == "NONE": continue
                
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
        
        prev_bal = pd.to_numeric(row.get('Previous Bal', 0), errors='coerce')
        df_calc.at[idx, 'Total CA'] = round(float(prev_bal if not pd.isna(prev_bal) else 0.0) + accrued, 1)
    return df_calc

def push_balances_to_future(start_date, start_df, rigs):
    current_df = start_df.copy()
    current_date = start_date
    for i in range(1, 13 - current_date.month):
        next_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)
        next_sheet = next_date.strftime("%m_%Y")
        try:
            time.sleep(2.5) 
            next_df = get_data_cached(next_sheet)
            if next_df.empty: continue
            balances = current_df.set_index('Full Name')['Total CA'].to_dict()
            for idx, row in next_df.iterrows():
                name = row['Full Name']
                if name in balances: next_df.at[idx, 'Previous Bal'] = balances[name]
            next_df = apply_logic(next_df, next_date.month, next_date.year, rigs)
            conn.update(worksheet=next_sheet, data=next_df)
            current_df = next_df
            current_date = next_date
        except: break

# --- 6. DATA INITIALIZATION ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = load_config_rigs()
if "NAMES" not in st.session_state:
    st.session_state.NAMES = load_config_names()
if "store" not in st.session_state:
    st.session_state.store = {}

col_date1, col_date2, col_date3 = st.columns([3, 2, 3])
with col_date2: wd = st.date_input("📅 SELECT MONTH:", value=date.today())

sheet_name = wd.strftime("%m_%Y")
curr_m, curr_y = wd.month, wd.year
days_in_m = calendar.monthrange(curr_y, curr_m)[1]
# English Day Names
DAYS_EN = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
DATE_COLS = [f"{d:02d}/{wd.strftime('%b')} ({DAYS_EN[date(curr_y,curr_m,d).weekday()]})" for d in range(1, days_in_m+1)]

if sheet_name not in st.session_state.store:
    with st.spinner(f"Synchronizing data..."):
        df_raw = get_data_cached(sheet_name)
        current_config_names = load_config_names()
        st.session_state.NAMES = current_config_names
        
        if df_raw.empty:
            df_raw = pd.DataFrame({'No.': range(1, len(current_config_names)+1), 'Full Name': current_config_names})
            df_raw['Company'] = 'PVDWS'; df_raw['Title'] = 'Casing crew'; df_raw['Previous Bal'] = 0.0
            for c in DATE_COLS: df_raw[c] = ""
            prev_date = wd.replace(day=1) - timedelta(days=1)
            prev_df = get_data_cached(prev_date.strftime("%m_%Y"))
            if not prev_df.empty:
                # Assuming Previous sheets might have VN headers, we map them
                bal_col = 'Total CA' if 'Total CA' in prev_df.columns else 'Tổng CA'
                name_col = 'Full Name' if 'Full Name' in prev_df.columns else 'Họ và Tên'
                balances = prev_df.set_index(name_col)[bal_col].to_dict()
                for idx, row in df_raw.iterrows():
                    if row['Full Name'] in balances: df_raw.at[idx, 'Previous Bal'] = balances[row['Full Name']]
        else:
            # Rename existing Vietnamese headers to English for UI consistency
            vn_to_en = {'STT': 'No.', 'Họ và Tên': 'Full Name', 'Công ty': 'Company', 'Chức danh': 'Title', 'Tồn cũ': 'Previous Bal', 'Tổng CA': 'Total CA'}
            df_raw = df_raw.rename(columns=vn_to_en)
            
            existing_names = df_raw['Full Name'].dropna().tolist()
            new_names = [n for n in current_config_names if n not in existing_names]
            if new_names:
                new_df = pd.DataFrame({'Full Name': new_names})
                new_df['Company'] = 'PVDWS'; new_df['Title'] = 'Casing crew'; new_df['Previous Bal'] = 0.0
                for c in DATE_COLS: new_df[c] = ""
                df_raw = pd.concat([df_raw, new_df], ignore_index=True)
            df_raw['No.'] = range(1, len(df_raw)+1)

        now = datetime.now()
        if sheet_name == now.strftime("%m_%Y"):
            has_updated = False
            target_day = min(now.day, days_in_m)
            for d in range(2, target_day + 1):
                p_col_name = [c for c in DATE_COLS if c.startswith(f"{(d-1):02d}/")]
                c_col_name = [c for c in DATE_COLS if c.startswith(f"{d:02d}/")]
                if p_col_name and c_col_name:
                    pc, cc = p_col_name[0], c_col_name[0]
                    mask = (df_raw[cc].isna() | (df_raw[cc].astype(str).str.strip() == "None") | (df_raw[cc].astype(str).str.strip() == "")) & \
                           (df_raw[pc].notna() & (df_raw[pc].astype(str).str.strip() != "None") & (df_raw[pc].astype(str).str.strip() != ""))
                    if mask.any():
                        df_raw.loc[mask, cc] = df_raw.loc[mask, pc]
                        has_updated = True
            if has_updated:
                df_raw = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)
                conn.update(worksheet=sheet_name, data=df_raw)
                st.toast(f"⚡ Auto-extended data to day {target_day:02d}!", icon="✅")
        st.session_state.store[sheet_name] = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)

# --- 7. MAIN INTERFACE ---
t1, t2 = st.tabs(["🚀 OPERATIONS", "📊 SUMMARY CHARTS"])

with t1:
    db = st.session_state.store[sheet_name]
    rigs_up = [r.upper() for r in st.session_state.GIANS]

    def highlight_holidays(s):
        res = ['' for _ in s]
        col_name = s.name
        try:
            d_num = int(col_name[:2])
            target_date = date(curr_y, curr_m, d_num)
            if target_date in HOLIDAYS_2026:
                for i, val in enumerate(s):
                    v = str(val).upper().strip()
                    if any(g in v for g in rigs_up) or v == "WS":
                        res[i] = 'background-color: #FF4B4B; color: white; font-weight: bold'
        except: pass
        return res

    fixed_cols = ['No.', 'Full Name', 'Company', 'Title']
    calc_cols = ['Previous Bal', 'Total CA']
    actual_cols = [c for c in fixed_cols if c in db.columns] + \
                  [c for c in calc_cols if c in db.columns] + \
                  [c for c in DATE_COLS if c in db.columns]
    db = db[actual_cols]

    c1, c2, c3 = st.columns([2, 2, 4])
    if c1.button("📤 SAVE & UPDATE FULL YEAR", type="primary", use_container_width=True):
        with st.spinner("Saving and updating future balances..."):
            db = apply_logic(db, curr_m, curr_y, st.session_state.GIANS)
            conn.update(worksheet=sheet_name, data=db)
            push_balances_to_future(wd, db, st.session_state.GIANS)
            st.cache_data.clear()
            st.session_state.store.clear()
            st.success("Success!")
            st.rerun()

    with c3:
        buf = io.BytesIO()
        db.to_excel(buf, index=False)
        st.download_button("📥 EXPORT EXCEL", buf.getvalue(), f"PVD_{sheet_name}.xlsx", use_container_width=True)

    with st.expander("🛠️ QUICK INPUT TOOL"):
        names_sel = st.multiselect("Personnel:", st.session_state.NAMES)
        dr = st.date_input("Date Range:", value=(date(curr_y, curr_m, 1), date(curr_y, curr_m, 5)))
        r1, r2, r3, r4 = st.columns(4)
        stt_list = ["Offshore", "CA", "Workshop", "Holiday", "Annual Leave", "Sick Leave", "Clear"]
        stt = r1.selectbox("Status:", stt_list)
        
        # Internal mapping for logic
        map_val = {"Workshop": "WS", "Holiday": "Lễ", "Annual Leave": "NP", "Sick Leave": "Ốm"}
        
        rig = r2.selectbox("Rig Name:", st.session_state.GIANS) if stt == "Offshore" else map_val.get(stt, stt)
        co = r3.selectbox("Company:", ["Keep Current"] + COMPANIES)
        ti = r4.selectbox("Title:", ["Keep Current"] + TITLES)
        
        if st.button("✅ APPLY", use_container_width=True):
            if names_sel and len(dr) == 2:
                for n in names_sel:
                    idx_list = db.index[db['Full Name'] == n].tolist()
                    if idx_list:
                        idx = idx_list[0]
                        if co != "Keep Current": db.at[idx, 'Company'] = co
                        if ti != "Keep Current": db.at[idx, 'Title'] = ti
                        sd, ed = dr
                        while sd <= ed:
                            if sd.month == curr_m:
                                m_cols = [c for c in DATE_COLS if c.startswith(f"{sd.day:02d}/")]
                                if m_cols: db.at[idx, m_cols[0]] = "" if stt == "Clear" else rig
                            sd += timedelta(days=1)
                st.session_state.store[sheet_name] = apply_logic(db, curr_m, curr_y, st.session_state.GIANS)
                st.rerun()

    col_config = {
        "No.": st.column_config.NumberColumn("No.", width="min", pinned=True, format="%d"),
        "Full Name": st.column_config.TextColumn("Full Name", width="medium", pinned=True),
        "Company": st.column_config.SelectboxColumn("Company", options=COMPANIES, width="normal"),
        "Title": st.column_config.SelectboxColumn("Title", options=TITLES, width="normal"),
        "Previous Bal": st.column_config.NumberColumn("Prev Bal", format="%.1f", width="normal"),
        "Total CA": st.column_config.NumberColumn("Total CA", format="%.1f", width="normal"),
    }
    status_options = st.session_state.GIANS + ["CA", "WS", "Lễ", "NP", "Ốm", ""]
    for c in DATE_COLS:
        col_config[c] = st.column_config.SelectboxColumn(c, options=status_options, width="normal")

    styled_db = db.style.apply(highlight_holidays, axis=0)
    ed_db = st.data_editor(styled_db, use_container_width=True, height=600, hide_index=True, column_config=col_config, key=f"editor_{sheet_name}")
    
    if not ed_db.equals(db):
        st.session_state.store[sheet_name].update(ed_db)
        st.session_state.store[sheet_name] = st.session_state.store[sheet_name][actual_cols]
        st.session_state.store[sheet_name] = apply_logic(st.session_state.store[sheet_name], curr_m, curr_y, st.session_state.GIANS)
        st.rerun()

# --- 8. SUMMARY CHARTS ---
with t2:
    st.subheader(f"📊 Personnel Statistics {curr_y}")
    sel_name = st.selectbox("🔍 Select personnel for report:", st.session_state.NAMES)
    if sel_name:
        yearly_data = []
        with st.spinner("Aggregating yearly data..."):
            for m in range(1, 13):
                m_df = get_data_cached(f"{m:02d}_{curr_y}")
                if not m_df.empty:
                    name_col = 'Full Name' if 'Full Name' in m_df.columns else 'Họ và Tên'
                    if sel_name in m_df[name_col].values:
                        p_row = m_df[m_df[name_col] == sel_name].iloc[0]
                        counts = {"Offshore": 0, "CA Leave": 0, "Workshop": 0, "Holiday": 0, "Annual Leave": 0, "Sick Leave": 0}
                        for c in m_df.columns:
                            if "/" in c and "(" in c:
                                val = str(p_row[c]).strip().upper()
                                if any(g in val for g in rigs_up) and val != "": counts["Offshore"] += 1
                                elif val == "CA": counts["CA Leave"] += 1
                                elif val == "WS": counts["Workshop"] += 1
                                elif val == "NP": counts["Annual Leave"] += 1
                                elif val == "ỐM": counts["Sick Leave"] += 1
                                elif val == "LỄ": counts["Holiday"] += 1
                        for k, v in counts.items():
                            if v > 0: yearly_data.append({"Month": f"Month {m}", "Type": k, "Days": v})
        
        if yearly_data:
            df_chart = pd.DataFrame(yearly_data)
            fig = px.bar(df_chart, x="Month", y="Days", color="Type", barmode="stack", text="Days", template="plotly_dark",
                         color_discrete_map={
                             "Offshore": "#636EFA", "Annual Leave": "#EF553B", "CA Leave": "#00CC96",
                             "Workshop": "#AB63FA", "Holiday": "#FFA15A", "Sick Leave": "#FF6692"
                         })
            st.plotly_chart(fig, use_container_width=True)
            pv = df_chart.pivot_table(index='Type', columns='Month', values='Days', aggfunc='sum', fill_value=0).astype(int)
            pv['TOTAL YEAR'] = pv.sum(axis=1)
            st.table(pv)

# --- 9. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ SYSTEM MANAGEMENT")
    with st.expander("🏗️ Rig Management"):
        ng = st.text_input("➕ Add Rig:").upper().strip()
        if st.button("Add Rig"):
            if ng and ng not in st.session_state.GIANS:
                st.session_state.GIANS.append(ng); save_config_rigs(st.session_state.GIANS); st.rerun()
        dg = st.selectbox("❌ Delete Rig:", st.session_state.GIANS)
        if st.button("Delete Rig"):
            st.session_state.GIANS.remove(dg); save_config_rigs(st.session_state.GIANS); st.rerun()

    with st.expander("👤 Personnel Management"):
        new_per = st.text_input("➕ Add Employee:").strip()
        if st.button("Add Employee"):
            if new_per and new_per not in st.session_state.NAMES:
                st.session_state.NAMES.append(new_per); save_config_names(st.session_state.NAMES); st.session_state.store.clear(); st.rerun()
        del_per = st.selectbox("❌ Delete Employee:", st.session_state.NAMES)
        if st.button("Delete Employee"):
            st.session_state.NAMES.remove(del_per); save_config_names(st.session_state.NAMES); st.session_state.store.clear(); st.rerun()

    if st.button("🔄 REFRESH SYSTEM"):
        st.cache_data.clear(); st.session_state.clear(); st.rerun()
