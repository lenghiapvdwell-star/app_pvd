import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import plotly.express as px

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

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

# --- 2. HEADER ---
c_logo, _ = st.columns([1, 4])
with c_logo:
    logo_path = "logo_pvd.png" 
    if os.path.exists(logo_path): st.image(logo_path, width=180)
    else: st.markdown("### 🔴 PVD WELL")

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. CHỌN THÁNG ---
_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today(), key="main_date_picker")

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b") 

# Xác định tháng trước để lấy "Tồn Cũ"
prev_date = working_date.replace(day=1) - timedelta(days=1)
prev_sheet_name = prev_date.strftime("%m_%Y")

if "current_sheet" not in st.session_state: st.session_state.current_sheet = sheet_name
if st.session_state.current_sheet != sheet_name:
    for key in list(st.session_state.keys()):
        if key.startswith("ed_") or key == "db": del st.session_state[key]
    st.session_state.current_sheet = sheet_name
    st.rerun()

# --- 4. KẾT NỐI & DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)
GIANS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong"]

def get_prev_ton_dau():
    """Lấy kết quả Quỹ CA Tổng của tháng trước để làm Tồn Cũ tháng này"""
    try:
        df_prev = conn.read(worksheet=prev_sheet_name, ttl=0)
        if df_prev is not None and 'Quỹ CA Tổng' in df_prev.columns:
            return df_prev.set_index('Họ và Tên')['Quỹ CA Tổng'].to_dict()
    except: return {}
    return {}

if 'db' not in st.session_state:
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        if df_load is not None and not df_load.empty:
            st.session_state.db = df_load
        else: raise Exception
    except:
        # Nếu là tháng mới chưa có dữ liệu, bê Tồn Cũ từ Quỹ CA Tổng tháng trước qua
        prev_map = get_prev_ton_dau()
        st.session_state.db = pd.DataFrame({
            'STT': range(1, 66), 
            'Họ và Tên': NAMES_64[:65], 
            'Công ty': 'PVDWS', 
            'Chức danh': 'Casing crew', 
            'Job Detail': '', 
            'CA Tháng Trước': [prev_map.get(name, 0.0) for name in NAMES_64[:65]],
            'Quỹ CA Tổng': 0.0
        })

num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
for col in DATE_COLS:
    if col not in st.session_state.db.columns: st.session_state.db[col] = ""

# --- 5. LOGIC TÍNH CA (GIỮ NGUYÊN) ---
def calculate_pvd_logic(df):
    hols = [date(2026,1,1), date(2026,4,30), date(2026,5,1), date(2026,9,2),
            date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19)]
    
    def row_calc(row):
        accrued = 0.0
        for col in DATE_COLS:
            v = str(row.get(col, "")).strip().upper()
            if not v or v in ["NAN", "NONE", ""]: continue
            try:
                dt = date(curr_year, curr_month, int(col[:2]))
                is_we = dt.weekday() >= 5
                is_ho = dt in hols
                if any(g.upper() in v for g in GIANS):
                    if is_ho: accrued += 2.0
                    elif is_we: accrued += 1.0
                    else: accrued += 0.5
                elif v == "CA":
                    if not is_we and not is_ho: accrued -= 1.0
            except: continue
        return accrued

    df['CA Tháng Trước'] = pd.to_numeric(df['CA Tháng Trước'], errors='coerce').fillna(0.0)
    # TỔNG CA (Quỹ CA Tổng) = Tồn Cũ (CA Tháng Trước) + Phát sinh trong tháng
    df['Quỹ CA Tổng'] = df['CA Tháng Trước'] + df.apply(row_calc, axis=1)
    return df

st.session_state.db = calculate_pvd_logic(st.session_state.db)

# --- 6. GIAO DIỆN ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ"])

with t1:
    bc1, bc2, _ = st.columns([1.5, 1.5, 5])
    with bc1:
        if st.button("📤 LƯU CLOUD", type="primary", use_container_width=True):
            try:
                conn.update(worksheet=sheet_name, data=st.session_state.db)
                st.success("Đã lưu!")
            except: st.error("Lỗi kết nối.")

    with bc2:
        buf = io.BytesIO()
        st.session_state.db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf, f"PVD_{sheet_name}.xlsx", use_container_width=True)

    # Bảng Editor
    config = {
        "STT": st.column_config.NumberColumn(disabled=True),
        "Họ và Tên": st.column_config.TextColumn(disabled=True),
        "CA Tháng Trước": st.column_config.NumberColumn("Tồn Cũ", format="%.1f"),
        "Quỹ CA Tổng": st.column_config.NumberColumn("Tổng ca", format="%.1f", disabled=True),
    }
    
    # Hiển thị bảng
    ed_df = st.data_editor(st.session_state.db, column_config=config, use_container_width=True, height=600, hide_index=True, key=f"ed_{sheet_name}")
    if not ed_df.equals(st.session_state.db):
        st.session_state.db = ed_df
        st.rerun()

# --- BIỂU ĐỒ (GIỮ NGUYÊN) ---
with t2:
    st.info("Biểu đồ phân tích dữ liệu 12 tháng.")
