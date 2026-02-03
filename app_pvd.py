import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

# Quy ước thời gian cố định 02/2026
YEAR, MONTH = 2026, 2
DATE_COLS = [f"{d:02d}/02" for d in range(1, 29)]
HOLIDAYS = [15, 16, 17, 18, 19]

# Danh sách 64 nhân sự
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

# --- 2. KHỞI TẠO DỮ LIỆU (CHỐNG MẤT DỮ LIỆU) ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Chỉ khởi tạo DB một lần duy nhất vào Session State
if 'db' not in st.session_state:
    try:
        # Thử lấy dữ liệu từ Cloud về trước
        df_load = conn.read(worksheet="Sheet1")
        if df_load is not None and not df_load.empty:
            st.session_state.db = df_load
        else: raise Exception
    except:
        # Nếu Cloud trống, tạo mới từ 64 nhân sự
        df_init = pd.DataFrame({'STT': range(1, 65), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': ''})
        for c in DATE_COLS: df_init[c] = ""
        st.session_state.db = df_init

if 'gians' not in st.session_state:
    st.session_state.gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

# --- 3. HÀM TÍNH TOÁN (LOGIC CHUẨN) ---
def update_logic():
    gians = st.session_state.gians
    def calc_row(row):
        total = 0.0
        for col in DATE_COLS:
            if col in row.index:
                val = str(row[col]).strip()
                if not val or val.lower() in ["nan", "none", ""]: continue
                day_num = int(col.split('/')[0])
                dt = date(YEAR, MONTH, day_num)
                is_weekend = dt.weekday() >= 5
                is_holiday = day_num in HOLIDAYS
                if val in gians:
                    if is_holiday: total += 2.0
                    elif is_weekend: total += 1.0
                    else: total += 0.5
                elif val.upper() == "CA":
                    if not is_weekend and not is_holiday: total -= 1.0
        return total
    st.session_state.db['Nghỉ Ca Còn Lại'] = st.session_state.db.apply(calc_row, axis=1)

# --- 4. GIAO DIỆN (LOGO TO 1.5 LẦN) ---
c_logo, c_title = st.columns([1.5, 5])
with c_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=180)
    else:
        st.subheader("PVD LOGO")
with c_title:
    st.markdown('<h1 style="color: #00f2ff; margin-top: 15px;">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 5. TABS CHỨC NĂNG ---
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "💾 ĐỒNG BỘ CLOUD"])

# TAB 1: ĐIỀU ĐỘNG (KHU VỰC CHÍNH)
with tabs[0]:
    # Sử dụng Form để CHỐNG NHẢY LAG khi đang nhập liệu
    with st.form("quick_input_form"):
        st.markdown("### ➕ NHẬP LIỆU NHANH")
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        f_staff = c1.multiselect("Chọn nhân viên:", st.session_state.db['Họ và Tên'].tolist())
        f_status = c2.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm"])
        f_gian = c3.selectbox("Chọn Giàn:", st.session_state.gians) if f_status == "Đi Biển" else f_status
        f_date = c4.date_input("Thời gian:", value=(date(YEAR, MONTH, 1), date(YEAR, MONTH, 2)))
        
        # Nút submit của form - Chỉ bấm mới chạy lại App
        if st.form_submit_button("✅ XÁC NHẬN VÀO BẢNG TẠM", use_container_width=True):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                for d in range(f_date[0].day, f_date[1].day + 1):
                    col_name = f"{d:02d}/02"
                    if col_name in st.session_state.db.columns:
                        st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), col_name] = f_gian
                update_logic()
                st.rerun()

    # HIỂN THỊ BẢNG (Dùng key cố định để tránh reset bảng khi cuộn)
    update_logic()
    cols_order = ['STT', 'Họ và Tên', 'Nghỉ Ca Còn Lại'] + [c for c in st.session_state.db.columns if c not in ['STT', 'Họ và Tên', 'Nghỉ Ca Còn Lại']]
    
    st.data_editor(
        st.session_state.db[cols_order],
        column_config={
            "Nghỉ Ca Còn Lại": st.column_config.NumberColumn("Quỹ CA", format="%.1f", disabled=True),
            "Họ và Tên": st.column_config.TextColumn(pinned=True, width="medium")
        },
        use_container_width=True,
        height=600,
        key="main_editor" 
    )

# TAB 4: ĐỒNG BỘ CLOUD (NƠI LƯU DỮ LIỆU)
with tabs[3]:
    st.header("💾 LƯU TRỮ DỮ LIỆU")
    st.info("Nhập liệu xong ở Tab 'Điều động', hãy sang đây để lưu lên Google Sheets.")
    
    col_save, col_export = st.columns(2)
    with col_save:
        if st.button("📤 ĐỒNG BỘ LÊN GOOGLE SHEETS", use_container_width=True, type="primary"):
            try:
                conn.update(worksheet="Sheet1", data=st.session_state.db)
                st.success("✅ Đã lưu dữ liệu lên Cloud thành công!")
            except:
                st.error("❌ Lỗi! Không tìm thấy Tab 'Sheet1' trên Google Sheets.")
    
    with col_export:
        buffer = io.BytesIO()
        st.session_state.db.to_excel(buffer, index=False)
        st.download_button("📥 TẢI FILE EXCEL DỰ PHÒNG", data=buffer.getvalue(), file_name="PVD_Management.xlsx", use_container_width=True)

# Các Tab cấu hình khác giữ nguyên logic
with tabs[1]:
    new_gians = st.data_editor(pd.DataFrame({"Giàn": st.session_state.gians}), num_rows="dynamic")
    if st.button("Lưu Giàn"): st.session_state.gians = new_gians["Giàn"].dropna().tolist()

with tabs[2]:
    staff_info = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail']
    new_staff = st.data_editor(st.session_state.db[staff_info], num_rows="dynamic")
    if st.button("Lưu Nhân sự"): st.session_state.db.update(new_staff)
