import streamlit as st
import pandas as pd
from datetime import datetime, date
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
        [data-testid="stStatusWidget"] {display: none !important;}
        .stButton button {border-radius: 8px; font-weight: bold;}
        div.stButton > button { background-color: #00f2ff !important; color: #1a1c24 !important; }
        [data-testid="stDataEditor"] { border: 2px solid #00f2ff; border-radius: 10px; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] { background-color: #262730; border-radius: 5px; padding: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. KHỞI TẠO DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

if 'db' not in st.session_state:
    try:
        df_cloud = conn.read(worksheet="Sheet1")
        st.session_state.db = df_cloud if (df_cloud is not None and not df_cloud.empty) else pd.DataFrame()
    except:
        st.session_state.db = pd.DataFrame()

if 'gians' not in st.session_state:
    try:
        g_raw = conn.read(worksheet="Gians")
        st.session_state.gians = g_raw['TenGian'].dropna().tolist()
    except:
        st.session_state.gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

if 'editor_v' not in st.session_state:
    st.session_state.editor_v = 0

if st.session_state.db.empty:
    NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang"]
    DATE_COLS = [f"{d:02d}/02" for d in range(1, 29)]
    df = pd.DataFrame({'STT': range(1, len(NAMES)+1), 'Họ và Tên': NAMES, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': ''})
    for c in DATE_COLS: df[c] = ""
    st.session_state.db = df

# --- 3. TIÊU ĐỀ CÓ LOGO (Cùng hàng) ---
c_logo, c_title = st.columns([1, 4])
with c_logo:
    # Thử tìm file logo trong thư mục gốc (GitHub)
    # Thay 'logo_pvd.png' bằng tên file chính xác của bạn trên GitHub
    logo_path = "logo_pvd.png" 
    if os.path.exists(logo_path):
        st.image(logo_path, width=150)
    else:
        st.write("📌 (Logo)") # Hiện chữ nếu chưa tìm thấy file

with c_title:
    st.markdown('<br><h1 style="color: #00f2ff; text-align: left; margin-top: -10px;">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 4. GIAO DIỆN TABS ---
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "📝 CHI TIẾT", "📥 XUẤT FILE"])

with tabs[0]: # ĐIỀU ĐỘNG
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        with st.expander("➕ NHẬP DỮ LIỆU NHANH", expanded=False):
            with st.form("input_form"):
                f_staff = st.multiselect("Nhân viên:", st.session_state.db['Họ và Tên'].tolist())
                f_status = st.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP"])
                f_gian = st.selectbox("Giàn:", st.session_state.gians) if f_status == "Đi Biển" else f_status
                f_date = st.date_input("Từ ngày - Đến ngày:", value=(date(2026, 2, 1), date(2026, 2, 2)))
                if st.form_submit_button("XÁC NHẬN"):
                    if len(f_date) == 2:
                        for d in range(f_date[0].day, f_date[1].day + 1):
                            col = next((c for c in st.session_state.db.columns if c.startswith(f"{d:02d}")), None)
                            if col: st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), col] = f_gian
                        st.session_state.editor_v += 1
                        st.rerun()
    with c2:
        if st.button("💾 LƯU LÊN CLOUD", use_container_width=True):
            conn.update(worksheet="Sheet1", data=st.session_state.db)
            st.success("Đã lưu!")
    with c3:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            st.session_state.db.to_excel(writer, index=False, sheet_name='Management')
        st.download_button("📥 TẢI EXCEL", data=buffer.getvalue(), file_name=f"PVD_Export_{date.today()}.xlsx", use_container_width=True)

    edited_df = st.data_editor(
        st.session_state.db,
        use_container_width=True,
        height=500,
        key=f"main_editor_{st.session_state.editor_v}"
    )
    if not edited_df.equals(st.session_state.db):
        st.session_state.db = edited_df

with tabs[1]: # GIÀN KHOAN
    st.subheader("🏗️ Danh sách Giàn khoan")
    g_df = pd.DataFrame({"TenGian": st.session_state.gians})
    new_g = st.data_editor(g_df, num_rows="dynamic", use_container_width=True, key="g_editor")
    if st.button("Cập nhật Giàn"):
        st.session_state.gians = new_g['TenGian'].dropna().tolist()
        conn.update(worksheet="Gians", data=pd.DataFrame({"TenGian": st.session_state.gians}))
        st.rerun()

with tabs[2]: # NHÂN VIÊN
    st.subheader("👤 Danh sách Nhân sự")
    staff_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh']
    st.data_editor(st.session_state.db[staff_cols], num_rows="dynamic", use_container_width=True, key="staff_editor")

with tabs[3]: # CHI TIẾT
    st.subheader("📝 Ghi chú Job Detail")
    sel = st.selectbox("Chọn nhân viên:", st.session_state.db['Họ và Tên'].tolist())
    idx = st.session_state.db[st.session_state.db['Họ và Tên'] == sel].index[0]
    note = st.text_area("Nội dung công việc:", value=st.session_state.db.at[idx, 'Job Detail'], height=200)
    if st.button("Lưu ghi chú"):
        st.session_state.db.at[idx, 'Job Detail'] = note
        st.success("Đã lưu ghi chú!")

with tabs[4]: # XUẤT FILE
    st.subheader("📥 Xuất báo cáo Excel")
    st.download_button("BẮT ĐẦU TẢI FILE (.xlsx)", data=buffer.getvalue(), file_name="Bao_cao_PVD.xlsx", key="btn_download_tab")

# --- 5. HỖ TRỢ CUỘN NGANG ---
components.html("""
<script>
    setTimeout(() => {
        const el = window.parent.document.querySelector('div[data-testid="stDataEditor"] [role="grid"]');
        if (el) {
            el.style.cursor = "grab";
            let isDown = false; let startX; let scrollLeft;
            el.addEventListener('mousedown', (e) => { isDown = true; startX = e.pageX - el.offsetLeft; scrollLeft = el.scrollLeft; });
            el.addEventListener('mouseleave', () => { isDown = false; });
            el.addEventListener('mouseup', () => { isDown = false; });
            el.addEventListener('mousemove', (e) => { if(!isDown) return; e.preventDefault(); const x = e.pageX - el.offsetLeft; const walk = (x - startX) * 2; el.scrollLeft = scrollLeft - walk; });
        }
    }, 1000);
</script>
""", height=0)
