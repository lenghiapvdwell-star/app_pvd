import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="PVD Crew Dispatch Pro", layout="wide", page_icon="🚢")

# --- LOGO & TIÊU ĐỀ ---
col_logo, col_title = st.columns([1, 6])
with col_logo:
    # Link Raw Logo của bạn
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
    # Tết 2026: M1-M5 (17/02 - 21/02)
    tet_2026 = [datetime(2026, 2, 17).date(), datetime(2026, 2, 18).date(), 
                datetime(2026, 2, 19).date(), datetime(2026, 2, 20).date(), datetime(2026, 2, 21).date()]
    
    while current <= end_date:
        if current in tet_2026: total_off += 2.0
        elif current.weekday() >= 5: total_off += 1.0 # T7, CN
        else: total_off += 0.5 # Ngày thường
        current += timedelta(days=1)
    return total_off

# --- GIAO DIỆN TABS ---
tab1, tab2, tab3 = st.tabs(["🆕 ĐIỀU ĐỘNG & TÍNH PHIÊN", "📅 LỊCH TRÌNH BIỂN", "📊 DỮ LIỆU TỔNG"])

with tab1:
    st.subheader("📝 Công cụ tính & Nhập liệu Cloud")
    
    # Khối tính toán nhanh (Dùng st.container thay vì st.form để tránh lỗi Submit button)
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.selectbox("Chọn nhân viên", STAFF_LIST)
            rig_name = st.selectbox("Chọn Giàn", RIG_LIST)
        with c2:
            d_start = st.date_input("Ngày đi biển", datetime.now())
            d_end = st.date_input("Ngày về dự kiến", datetime.now() + timedelta(days=14))
        with c3:
            off_res = calculate_pvd_off_days(d_start, d_end)
            st.metric("Số ngày nghỉ phiên", f"{off_res} ngày")
            st.caption("Ghi chú: T2-T6 (0.5), T7-CN (1.0), Tết (2.0)")

    st.markdown("---")
    st.write("👇 **BƯỚC 2: ĐIỀN THÔNG TIN VÀO FORM DƯỚI ĐÂY ĐỂ LƯU**")
    
    # Kiểm tra Key form_url trước khi hiển thị
    if "form_url" in st.secrets:
        st.components.v1.iframe(st.secrets["form_url"], height=600, scrolling=True)
    else:
        st.error("Lỗi: Chưa tìm thấy 'form_url' trong Secrets của Streamlit.")

with tab2:
    st.subheader("📅 Theo dõi lịch trình biển (14 ngày tới)")
    today = datetime.now().date()
    dates = [today + timedelta(days=i) for i in range(14)]
    
    cols = st.columns([1.5] + [1]*14)
    cols[0].write("**Nhân sự**")
    for i, d in enumerate(dates):
        d_str = d.strftime("%d/%b")
        w_str = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"][d.weekday()]
        cols[i+1].markdown(f"<div style='text-align:center; font-size:11px;'><b>{d_str}</b><br>{w_str}</div>", unsafe_allow_html=True)
    
    st.divider()
    for staff in STAFF_LIST:
        r_cols = st.columns([1.5] + [1]*14)
        r_cols[0].write(f"👷 {staff}")
        # Giả lập màu sắc (Sau này kết nối data thật từ Sheet)
        color = RIG_COLORS["PVD I"] if staff == "Bùi Anh Phong" else RIG_COLORS["PVD VI"]
        for i in range(1, 8): # Giả lập 7 ngày đang đi biển
            r_cols[i].markdown(f"<div style='background-color:{color}; color:white; font-size:10px; text-align:center; border-radius:4px; padding:2px;'>ON</div>", unsafe_allow_html=True)

with tab3:
    st.subheader("📊 Dữ liệu tổng hợp từ Cloud")
    if st.button("🔄 Làm mới dữ liệu từ Google Sheets"):
        st.cache_data.clear()
        st.rerun()
    
    if "sheet_url" in st.secrets:
        try:
            df = pd.read_csv(st.secrets["sheet_url"] + "&cache_bust=" + str(time.time()))
            st.dataframe(df, use_container_width=True, hide_index=True)
        except:
            st.warning("Đang kết nối dữ liệu hoặc Sheet đang trống...")
    else:
        st.error("Thiếu link 'sheet_url' trong Secrets.")
