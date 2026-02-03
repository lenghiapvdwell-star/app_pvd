import streamlit as st
import pandas as pd
from datetime import datetime, date
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import os

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="PVD Management 2026", layout="wide")

st.markdown("""
    <style>
        [data-testid="stStatusWidget"] {display: none !important;}
        .stButton button {border-radius: 8px; font-weight: bold; height: 3em; border: 1px solid #00f2ff; background-color: #1a1c24; color: #00f2ff;}
        [data-testid="stDataEditor"] { border: 2px solid #00f2ff; border-radius: 10px; }
        .stDataFrame { font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. KHỞI TẠO DỮ LIỆU ---
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/02\n{days_vn[d.weekday()]}"

DATE_COLS = [get_col_name(d) for d in range(1, 29)]

# KẾT NỐI GSHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

# CHỈ LOAD DỮ LIỆU KHI MỞ APP (Dùng cache để chống reset)
@st.cache_data(ttl=600)
def load_initial_data():
    try:
        df = conn.read(worksheet="Sheet1")
        g_raw = conn.read(worksheet="Gians")
        gians = g_raw['TenGian'].dropna().astype(str).tolist()
        return df, gians
    except:
        # Nếu chưa có gì trên Cloud, tạo khung mặc định
        df = pd.DataFrame({'STT': range(1, 65), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': '', 'Nghỉ Ca Còn Lại': 0.0})
        for c in DATE_COLS: df[c] = ""
        return df, ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

# Gán vào Session State nếu chưa có
if 'db' not in st.session_state:
    st.session_state.db, st.session_state.gians = load_initial_data()

def save_to_cloud():
    try:
        # Cập nhật Sheet1 và Gians
        conn.update(worksheet="Sheet1", data=st.session_state.db)
        conn.update(worksheet="Gians", data=pd.DataFrame({"TenGian": st.session_state.gians}))
        st.success("✅ Đã lưu lên Google Sheets!")
        st.cache_data.clear() # Xóa cache để lần sau load lại dữ liệu mới nhất
    except Exception as e:
        st.error(f"❌ Lỗi: Bạn cần đổi tên 'Trang tính1' thành 'Sheet1' trên Google Sheets.")

# --- 3. GIAO DIỆN ---
c_logo, c_title = st.columns([1, 5])
with c_logo:
    if os.path.exists("logo_pvd.png"): st.image("logo_pvd.png", width=120)
with c_title:
    st.markdown('<h1 style="color: #00f2ff;">PVD WELL SERVICES - 2026</h1>', unsafe_allow_html=True)

tabs = st.tabs(["🚀 ĐIỀU ĐỘNG & TỔNG HỢP", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "📝 CHI TIẾT"])

with tabs[0]:
    # Nút Lưu Cloud nằm trong Tab
    c_btn1, c_btn2 = st.columns([5, 1])
    with c_btn2:
        if st.button("💾 LƯU CLOUD", key="save_t1"): save_to_cloud()

    with st.form("input_form"):
        st.subheader("🚀 NHẬP DỮ LIỆU NHANH")
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1.5])
        sel_staff = c1.multiselect("CHỌN NHÂN VIÊN:", st.session_state.db['Họ và Tên'].tolist())
        status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "CA", "WS", "NP"])
        gian_val = c3.selectbox("CHỌN GIÀN:", st.session_state.gians) if status == "Đi Biển" else status
        dates = c4.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))
        
        if st.form_submit_button("✅ XÁC NHẬN NHẬP"):
            if isinstance(dates, tuple) and len(dates) == 2 and sel_staff:
                for d in range(dates[0].day, dates[1].day + 1):
                    col = get_col_name(d)
                    st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col] = gian_val
                st.toast("Đã cập nhật bảng tạm!")

    st.divider()
    
    # Cấu hình độ rộng cột để hiện đủ thông tin
    col_cfg = {
        "STT": st.column_config.NumberColumn(width=50),
        "Họ và Tên": st.column_config.TextColumn("Họ và Tên", width=220),
        "Job Detail": st.column_config.TextColumn("Job Detail", width=300),
    }
    for c in DATE_COLS: col_cfg[c] = st.column_config.TextColumn(c, width=85)

    # Dùng key cố định để chống reset bảng khi đang gõ
    st.session_state.db = st.data_editor(
        st.session_state.db,
        column_config=col_cfg,
        use_container_width=True,
        height=600,
        num_rows="dynamic",
        key="editor_chinh" 
    )

with tabs[1]: # GIÀN KHOAN
    c_g1, c_g2 = st.columns([5, 1])
    with c_g2:
        if st.button("💾 LƯU CLOUD", key="save_t2"): save_to_cloud()
    
    st.subheader("🏗️ Quản lý Giàn Khoan")
    g_df = pd.DataFrame({"TenGian": st.session_state.gians}).astype(str)
    edited_g = st.data_editor(g_df, num_rows="dynamic", use_container_width=True, key="rig_ed")
    if st.button("Xác nhận cập nhật Giàn"):
        st.session_state.gians = edited_g['TenGian'].dropna().tolist()
        st.success("Đã ghi nhớ danh sách giàn!")

with tabs[2]: # NHÂN VIÊN
    c_s1, c_s2 = st.columns([5, 1])
    with c_s2:
        if st.button("💾 LƯU CLOUD", key="save_t3"): save_to_cloud()
        
    st.subheader("👤 Quản lý Nhân sự")
    s_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail']
    edited_s = st.data_editor(st.session_state.db[s_cols], num_rows="dynamic", use_container_width=True, key="staff_ed")
    if st.button("Đồng bộ danh sách người"):
        others = [c for c in st.session_state.db.columns if c not in s_cols]
        st.session_state.db = pd.concat([edited_s.reset_index(drop=True), st.session_state.db[others].reset_index(drop=True)], axis=1)
        st.success("Đã đồng bộ!")

with tabs[3]: # CHI TIẾT
    pick_n = st.selectbox("Chọn nhân viên:", st.session_state.db['Họ và Tên'].tolist())
    if pick_n:
        idx = st.session_state.db[st.session_state.db['Họ và Tên'] == pick_n].index[0]
        st.session_state.db.at[idx, 'Job Detail'] = st.text_area("Nội dung:", value=st.session_state.db.at[idx, 'Job Detail'], height=300)

# JS cuộn ngang
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
