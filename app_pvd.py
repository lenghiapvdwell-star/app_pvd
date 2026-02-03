import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH & THỜI GIAN ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

c_top1, c_top2 = st.columns([1, 4])
with c_top1:
    working_date = st.date_input("📅 Chọn Tháng làm việc:", value=date.today())
    
curr_month = working_date.month
curr_year = working_date.year
month_abbr = working_date.strftime("%b") 
sheet_name = working_date.strftime("%m_%Y") 

# Tính toán tên sheet tháng trước
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
    except:
        return {}
    return {}

# Danh sách nhân viên mặc định
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

if 'active_sheet' not in st.session_state or st.session_state.active_sheet != sheet_name:
    st.session_state.active_sheet = sheet_name
    prev_ca_data = get_prev_ca() 
    
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        if df_load is not None and not df_load.empty:
            st.session_state.db = df_load
            # Kiểm tra và thêm cột thiếu để tránh lỗi KeyError
            for col in ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail']:
                if col not in st.session_state.db.columns:
                    st.session_state.db[col] = ""
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
    current_year_holidays = get_holidays(curr_year)
    
    def calc_in_month(row):
        total = 0.0
        for col in DATE_COLS:
            if col in row.index:
                val = str(row[col]).strip()
                if not val or val.lower() in ["nan", "none", ""]: continue
                d_num = int(col.split('/')[0])
                dt = date(curr_year, curr_month, d_num)
                is_weekend = dt.weekday() >= 5
                is_holiday = dt in current_year_holidays
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
main_info = ['STT', 'Họ và Tên', 'CA Tháng Trước', 'Phát sinh trong tháng', 'Quỹ CA Tổng', 'Job Detail', 'Công ty', 'Chức danh']
# Lọc các cột hiện có để reindex không bị lỗi
existing_cols = [c for c in main_info if c in st.session_state.db.columns] + [c for c in DATE_COLS if c in st.session_state.db.columns]
st.session_state.db = st.session_state.db.reindex(columns=existing_cols)

# --- 4. GIAO DIỆN ---
st.markdown(f'<h1 style="color: #00f2ff;">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "💾 LƯU & XUẤT FILE"])

with tabs[0]: # ĐIỀU ĐỘNG
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1.2])
    f_staff = c1.multiselect("Nhân viên:", st.session_state.db['Họ và Tên'].tolist())
    f_status = c2.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm"])
    f_val = c3.selectbox("Giàn:", st.session_state.gians) if f_status == "Đi Biển" else f_status
    f_date = c4.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, num_days)))
    
    if st.button("✅ CẬP NHẬT"):
        if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
            s_d, e_d = f_date
            for i in range((e_d - s_d).days + 1):
                day = s_d + timedelta(days=i)
                if day.month == curr_month:
                    col = f"{day.day:02d}/{month_abbr} ({get_vi_day(day)})"
                    if col in st.session_state.db.columns:
                        st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), col] = f_val
            st.rerun()
    st.data_editor(st.session_state.db, use_container_width=True, height=500, hide_index=True)

with tabs[1]: # GIÀN KHOAN
    st.write("Danh sách giàn:", st.session_state.gians)
    new_g = st.text_input("Thêm giàn:")
    if st.button("Thêm"):
        st.session_state.gians.append(new_g)
        st.rerun()

with tabs[2]: # NHÂN VIÊN
    # Dùng .get() để an toàn, không lo lỗi KeyError nếu mất cột
    cols_to_show = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh']
    available = [c for c in cols_to_show if c in st.session_state.db.columns]
    st.dataframe(st.session_state.db[available], use_container_width=True)

with tabs[3]: # LƯU TRỮ
    if st.button("📤 UPLOAD GOOGLE SHEETS"):
        conn.update(worksheet=sheet_name, data=st.session_state.db)
        st.success("Đã lưu!")
