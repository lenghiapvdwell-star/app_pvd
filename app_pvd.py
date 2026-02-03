import streamlit as st
import pandas as pd
from datetime import datetime, date
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="PVD Management 2026", layout="wide")

st.markdown("""
    <style>
        [data-testid="stStatusWidget"] {display: none !important;}
        .main { background-color: #0e1117; }
        .stButton button {border-radius: 8px; font-weight: bold; height: 3em;}
        /* Làm nổi bật bảng dữ liệu */
        [data-testid="stDataEditor"] { border: 2px solid #00f2ff; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# Hiển thị Logo và Tiêu đề
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists("logo_pvd.png"): st.image("logo_pvd.png", width=120)
with col_title:
    st.markdown('<h1 style="color: #00f2ff; text-align: center;">PVD WELL SERVICES MANAGEMENT 2026</h1>', unsafe_allow_html=True)

# --- KẾT NỐI DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/02\n{days_vn[d.weekday()]}"

DATE_COLS = [get_col_name(d) for d in range(1, 29)]
NGAY_LE_TET = [15, 16, 17, 18, 19, 20, 21]

@st.cache_data(ttl=300)
def load_data():
    try:
        db = conn.read(worksheet="Sheet1")
        gians = conn.read(worksheet="Gians")['TenGian'].dropna().tolist()
        staffs = conn.read(worksheet="Staffs")
        return db, gians, staffs
    except:
        return pd.DataFrame(), ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"], pd.DataFrame()

if 'db' not in st.session_state:
    db_r, gians_r, staffs_r = load_data()
    # Nếu chưa có 64 nhân viên, bạn hãy nạp vào tab Staffs. 
    # Ở đây tôi mặc định lấy từ Sheets về để đảm bảo tính đồng bộ.
    st.session_state.db = db_r
    st.session_state.gians = gians_r
    st.session_state.staffs = staffs_r

# --- NÚT LƯU TỔNG CỐ ĐỊNH ---
st.divider()
c_save_l, c_save_r = st.columns([4, 1])
with c_save_r:
    if st.button("💾 LƯU CLOUD (SAVE ALL)", type="primary", use_container_width=True):
        conn.update(worksheet="Sheet1", data=st.session_state.db)
        conn.update(worksheet="Gians", data=pd.DataFrame({"TenGian": st.session_state.gians}))
        conn.update(worksheet="Staffs", data=st.session_state.staffs)
        st.success("Đã lưu!")

# --- PHẦN 1: ĐIỀU ĐỘNG (THAO TÁC NHANH) ---
st.subheader("🚀 BẢNG ĐIỀU ĐỘNG NHANH")
with st.container():
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1.5])
    
    sel_staff = c1.multiselect("CHỌN NHÂN VIÊN:", st.session_state.db['Họ và Tên'].tolist())
    
    # Ở đây KHÔNG dùng form để Option nhảy ngay lập tức
    status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "CA", "WS", "NP"])
    
    # Logic nhảy Option: Nếu chọn Đi Biển mới hiện List Giàn
    if status == "Đi Biển":
        val = c3.selectbox("CHỌN GIÀN:", st.session_state.gians)
    else:
        val = status
        c3.info(f"Sẽ nhập: {status}")
        
    dates = c4.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))

    if st.button("✅ ÁP DỤNG VÀO BẢNG DƯỚI", type="secondary"):
        if isinstance(dates, tuple) and len(dates) == 2:
            for d in range(dates[0].day, dates[1].day + 1):
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), get_col_name(d)] = val
            st.toast("Đã cập nhật dữ liệu tạm thời!")

# --- PHẦN 2: TỔNG HỢP (HIỆN NGAY PHÍA DƯỚI) ---
st.divider()
st.subheader("📊 BẢNG TỔNG HỢP CHI TIẾT")

c_tool1, c_tool2 = st.columns([1, 5])
if c_tool1.button("🚀 TÍNH NGHỈ CA"):
    for idx, row in st.session_state.db.iterrows():
        bal = 0.0
        for d in range(1, 29):
            col = get_col_name(d); v = row[col]; d_obj = date(2026, 2, d); thu = d_obj.weekday()
            if v in st.session_state.gians:
                bal += (2.0 if d in NGAY_LE_TET else (1.0 if thu >= 5 else 0.5))
            elif v == "CA" and thu < 5 and d not in NGAY_LE_TET: bal -= 1.0
        st.session_state.db.at[idx, 'Nghỉ Ca Còn Lại'] = round(bal, 1)
    st.rerun()

# BẢNG CHÍNH VỚI TÍNH NĂNG COPY/PASTE/DRAG GIỐNG EXCEL
# Lưu ý: Tính năng kéo thả (Fill handle) được kích hoạt mặc định trong data_editor mới nhất
st.session_state.db = st.data_editor(
    st.session_state.db, 
    use_container_width=True, 
    height=600,
    num_rows="dynamic"
)

# --- PHẦN 3: CÁC TAB PHỤ TRỢ ---
st.divider()
sub_tabs = st.tabs(["🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "📝 CHI TIẾT", "📥 XUẤT FILE"])

with sub_tabs[0]: # GIÀN KHOAN
    gians_df = pd.DataFrame({"TenGian": st.session_state.gians})
    edited_gians = st.data_editor(gians_df, num_rows="dynamic")
    st.session_state.gians = edited_gians['TenGian'].dropna().tolist()

with sub_tabs[1]: # NHÂN VIÊN
    st.session_state.staffs = st.data_editor(st.session_state.staffs, use_container_width=True, num_rows="dynamic")
    if st.button("ĐỒNG BỘ THÔNG TIN SANG BẢNG CHÍNH"):
        merged = st.session_state.db.drop(columns=['Công ty', 'Chức danh'], errors='ignore')
        st.session_state.db = pd.merge(merged, st.session_state.staffs[['Họ và Tên', 'Công ty', 'Chức danh']], on='Họ và Tên', how='left')
        st.success("Đã đồng bộ!")

with sub_tabs[2]: # CHI TIẾT
    sel_n = st.selectbox("Chọn nhân viên sửa Job Detail:", st.session_state.db['Họ và Tên'].tolist())
    idx_n = st.session_state.db[st.session_state.db['Họ và Tên'] == sel_n].index[0]
    st.session_state.db.at[idx_n, 'Job Detail'] = st.text_area("Nội dung Job Detail:", value=st.session_state.db.at[idx_n, 'Job Detail'], height=200)

with sub_tabs[3]: # XUẤT FILE
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        st.session_state.db.to_excel(writer, index=False, sheet_name='Management')
    st.download_button("📥 TẢI FILE EXCEL (.xlsx)", data=output.getvalue(), file_name=f"PVD_Report_2026.xlsx", use_container_width=True)

# JS Cải thiện cuộn ngang
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
