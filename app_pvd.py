import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH & THỜI GIAN ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

# CSS để thu nhỏ khoảng cách và làm giao diện chuyên nghiệp hơn
st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    [data-testid="stMetricValue"] {font-size: 1.5rem;}
    </style>
    """, unsafe_allow_html=True)

c_top1, c_top2 = st.columns([1, 4])
with c_top1:
    working_date = st.date_input("📅 Chọn Tháng làm việc:", value=date.today())
    
curr_month = working_date.month
curr_year = working_date.year
month_abbr = working_date.strftime("%b") 
sheet_name = working_date.strftime("%m_%Y") 

first_day_curr = date(curr_year, curr_month, 1)
last_day_prev = first_day_curr - timedelta(days=1)
prev_sheet_name = last_day_prev.strftime("%m_%Y")

# --- HÀM TÍNH NGÀY LỄ ---
def get_holidays(year):
    holidays = [date(year, 1, 1), date(year, 4, 30), date(year, 5, 1), date(year, 9, 2)]
    if year == 2026: holidays += [date(2026, 2, 16), date(2026, 2, 17), date(2026, 2, 18), date(2026, 2, 19), date(2026, 4, 26)]
    return holidays

def get_vi_day(dt):
    return ["T2", "T3", "T4", "T5", "T6", "T7", "CN"][dt.weekday()]

num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({get_vi_day(date(curr_year, curr_month, d))})" for d in range(1, num_days + 1)]

# --- 2. KHỞI TẠO DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

if 'gians' not in st.session_state:
    st.session_state.gians = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9" , "THOR", "SDE" , "GUNNLOD"]

def get_prev_ca():
    try:
        df_prev = conn.read(worksheet=prev_sheet_name, ttl=0)
        if df_prev is not None and 'Quỹ CA Tổng' in df_prev.columns:
            return df_prev.set_index('Họ và Tên')['Quỹ CA Tổng'].to_dict()
    except: return {}
    return {}

NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

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
        df_init = pd.DataFrame({'STT': range(1, 65), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': ''})
        df_init['CA Tháng Trước'] = df_init['Họ và Tên'].map(prev_ca_data).fillna(0.0)
        for c in DATE_COLS: df_init[c] = ""
        st.session_state.db = df_init

# --- 3. LOGIC TÍNH TOÁN ---
def update_logic_pvd_ws(df):
    gians = st.session_state.gians
    holidays = get_holidays(curr_year)
    def calc_in_month(row):
        total = 0.0
        for col in DATE_COLS:
            val = str(row.get(col, "")).strip()
            if not val or val.lower() in ["nan", "none", ""]: continue
            d_num = int(col.split('/')[0])
            dt = date(curr_year, curr_month, d_num)
            is_weekend = dt.weekday() >= 5
            is_holiday = dt in holidays
            if val in gians:
                if is_holiday: total += 2.0
                elif is_weekend: total += 1.0
                else: total += 0.5
            elif val.upper() == "CA":
                if not is_weekend and not is_holiday: total -= 1.0
        return total
    df['CA Tháng Trước'] = pd.to_numeric(df.get('CA Tháng Trước', 0), errors='coerce').fillna(0.0)
    df['Phát sinh trong tháng'] = df.apply(calc_in_month, axis=1)
    df['Quỹ CA Tổng'] = df['CA Tháng Trước'] + df['Phát sinh trong tháng']
    return df

st.session_state.db = update_logic_pvd_ws(st.session_state.db)

# --- 4. GIAO DIỆN ---
c_logo, c_title = st.columns([1, 5])
with c_logo:
    # Kiểm tra file logo trên GitHub (đảm bảo file tên logo_pvd.png nằm cùng thư mục app)
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=120)
    else:
        st.write("🔴 Thiếu Logo")

with c_title:
    st.markdown(f'<h2 style="color: #00f2ff; margin-top: 0px;">PVD WELL SERVICES MANAGEMENT - {sheet_name}</h2>', unsafe_allow_html=True)

tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "💾 LƯU & XUẤT"])

with tabs[0]:
    # Khu vực cập nhật nhanh
    with st.expander("🛠️ Công cụ cập nhật nhanh", expanded=False):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1.2])
        f_staff = c1.multiselect("Chọn nhân sự:", st.session_state.db['Họ và Tên'].tolist())
        f_status = c2.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm"])
        f_val = c3.selectbox("Chọn Giàn:", st.session_state.gians) if f_status == "Đi Biển" else f_status
        f_date = c4.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, num_days)))
        
        if st.button("✅ ÁP DỤNG", use_container_width=True):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                s_d, e_d = f_date
                for i in range((e_d - s_d).days + 1):
                    day = s_d + timedelta(days=i)
                    if day.month == curr_month:
                        col = f"{day.day:02d}/{month_abbr} ({get_vi_day(day)})"
                        if col in st.session_state.db.columns:
                            st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), col] = f_val
                st.rerun()

    # BẢNG DỮ LIỆU CHÍNH - Tối ưu độ rộng cột
    config = {
        "STT": st.column_config.NumberColumn("STT", width=40, disabled=True),
        "Họ và Tên": st.column_config.TextColumn("Họ và Tên", width=180, pinned=True),
        "CA Tháng Trước": st.column_config.NumberColumn("Tồn cũ", width=70, format="%.1f"),
        "Phát sinh trong tháng": st.column_config.NumberColumn("Phát sinh", width=80, format="%.1f", disabled=True),
        "Quỹ CA Tổng": st.column_config.NumberColumn("TỔNG", width=70, format="%.1f", disabled=True, pinned=True),
        "Job Detail": st.column_config.TextColumn("Ghi chú", width=150),
        "Công ty": st.column_config.TextColumn("Công ty", width=80),
        "Chức danh": st.column_config.TextColumn("Chức danh", width=100),
    }
    # Cấu hình tự động cho các cột ngày (thu nhỏ lại)
    for col in DATE_COLS:
        config[col] = st.column_config.TextColumn(col, width=65)

    st.data_editor(
        st.session_state.db,
        column_config=config,
        use_container_width=True,
        height=600,
        hide_index=True,
        key=f"editor_{sheet_name}"
    )

with tabs[1]:
    st.subheader("🏗️ Danh sách Giàn khoan")
    # Hiển thị giàn dạng DataFrame cho đẹp
    df_gians = pd.DataFrame({"Tên Giàn": st.session_state.gians})
    st.dataframe(df_gians, use_container_width=True)
    
    new_g = st.text_input("Nhập tên giàn mới:")
    if st.button("➕ Thêm Giàn"):
        if new_g and new_g not in st.session_state.gians:
            st.session_state.gians.append(new_g)
            st.rerun()

with tabs[2]:
    st.subheader("👤 Danh sách nhân sự")
    st.dataframe(st.session_state.db[['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail']], use_container_width=True, hide_index=True)

with tabs[3]:
    st.header("💾 Quản lý dữ liệu")
    if st.button("📤 UPLOAD LÊN GOOGLE SHEETS (CHỐT SỐ)", use_container_width=True, type="primary"):
        conn.update(worksheet=sheet_name, data=st.session_state.db)
        st.success(f"Đã cập nhật dữ liệu tháng {sheet_name} thành công!")
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        st.session_state.db.to_excel(writer, index=False, sheet_name=sheet_name)
    st.download_button("📥 TẢI FILE EXCEL", buffer, file_name=f"PVD_{sheet_name}.xlsx", use_container_width=True)
