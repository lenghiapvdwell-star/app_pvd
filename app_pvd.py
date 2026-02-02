import streamlit as st
import pandas as pd
from datetime import datetime, date
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import io
import os

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="PVD Well Services 2026", layout="wide")

# CSS để ẩn các vòng xoay Connecting gây khó chịu và tối ưu giao diện
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        .stButton button {width: 100%; border-radius: 5px;}
        [data-testid="stStatusWidget"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# Hiển thị Logo và Tiêu đề
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=120)
with col_title:
    st.markdown('<h1 style="color: #00f2ff; text-align: center; margin-bottom: 0;">PVD WELL SERVICES MANAGEMENT 2026</h1>', unsafe_allow_html=True)

# 2. KHỞI TẠO KẾT NỐI & DỮ LIỆU (Chỉ chạy 1 lần)
conn = st.connection("gsheets", type=GSheetsConnection)

def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/02\n{days_vn[d.weekday()]}"

DATE_COLS = [get_col_name(d) for d in range(1, 29)]
NGAY_LE_TET = [15, 16, 17, 18, 19, 20, 21]

@st.cache_data(ttl=3600) # Lưu bộ nhớ đệm trong 1 tiếng
def fetch_data():
    try:
        db = conn.read(worksheet="Sheet1")
        # Kiểm tra cấu trúc cột
        for col in ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Nghỉ Ca Còn Lại', 'Job Detail'] + DATE_COLS:
            if col not in db.columns: db[col] = ""
    except:
        db = pd.DataFrame(columns=['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Nghỉ Ca Còn Lại', 'Job Detail'] + DATE_COLS)
    
    try:
        gians = conn.read(worksheet="Gians")['TenGian'].dropna().tolist()
    except:
        gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]
        
    try:
        staffs = conn.read(worksheet="Staffs")
    except:
        staffs = pd.DataFrame(columns=['STT', 'Họ và Tên', 'Công ty', 'Chức danh'])
        
    return db, gians, staffs

if 'db' not in st.session_state:
    st.session_state.db, st.session_state.gians, st.session_state.staffs = fetch_data()

# 3. CÁC HÀM XỬ LÝ (Không rerun toàn bộ)
def trigger_save():
    with st.spinner("Đang đồng bộ dữ liệu..."):
        conn.update(worksheet="Sheet1", data=st.session_state.db)
        conn.update(worksheet="Gians", data=pd.DataFrame({"TenGian": st.session_state.gians}))
        conn.update(worksheet="Staffs", data=st.session_state.staffs)
        st.cache_data.clear() # Xóa cache sau khi lưu thành công
        st.success("✅ ĐÃ LƯU LÊN CLOUD VÀ LÀM MỚI BỘ NHỚ!")

# NÚT LƯU CỐ ĐỊNH TRÊN CÙNG
c_s1, c_s2 = st.columns([4, 1])
with c_s2:
    if st.button("💾 LƯU DỮ LIỆU", type="primary"):
        trigger_save()

# 4. GIAO DIỆN TABS
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 TỔNG HỢP", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "📝 CHI TIẾT", "📥 XUẤT FILE"])

# TAB ĐIỀU ĐỘNG (Sử dụng Fragment để không load lại toàn app)
@st.fragment
def tab_dieu_dong():
    c1, c2, c3 = st.columns([2, 1, 1.5])
    sel_staff = c1.multiselect("NHÂN VIÊN:", st.session_state.db['Họ và Tên'].tolist())
    status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "CA", "WS", "NP"])
    val = c2.selectbox("GIÀN:", st.session_state.gians) if status == "Đi Biển" else status
    dates = c3.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))
    if st.button("XÁC NHẬN ĐIỀU ĐỘNG"):
        if isinstance(dates, tuple) and len(dates) == 2:
            for d in range(dates[0].day, dates[1].day + 1):
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), get_col_name(d)] = val
            st.toast("Đã ghi nhớ thay đổi!")

with tabs[0]: tab_dieu_dong()

with tabs[1]: # BẢNG TỔNG HỢP
    if st.button("🚀 TÍNH TOÁN NGHỈ CA NHANH"):
        for idx, row in st.session_state.db.iterrows():
            bal = 0.0
            for d in range(1, 29):
                col = get_col_name(d); v = row[col]; d_obj = date(2026, 2, d); thu = d_obj.weekday()
                if v in st.session_state.gians:
                    if d in NGAY_LE_TET: bal += 2.0
                    elif thu >= 5: bal += 1.0
                    else: bal += 0.5
                elif v == "CA" and thu < 5 and d not in NGAY_LE_TET: bal -= 1.0
            st.session_state.db.at[idx, 'Nghỉ Ca Còn Lại'] = round(bal, 1)
        st.rerun()

    disp_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Nghỉ Ca Còn Lại', 'Job Detail'] + DATE_COLS
    # Sử dụng bộ editor không tự động rerun
    st.session_state.db = st.data_editor(st.session_state.db[disp_cols], use_container_width=True, height=500)

with tabs[3]: # QUẢN LÝ NHÂN VIÊN
    st.session_state.staffs = st.data_editor(st.session_state.staffs, use_container_width=True, num_rows="dynamic")
    if st.button("Cập nhật vào bảng chính"):
        # Logic này giúp thêm người mới mà không mất dữ liệu cũ
        for _, s in st.session_state.staffs.iterrows():
            if s['Họ và Tên'] not in st.session_state.db['Họ và Tên'].tolist():
                new_row = {c: "" for c in st.session_state.db.columns}
                new_row.update(s.to_dict()); new_row['Nghỉ Ca Còn Lại'] = 0.0
                st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_row])], ignore_index=True)
        st.rerun()

with tabs[5]: # XUẤT FILE
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        st.session_state.db.to_excel(writer, index=False, sheet_name='Management')
    st.download_button("📥 TẢI FILE EXCEL (.xlsx)", data=output.getvalue(), file_name=f"PVD_2026.xlsx", use_container_width=True)

# 5. JS CHO CUỘN NGANG MƯỢT
components.html("""
<script>
    const interval = setInterval(() => {
        const el = window.parent.document.querySelector('div[data-testid="stDataEditor"] [role="grid"]');
        if (el) {
            el.style.cursor = "grab";
            let isDown = false; let startX, scrollLeft;
            el.addEventListener('mousedown', (e) => { isDown = true; startX = e.pageX - el.offsetLeft; scrollLeft = el.scrollLeft; el.style.cursor = "grabbing"; });
            el.addEventListener('mouseleave', () => { isDown = false; el.style.cursor = "grab"; });
            el.addEventListener('mouseup', () => { isDown = false; el.style.cursor = "grab"; });
            el.addEventListener('mousemove', (e) => {
                if(!isDown) return;
                e.preventDefault();
                const x = e.pageX - el.offsetLeft;
                el.scrollLeft = scrollLeft - (x - startX) * 2.5;
            });
            clearInterval(interval);
        }
    }, 1000);
</script>
""", height=0)
