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

# Danh sách ngày lễ tháng 2/2026 (Ví dụ: Tết Nguyên Đán thường rơi vào tầm này)
# Bạn có thể bổ sung thêm ngày lễ vào list này
HOLIDAYS = [15, 16, 17, 18, 19] # Ví dụ các ngày nghỉ Tết âm lịch

if 'db' not in st.session_state:
    try:
        df_cloud = conn.read(worksheet="Sheet1")
        st.session_state.db = df_cloud if (df_cloud is not None and not df_cloud.empty) else pd.DataFrame()
    except:
        st.session_state.db = pd.DataFrame()

if 'gians' not in st.session_state:
    st.session_state.gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

if 'editor_v' not in st.session_state:
    st.session_state.editor_v = 0

DATE_COLS = [f"{d:02d}/02" for d in range(1, 29)]

# --- HÀM LOGIC TÍNH NGHỈ CA (QUY ƯỚC MỚI) ---
def calculate_pvd_offshore(row):
    total_accrued = 0.0
    rigs = st.session_state.gians
    
    for col in DATE_COLS:
        day_val = int(col.split('/')[0])
        # Xác định thứ trong tuần (2026-02-day)
        d_obj = date(2026, 2, day_val)
        weekday = d_obj.weekday() # 0:T2, 5:T7, 6:CN
        
        val = row[col]
        
        # 1. LOGIC CỘNG NGÀY (KHI ĐI BIỂN)
        if val in rigs:
            if day_val in HOLIDAYS:
                total_accrued += 2.0  # Lễ tết: 1 biển = 2 ca
            elif weekday >= 5:
                total_accrued += 1.0  # T7, CN: 1 biển = 1 ca
            else:
                total_accrued += 0.5  # T2-T6: 2 biển = 1 ca (1 ngày = 0.5)

        # 2. LOGIC TRỪ NGÀY (KHI NGHỈ CA)
        elif val == "CA":
            # Chỉ trừ nếu là ngày thường (T2-T6) và không phải lễ
            if weekday < 5 and day_val not in HOLIDAYS:
                total_accrued -= 1.0
            # T7, CN và Lễ không trừ ngày nghỉ ca theo quy ước của bạn
            
    return round(total_accrued, 2)

if st.session_state.db.empty:
    NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang"]
    df = pd.DataFrame({'STT': range(1, len(NAMES)+1), 'Họ và Tên': NAMES, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': '', 'Nghỉ Ca Còn Lại': 0.0})
    for c in DATE_COLS: df[c] = ""
    st.session_state.db = df

# Cập nhật số liệu tự động
st.session_state.db['Nghỉ Ca Còn Lại'] = st.session_state.db.apply(calculate_pvd_offshore, axis=1)

# --- 3. TIÊU ĐỀ ---
c_logo, c_title = st.columns([1, 4])
with c_logo:
    logo_path = "logo_pvd.png"
    if os.path.exists(logo_path): st.image(logo_path, width=150)
    else: st.write("📌 (Logo)")
with c_title:
    st.markdown('<br><h1 style="color: #00f2ff; text-align: left; margin-top: -10px;">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 4. GIAO DIỆN TABS ---
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "📝 CHI TIẾT", "📥 XUẤT FILE"])

with tabs[0]: 
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        with st.expander("➕ NHẬP DỮ LIỆU NHANH", expanded=False):
            with st.form("input_form"):
                f_staff = st.multiselect("Nhân viên:", st.session_state.db['Họ và Tên'].tolist())
                f_status = st.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm"])
                f_gian = st.selectbox("Giàn:", st.session_state.gians) if f_status == "Đi Biển" else f_status
                f_date = st.date_input("Từ ngày - Đến ngày:", value=(date(2026, 2, 1), date(2026, 2, 2)))
                if st.form_submit_button("XÁC NHẬN"):
                    if isinstance(f_date, tuple) and len(f_date) == 2:
                        for d in range(f_date[0].day, f_date[1].day + 1):
                            col = f"{d:02d}/02"
                            if col in st.session_state.db.columns:
                                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), col] = f_gian
                        st.session_state.editor_v += 1
                        st.rerun()
    with c2:
        if st.button("💾 LƯU LÊN CLOUD", use_container_width=True):
            conn.update(worksheet="Sheet1", data=st.session_state.db)
            st.success("Đã lưu thành công!")
    with c3:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            st.session_state.db.to_excel(writer, index=False, sheet_name='Management')
        st.download_button("📥 TẢI EXCEL", data=buffer.getvalue(), file_name=f"PVD_Export_{date.today()}.xlsx", use_container_width=True)

    edited_df = st.data_editor(
        st.session_state.db,
        column_config={"Nghỉ Ca Còn Lại": st.column_config.NumberColumn("Nghỉ Ca Còn Lại", disabled=True, format="%.1f")},
        use_container_width=True, height=500, key=f"main_editor_{st.session_state.editor_v}"
    )
    if not edited_df.equals(st.session_state.db):
        st.session_state.db = edited_df

# (Các Tab khác giữ nguyên cấu trúc cũ)
with tabs[1]:
    st.subheader("🏗️ Danh sách Giàn khoan")
    g_df = pd.DataFrame({"TenGian": st.session_state.gians})
    new_g = st.data_editor(g_df, num_rows="dynamic", use_container_width=True, key="g_editor")
    if st.button("Cập nhật Giàn"):
        st.session_state.gians = new_g['TenGian'].dropna().tolist()
        conn.update(worksheet="Gians", data=pd.DataFrame({"TenGian": st.session_state.gians}))
        st.rerun()

# --- 5. HỖ TRỢ CUỘN NGANG ---
components.html("""
<script>
    setTimeout(() => {
        const el = window.parent.document.querySelector('div[data-testid="stDataEditor"] [role="grid"]');
        if (el) {
            el.style.cursor = "grab";
            let isDown = false; let startX, scrollLeft;
            el.addEventListener('mousedown', (e) => { isDown = true; startX = e.pageX - el.offsetLeft; scrollLeft = el.scrollLeft; });
            el.addEventListener('mouseleave', () => { isDown = false; });
            el.addEventListener('mouseup', () => { isDown = false; });
            el.addEventListener('mousemove', (e) => { if(!isDown) return; e.preventDefault(); const x = e.pageX - el.offsetLeft; el.scrollLeft = scrollLeft - (x - startX) * 2; });
        }
    }, 1000);
</script>
""", height=0)
