import streamlit as st
import pandas as pd
from datetime import datetime, date
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

# Danh sách ngày Lễ/Tết năm 2026
HOLIDAYS_2026 = [
    date(2026, 1, 1), date(2026, 2, 16), date(2026, 2, 17), 
    date(2026, 2, 18), date(2026, 2, 19), date(2026, 4, 26), 
    date(2026, 4, 30), date(2026, 5, 1), date(2026, 9, 2),
]

def get_vi_day(dt):
    return ["T2", "T3", "T4", "T5", "T6", "T7", "CN"][dt.weekday()]

num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({get_vi_day(date(curr_year, curr_month, d))})" for d in range(1, num_days + 1)]

# --- 2. KHỞI TẠO DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

if 'gians' not in st.session_state:
    st.session_state.gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

if 'active_sheet' not in st.session_state or st.session_state.active_sheet != sheet_name:
    st.session_state.active_sheet = sheet_name
    try:
        df_load = conn.read(worksheet=sheet_name)
        if df_load is not None and not df_load.empty:
            st.session_state.db = df_load
        else: raise Exception
    except:
        NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]
        df_init = pd.DataFrame({
            'STT': range(1, 65), 
            'Họ và Tên': NAMES_64, 
            'Công ty': 'PVDWS', 
            'Chức danh': 'Kỹ sư', 
            'Job Detail': ''
        })
        for c in DATE_COLS: df_init[c] = ""
        st.session_state.db = df_init

# --- 3. LOGIC TÍNH QUỸ CA ---
def update_logic_pvd_ws(df):
    gians = st.session_state.gians
    def calc_row(row):
        total_ca = 0.0
        for col in DATE_COLS:
            if col in row.index:
                val = str(row[col]).strip()
                if not val or val.lower() in ["nan", "none", ""]: continue
                d_num = int(col.split('/')[0])
                dt = date(curr_year, curr_month, d_num)
                is_weekend = dt.weekday() >= 5
                is_holiday = dt in HOLIDAYS_2026
                if val in gians:
                    if is_holiday: total_ca += 2.0
                    elif is_weekend: total_ca += 1.0
                    else: total_ca += 0.5
                elif val.upper() == "CA":
                    if not is_weekend and not is_holiday: total_ca -= 1.0
        return total_ca
    df['Quỹ CA'] = df.apply(calc_row, axis=1)
    return df

st.session_state.db = update_logic_pvd_ws(st.session_state.db)

# SẮP XẾP THỨ TỰ CỘT THEO YÊU CẦU: STT -> Họ và Tên -> ...
main_info = ['Họ và Tên', 'STT', 'Công ty', 'Chức danh', 'Job Detail', 'Quỹ CA']
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
        else:
            f_val = f_status
            c3.text_input("Ghi chú:", value=f_status, disabled=True)
        f_date = c4.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, 2)))
        if st.button("✅ CẬP NHẬT VÀO BẢNG", use_container_width=True):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                for d in range(f_date[0].day, f_date[1].day + 1):
                    dt_temp = date(curr_year, curr_month, d)
                    col_target = f"{d:02d}/{month_abbr} ({get_vi_day(dt_temp)})"
                    if col_target in st.session_state.db.columns:
                        st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), col_target] = f_val
                st.rerun()

    st.data_editor(
        st.session_state.db,
        column_config={
            "STT": st.column_config.NumberColumn("STT", width="small", disabled=True),
            "Quỹ CA": st.column_config.NumberColumn("Quỹ CA", format="%.1f", disabled=True),
            "Họ và Tên": st.column_config.TextColumn(pinned=True, width="medium"),
        },
        use_container_width=True, height=550, key=f"table_{sheet_name}", hide_index=True
    )

with tabs[1]:
    df_gians = pd.DataFrame({"Tên Giàn": st.session_state.gians})
    edited_gians = st.data_editor(df_gians, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Lưu danh sách Giàn"):
        st.session_state.gians = edited_gians["Tên Giàn"].dropna().tolist()
        st.rerun()

with tabs[2]:
    staff_info_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail']
    df_staff = st.session_state.db[staff_info_cols]
    edited_staff = st.data_editor(df_staff, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 Lưu thông tin Nhân viên"):
        date_data = st.session_state.db[DATE_COLS]
        st.session_state.db = pd.concat([edited_staff.reset_index(drop=True), date_data.reset_index(drop=True)], axis=1)
        st.rerun()

with tabs[3]:
    st.header(f"💾 Dữ liệu tháng {sheet_name}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📤 UPLOAD GOOGLE SHEETS", use_container_width=True, type="primary"):
            try:
                conn.update(worksheet=sheet_name, data=st.session_state.db)
                st.success("Đã lưu thành công!")
            except: st.error("Lỗi: Kiểm tra Tab trên Google Sheets.")
    with c2:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            st.session_state.db.to_excel(writer, index=False, sheet_name=sheet_name)
        st.download_button(label="📥 TẢI FILE EXCEL (.xlsx)", data=buffer.getvalue(), file_name=f"PVD_{sheet_name}.xlsx", use_container_width=True)
