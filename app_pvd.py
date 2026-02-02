import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="PVD Crew Management", layout="wide", page_icon="🚢")

# --- LOGO & TIÊU ĐỀ ---
col_logo, col_title = st.columns([1, 6])
with col_logo:
    # Link Raw Logo từ GitHub của bạn
    logo_url = "https://raw.githubusercontent.com/lenghiapvdwell-star/app_pvd/main/424911181_712854060938641_6819448166542158882_n.jpg"
    st.image(logo_url, width=150)

with col_title:
    st.markdown("<h1 style='color: #1C83E1; margin-top: 15px;'>HỆ THỐNG QUẢN LÝ NHÂN SỰ & ĐIỀU ĐỘNG PVD</h1>", unsafe_allow_html=True)

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

# --- HÀM TÍNH NGHỈ PHIÊN ---
def calculate_off_days(start_date, end_date):
    if not start_date or not end_date: return 0
    total_off = 0.0
    current = start_date
    # Tết 2026: M1-M5 (17/02 - 21/02)
    tet_2026 = [datetime(2026, 2, 17).date(), datetime(2026, 2, 18).date(), 
                datetime(2026, 2, 19).date(), datetime(2026, 2, 20).date(), datetime(2026, 2, 21).date()]
    
    while current <= end_date:
        if current in tet_2026: total_off += 2.0  # Tết x2
        elif current.weekday() >= 5: total_off += 1.0 # T7, CN x1
        else: total_off += 0.5 # T2-T6 x0.5
        current += timedelta(days=1)
    return total_off

# --- GIAO DIỆN TABS ---
tab1, tab2, tab3 = st.tabs(["📊 LỊCH TRÌNH CHI TIẾT", "📝 ĐIỀU ĐỘNG MỚI", "⚙️ QUẢN LÝ"])

with tab1:
    st.subheader("📅 Bảng theo dõi điều động & Nghỉ phiên")
    
    # 1. Cấu hình Header ngày tháng (01/Feb + Thứ)
    today = datetime.now().date()
    num_days = 14
    dates = [today + timedelta(days=i) for i in range(num_days)]
    
    # Chia cột: Tên(2) + Nghỉ(1.5) + 14 ngày(1 mỗi ngày)
    cols = st.columns([2, 1.5] + [1]*num_days)
    cols[0].markdown("**Nhân sự**")
    cols[1].markdown("**Nghỉ Phiên**")
    
    for i, d in enumerate(dates):
        d_str = d.strftime("%d/%b")
        w_str = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"][d.weekday()]
        cols[i+2].markdown(f"<div style='text-align:center; font-size:11px;'><b>{d_str}</b><br>{w_str}</div>", unsafe_allow_html=True)
    
    st.divider()

    # 2. Hiển thị dữ liệu nhân sự
    for staff in STAFF_LIST[:15]: # Hiển thị mẫu 15 người
        r_cols = st.columns([2, 1.5] + [1]*num_days)
        r_cols[0].write(f"👷 {staff}")
        
        # Giả lập tính toán nghỉ phiên (Ví dụ đi biển từ hôm nay đến 10 ngày tới)
        off_calc = calculate_off_days(today, today + timedelta(days=10))
        r_cols[1].markdown(f"<div style='text-align:center; color:red; font-weight:bold;'>{off_calc}</div>", unsafe_allow_html=True)
        
        # Đổ màu giàn khoan lên lịch
        current_rig = "PVD I" if "Phuong" in staff else "PVD VI"
        color = RIG_COLORS.get(current_rig, "#EEE")
        
        for i in range(num_days):
            if i < 10: # Giả lập đang đi biển 10 ngày
                r_cols[i+2].markdown(f"<div style='background-color:{color}; color:white; font-size:10px; text-align:center; border-radius:4px; padding:2px;'>{current_rig}</div>", unsafe_allow_html=True)

with tab2:
    st.subheader("📝 Nhập Job Detail")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        name_input = c1.selectbox("Họ tên nhân viên", STAFF_LIST)
        pos_input = c1.text_input("Chức danh")
        rig_input = c2.selectbox("Tên Giàn", RIG_LIST)
        date_in = c2.date_input("Ngày đi biển", today)
        date_out = c2.date_input("Ngày về dự kiến", today + timedelta(days=14))
        
        if st.button("💾 Tính toán & Xác nhận"):
            total = calculate_off_days(date_in, date_out)
            st.success(f"Nhân viên: {name_input} | Giàn: {rig_input} | Tổng ngày nghỉ tích lũy: {total} ngày")

with tab3:
    st.subheader("⚙️ Quản lý Giàn")
    # Giữ nguyên tính năng thêm xóa giàn như hôm qua
