import streamlit as st
import pandas as pd
from datetime import datetime, date
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH HỆ THỐNG (GIỮ NGUYÊN GIAO DIỆN ĐẸP) ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
        [data-testid="stStatusWidget"] {display: none !important;}
        .stButton button {border-radius: 8px; font-weight: bold; height: 3em;}
        div.stButton > button { background-color: #00f2ff !important; color: #1a1c24 !important; }
        [data-testid="stDataEditor"] { border: 2px solid #00f2ff; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. DỮ LIỆU GỐC (64 NHÂN VIÊN) ---
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]
DATE_COLS = [f"{d:02d}/02" for d in range(1, 29)]
HOLIDAYS = [15, 16, 17, 18, 19] # Ngày lễ Tết

# --- 3. KHỞI TẠO DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

if 'db' not in st.session_state:
    try:
        df_cloud = conn.read(worksheet="Sheet1")
        if df_cloud is not None and not df_cloud.empty:
            st.session_state.db = df_cloud
        else:
            st.session_state.db = pd.DataFrame()
    except:
        st.session_state.db = pd.DataFrame()

if st.session_state.db.empty:
    df = pd.DataFrame({'STT': range(1, 65), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': '', 'Nghỉ Ca Còn Lại': 0.0})
    for c in DATE_COLS: df[c] = ""
    st.session_state.db = df

if 'gians' not in st.session_state:
    st.session_state.gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

# --- 4. HÀM TÍNH TOÁN (VÁ LỖI TRIỆT ĐỂ) ---
def calculate_pvd_logic(row):
    accrued = 0.0
    rigs = st.session_state.gians
    for col in DATE_COLS:
        if col in row.index:
            val = str(row[col]).strip() if pd.notna(row[col]) else ""
            if not val: continue
            
            day = int(col.split('/')[0])
            weekday = date(2026, 2, day).weekday() # 0=T2, 5=T7, 6=CN
            
            if val in rigs: # ĐI BIỂN
                if day in HOLIDAYS: accrued += 2.0
                elif weekday >= 5: accrued += 1.0
                else: accrued += 0.5
            elif val == "CA": # NGHỈ CA
                if weekday < 5 and day not in HOLIDAYS: accrued -= 1.0
    return round(accrued, 2)

# Cập nhật số liệu
st.session_state.db['Nghỉ Ca Còn Lại'] = st.session_state.db.apply(calculate_pvd_logic, axis=1)

# --- 5. GIAO DIỆN CHÍNH (GIỮ NGUYÊN NHƯ CŨ) ---
c_logo, c_title = st.columns([1, 4])
with c_logo:
    if os.path.exists("logo_pvd.png"): st.image("logo_pvd.png", width=150)
with c_title:
    st.markdown('<br><h1 style="color: #00f2ff; text-align: left; margin-top: -10px;">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "📝 CHI TIẾT", "📥 XUẤT FILE"])

with tabs[0]: 
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        with st.expander("➕ NHẬP DỮ LIỆU NHANH", expanded=False):
            with st.form("input_form"):
                f_staff = st.multiselect("Nhân viên:", st.session_state.db['Họ và Tên'].tolist())
                f_status = st.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP"])
                f_gian = st.selectbox("Giàn:", st.session_state.gians) if f_status == "Đi Biển" else f_status
                f_date = st.date_input("Khoảng ngày:", value=(date(2026, 2, 1), date(2026, 2, 2)))
                if st.form_submit_button("XÁC NHẬN"):
                    if isinstance(f_date, tuple) and len(f_date) == 2:
                        for d in range(f_date[0].day, f_date[1].day + 1):
                            col = f"{d:02d}/02"
                            if col in st.session_state.db.columns:
                                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), col] = f_gian
                        st.rerun()
    with c2:
        if st.button("💾 LƯU LÊN CLOUD", use_container_width=True):
            conn.update(worksheet="Sheet1", data=st.session_state.db)
            st.success("Đã lưu!")
    with c3:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            st.session_state.db.to_excel(writer, index=False)
        st.download_button("📥 TẢI EXCEL", data=buffer.getvalue(), file_name="PVD_Export.xlsx", use_container_width=True)

    st.data_editor(
        st.session_state.db,
        column_config={"Nghỉ Ca Còn Lại": st.column_config.NumberColumn("Quỹ CA", disabled=True, format="%.1f")},
        use_container_width=True, height=550, key="main_editor"
    )

with tabs[1]:
    st.subheader("🏗️ Danh sách Giàn khoan")
    g_df = pd.DataFrame({"TenGian": st.session_state.gians})
    new_g = st.data_editor(g_df, num_rows="dynamic", use_container_width=True)
    if st.button("Cập nhật Giàn"):
        st.session_state.gians = new_g['TenGian'].dropna().tolist()
        st.rerun()

# --- 6. HỖ TRỢ CUỘN NGANG ---
components.html("""
<script>
    setTimeout(() => {
        const el = window.parent.document.querySelector('div[data-testid="stDataEditor"] [role="grid"]');
        if (el) {
            let isDown = false; let startX, scrollLeft;
            el.addEventListener('mousedown', (e) => { isDown = true; startX = e.pageX - el.offsetLeft; scrollLeft = el.scrollLeft; });
            el.addEventListener('mouseleave', () => { isDown = false; });
            el.addEventListener('mouseup', () => { isDown = false; });
            el.addEventListener('mousemove', (e) => { if(!isDown) return; e.preventDefault(); const x = e.pageX - el.offsetLeft; el.scrollLeft = scrollLeft - (x - startX) * 2; });
        }
    }, 1000);
</script>
""", height=0)
