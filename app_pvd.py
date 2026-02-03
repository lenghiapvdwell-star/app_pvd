import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH & THỜI GIAN ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

# Lấy tháng và năm hiện tại để làm tên Sheet (Ví dụ: 02_2026)
now = datetime.now()
current_month_year = now.strftime("%m_%Y") # Kết quả: "02_2026"
month_days = calendar.monthrange(now.year, now.month)[1] # Tự động lấy 28, 29, 30 hoặc 31 ngày
DATE_COLS = [f"{d:02d}/{now.strftime('%m')}" for d in range(1, month_days + 1)]

# --- 2. KHỞI TẠO DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

if 'db' not in st.session_state:
    try:
        # App sẽ đọc đúng Sheet của tháng hiện tại
        df_cloud = conn.read(worksheet=current_month_year)
        if df_cloud is not None and not df_cloud.empty:
            st.session_state.db = df_cloud
        else:
            st.session_state.db = pd.DataFrame()
    except:
        # Nếu chưa có Sheet tháng mới, App sẽ tạo mới từ danh sách gốc
        st.session_state.db = pd.DataFrame()

# Tạo cấu trúc nếu Sheet tháng mới chưa tồn tại
if st.session_state.db.empty:
    NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang"]
    df = pd.DataFrame({
        'STT': range(1, len(NAMES)+1), 
        'Họ và Tên': NAMES, 
        'Công ty': 'PVDWS', 
        'Chức danh': 'Kỹ sư', 
        'Job Detail': '', 
        'Dư Đầu Kỳ': 0.0, # Số dư từ tháng trước chuyển sang
        'Nghỉ Ca Còn Lại': 0.0
    })
    for c in DATE_COLS: df[c] = ""
    st.session_state.db = df

# --- 3. LOGIC TÍNH TOÁN (Cộng dồn Dư Đầu Kỳ) ---
def calculate_pvd_offshore(row):
    accrued = float(row['Dư Đầu Kỳ']) # Bắt đầu từ số dư tháng trước
    rigs = st.session_state.get('gians', ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"])
    
    for col in DATE_COLS:
        if col in row.index:
            day_val = int(col.split('/')[0])
            d_obj = date(now.year, now.month, day_val)
            weekday = d_obj.weekday()
            val = str(row[col]).strip() if pd.notna(row[col]) else ""
            
            if val in rigs: # ĐI BIỂN
                if weekday >= 5: accrued += 1.0 # T7, CN
                else: accrued += 0.5 # Thứ 2 - 6
            elif val == "CA": # NGHỈ CA
                if weekday < 5: accrued -= 1.0 # Chỉ trừ ngày thường
    return round(accrued, 2)

st.session_state.db['Nghỉ Ca Còn Lại'] = st.session_state.db.apply(calculate_pvd_offshore, axis=1)

# --- 4. GIAO DIỆN ---
st.markdown(f'<h1 style="color: #00f2ff;">PVD MANAGEMENT - THÁNG {now.strftime("%m/%Y")}</h1>', unsafe_allow_html=True)

# Nút lưu dữ liệu
if st.button("💾 CHỐT DỮ LIỆU & LƯU CLOUD"):
    # conn.update sẽ tự động tạo Sheet mới nếu tên current_month_year chưa có
    conn.update(worksheet=current_month_year, data=st.session_state.db)
    st.success(f"Đã lưu dữ liệu vào Sheet: {current_month_year}")

# Hiển thị Editor
st.data_editor(st.session_state.db, use_container_width=True, height=500)
