import streamlit as st
import pandas as pd
from datetime import datetime, date
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import io
import os

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="PVD Management 2026", layout="wide")

st.markdown("""
    <style>
        [data-testid="stStatusWidget"] {display: none !important;}
        .stButton button {border-radius: 8px; font-weight: bold; height: 3em;}
        [data-testid="stDataEditor"] { border: 2px solid #00f2ff; }
    </style>
""", unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU & KẾT NỐI
conn = st.connection("gsheets", type=GSheetsConnection)

def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/02\n{days_vn[d.weekday()]}"

DATE_COLS = [get_col_name(d) for d in range(1, 29)]
REQUIRED_COLS = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Nghỉ Ca Còn Lại', 'Job Detail'] + DATE_COLS

@st.cache_data(ttl=300)
def load_data():
    try:
        db = conn.read(worksheet="Sheet1")
        # Kiểm tra nếu bảng trống hoặc thiếu cột
        if db.empty or 'Họ và Tên' not in db.columns:
            db = pd.DataFrame(columns=REQUIRED_COLS)
    except:
        db = pd.DataFrame(columns=REQUIRED_COLS)
        
    try:
        gians = conn.read(worksheet="Gians")['TenGian'].dropna().tolist()
    except:
        gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]
        
    try:
        staffs = conn.read(worksheet="Staffs")
        if staffs.empty: staffs = pd.DataFrame(columns=['STT', 'Họ và Tên', 'Công ty', 'Chức danh'])
    except:
        staffs = pd.DataFrame(columns=['STT', 'Họ và Tên', 'Công ty', 'Chức danh'])
        
    return db, gians, staffs

# Khởi tạo Session State
if 'db' not in st.session_state:
    st.session_state.db, st.session_state.gians, st.session_state.staffs = load_data()

# 3. GIAO DIỆN TIÊU ĐỀ & NÚT LƯU
col_logo, col_title, col_save = st.columns([1, 4, 1])
with col_title:
    st.markdown('<h1 style="color: #00f2ff; text-align: center;">PVD MANAGEMENT 2026</h1>', unsafe_allow_html=True)
with col_save:
    if st.button("💾 LƯU CLOUD", type="primary", use_container_width=True):
        conn.update(worksheet="Sheet1", data=st.session_state.db)
        conn.update(worksheet="Gians", data=pd.DataFrame({"TenGian": st.session_state.gians}))
        conn.update(worksheet="Staffs", data=st.session_state.staffs)
        st.success("Đã lưu!")

# 4. PHẦN ĐIỀU ĐỘNG (NHẢY OPTION TỨC THÌ)
st.subheader("🚀 ĐIỀU ĐỘNG NHANH")
c1, c2, c3, c4 = st.columns([2, 1, 1, 1.5])

# Bảo vệ chống lỗi KeyError bằng cách kiểm tra cột tồn tại
staff_list = st.session_state.db['Họ và Tên'].tolist() if 'Họ và Tên' in st.session_state.db.columns else []
sel_staff = c1.multiselect("CHỌN NHÂN VIÊN:", staff_list)

status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "CA", "WS", "NP"])

# Nhảy Option Giàn ngay lập tức
if status == "Đi Biển":
    val = c3.selectbox("CHỌN GIÀN:", st.session_state.gians)
else:
    val = status
    c3.markdown(f"<br><p style='text-align:center; color:gray;'>{status}</p>", unsafe_allow_html=True)

dates = c4.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))

if st.button("✅ ÁP DỤNG XUỐNG BẢNG", use_container_width=True):
    if isinstance(dates, tuple) and len(dates) == 2:
        for d in range(dates[0].day, dates[1].day + 1):
            st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), get_col_name(d)] = val
        st.toast("Đã cập nhật!")

# 5. BẢNG TỔNG HỢP (HIỆN NGAY DƯỚI)
st.divider()
st.subheader("📊 BẢNG TỔNG HỢP (Kéo/Copy như Excel)")

# Bảng chính - Cho phép kéo thả (Fill handle)
st.session_state.db = st.data_editor(
    st.session_state.db,
    use_container_width=True,
    height=500,
    num_rows="dynamic"
)

# 6. CÁC TAB PHỤ
tabs = st.tabs(["🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "📝 CHI TIẾT"])
with tabs[0]:
    st.session_state.gians = st.data_editor(pd.DataFrame({"TenGian": st.session_state.gians}), num_rows="dynamic")['TenGian'].dropna().tolist()
with tabs[1]:
    st.session_state.staffs = st.data_editor(st.session_state.staffs, num_rows="dynamic", use_container_width=True)
    if st.button("ĐỒNG BỘ NHÂN VIÊN"):
        # Logic cập nhật an toàn
        new_staffs = st.session_state.staffs[~st.session_state.staffs['Họ và Tên'].isin(st.session_state.db['Họ và Tên'])]
        if not new_staffs.empty:
            for _, row in new_staffs.iterrows():
                new_row = {c: "" for c in REQUIRED_COLS}
                new_row.update(row.to_dict())
                st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_row])], ignore_index=True)
            st.success("Đã thêm nhân viên mới!")

# 7. JS CUỘN NGANG
components.html("""
<script>
    const interval = setInterval(() => {
        const el = window.parent.document.querySelector('div[data-testid="stDataEditor"] [role="grid"]');
        if (el) {
            let isDown = false; let startX, scrollLeft;
            el.addEventListener('mousedown', (e) => { isDown = true; startX = e.pageX - el.offsetLeft; scrollLeft = el.scrollLeft; });
            el.addEventListener('mouseleave', () => { isDown = false; });
            el.addEventListener('mouseup', () => { isDown = false; });
            el.addEventListener('mousemove', (e) => {
                if(!isDown) return;
                const x = e.pageX - el.offsetLeft;
                el.scrollLeft = scrollLeft - (x - startX) * 2;
            });
            clearInterval(interval);
        }
    }, 1000);
</script>
""", height=0)
