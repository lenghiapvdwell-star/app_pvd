import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 0.5rem; padding-bottom: 0rem;}
    
    /* Logo cố định ở góc trái */
    .logo-fixed {
        position: absolute;
        top: -10px;
        left: 0px;
        z-index: 1000;
    }
    
    /* Tiêu đề chính GẤP 2.5 LẦN, căn giữa tuyệt đối */
    .main-title {
        color: #00f2ff; 
        font-size: 90px; /* Điều chỉnh về mức 2.5 lần */
        font-weight: bold;
        text-align: center; 
        width: 100%;
        margin-top: 15px;
        margin-bottom: 15px;
        text-shadow: 4px 4px 8px #000;
        font-family: 'Arial Black', sans-serif;
        letter-spacing: 1.5px;
        line-height: 1.1;
    }
    
    .stButton>button {border-radius: 5px; height: 3em; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. HIỂN THỊ HEADER ---

# Hiển thị Logo
c_logo, _ = st.columns([1, 4])
with c_logo:
    if os.path.exists("logo_pvd.png"): 
        st.image("logo_pvd.png", width=220) 
    else: 
        st.markdown("### 🔴 PVD")

# Hiển thị Tiêu đề (Gấp 2.5 lần)
st.markdown('<p class="main-title">PVD WELL SERVICES MANAGEMENT</p>', unsafe_allow_html=True)

# Hiển thị Ô chọn ngày (Căn giữa)
_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

st.write("---")

# --- 3. DỮ LIỆU & KẾT NỐI ---
conn = st.connection("gsheets", type=GSheetsConnection)
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b") 
sheet_name = working_date.strftime("%m_%Y") 

if 'gians' not in st.session_state:
    st.session_state.gians = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9" , "THOR", "SDE" , "GUNNLOD"]

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

def get_prev_ca():
    prev_date = date(curr_year, curr_month, 1) - timedelta(days=1)
    prev_sheet = prev_date.strftime("%m_%Y")
    try:
        df_prev = conn.read(worksheet=prev_sheet, ttl=0)
        series = df_prev.set_index('Họ và Tên')['Quỹ CA Tổng']
        return pd.to_numeric(series, errors='coerce').fillna(0.0).to_dict()
    except: return {}

if 'active_sheet' not in st.session_state or st.session_state.active_sheet != sheet_name:
    st.session_state.active_sheet = sheet_name
    prev_ca_data = get_prev_ca()
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        if df_load is not None and not df_load.empty:
            st.session_state.db = df_load
            st.session_state.db['CA Tháng Trước'] = st.session_state.db['Họ và Tên'].map(prev_ca_data).fillna(0.0)
        else: raise Exception
    except:
        df_init = pd.DataFrame({'STT': range(1, 66), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Casing Crew', 'Job Detail': '', 'CA Tháng Trước': 0.0})
        df_init['CA Tháng Trước'] = df_init['Họ và Tên'].map(prev_ca_data).fillna(0.0)
        st.session_state.db = df_init

num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
for c in DATE_COLS:
    if c not in st.session_state.db.columns: st.session_state.db[c] = ""

def apply_calculation(df):
    holidays = [date(curr_year, 1, 1), date(curr_year, 4, 30), date(curr_year, 5, 1), date(curr_year, 9, 2)]
    if curr_year == 2026: holidays += [date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19)]
    
    def calc_row(row):
        total = 0.0
        for col in DATE_COLS:
            val = str(row.get(col, "")).strip()
            if not val or val.lower() in ["nan", ""]: continue
            d = int(col[:2])
            dt = date(curr_year, curr_month, d)
            if val in st.session_state.gians:
                if dt in holidays: total += 2.0
                elif dt.weekday() >= 5: total += 1.0
                else: total += 0.5
            elif val.upper() == "CA" and dt.weekday() < 5 and dt not in holidays:
                total -= 1.0
        return total

    df['CA Tháng Trước'] = pd.to_numeric(df['CA Tháng Trước'], errors='coerce').fillna(0.0).astype(float)
    df['Phát sinh trong tháng'] = df.apply(calc_row, axis=1).astype(float)
    df['Quỹ CA Tổng'] = df['CA Tháng Trước'] + df['Phát sinh trong tháng']
    return df

st.session_state.db = apply_calculation(st.session_state.db)

# Sắp xếp cột: STT ĐẦU TIÊN TUYỆT ĐỐI
main_cols = ['STT', 'Họ và Tên', 'Quỹ CA Tổng', 'CA Tháng Trước', 'Công ty', 'Chức danh', 'Job Detail']
st.session_state.db = st.session_state.db.reindex(columns=main_cols + DATE_COLS)

# --- 4. NÚT CHỨC NĂNG ---
bc1, bc2, _ = st.columns([1.5, 1.5, 5])
with bc1:
    if st.button("📤 LƯU CLOUD", use_container_width=True, type="primary"):
        conn.update(worksheet=sheet_name, data=st.session_state.db)
        st.success("Đã lưu dữ liệu!")
with bc2:
    buffer = io.BytesIO()
    st.session_state.db.to_excel(buffer, index=False)
    st.download_button("📥 XUẤT EXCEL", buffer, file_name=f"PVD_WS_{sheet_name}.xlsx", use_container_width=True)

# --- 5. TABS ---
t1, t2, t3 = st.tabs(["🚀 ĐIỀU ĐỘNG", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN"])

with t1:
    with st.expander("🛠️ Công cụ cập nhật nhanh"):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1.2])
        f_staff = c1.multiselect("Nhân sự:", st.session_state.db['Họ và Tên'].tolist())
        f_status = c2.selectbox("Trạng thái:", ["Đi Biển", "CA", "NP", "Ốm", "WS"])
        f_val = c3.selectbox("Giàn:", st.session_state.gians) if f_status == "Đi Biển" else f_status
        f_date = c4.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, num_days)))
        
        if st.button("✅ ÁP DỤNG", use_container_width=True):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                s_d, e_d = f_date
                for i in range((e_d - s_d).days + 1):
                    day = s_d + timedelta(days=i)
                    if day.month == curr_month:
                        col = f"{day.day:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][day.weekday()]})"
                        if col in st.session_state.db.columns:
                            st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), col] = f_val
                st.rerun()

    config = {
        "STT": st.column_config.NumberColumn("STT", width=40, disabled=True, pinned=True),
        "Họ và Tên": st.column_config.TextColumn("Họ và Tên", width=180, pinned=True),
        "Quỹ CA Tổng": st.column_config.NumberColumn("T ca", width=65, format="%.1f", disabled=True, pinned=True),
        "CA Tháng Trước": st.column_config.NumberColumn("Tồn cũ", width=65, format="%.1f", pinned=True),
    }
    for col in DATE_COLS: config[col] = st.column_config.TextColumn(col, width=75)

    st.data_editor(st.session_state.db, column_config=config, use_container_width=True, height=600, hide_index=True, key=f"final_v12_{sheet_name}")

with t2:
    st.subheader("🏗️ Quản lý danh sách Giàn khoan")
    st.dataframe(pd.DataFrame({"Tên Giàn": st.session_state.gians}), use_container_width=True)
    cg1, cg2 = st.columns([3, 1])
    new_g = cg1.text_input("Thêm giàn mới:")
    if cg2.button("➕ Thêm"):
        if new_g and new_g not in st.session_state.gians:
            st.session_state.gians.append(new_g)
            st.rerun()

with t3:
    st.subheader("👤 Nhân sự PVDWS")
    st.dataframe(st.session_state.db[['STT', 'Họ và Tên', 'Công ty', 'Chức danh']], use_container_width=True, hide_index=True)
