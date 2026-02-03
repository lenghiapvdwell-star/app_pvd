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

# Tính toán tên sheet tháng trước để lấy dữ liệu cộng dồn
first_day_curr = date(curr_year, curr_month, 1)
last_day_prev = first_day_curr - timedelta(days=1)
prev_sheet_name = last_day_prev.strftime("%m_%Y")

# --- HÀM TÍNH NGÀY LỄ TỰ ĐỘNG (2026 - 2030) ---
def get_holidays(year):
    holidays = [date(year, 1, 1), date(year, 4, 30), date(year, 5, 1), date(year, 9, 2)]
    if year == 2026: holidays += [date(2026, 2, 16), date(2026, 2, 17), date(2026, 2, 18), date(2026, 2, 19), date(2026, 4, 26)]
    elif year == 2027: holidays += [date(2027, 2, 5), date(2027, 2, 6), date(2027, 2, 7), date(2027, 2, 8), date(2027, 2, 9), date(2027, 4, 16)]
    elif year == 2028: holidays += [date(2028, 1, 25), date(2028, 1, 26), date(2028, 1, 27), date(2028, 1, 28), date(2028, 1, 29), date(2028, 4, 5)]
    elif year == 2029: holidays += [date(2029, 2, 12), date(2029, 2, 13), date(2029, 2, 14), date(2029, 2, 15), date(2029, 2, 16), date(2029, 4, 23)]
    elif year == 2030: holidays += [date(2030, 2, 2), date(2030, 2, 3), date(2030, 2, 4), date(2030, 2, 5), date(2030, 2, 6), date(2030, 4, 12)]
    return holidays

def get_vi_day(dt):
    return ["T2", "T3", "T4", "T5", "T6", "T7", "CN"][dt.weekday()]

num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({get_vi_day(date(curr_year, curr_month, d))})" for d in range(1, num_days + 1)]

# --- 2. KHỞI TẠO DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

if 'gians' not in st.session_state:
    st.session_state.gians = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9" , "THOR", "SDE" , "GUNNLOD"]

# Hàm lấy quỹ CA từ sheet của tháng trước
def get_prev_ca():
    try:
        df_prev = conn.read(worksheet=prev_sheet_name)
        if df_prev is not None and 'Quỹ CA Tổng' in df_prev.columns:
            return df_prev.set_index('Họ và Tên')['Quỹ CA Tổng'].to_dict()
    except:
        return {}
    return {}

if 'active_sheet' not in st.session_state or st.session_state.active_sheet != sheet_name:
    st.session_state.active_sheet = sheet_name
    prev_ca_data = get_prev_ca() # Lấy dữ liệu tồn cũ
    
    try:
        df_load = conn.read(worksheet=sheet_name)
        if df_load is not None and not df_load.empty:
            st.session_state.db = df_load
            # Cập nhật lại cột Tồn cũ từ tháng trước để dữ liệu luôn mới nhất
            st.session_state.db['CA Tháng Trước'] = st.session_state.db['Họ và Tên'].map(prev_ca_data).fillna(0.0)
        else: raise Exception
    except:
        NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]
        df_init = pd.DataFrame({'STT': range(1, 65), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': ''})
        # Áp dụng tồn cũ cho bảng mới tạo
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

    df['Phát sinh trong tháng'] = df.apply(calc_in_month, axis=1)
    if 'CA Tháng Trước' not in df.columns: df['CA Tháng Trước'] = 0.0
    # CÔNG THỨC CỘNG DỒN: TỔNG = TỒN CŨ + PHÁT SINH
    df['Quỹ CA Tổng'] = df['CA Tháng Trước'] + df['Phát sinh trong tháng']
    return df

st.session_state.db = update_logic_pvd_ws(st.session_state.db)
main_info = ['STT', 'Họ và Tên', 'CA Tháng Trước', 'Phát sinh trong tháng', 'Quỹ CA Tổng', 'Job Detail']
st.session_state.db = st.session_state.db.reindex(columns=main_info + DATE_COLS)

# --- 4. GIAO DIỆN ---
c_logo, c_title = st.columns([1.5, 5])
with c_logo:
    if os.path.exists("logo_pvd.png"): st.image("logo_pvd.png", width=180)
    else: st.markdown("### PVD LOGO")
with c_title:
    st.markdown(f'<h1 style="color: #00f2ff; margin-top: 15px;">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "💾 LƯU & XUẤT FILE"])

with tabs[0]:
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1.2])
        f_staff = c1.multiselect("Nhân viên:", st.session_state.db['Họ và Tên'].tolist())
        f_status = c2.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm"])
        if f_status == "Đi Biển": f_val = c3.selectbox("Chọn Giàn:", st.session_state.gians)
        else: f_val = f_status
        f_date = c4.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, 2)))
        
        if st.button("✅ CẬP NHẬT VÀO BẢNG", use_container_width=True):
            if f_staff and isinstance(f_date, tuple):
                start_d = f_date[0]
                end_d = f_date[1] if len(f_date) > 1 else f_date[0]
                delta = end_d - start_d
                for i in range(delta.days + 1):
                    day_to_update = start_d + timedelta(days=i)
                    if day_to_update.month == curr_month and day_to_update.year == curr_year:
                        d_num = day_to_update.day
                        col_target = f"{d_num:02d}/{month_abbr} ({get_vi_day(day_to_update)})"
                        if col_target in st.session_state.db.columns:
                            st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), col_target] = f_val
                st.session_state.db = update_logic_pvd_ws(st.session_state.db)
                st.rerun()

    st.data_editor(
        st.session_state.db,
        column_config={
            "STT": st.column_config.NumberColumn("STT", width="small", disabled=True, pinned=True),
            "Họ và Tên": st.column_config.TextColumn("Họ và Tên", pinned=True, width="medium"),
            "CA Tháng Trước": st.column_config.NumberColumn("Tồn cũ", format="%.1f", help="Dư nợ CA từ tháng trước chuyển sang"),
            "Phát sinh trong tháng": st.column_config.NumberColumn("Trong tháng", format="%.1f", disabled=True),
            "Quỹ CA Tổng": st.column_config.NumberColumn("TỔNG CỘNG", format="%.1f", disabled=True, pinned=True),
        },
        use_container_width=True, height=550, key=f"table_{sheet_name}", hide_index=True
    )

with tabs[3]:
    st.header(f"💾 Dữ liệu tháng {sheet_name}")
    if st.button("📤 UPLOAD GOOGLE SHEETS (CHỐT SỔ THÁNG)", use_container_width=True, type="primary"):
        try:
            conn.update(worksheet=sheet_name, data=st.session_state.db)
            st.success(f"Đã lưu dữ liệu tháng {sheet_name}. Tháng sau sẽ tự động lấy 'Quỹ CA Tổng' làm số dư đầu kỳ.")
        except: st.error("Lỗi: Kiểm tra kết nối Google Sheets.")
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        st.session_state.db.to_excel(writer, index=False, sheet_name=sheet_name)
    st.download_button(label="📥 TẢI FILE EXCEL", data=buffer.getvalue(), file_name=f"PVD_{sheet_name}.xlsx", use_container_width=True)
