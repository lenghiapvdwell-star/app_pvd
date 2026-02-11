import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import time
import plotly.express as px

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="PVD MANAGEMENT PRO", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 0.5rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; font-size: 45px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 3px 3px 6px #000 !important;
        font-family: 'Arial Black', sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO ---
c_logo, _ = st.columns([1, 4])
with c_logo:
    if os.path.exists("logo_pvd.png"): st.image("logo_pvd.png", width=180)
    else: st.markdown("### 🔴 PVD WELL")

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. KẾT NỐI ---
conn = st.connection("gsheets", type=GSheetsConnection)

def save_to_cloud_silent(worksheet_name, df):
    df_clean = df.fillna("").replace(["nan", "NaN", "None"], "")
    try:
        conn.update(worksheet=worksheet_name, data=df_clean)
        st.cache_data.clear()
        return True
    except: return False

# --- 4. DANH MỤC ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]

# --- 5. THỜI GIAN ---
_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today(), key="date_selector")

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
num_days_curr = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{working_date.strftime('%b')} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days_curr+1)]

# --- 6. ENGINE CẢI TIẾN (FIX LỖI AUTOFILL) ---
def auto_engine(df):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    now = datetime.now()
    today = now.date()
    df_calc = df.copy()
    data_changed = False
    
    for idx, row in df_calc.iterrows():
        accrued = 0.0
        # TRUY VẾT GIÁ TRỊ GẦN NHẤT
        last_val = ""
        
        for col in DATE_COLS:
            if col not in df_calc.columns: df_calc[col] = ""
            d_num = int(col[:2])
            target_date = date(curr_year, curr_month, d_num)
            val = str(df_calc.at[idx, col]).strip()
            
            # Nếu ô trống -> Thử Autofill
            if (val == "" or val.lower() == "nan") and (target_date < today or (target_date == today and now.hour >= 6)):
                if last_val != "":
                    lv_up = last_val.upper()
                    if any(g.upper() in lv_up for g in st.session_state.GIANS) or lv_up in ["CA", "WS"]:
                        df_calc.at[idx, col] = last_val
                        val = last_val
                        data_changed = True
            
            if val != "" and val.lower() != "nan":
                last_val = val # Cập nhật giá trị mốc
            
            # TÍNH CA KỊP
            v_up = val.upper()
            if v_up:
                is_we = target_date.weekday() >= 5
                is_ho = target_date in hols
                if any(g.upper() in v_up for g in st.session_state.GIANS):
                    if is_ho: accrued += 2.0
                    elif is_we: accrued += 1.0
                    else: accrued += 0.5
                elif v_up == "CA":
                    if not is_we and not is_ho: accrued -= 1.0
        
        ton_cu = float(row.get('CA Tháng Trước', 0))
        df_calc.at[idx, 'Quỹ CA Tổng'] = round(ton_cu + accrued, 1)
        
    return df_calc, data_changed

# --- 7. LOAD & SYNC ---
if 'active_sheet' not in st.session_state or st.session_state.active_sheet != sheet_name:
    st.session_state.active_sheet = sheet_name
    if 'db' in st.session_state: del st.session_state.db

if 'db' not in st.session_state:
    with st.spinner("🔄 Đang đồng bộ dữ liệu..."):
        # Lấy tồn cũ
        prev_sheet = (working_date.replace(day=1) - timedelta(days=1)).strftime("%m_%Y")
        b_map = {}
        try:
            df_p = conn.read(worksheet=prev_sheet, ttl="1m")
            b_map = dict(zip(df_p['Họ và Tên'], df_p['Quỹ CA Tổng']))
        except: pass

        # Đọc sheet hiện tại
        try:
            df_l = conn.read(worksheet=sheet_name, ttl=0).fillna("")
            if df_l.empty or len(df_l) < 10: raise ValueError
        except:
            df_l = pd.DataFrame({'STT': range(1, len(NAMES_66)+1), 'Họ và Tên': NAMES_66, 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Job Detail': '', 'CA Tháng Trước': [float(b_map.get(n, 0.0)) for n in NAMES_66], 'Quỹ CA Tổng': 0.0})

        # Chạy Engine và ÉP LƯU
        df_final, has_up = auto_engine(df_l)
        if has_up: save_to_cloud_silent(sheet_name, df_final)
        st.session_state.db = df_final

# --- 8. GIAO DIỆN ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ"])

with t1:
    c1, c2, c3 = st.columns(3)
    if c1.button("📤 LƯU CLOUD", use_container_width=True, type="primary"):
        df_s, _ = auto_engine(st.session_state.db)
        if save_to_cloud_silent(sheet_name, df_s): st.toast("✅ Đã lưu!"); st.rerun()
    if c2.button("🔄 LÀM MỚI", use_container_width=True): 
        st.cache_data.clear(); del st.session_state.db; st.rerun()
    c3.download_button("📥 EXCEL", st.session_state.db.to_csv().encode('utf-8-sig'), f"PVD_{sheet_name}.csv", use_container_width=True)

    with st.expander("🛠️ CÔNG CỤ NHẬP NHANH"):
        f_staff = st.multiselect("Nhân sự:", NAMES_66)
        f_date = st.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, num_days_curr)))
        r1, r2 = st.columns(2)
        f_status = r1.selectbox("Trạng thái:", ["Xóa", "Đi Biển", "CA", "WS", "NP"])
        f_val = r2.selectbox("Giàn:", st.session_state.GIANS) if f_status == "Đi Biển" else f_status
        if st.button("✅ ÁP DỤNG"):
            for person in f_staff:
                idx = st.session_state.db.index[st.session_state.db['Họ và Tên'] == person][0]
                for i in range((f_date[1] - f_date[0]).days + 1):
                    d = f_date[0] + timedelta(days=i)
                    col = [c for c in DATE_COLS if c.startswith(f"{d.day:02d}/")][0]
                    st.session_state.db.at[idx, col] = "" if f_status == "Xóa" else f_val
            df_up, _ = auto_engine(st.session_state.db)
            st.session_state.db = df_up
            save_to_cloud_silent(sheet_name, df_up); st.rerun()

    ed_df = st.data_editor(st.session_state.db, use_container_width=True, height=600, hide_index=True,
                           column_config={"Quỹ CA Tổng": st.column_config.NumberColumn(disabled=True)})
