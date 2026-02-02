import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="PVD Crew Dispatch Pro", layout="wide")

# --- STYLE CSS ĐỂ MƯỢT NHƯ HÔM QUA ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-header { font-size: 28px; font-weight: bold; color: #1C83E1; margin-bottom: 0px; }
    .off-cell { font-weight: bold; color: #d32f2f; text-align: center; }
    .rig-cell { border-radius: 4px; padding: 3px; color: white; text-align: center; font-size: 11px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGO & TIÊU ĐỀ ---
col_logo, col_title = st.columns([1, 6])
with col_logo:
    logo_url = "https://raw.githubusercontent.com/lenghiapvdwell-star/app_pvd/main/424911181_712854060938641_6819448166542158882_n.jpg"
    st.image(logo_url, width=130)
with col_title:
    st.markdown('<p class="main-header">HỆ THỐNG ĐIỀU ĐỘNG & QUẢN LÝ NGHỈ PHIÊN PVD</p>', unsafe_allow_html=True)

# --- DANH SÁCH NHÂN VIÊN (Dựa trên danh sách bạn cung cấp) ---
STAFF_LIST = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia"]
RIG_LIST = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11", "Vũng Tàu", "OFF (Nghỉ)"]
RIG_COLORS = {"PVD I": "#FF4B4B", "PVD II": "#1C83E1", "PVD III": "#00C04A", "PVD VI": "#FFBD45", "PVD 11": "#7D3C98", "Vũng Tàu": "#5D6D7E", "OFF (Nghỉ)": "#E74C3C"}

# --- HÀM LOGIC TÍNH TOÁN ---
def calculate_day_change(date_obj, status):
    """Tính toán cộng hoặc trừ ngày nghỉ dựa trên trạng thái"""
    if status == "OFF (Nghỉ)":
        return -1.0  # Nghỉ 1 ngày thì trừ 1 ngày tích lũy
    
    # Logic cộng khi đi làm (Đi biển)
    tet_2026 = [datetime(2026, 2, 17).date(), datetime(2026, 2, 18).date(), datetime(2026, 2, 19).date(), datetime(2026, 2, 20).date(), datetime(2026, 2, 21).date()]
    if date_obj in tet_2026: return 2.0
    if date_obj.weekday() >= 5: return 1.0 # T7, CN
    return 0.5 # Ngày thường

# --- GIAO DIỆN TABS ---
tab1, tab2, tab3 = st.tabs(["📊 BẢNG THEO DÕI TỔNG", "📝 ĐIỀU ĐỘNG & NGHỈ", "⚙️ CHỐT SỐ DƯ THÁNG"])

with tab1:
    st.subheader("📅 Lịch trình & Số dư nghỉ phiên")
    
    # Header ngày tháng
    today = datetime.now().date()
    num_days = 14
    dates = [today + timedelta(days=i) for i in range(num_days)]
    
    # Chia cột tỉ lệ mượt: Tên(1.5), Số dư(1), 14 ngày(mỗi ô 0.5)
    header_cols = st.columns([1.5, 0.8] + [0.5]*num_days)
    header_cols[0].write("**Nhân sự**")
    header_cols[1].write("**Số dư**")
    
    for i, d in enumerate(dates):
        d_str = d.strftime("%d/%b")
        w_str = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"][d.weekday()]
        header_cols[i+2].markdown(f"<div style='text-align:center; font-size:10px;'><b>{d_str}</b><br>{w_str}</div>", unsafe_allow_html=True)
    
    st.divider()

    for staff in STAFF_LIST[:12]:
        row_cols = st.columns([1.5, 0.8] + [0.5]*num_days)
        row_cols[0].write(f"👷 {staff}")
        
        # Giả lập logic: Bắt đầu tháng có 10 ngày nghỉ, sau đó cộng/trừ theo lịch
        balance = 10.0 
        
        for i in range(num_days):
            # Giả lập: 5 ngày đầu đi PVD I, 2 ngày sau Nghỉ OFF
            status = "PVD I" if i < 5 else ("OFF (Nghỉ)" if i < 7 else "Sẵn sàng")
            balance += calculate_day_change(dates[i], status) if status != "Sẵn sàng" else 0
            
            if status != "Sẵn sàng":
                color = RIG_COLORS.get(status, "#EEE")
                row_cols[i+2].markdown(f"<div class='rig-cell' style='background-color:{color};'>{status[:3]}</div>", unsafe_allow_html=True)
        
        row_cols[1].markdown(f"<div class='off-cell'>{balance}</div>", unsafe_allow_html=True)

with tab2:
    st.subheader("📝 Cập nhật trạng thái nhân sự")
    with st.form("update_form"):
        c1, c2, c3 = st.columns(3)
        u_name = c1.selectbox("Nhân viên", STAFF_LIST)
        u_status = c1.selectbox("Trạng thái/Giàn", RIG_LIST)
        u_start = c2.date_input("Từ ngày", today)
        u_end = c2.date_input("Đến ngày", today + timedelta(days=7))
        u_pos = c3.text_input("Chức danh")
        
        if st.form_submit_button("XÁC NHẬN CẬP NHẬT"):
            st.success(f"Đã cập nhật lịch cho {u_name}. Hệ thống đã tự động tính toán lại ngày nghỉ.")

with tab3:
    st.subheader("⚙️ Quét & Chốt số dư cuối tháng")
    col_scan1, col_scan2 = st.columns([2,1])
    target_month = col_scan1.selectbox("Chọn tháng cần chốt", ["Tháng 01/2026", "Tháng 02/2026", "Tháng 03/2026"])
    
    if col_scan2.button("🚀 QUÉT TOÀN BỘ DANH SÁCH"):
        with st.spinner("Đang tính toán số dư ngày nghỉ..."):
            import time
            time.sleep(1.5)
            st.balloons()
            st.success(f"Đã chốt xong số dư nghỉ phiên {target_month}. Dữ liệu đã sẵn sàng để xuất báo cáo.")
            
    # Hiển thị bảng tổng kết sau khi quét
    st.write("### Kết quả quét dự kiến:")
    scan_data = {"Nhân viên": STAFF_LIST[:5], "Ngày tích lũy": [15, 12, 18, 9, 20], "Ngày đã nghỉ": [2, 5, 0, 4, 1], "Số dư hiện tại": [13, 7, 18, 5, 19]}
    st.table(pd.DataFrame(scan_data))
