import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="PVD Crew Dispatch Pro", layout="wide", page_icon="🚢")

# --- LOGO & TIÊU ĐỀ ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    # Link ảnh raw từ GitHub của bạn
    logo_url = "https://raw.githubusercontent.com/lenghiapvdwell-star/app_pvd/main/424911181_712854060938641_6819448166542158882_n.jpg"
    st.image(logo_url, width=150)

with col_title:
    st.markdown("<h1 style='color: #1C83E1; margin-top: 20px;'>HỆ THỐNG ĐIỀU ĐỘNG & TÍNH NGHỈ PHIÊN PVD</h1>", unsafe_allow_html=True)

st.markdown("---")

# --- DANH SÁCH NHÂN VIÊN ---
STAFF_LIST = [
    "Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang",
    "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong",
    "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia",
    "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin",
    "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang",
    "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu",
    "Do Duc Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong",
    "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh",
    "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy",
    "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh",
    "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung",
    "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat",
    "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"
]

RIG_LIST = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11", "Vũng Tàu", "Bãi Cháy"]
RIG_COLORS = {
    "PVD I": "#FF4B4B", "PVD II": "#1C83E1", "PVD III": "#00C04A", 
    "PVD VI": "#FFBD45", "PVD 11": "#7D3C98", "Vũng Tàu": "#A0A0A0", "Bãi Cháy": "#2E4053"
}

# --- HÀM TÍNH NGHỈ PHIÊN THEO QUY ƯỚC ---
def calculate_pvd_off_days(start_date, end_date):
    if not start_date or not end_date: return 0
    total_off = 0.0
    current = start_date
    # Tết 2026: M1-M5 (Giả định 17/02 - 21/02)
    tet_2026 = [datetime(2026, 2, 17).date(), datetime(2026, 2, 18).date(), 
                datetime(2026, 2, 19).date(), datetime(2026, 2, 20).date(), datetime(2026, 2, 21).date()]
    
    while current <= end_date:
        # Lễ (Tạm thời ví dụ 30/4, 1/5) hoặc Tết
        if current in tet_2026 or (current.month == 4 and current.day == 30) or (current.month == 5 and current.day == 1):
            total_off += 2.0
        # Thứ 7 & Chủ Nhật
        elif current.weekday() >= 5:
            total_off += 1.0
        # Thứ 2 - Thứ 6
        else:
            total_off += 0.5
        current += timedelta(days=1)
    return total_off

# --- GIAO DIỆN TABS ---
tab1, tab2, tab3 = st.tabs(["🆕 ĐIỀU ĐỘNG & TÍNH PHIÊN", "📅 LỊCH TRÌNH CHI TIẾT", "⚙️ QUẢN LÝ DANH SÁCH"])

with tab1:
    st.subheader("📝 Cập nhật thông tin đi biển")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.selectbox("Họ tên nhân viên", STAFF_LIST)
            position = st.text_input("Chức danh (Tự nhập)")
            rig_name = st.selectbox("Tên Giàn", RIG_LIST)
        with c2:
            d_start = st.date_input("Ngày đi biển", datetime.now())
            d_end = st.date_input("Ngày về dự kiến", datetime.now() + timedelta(days=14))
        with c3:
            off_res = calculate_pvd_off_days(d_start, d_end)
            st.metric("NGHỈ PHIÊN DỰ KIẾN", f"{off_res} ngày")
            st.info("Quy ước: T2-T6 (0.5), T7-CN (1.0), Lễ (2.0)")

with tab2:
    st.subheader("📅 Theo dõi lịch trình biển (14 ngày tới)")
    
    # Header ngày tháng 01/Feb + Thứ (Căn giữa)
    today = datetime.now().date()
    dates = [today + timedelta(days=i) for i in range(14)]
    
    cols = st.columns([1.5] + [1]*14)
    cols[0].write("**Nhân sự**")
    for i, d in enumerate(dates):
        d_str = d.strftime("%d/%b")
        w_str = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"][d.weekday()]
        cols[i+1].markdown(f"<div style='text-align:center; font-size:11px;'><b>{d_str}</b><br>{w_str}</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # Hiển thị màu sắc theo giàn cho danh sách
    for staff in STAFF_LIST[:10]: # Hiển thị 10 người đầu làm mẫu
        r_cols = st.columns([1.5] + [1]*14)
        r_cols[0].write(f"👷 {staff}")
        
        # Giả lập hiển thị màu sắc theo giàn
        test_rig = "PVD I" if "Phuong" in staff else "PVD VI"
        color = RIG_COLORS.get(test_rig, "#EEE")
        
        for i in range(1, 15):
            if i <= 7: # Giả lập đang ở biển 7 ngày
                r_cols[i].markdown(f"<div style='background-color:{color}; color:white; font-size:9px; text-align:center; border-radius:4px; padding:2px;'>{test_rig}</div>", unsafe_allow_html=True)

with tab3:
    st.subheader("⚙️ Quản lý danh sách Giàn")
    new_rig = st.text_input("Thêm tên giàn mới")
    if st.button("Thêm Giàn"):
        st.success(f"Đã thêm {new_rig} vào danh sách.")
    
    st.write("---")
    st.write("Danh sách giàn hiện tại:")
    for r in RIG_LIST:
        col_r1, col_r2 = st.columns([4, 1])
        col_r1.text(f"🏗️ {r}")
        if col_r2.button("Xóa", key=r):
            st.error(f"Đã xóa {r}")
