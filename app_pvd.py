import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff; font-size: 36px; font-weight: bold;
        text-align: center; margin: 0; text-shadow: 2px 2px 4px #000; line-height: 1.5;
    }
    .stButton>button {border-radius: 5px; height: 3em; font-weight: bold;}
    div[data-testid="stDateInput"] {float: right;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER ---
c1, c2, c3 = st.columns([1.5, 4, 1.5])
with c1:
    if os.path.exists("logo_pvd.png"): st.image("logo_pvd.png", width=180)
    else: st.write("### PVD LOGO")

with c2:
    st.markdown('<p class="main-title">PVD WELL SERVICES MANAGEMENT</p>', unsafe_allow_html=True)

with c3:
    st.write("##") 
    working_date = st.date_input("📅 THÁNG LÀM VIỆC:", value=date.today())

st.write("---")

# --- 3. KHỞI TẠO BIẾN ---
conn = st.connection("gsheets", type=GSheetsConnection)
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b") 
sheet_name = working_date.strftime("%m_%Y") 

# Danh sách nhân viên (Đảm bảo đủ 65 phần tử cho range 1-65)
NAMES_64 = [
    "Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", 
    "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", 
    "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", 
    "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", 
    "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", 
    "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", 
    "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", 
    "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", 
    "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", 
    "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", 
    "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong"
]

if 'gians' not in st.session_state:
    st.session_state.gians = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9" , "THOR", "SDE" , "GUNNLOD"]

# --- 4. LOAD DỮ LIỆU ---
@st.cache_data(ttl=60)
def load_data_from_gsheets(s_name):
    try:
        return conn.read(worksheet=s_name, ttl=0)
    except:
        return None

# Xử lý Logic Load
if 'active_sheet' not in st.session_state or st.session_state.active_sheet != sheet_name:
    st.session_state.active_sheet = sheet_name
    df_load = load_data_from_gsheets(sheet_name)
    
    if df_load is not None and not df_load.empty:
        st.session_state.db = df_load
    else:
        # Tạo mới hoàn toàn nếu không thấy sheet
        df_init = pd.DataFrame({
            'STT': range(1, 65),
            'Họ và Tên': NAMES_64,
            'Công ty': 'PVDWS',
            'Chức danh': 'Kỹ sư',
            'Job Detail': '',
            'CA Tháng Trước': 0.0
        })
        st.session_state.db = df_init

# Đảm bảo các cột ngày tồn tại
num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
for c in DATE_COLS:
    if c not in st.session_state.db.columns: st.session_state.db[c] = ""

# --- 5. TÍNH TOÁN & ÉP KIỂU "SẠCH" ---
def finalize_data(df):
    holidays = [date(curr_year, 1, 1), date(curr_year, 4, 30), date(curr_year, 5, 1), date(curr_year, 9, 2)]
    
    def calc_row(row):
        total = 0.0
        for col in DATE_COLS:
            val = str(row.get(col, "")).strip()
            if val in st.session_state.gians:
                d = int(col[:2])
                dt = date(curr_year, curr_month, d)
                if dt in holidays: total += 2.0
                elif dt.weekday() >= 5: total += 1.0
                else: total += 0.5
            elif val.upper() == "CA":
                total -= 1.0
        return total

    # Ép kiểu dứt điểm cho các cột số
    for col in ['CA Tháng Trước', 'Quỹ CA Tổng']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0).astype(float)
    
    df['Phát sinh trong tháng'] = df.apply(calc_row, axis=1).astype(float)
    df['Quỹ CA Tổng'] = df['CA Tháng Trước'] + df['Phát sinh trong tháng']
    return df

st.session_state.db = finalize_data(st.session_state.db)

# --- 6. GIAO DIỆN NÚT BẤM ---
bc1, bc2, _ = st.columns([1.5, 1.5, 4])
with bc1:
    if st.button("📤 UPLOAD CLOUD", use_container_width=True, type="primary"):
        conn.update(worksheet=sheet_name, data=st.session_state.db)
        st.success("Đã lưu thành công!")
with bc2:
    buffer = io.BytesIO()
    st.session_state.db.to_excel(buffer, index=False)
    st.download_button("📥 XUẤT EXCEL", buffer, file_name=f"PVD_{sheet_name}.xlsx", use_container_width=True)

# --- 7. BẢNG DỮ LIỆU ---
t1, t2, t3 = st.tabs(["🚀 ĐIỀU ĐỘNG", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN"])

with t1:
    # Cấu hình Column Config
    column_config = {
        "STT": st.column_config.NumberColumn("STT", disabled=True, width=40),
        "Họ và Tên": st.column_config.TextColumn("Họ và Tên", width=200, pinned=True),
        "Quỹ CA Tổng": st.column_config.NumberColumn("Tổng CA", format="%.1f", disabled=True),
        "CA Tháng Trước": st.column_config.NumberColumn("Tồn cũ", format="%.1f"),
    }

    # Hiển thị với Key động để tránh lỗi Cache Type
    # Sử dụng key chứa sheet_name để khi đổi tháng nó reset lại hoàn toàn bảng
    st.data_editor(
        st.session_state.db,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        height=600,
        key=f"editor_v1_{sheet_name}" 
    )

with t2:
    st.write("Danh sách giàn:", st.session_state.gians)

with t3:
    st.dataframe(st.session_state.db[['STT', 'Họ và Tên', 'Công ty']], use_container_width=True)
