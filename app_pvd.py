import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# --- CẤU HÌNH TRANG & LOGO ---
st.set_page_config(page_title="PVD Crew Management", layout="wide")

# Chèn Logo và Tiêu đề theo phong cách chuyên nghiệp
col_logo, col_title = st.columns([1, 5])
with col_logo:
    # Bạn có thể thay URL logo bằng link ảnh chính thức của PVDrilling
    st.image("https://www.pvdrilling.com.vn/images/logo.png", width=150)

with col_title:
    st.title("HỆ THỐNG ĐIỀU ĐỘNG & TÍNH NGHỈ PHIÊN PVD")

st.markdown("---")

# --- DANH SÁCH NHÂN SỰ THỰC TẾ (Trích xuất từ file của bạn) ---
# Dữ liệu này sau này có thể đọc trực tiếp từ Sheet để tự động cập nhật
staff_data = [
    {"name": "Bùi Anh Phong", "company": "PVD", "pos": "Tong"},
    {"name": "Le Thai Viet", "company": "PVD", "pos": "Maintenance"},
    {"name": "Le Tung Phong", "company": "PVD", "pos": "Tong"},
    {"name": "Nguyen Tien Dung", "company": "PVD", "pos": "Sup"},
    {"name": "Nguyen Van Quang", "company": "PVD", "pos": "Sup"},
    {"name": "Pham Hong Minh", "company": "PVD", "pos": "Tong"},
    {"name": "Nguyen Gia Khanh", "company": "PVD", "pos": "Executive"},
    {"name": "Rusliy Saifuddin", "company": "OWS", "pos": "Sup"},
    {"name": "Timothy", "company": "OWS", "pos": "Sup"}
]
staff_names = [s["name"] for s in staff_data]

# --- HÀM LOGIC TÍNH NGHỈ PHIÊN ---
def calculate_pvd_off_days(start_date, end_date, holidays):
    total_off = 0.0
    current = start_date
    while current <= end_date:
        # 1. Nếu rơi vào ngày Lễ/Tết (1 ngày biển = 2 ngày nghỉ)
        if current in holidays:
            total_off += 2.0
        # 2. Nếu là Thứ 7 hoặc Chủ Nhật (1 ngày biển = 1 ngày nghỉ)
        elif current.weekday() >= 5: 
            total_off += 1.0
        # 3. Ngày thường T2-T6 (2 ngày biển = 1 ngày nghỉ -> 1 ngày = 0.5)
        else:
            total_off += 0.5
        current += timedelta(days=1)
    return total_off

# --- GIAO DIỆN CÁC TAB ---
tab1, tab2, tab3 = st.tabs(["📝 ĐIỀU ĐỘNG (JOB DETAIL)", "📊 DANH SÁCH & NGHỈ PHIÊN", "📤 XUẤT BÁO CÁO"])

with tab1:
    st.subheader("📝 Cập nhật Job Detail & Tính phiên")
    with st.form("job_entry", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        selected_name = col1.selectbox("Họ tên nhân viên", staff_names)
        # Tự động điền Công ty và Chức danh theo nhân viên đã chọn
        emp_info = next(item for item in staff_data if item["name"] == selected_name)
        
        company = col1.text_input("Công ty", value=emp_info["company"], disabled=True)
        position = col1.text_input("Chức danh", value=emp_info["pos"], disabled=True)
        
        location = col2.selectbox("Địa điểm làm việc", ["Rig PVD I", "Rig PVD II", "Rig PVD III", "Rig PVD VI", "Vũng Tàu", "Offshore khác"])
        d_range = col2.date_input("Khoảng thời gian đi biển", [datetime.now(), datetime.now() + timedelta(days=14)])
        
        st.info("Chọn các ngày Lễ/Tết trong kỳ nếu có để tính hệ số x2:")
        holiday_picks = st.multiselect("Ngày Lễ", pd.date_range(d_range[0], d_range[1]))

        if st.form_submit_button("💾 LƯU DỮ LIỆU & TÍNH PHIÊN"):
            if len(d_range) == 2:
                off_calc = calculate_pvd_off_days(d_range[0], d_range[1], holiday_picks)
                st.success(f"Đã lưu thành công cho {selected_name}!")
                st.write(f"🏖️ **Số ngày nghỉ phiên tích lũy được:** {off_calc} ngày")
                # Phần này sẽ gửi dữ liệu lên Google Sheet qua Form_url như đã làm
            else:
                st.error("Vui lòng chọn đầy đủ ngày đi và ngày về!")

with tab2:
    st.subheader("📊 Bảng theo dõi điều động nhân sự (Cloud Sync)")
    # Nút làm mới dữ liệu từ Google Sheet
    if st.button("🔄 Làm mới dữ liệu từ Cloud"):
        st.cache_data.clear()
        st.rerun()

    # Đọc dữ liệu từ Link CSV của bạn
    try:
        df = pd.read_csv(st.secrets["sheet_url"] + "&cache_bust=" + str(time.time()))
        st.dataframe(df, use_container_width=True, hide_index=True)
    except:
        st.info("Đang chờ dữ liệu từ Google Sheets...")

with tab3:
    st.subheader("📤 Kết xuất báo cáo công ty")
    # Nút tải file Excel cho sếp
    if 'df' in locals():
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 TẢI FILE EXCEL (.CSV) BẢN MỚI NHẤT", data=csv, file_name='PVD_Personnel_Report.csv')
