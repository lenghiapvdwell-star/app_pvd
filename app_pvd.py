import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH & THỜI GIAN TỰ ĐỘNG ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

now = datetime.now()
curr_month = now.month
curr_year = now.year
month_abbr = now.strftime("%b") 
sheet_name = now.strftime("%m_%Y") 

def get_vi_day(dt):
    return ["T2", "T3", "T4", "T5", "T6", "T7", "CN"][dt.weekday()]

num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({get_vi_day(date(curr_year, curr_month, d))})" for d in range(1, num_days + 1)]

# --- 2. DANH SÁCH 64 NHÂN SỰ ---
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

# --- 3. KHỞI TẠO DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

if 'db' not in st.session_state:
    try:
        df_load = conn.read(worksheet=sheet_name)
        if df_load is not None and not df_load.empty:
            st.session_state.db = df_load
        else: raise Exception
    except:
        df_init = pd.DataFrame({'STT': range(1, 65), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': ''})
        for c in DATE_COLS: df_init[c] = ""
        st.session_state.db = df_init

if 'gians' not in st.session_state:
    st.session_state.gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

# --- 4. LOGIC TÍNH TOÁN QUỸ CA ---
def apply_pvd_logic(df):
    gians = st.session_state.gians
    holidays = [15, 16, 17, 18, 19] if curr_month == 2 else [] 
    def calc_row(row):
        total = 0.0
        for col in DATE_COLS:
            if col in row.index:
                val = str(row[col]).strip()
                if not val or val.lower() in ["nan", "none", ""]: continue
                d_num = int(col.split('/')[0])
                dt = date(curr_year, curr_month, d_num)
                is_weekend = dt.weekday() >= 5
                is_holiday = d_num in holidays
                if val in gians:
                    if is_holiday: total += 2.0
                    elif is_weekend: total += 1.0
                    else: total += 0.5
                elif val.upper() == "CA":
                    if not is_weekend and not is_holiday: total -= 1.0
        return total
    df['Quỹ CA'] = df.apply(calc_row, axis=1)
    return df

st.session_state.db = apply_pvd_logic(st.session_state.db)
main_info = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail', 'Quỹ CA']
st.session_state.db = st.session_state.db.reindex(columns=main_info + DATE_COLS)

# --- 5. GIAO DIỆN ---
c_logo, c_title = st.columns([1.5, 5])
with c_logo:
    if os.path.exists("logo_pvd.png"): st.image("logo_pvd.png", width=180)
    else: st.markdown("### PVD LOGO")
with c_title:
    st.markdown('<h1 style="color: #00f2ff; margin-top: 15px;">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "💾 LƯU GG SHEETS"])

# --- TAB 1: ĐIỀU ĐỘNG ---
with tabs[0]:
    st.markdown(f"#### ➕ NHẬP LIỆU NHANH - THÁNG {curr_month}/{curr_year}")
    
    # Sử dụng container để bao bọc phần nhập liệu tránh Lag
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1.2])
        f_staff = c1.multiselect("Nhân viên:", st.session_state.db['Họ và Tên'].tolist())
        f_status = c2.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm"])
        
        # --- SỬA LỖI Ở ĐÂY: Logic hiển thị giàn khoan linh hoạt ---
        if f_status == "Đi Biển":
            f_val = c3.selectbox("Chọn Giàn:", st.session_state.gians)
        else:
            f_val = f_status # Tự động lấy CA, WS, NP...
            c3.text_input("Trạng thái đã chọn:", value=f_status, disabled=True)
            
        f_date = c4.date_input("Khoảng thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, 2)))
        
        if st.button("✅ CẬP NHẬT VÀO BẢNG", use_container_width=True, type="secondary"):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                for d in range(f_date[0].day, f_date[1].day + 1):
                    dt_temp = date(curr_year, curr_month, d)
                    col_target = f"{d:02d}/{month_abbr} ({get_vi_day(dt_temp)})"
                    if col_target in st.session_state.db.columns:
                        st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), col_target] = f_val
                st.rerun()

    # Bảng dữ liệu chính
    st.data_editor(
        st.session_state.db,
        column_config={
            "Quỹ CA": st.column_config.NumberColumn("Quỹ CA", format="%.1f", disabled=True),
            "Họ và Tên": st.column_config.TextColumn(pinned=True, width="medium"),
        },
        use_container_width=True, height=550, key="main_table"
    )

# --- CÁC TAB CÒN LẠI ---
with tabs[3]:
    st.header(f"💾 LƯU TRỮ THÁNG {sheet_name}")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("📤 UPLOAD GOOGLE SHEETS", use_container_width=True, type="primary"):
            try:
                conn.update(worksheet=sheet_name, data=st.session_state.db)
                st.success(f"Đã lưu thành công vào Tab {sheet_name}!")
            except: st.error(f"Hãy tạo Tab '{sheet_name}' trên Google Sheets.")
    with col_s2:
        buffer = io.BytesIO()
        st.session_state.db.to_excel(buffer, index=False)
        st.download_button("📥 XUẤT FILE EXCEL", data=buffer.getvalue(), file_name=f"PVD_{sheet_name}.xlsx", use_container_width=True)

with tabs[1]:
    new_gians = st.data_editor(pd.DataFrame({"Giàn": st.session_state.gians}), num_rows="dynamic")
    if st.button("Lưu cấu hình Giàn"): st.session_state.gians = new_gians["Giàn"].dropna().tolist()

with tabs[2]:
    new_staff = st.data_editor(st.session_state.db[main_info[:5]], num_rows="dynamic")
    if st.button("Lưu thông tin Nhân viên"): st.session_state.db.update(new_staff)
