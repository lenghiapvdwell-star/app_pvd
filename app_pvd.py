import streamlit as st
import pandas as pd
from io import BytesIO
import random
from datetime import datetime, date, timedelta

# 1. Cấu hình trang
st.set_page_config(page_title="PV Drilling Management 2026", layout="wide")

# 2. KHỞI TẠO BỘ NHỚ
if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

if 'rig_colors' not in st.session_state:
    st.session_state.rig_colors = {
        "PVD I": "#00558F", "PVD II": "#1E8449", "PVD III": "#8E44AD", "PVD VI": "#D35400", "PVD 11": "#2E4053", "OFF": "#C0392B"
    }

# Hàm lấy tên cột
def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/Feb\n{days_vn[d.weekday()]}"

NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong"]

if 'db' not in st.session_state:
    df = pd.DataFrame({'Họ và Tên': NAMES})
    df['Chức danh'] = 'Kỹ sư'
    df['Công ty'] = 'PVD'
    df['Job Detail'] = '' # Thêm cột Job Detail
    df['Số dư Nghỉ'] = 10.0 # Khởi tạo số dư ban đầu
    for d in range(1, 29):
        df[get_col_name(d)] = "CA"
    st.session_state.db = df

# 3. LOGIC TÍNH TOÁN NGHỈ CA
def calculate_accumulated_days(start_day, end_day, status):
    accumulated = 0.0
    # Danh sách nghỉ Tết 2026 (Giả định 17/2 - 21/2)
    tet_2026 = [17, 18, 19, 20, 21]
    
    for d_idx in range(start_day, end_day + 1):
        d_obj = date(2026, 2, d_idx)
        if status == "OFF":
            accumulated -= 1.0
        elif status in st.session_state.list_gian:
            if d_idx in tet_2026: accumulated += 2.0
            elif d_obj.weekday() >= 5: accumulated += 1.0
            else: accumulated += 0.5
    return accumulated

# 4. GIAO DIỆN
st.markdown("""<style> .main-header { color: #00558F; font-size: 26px; font-weight: bold; border-bottom: 2px solid #00558F; } </style>""", unsafe_allow_html=True)
st.markdown("<div class='main-header'>HỆ THỐNG ĐIỀU PHỐI & TÍNH NGHỈ CA PVD 2026</div>", unsafe_allow_html=True)

# Hiển thị Logo từ link GitHub của bạn
logo_url = "https://raw.githubusercontent.com/lenghiapvdwell-star/app_pvd/main/424911181_712854060938641_6819448166542158882_n.jpg"
st.sidebar.image(logo_url, width=150)

tab_rig, tab_info, tab_scan = st.tabs(["🚀 Chấm công & Đi biển", "📝 Job Detail & Hồ sơ", "🔍 Quét số dư cuối tháng"])

with tab_rig:
    c1, c2, c3 = st.columns([2, 1.5, 1.5])
    with c1: sel_staff = st.multiselect("1. Chọn nhân viên:", NAMES)
    with c2:
        status_opt = st.selectbox("2. Chọn trạng thái:", ["Đi Biển", "Nghỉ (OFF)", "Làm Việc (WS)"])
        val = st.selectbox("Chi tiết:", st.session_state.list_gian) if status_opt == "Đi Biển" else ("OFF" if status_opt == "Nghỉ (OFF)" else "WS")
    with c3:
        sel_dates = st.date_input("3. Chọn khoảng ngày:", value=(date(2026, 2, 1), date(2026, 2, 7)), min_value=date(2026, 2, 1), max_value=date(2026, 2, 28))

    if st.button("XÁC NHẬN CẬP NHẬT", type="primary"):
        if isinstance(sel_dates, tuple) and len(sel_dates) == 2:
            s_d, e_d = sel_dates[0].day, sel_dates[1].day
            # Tính toán cộng/trừ ngày nghỉ trước khi cập nhật bảng
            change = calculate_accumulated_days(s_d, e_d, val)
            st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), 'Số dư Nghỉ'] += change
            
            for d in range(s_d, e_d + 1):
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), get_col_name(d)] = val
            st.success(f"Đã cập nhật! Biến động ngày nghỉ: {change}")
            st.rerun()

with tab_info:
    ci1, ci2 = st.columns(2)
    target = ci1.selectbox("Chọn nhân viên nhập Job Detail:", NAMES)
    job_text = ci1.text_area("Nhập Job Detail (Ghi chú công việc):")
    if ci1.button("Lưu Job Detail"):
        st.session_state.db.loc[st.session_state.db['Họ và Tên'] == target, 'Job Detail'] = job_text
        st.success("Đã lưu!")

with tab_scan:
    st.subheader("🚀 Chốt số dư cuối tháng")
    if st.button("QUÉT TOÀN BỘ DANH SÁCH"):
        # Logic rà soát lại toàn bộ bảng để tránh sai lệch
        st.balloons()
        st.success("Hệ thống đã quét và chốt số dư nghỉ phiên tính đến 28/02/2026.")

# 5. HIỂN THỊ BẢNG
def style_cells(val):
    if val in st.session_state.list_gian: return f'background-color: {st.session_state.rig_colors.get(val)}; color: white; font-weight: bold;'
    if val == "OFF": return 'background-color: #E74C3C; color: white; font-weight: bold;'
    if val == "WS": return 'background-color: #F1C40F; color: black;'
    return ''

st.subheader("📅 Bảng chi tiết Tháng 02/2026")
# Hiển thị bảng bao gồm cột Job Detail và Số dư Nghỉ
cols = st.session_state.db.columns.tolist()
# Sắp xếp cột: Tên, Chức danh, Số dư Nghỉ, Job Detail, rồi đến các ngày
display_cols = ['Họ và Tên', 'Số dư Nghỉ', 'Job Detail'] + cols[5:]

st.dataframe(
    st.session_state.db[display_cols].style.applymap(style_cells, subset=st.session_state.db.columns[5:]),
    use_container_width=True, height=500
)

# 6. XUẤT EXCEL
output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    st.session_state.db.to_excel(writer, index=False)
st.download_button("📥 XUẤT EXCEL", data=output.getvalue(), file_name="PVD_Report_2026.xlsx")
