import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH & THỜI GIAN ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff;
        font-size: 32px;
        font-weight: bold;
        text-align: center;
        margin: 0;
        text-shadow: 2px 2px 4px #000;
    }
    .stButton>button {border-radius: 5px; height: 3em;}
    </style>
    """, unsafe_allow_html=True)

# --- HEADER: LOGO - TIÊU ĐỀ - NGÀY ---
c_logo, c_title, c_date = st.columns([1.5, 4, 1.5])
with c_logo:
    if os.path.exists("logo_pvd.png"): st.image("logo_pvd.png", width=180)
    else: st.write("### PVD LOGO")

with c_title:
    st.markdown('<p class="main-title">PVD WELL SERVICES MANAGEMENT</p>', unsafe_allow_html=True)

with c_date:
    st.write("##")
    working_date = st.date_input("📅 THÁNG LÀM VIỆC:", value=date.today())

curr_month = working_date.month
curr_year = working_date.year
month_abbr = working_date.strftime("%b") 
sheet_name = working_date.strftime("%m_%Y") 

# --- HÀM HỖ TRỢ ---
def get_holidays(year):
    holidays = [date(year, 1, 1), date(year, 4, 30), date(year, 5, 1), date(year, 9, 2)]
    if year == 2026: holidays += [date(2026, 2, 16), date(2026, 2, 17), date(2026, 2, 18), date(2026, 2, 19), date(2026, 4, 26)]
    return holidays

def get_vi_day(dt):
    return ["T2", "T3", "T4", "T5", "T6", "T7", "CN"][dt.weekday()]

num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({get_vi_day(date(curr_year, curr_month, d))})" for d in range(1, num_days + 1)]

# --- 2. KẾT NỐI & TỰ ĐỘNG LOAD DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

if 'gians' not in st.session_state:
    st.session_state.gians = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9" , "THOR", "SDE" , "GUNNLOD"]

# Hàm lấy CA tồn từ tháng trước
def get_prev_ca_logic():
    last_day_prev = date(curr_year, curr_month, 1) - timedelta(days=1)
    prev_sheet = last_day_prev.strftime("%m_%Y")
    try:
        df_prev = conn.read(worksheet=prev_sheet, ttl=0)
        return df_prev.set_index('Họ và Tên')['Quỹ CA Tổng'].to_dict()
    except: return {}

# QUAN TRỌNG: Tự động tải dữ liệu khi đổi tháng hoặc mở app
if 'active_sheet' not in st.session_state or st.session_state.active_sheet != sheet_name:
    st.session_state.active_sheet = sheet_name
    prev_ca_data = get_prev_ca_logic()
    
    try:
        # Thử đọc từ Google Sheets trước
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        if df_load is not None and not df_load.empty:
            st.session_state.db = df_load
            # Luôn cập nhật lại CA Tồn cũ từ tháng trước để đảm bảo tính liên tục
            st.session_state.db['CA Tháng Trước'] = st.session_state.db['Họ và Tên'].map(prev_ca_data).fillna(0.0)
        else: raise Exception
    except:
        # Nếu Sheets chưa có (tháng mới), tạo bảng trắng
        NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]
        df_init = pd.DataFrame({'STT': range(1, 65), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': ''})
        df_init['CA Tháng Trước'] = df_init['Họ và Tên'].map(prev_ca_data).fillna(0.0)
        for c in DATE_COLS: df_init[c] = ""
        st.session_state.db = df_init

# --- 3. LOGIC TÍNH TOÁN ---
def update_logic(df):
    holidays = get_holidays(curr_year)
    def calc_in_month(row):
        total = 0.0
        for col in DATE_COLS:
            val = str(row.get(col, "")).strip()
            if not val or val.lower() in ["nan", "none", ""]: continue
            try:
                d_num = int(col.split('/')[0])
                dt = date(curr_year, curr_month, d_num)
                is_weekend = dt.weekday() >= 5
                is_holiday = dt in holidays
                if val in st.session_state.gians:
                    if is_holiday: total += 2.0
                    elif is_weekend: total += 1.0
                    else: total += 0.5
                elif val.upper() == "CA":
                    if not is_weekend and not is_holiday: total -= 1.0
            except: continue
        return total
    df['CA Tháng Trước'] = pd.to_numeric(df.get('CA Tháng Trước', 0), errors='coerce').fillna(0.0)
    df['Phát sinh trong tháng'] = df.apply(calc_in_month, axis=1)
    df['Quỹ CA Tổng'] = df['CA Tháng Trước'] + df['Phát sinh trong tháng']
    return df

st.session_state.db = update_logic(st.session_state.db)
cols_order = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail', 'Quỹ CA Tổng', 'CA Tháng Trước'] + DATE_COLS
st.session_state.db = st.session_state.db.reindex(columns=[c for c in cols_order if c in st.session_state.db.columns])

# --- 4. CÁC NÚT THAO TÁC NHANH (ĐÃ ĐƯA RA NGOÀI) ---
st.write("---")
c_btn1, c_btn2, _ = st.columns([1.5, 1.5, 4])
with c_btn1:
    if st.button("📤 UPLOAD CLOUD", use_container_width=True, type="primary"):
        conn.update(worksheet=sheet_name, data=st.session_state.db)
        st.success(f"Đã lưu dữ liệu {sheet_name} lên Cloud!")

with c_btn2:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        st.session_state.db.to_excel(writer, index=False, sheet_name=sheet_name)
    st.download_button("📥 XUẤT EXCEL", buffer, file_name=f"PVD_{sheet_name}.xlsx", use_container_width=True)

# --- 5. TABS CHỨC NĂNG ---
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN"])

with tabs[0]:
    with st.expander("🛠️ Cập nhật nhanh"):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1.2])
        f_staff = c1.multiselect("Nhân sự:", st.session_state.db['Họ và Tên'].tolist())
        f_status = c2.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm"])
        f_val = c3.selectbox("Giàn:", st.session_state.gians) if f_status == "Đi Biển" else f_status
        f_date = c4.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, num_days)))
        if st.button("✅ CẬP NHẬT", use_container_width=True):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                s_d, e_d = f_date
                for i in range((e_d - s_d).days + 1):
                    day = s_d + timedelta(days=i)
                    if day.month == curr_month:
                        col = f"{day.day:02d}/{month_abbr} ({get_vi_day(day)})"
                        if col in st.session_state.db.columns:
                            st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), col] = f_val
                st.rerun()

    config = {
        "STT": st.column_config.NumberColumn("STT", width=40, disabled=True, pinned=True),
        "Họ và Tên": st.column_config.TextColumn("Họ và Tên", width=180, pinned=True),
        "Công ty": st.column_config.TextColumn("Công ty", width=80),
        "Chức danh": st.column_config.TextColumn("Chức danh", width=100),
        "Job Detail": st.column_config.TextColumn("Job Detail", width=120),
        "Quỹ CA Tổng": st.column_config.NumberColumn("T ca", width=70, format="%.1f", disabled=True, pinned=True),
        "CA Tháng Trước": st.column_config.NumberColumn("Tồn cũ", width=70, format="%.1f", pinned=True),
    }
    for col in DATE_COLS: config[col] = st.column_config.TextColumn(col, width=65)

    st.data_editor(st.session_state.db, column_config=config, use_container_width=True, height=600, hide_index=True, key=f"ed_{sheet_name}")

with tabs[1]:
    st.subheader("🏗️ Quản lý Giàn khoan")
    st.dataframe(pd.DataFrame({"Tên Giàn": st.session_state.gians}), use_container_width=True)
    new_g = st.text_input("Thêm giàn mới:")
    if st.button("➕ Thêm"):
        if new_g and new_g not in st.session_state.gians:
            st.session_state.gians.append(new_g)
            st.rerun()

with tabs[2]:
    st.subheader("👤 Danh sách nhân sự")
    st.dataframe(st.session_state.db[['STT', 'Họ và Tên', 'Công ty', 'Chức danh']], use_container_width=True, hide_index=True)
