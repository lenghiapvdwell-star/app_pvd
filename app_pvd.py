import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH & THỜI GIAN TỰ ĐỘNG ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

# Tự động lấy tháng/năm hiện tại
now = datetime.now()
curr_month = now.month
curr_year = now.year
month_name = now.strftime("%b") # Ví dụ: Feb, Mar...
sheet_name = now.strftime("%m_%Y") # Ví dụ: 02_2026

# Hàm lấy tên Thứ viết tắt tiếng Việt
def get_vi_weekday(dt):
    days = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return days[dt.weekday()]

# Tạo danh sách cột ngày: "01/Feb (T2)"
num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = []
for d in range(1, num_days + 1):
    dt = date(curr_year, curr_month, d)
    col_name = f"{d:02d}/{month_name} ({get_vi_weekday(dt)})"
    DATE_COLS.append(col_name)

# --- 2. DANH SÁCH 64 NHÂN SỰ ---
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

# --- 3. KHỞI TẠO DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

if 'db' not in st.session_state:
    try:
        # Thử đọc tab của tháng hiện tại
        df_load = conn.read(worksheet=sheet_name)
        if df_load is not None and not df_load.empty:
            st.session_state.db = df_load
        else: raise Exception
    except:
        # Nếu chưa có tháng mới, tạo bảng trống
        df_init = pd.DataFrame({
            'STT': range(1, 65), 'Họ và Tên': NAMES_64, 
            'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': ''
        })
        for c in DATE_COLS: df_init[c] = ""
        st.session_state.db = df_init

if 'gians' not in st.session_state:
    st.session_state.gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

# --- 4. HÀM TÍNH TOÁN QUỸ CA ---
def apply_pvd_logic(df):
    gians = st.session_state.gians
    # Giả định ngày lễ cố định (có thể chỉnh sửa thêm)
    holidays = [15, 16, 17, 18, 19] if curr_month == 2 else [] 
    
    def calc_row(row):
        total = 0.0
        for col in DATE_COLS:
            if col in row.index:
                val = str(row[col]).strip()
                if not val or val.lower() in ["nan", "none", ""]: continue
                
                day_num = int(col.split('/')[0])
                dt = date(curr_year, curr_month, day_num)
                is_weekend = dt.weekday() >= 5
                is_holiday = day_num in holidays
                
                if val in gians:
                    if is_holiday: total += 2.0
                    elif is_weekend: total += 1.0
                    else: total += 0.5
                elif val.upper() == "CA":
                    if not is_weekend and not is_holiday: total -= 1.0
        return total
    
    df['Quỹ CA'] = df.apply(calc_row, axis=1)
    return df

# Cập nhật số liệu & Sắp xếp cột
st.session_state.db = apply_pvd_logic(st.session_state.db)
main_info = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail', 'Quỹ CA']
full_cols = main_info + DATE_COLS
st.session_state.db = st.session_state.db.reindex(columns=full_cols)

# --- 5. GIAO DIỆN ---
c_logo, c_title = st.columns([1.5, 5])
with c_logo:
    st.image("logo_pvd.png", width=180) if os.path.exists("logo_pvd.png") else st.subheader("PVD LOGO")
with c_title:
    st.markdown('<h1 style="color: #00f2ff; margin-top: 15px;">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "💾 ĐỒNG BỘ CLOUD"])

# TAB ĐIỀU ĐỘNG
with tabs[0]:
    with st.form("input_form"):
        st.markdown(f"### ➕ NHẬP LIỆU NHANH - THÁNG {curr_month}/{curr_year}")
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        f_staff = c1.multiselect("Nhân viên:", st.session_state.db['Họ và Tên'].tolist())
        f_status = c2.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm"])
        f_gian = c3.selectbox("Chọn Giàn:", st.session_state.gians) if f_status == "Đi Biển" else f_status
        f_date = c4.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, 2)))
        
        if st.form_submit_button("✅ CẬP NHẬT VÀO BẢNG", use_container_width=True):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                for d in range(f_date[0].day, f_date[1].day + 1):
                    dt_temp = date(curr_year, curr_month, d)
                    col_name = f"{d:02d}/{month_name} ({get_vi_weekday(dt_temp)})"
                    if col_name in st.session_state.db.columns:
                        st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), col_name] = f_gian
                st.rerun()

    # HIỂN THỊ BẢNG CHÍNH
    st.data_editor(
        st.session_state.db,
        column_config={
            "Quỹ CA": st.column_config.NumberColumn("Quỹ CA", format="%.1f", disabled=True),
            "Họ và Tên": st.column_config.TextColumn(pinned=True, width="medium"),
            "STT": st.column_config.NumberColumn(width="small")
        },
        use_container_width=True, height=600, key="editor_v1"
    )

# TAB ĐỒNG BỘ CLOUD
with tabs[3]:
    st.header(f"💾 LƯU TRỮ THÁNG {curr_month}/{curr_year}")
    st.info(f"Dữ liệu sẽ được lưu vào Tab: {sheet_name}")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("📤 ĐỒNG BỘ LÊN GOOGLE SHEETS", use_container_width=True, type="primary"):
            try:
                conn.update(worksheet=sheet_name, data=st.session_state.db)
                st.success(f"Đã lưu thành công vào tab {sheet_name}!")
            except:
                st.error("Lỗi: Hãy tạo sẵn tab tên '" + sheet_name + "' trên Google Sheets trước.")
    
    with col_s2:
        buffer = io.BytesIO()
        st.session_state.db.to_excel(buffer, index=False)
        st.download_button("📥 TẢI EXCEL DỰ PHÒNG", data=buffer.getvalue(), file_name=f"PVD_{sheet_name}.xlsx", use_container_width=True)

# Các tab còn lại
with tabs[1]:
    new_gians = st.data_editor(pd.DataFrame({"Giàn": st.session_state.gians}), num_rows="dynamic")
    if st.button("Lưu Giàn"): st.session_state.gians = new_gians["Giàn"].dropna().tolist()

with tabs[2]:
    new_staff = st.data_editor(st.session_state.db[main_info[:5]], num_rows="dynamic")
    if st.button("Lưu Nhân sự"): st.session_state.db.update(new_staff)
