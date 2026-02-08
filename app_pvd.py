import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import time

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="PVD WELL MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 0.5rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; font-size: 40px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 2px 2px 4px #000 !important;
        margin-bottom: 10px;
    }
    /* Làm nổi bật cột Quỹ CA */
    [data-testid="stTable"] td:last-child { background-color: #262730 !important; font-weight: bold; color: #00f2ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KẾT NỐI & DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_gians():
    try:
        df_config = conn.read(worksheet="CONFIG", ttl=10)
        return df_config.iloc[:, 0].dropna().astype(str).tolist()
    except:
        return ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

if "gians_list" not in st.session_state:
    st.session_state.gians_list = load_gians()

# --- 3. CHỌN THÁNG ---
_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b")

# --- 4. HÀM XỬ LÝ AUTOFILL & TÍNH TOÁN PRO ---
def process_pro_logic(df):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,2,21), date(2026,4,25), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    num_days = calendar.monthrange(curr_year, curr_month)[1]
    date_cols = [f"{d:02d}/{month_abbr}" for d in range(1, num_days+1)]
    
    df_res = df.copy()
    
    for idx, row in df_res.iterrows():
        if not str(row.get('Họ và Tên', '')).strip(): continue
        
        # Bước 1: Autofill logic "Rồng rắn"
        current_fill = ""
        for col in date_cols:
            val = str(df_res.at[idx, col]).strip()
            if val == "" or val.upper() in ["NAN", "NONE"]:
                df_res.at[idx, col] = current_fill
            else:
                current_fill = val # Cập nhật trạng thái mới để fill cho các ngày sau

        # Bước 2: Tính Quỹ CA ngay lập tức trên dữ liệu đã fill
        acc = 0.0
        for col in date_cols:
            v = str(df_res.at[idx, col]).strip().upper()
            if not v or v in ["WS", "NP", "ỐM"]: continue
            try:
                day_int = int(col[:2])
                dt = date(curr_year, curr_month, day_int)
                is_offshore = any(g.upper() in v for g in st.session_state.gians_list)
                
                if is_offshore:
                    if dt in hols: acc += 2.0
                    elif dt.weekday() >= 5: acc += 1.0
                    else: acc += 0.5
                elif v == "CA":
                    if dt.weekday() < 5 and dt not in hols: acc -= 1.0
            except: continue
        df_res.at[idx, 'Quỹ CA Tổng'] = acc
        
    return df_res

# --- 5. QUẢN LÝ SESSION STATE ---
if 'db_raw' not in st.session_state or st.session_state.get('active_sheet') != sheet_name:
    try:
        st.session_state.db_raw = conn.read(worksheet=sheet_name, ttl=0)
    except:
        st.session_state.db_raw = pd.DataFrame({'STT': range(1, 61), 'Họ và Tên': [""]*60})
    st.session_state.active_sheet = sheet_name

# --- 6. GIAO DIỆN ĐIỀU KHIỂN ---
c1, c2, c3 = st.columns([2.5, 2, 4])

if c1.button("☁️ LƯU VÀO GOOGLE SHEETS", type="primary", use_container_width=True):
    # Trước khi lưu, xử lý logic một lần nữa cho chắc chắn
    final_df = process_pro_logic(st.session_state.db_raw)
    conn.update(worksheet=sheet_name, data=final_df)
    st.success("Đã đồng bộ Cloud thành công!")
    st.rerun()

# --- 7. BẢNG NHẬP LIỆU "PRO" ---
st.info("⚡ **CHẾ ĐỘ AUTO PRO:** Nhập 1 ngày (VD: PVD8), các ngày trống phía sau sẽ tự nhảy theo và Quỹ CA tự tính.")

# Hiển thị bảng tính toán thời gian thực
display_df = process_pro_logic(st.session_state.db_raw)

edited_df = st.data_editor(
    display_df,
    use_container_width=True,
    height=650,
    hide_index=True,
    key="pvd_pro_editor"
)

# Cập nhật lại db_raw khi người dùng sửa
st.session_state.db_raw = edited_df

# Nút bổ sung dưới bảng để hỗ trợ người dùng
if st.button("🔄 Cập nhật lại toàn bộ bảng"):
    st.rerun()
