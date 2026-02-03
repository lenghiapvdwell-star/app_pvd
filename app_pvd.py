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
    # Khi đổi ngày này, toàn bộ logic sheet_name và prev_sheet_name sẽ chạy lại
    working_date = st.date_input("📅 Chọn Tháng làm việc:", value=date.today())
    
curr_month = working_date.month
curr_year = working_date.year
month_abbr = working_date.strftime("%b") 
sheet_name = working_date.strftime("%m_%Y") 

# Tính toán chính xác tên sheet tháng trước
first_day_curr = date(curr_year, curr_month, 1)
last_day_prev = first_day_curr - timedelta(days=1)
prev_sheet_name = last_day_prev.strftime("%m_%Y")

# --- HÀM TÍNH NGÀY LỄ TỰ ĐỘNG ---
def get_holidays(year):
    holidays = [date(year, 1, 1), date(year, 4, 30), date(year, 5, 1), date(year, 9, 2)]
    # (Giữ nguyên logic holidays của bạn...)
    if year == 2026: holidays += [date(2026, 2, 16), date(2026, 2, 17), date(2026, 2, 18), date(2026, 2, 19), date(2026, 4, 26)]
    elif year == 2027: holidays += [date(2027, 2, 5), date(2027, 2, 6), date(2027, 2, 7), date(2027, 2, 8), date(2027, 2, 9), date(2027, 4, 16)]
    return holidays

def get_vi_day(dt):
    return ["T2", "T3", "T4", "T5", "T6", "T7", "CN"][dt.weekday()]

num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({get_vi_day(date(curr_year, curr_month, d))})" for d in range(1, num_days + 1)]

# --- 2. KHỞI TẠO DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

if 'gians' not in st.session_state:
    st.session_state.gians = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9" , "THOR", "SDE" , "GUNNLOD"]

# Hàm lấy quỹ CA tháng trước (Thêm ttl=0 để luôn lấy dữ liệu mới nhất từ Cloud)
def get_prev_ca(p_sheet):
    try:
        # ttl=0 đảm bảo không lấy dữ liệu cũ trong bộ nhớ đệm
        df_prev = conn.read(worksheet=p_sheet, ttl=0)
        if df_prev is not None and 'Quỹ CA Tổng' in df_prev.columns:
            return df_prev.set_index('Họ và Tên')['Quỹ CA Tổng'].to_dict()
    except:
        return {}
    return {}

# Logic kiểm tra và nạp dữ liệu quan trọng
if 'active_sheet' not in st.session_state or st.session_state.active_sheet != sheet_name:
    st.session_state.active_sheet = sheet_name
    # Mỗi lần đổi tháng, ép buộc đi tìm số dư tháng trước đó
    prev_ca_data = get_prev_ca(prev_sheet_name) 
    
    try:
        # Thử đọc sheet hiện tại
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        if df_load is not None and not df_load.empty:
            st.session_state.db = df_load
            # CẬP NHẬT LẠI TỒN CŨ: Đảm bảo nếu tháng trước có sửa đổi thì tháng này cập nhật theo ngay
            st.session_state.db['CA Tháng Trước'] = st.session_state.db['Họ và Tên'].map(prev_ca_data).fillna(0.0)
        else: raise Exception
    except:
        # Nếu sheet chưa tồn tại, tạo bảng mới
        NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]
        df_init = pd.DataFrame({'STT': range(1, 65), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': ''})
        df_init['CA Tháng Trước'] = df_init['Họ và Tên'].map(prev_ca_data).fillna(0.0)
        for c in DATE_COLS: df_init[c] = ""
        st.session_state.db = df_init

# --- 3. LOGIC TÍNH QUỸ CA CỘNG DỒN ---
def update_logic_pvd_ws(df):
    gians = st.session_state.gians
    current_year_holidays = get_holidays(curr_year)
    
    def calc_in_month(row):
        total = 0.0
        for col in DATE_COLS:
            if col in row.index:
                val = str(row[col]).strip()
                if not val or val.lower() in ["nan", "none", ""]: continue
                try:
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
                except: continue
        return total

    df['Phát sinh trong tháng'] = df.apply(calc_in_month, axis=1)
    # Đảm bảo cột tồn cũ luôn là float
    df['CA Tháng Trước'] = pd.to_numeric(df['CA Tháng Trước'], errors='coerce').fillna(0.0)
    df['Quỹ CA Tổng'] = df['CA Tháng Trước'] + df['Phát sinh trong tháng']
    return df

# Luôn tính toán lại để hiển thị số liệu mới nhất
st.session_state.db = update_logic_pvd_ws(st.session_state.db)
main_info = ['STT', 'Họ và Tên', 'CA Tháng Trước', 'Phát sinh trong tháng', 'Quỹ CA Tổng', 'Job Detail']
st.session_state.db = st.session_state.db.reindex(columns=main_info + DATE_COLS)

# (Phần giao diện Tab 0, Tab 3 giữ nguyên như bản trước của bạn...)
# ... [Giao diện code của bạn] ...
