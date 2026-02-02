import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="PVD Crew Dispatch Pro", layout="wide", page_icon="🚢")

# --- LOGO & TIÊU ĐỀ ---
col_logo, col_title = st.columns([1, 6])
with col_logo:
    # Sử dụng link raw từ GitHub của bạn để hiển thị ảnh
    logo_url = "https://raw.githubusercontent.com/lenghiapvdwell-star/app_pvd/main/424911181_712854060938641_6819448166542158882_n.jpg"
    st.image(logo_url, width=150)

with col_title:
    st.markdown("<h1 style='color: #1C83E1;'>HỆ THỐNG ĐIỀU ĐỘNG & TÍNH NGHỈ PHIÊN PVD</h1>", unsafe_allow_html=True)

st.markdown("---")

# --- DỮ LIỆU CỐ ĐỊNH ---
STAFF_LIST = ["Bùi Anh Phong", "Lê Thái Việt", "Lê Tùng Phong", "Nguyễn Tiến Dũng", "Nguyen Van Quang", "Rusliy Saifuddin"]
RIG_LIST = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11", "Vũng Tàu", "Bãi Cháy"]
RIG_COLORS = {
    "PVD I": "#FF4B4B", "PVD II": "#1C83E1", "PVD III": "#00C04A", 
    "PVD VI": "#FFBD45", "PVD 11": "#7D3C98", "Vũng Tàu": "#A0A0A0", "Bãi Cháy": "#2E4053"
}

# --- HÀM TÍNH NGHỈ PHIÊN ---
def calculate_pvd_off_days(start_date, end_date):
    if not start_date or not end_date: return 0
    total_off = 0.0
    current = start_date
    # Danh sách nghỉ Tết 2026 (M1 - M5 âm lịch)
    tet_2026 = [datetime(2026, 2, 17), datetime(2026, 2, 18), datetime(2026, 2, 19), datetime(2026, 2, 20), datetime(2026, 2, 21)]
    
    while current <= end_date:
        if current in tet_2026: total_off += 2.0 # Tết x2
        elif current.weekday() == 5 or current.weekday() == 6: total_off += 1.0 # T7, CN x1
        else: total_off += 0.5 # Ngày thường x0.5
        current += timedelta(days=1)
    return total_off

# --- GIAO DIỆN TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["🆕 ĐIỀU ĐỘNG MỚI", "📅 LỊCH TRÌNH BIỂN", "📊 DỮ LIỆU TỔNG", "⚙️ QUẢN LÝ"])

with tab1:
    st.subheader("📝 Cập nhật Job Detail")
    with st.form("dispatch_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.selectbox("Nhân viên", STAFF_LIST)
            rig_name = st.selectbox("Tên Giàn", RIG_LIST)
        with c2:
            d_start = st.date_input("Ngày đi biển", datetime.now())
            d_end = st.date_input("Ngày về dự kiến", datetime.now() + timedelta(days=14))
        with c3:
            off_res = calculate_pvd_off_days(d_start, d_end)
            st.metric("Nghỉ phiên dự kiến", f"{off_res} ngày")
        
        st.info("Sau khi nhập xong, vui lòng gửi dữ liệu qua Form bên dưới để lưu Cloud.")
        st.components.v1.iframe(st.secrets["form_url"], height=400)

with tab2:
    st.subheader("📅 Theo dõi lịch trình biển (14 ngày tới)")
    
    # Tạo Header ngày tháng 01/Feb + Thứ
    today = datetime.now()
    dates = [today + timedelta(days=i) for i in range(14)]
    
    # Thiết kế bảng lịch trình
    cols = st.columns([2] + [1]*14)
    cols[0].write("**Nhân sự**")
    for i, d in enumerate(dates):
        d_str = d.strftime("%d/%b")
        w_str = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"][d.weekday()]
        cols[i+1].markdown(f"<div style='text-align:center; font-size:12px;'><b>{d_str}</b><br>{w_str}</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # Giả lập dữ liệu hiển thị (Sau này sẽ đọc từ Sheet)
    for staff in STAFF_LIST:
        r_cols = st.columns([2] + [1]*14)
        r_cols[0].write(f"👤 {staff}")
        
        # Logic tô màu: Nếu nhân viên đang ở giàn (giả lập)
        current_rig = "PVD I" if staff == "Bùi Anh Phong" else "PVD VI"
        color = RIG_COLORS.get(current_rig, "#EEE")
        
        for i in range(1, 15):
            # Hiển thị giàn khoan theo màu sắc trong 7 ngày đầu
            if i <= 7:
                r_cols[i].markdown(f"<div style='background-color:{color}; color:white; font-size:10px; text-align:center; border-radius:4px; padding:2px;'>{current_rig}</div>", unsafe_allow_html=True)

with tab3:
    st.subheader("📊 Dữ liệu tổng hợp từ Google Sheets")
    if st.button("🔄 Làm mới dữ liệu Cloud"):
        st.cache_data.clear()
        st.rerun()
    
    try:
        df = pd.read_csv(st.secrets["sheet_url"] + "&cache_bust=" + str(time.time()))
        st.dataframe(df, use_container_width=True, hide_index=True)
    except:
        st.warning("Đang kết nối dữ liệu...")

with tab4:
    st.subheader("⚙️ Quản lý danh sách")
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("**Danh sách Giàn Khoan**")
        for r in RIG_LIST:
            st.text(f"🏗️ {r}")
    with col_b:
        st.write("**Danh sách Nhân sự**")
        for s in STAFF_LIST:
            st.text(f"👷 {s}")
