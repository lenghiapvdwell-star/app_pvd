import streamlit as st
import pandas as pd
from datetime import datetime, date
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="PVD Management 2026", layout="wide")

st.markdown("""
    <style>
        [data-testid="stStatusWidget"] {display: none !important;}
        .stButton button {border-radius: 8px; font-weight: bold; height: 3em; border: 1px solid #00f2ff;}
        [data-testid="stDataEditor"] { border: 1px solid #00f2ff; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. DỮ LIỆU GỐC 64 NHÂN VIÊN ---
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/02\n{days_vn[d.weekday()]}"

DATE_COLS = [get_col_name(d) for d in range(1, 29)]

# --- 3. KẾT NỐI & KHỞI TẠO DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

def create_default_db():
    df = pd.DataFrame({
        'STT': range(1, 65),
        'Họ và Tên': NAMES_64,
        'Công ty': 'PVDWS',
        'Chức danh': 'Kỹ sư',
        'Job Detail': '',
        'Nghỉ Ca Còn Lại': 0.0
    })
    for col in DATE_COLS: df[col] = ""
    return df

@st.cache_data(ttl=300)
def load_data():
    try:
        db = conn.read(worksheet="Sheet1")
        if db.empty or 'Họ và Tên' not in db.columns: db = create_default_db()
    except: db = create_default_db()
    try:
        gians = conn.read(worksheet="Gians")['TenGian'].dropna().astype(str).tolist()
    except:
        gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]
    return db, gians

# Khởi tạo Session State (Bộ nhớ tạm)
if 'db' not in st.session_state:
    st.session_state.db, st.session_state.gians = load_data()
if 'recent_staff' not in st.session_state:
    st.session_state.recent_staff = []

# --- 4. GIAO DIỆN LOGO & TIÊU ĐỀ ---
col_logo, col_title, col_save = st.columns([1, 4, 1.2])
with col_logo:
    # Nếu file logo_pvd.png nằm cùng thư mục trên GitHub, app sẽ tự nhận
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=100)
    else:
        st.error("Thiếu logo_pvd.png")

with col_title:
    st.markdown('<h1 style="color: #00f2ff; text-align: center;">PVD MANAGEMENT 2026</h1>', unsafe_allow_html=True)

with col_save:
    if st.button("💾 LƯU CLOUD (SAVE ALL)", type="primary", use_container_width=True):
        conn.update(worksheet="Sheet1", data=st.session_state.db)
        conn.update(worksheet="Gians", data=pd.DataFrame({"TenGian": st.session_state.gians}))
        st.success("✅ Đã lưu thành công!")

# --- 5. TABS ---
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG & TỔNG HỢP", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "📝 CHI TIẾT"])

with tabs[0]: # TAB CHÍNH
    with st.container():
        st.subheader("🚀 THAO TÁC NHẬP LIỆU")
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1.5])
        
        all_names = st.session_state.db['Họ và Tên'].tolist()
        sel_staff = c1.multiselect("CHỌN NHÂN VIÊN:", all_names, default=st.session_state.recent_staff if any(n in all_names for n in st.session_state.recent_staff) else None)
        
        status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "CA", "WS", "NP"])
        val = c3.selectbox("CHỌN GIÀN:", st.session_state.gians) if status == "Đi Biển" else status
        
        dates = c4.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))

        if st.button("✅ NHẬP DỮ LIỆU", use_container_width=True):
            if isinstance(dates, tuple) and len(dates) == 2 and sel_staff:
                for d in range(dates[0].day, dates[1].day + 1):
                    st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), get_col_name(d)] = val
                st.session_state.recent_staff = sel_staff # Lưu lịch sử
                st.toast("Đã nhập dữ liệu thành công!")
                st.rerun()

    st.divider()
    # Cấu hình thu nhỏ cột
    col_cfg = {
        "STT": st.column_config.NumberColumn(width=40),
        "Họ và Tên": st.column_config.TextColumn(width=180),
        "Công ty": st.column_config.TextColumn(width=70),
        "Job Detail": st.column_config.TextColumn(width=150),
        "Nghỉ Ca Còn Lại": st.column_config.NumberColumn(width=60),
    }
    for col in DATE_COLS: col_cfg[col] = st.column_config.TextColumn(width=55)

    # Bảng Tổng hợp - Dùng key để chống reset khi đang sửa
    st.session_state.db = st.data_editor(st.session_state.db, column_config=col_cfg, use_container_width=True, height=500, num_rows="dynamic", key="main_editor")

with tabs[1]: # GIÀN KHOAN
    st.subheader("🏗️ Danh sách Giàn khoan")
    # Ép kiểu dữ liệu văn bản để nhập được chữ
    g_df = pd.DataFrame({"TenGian": st.session_state.gians}).astype(str)
    edited_g = st.data_editor(g_df, num_rows="dynamic", use_container_width=True, key="rig_editor", column_config={"TenGian": st.column_config.TextColumn("Tên Giàn (Nhập chữ/số)")})
    st.session_state.gians = edited_g['TenGian'].dropna().tolist()

with tabs[2]: # NHÂN VIÊN
    staff_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail']
    edited_staff = st.data_editor(st.session_state.db[staff_cols], num_rows="dynamic", use_container_width=True, key="staff_editor")
    
    if st.button("XÁC NHẬN CẬP NHẬT NHÂN SỰ"):
        # Ghép lại dữ liệu đồng bộ
        others = [c for c in st.session_state.db.columns if c not in staff_cols]
        new_db = pd.concat([edited_staff.reset_index(drop=True), st.session_state.db[others].reset_index(drop=True)], axis=1)
        st.session_state.db = new_db
        st.success("Đã đồng bộ nhân sự!")

with tabs[3]: # CHI TIẾT
    pick_n = st.selectbox("Chọn nhanh nhân viên sửa Job Detail:", st.session_state.db['Họ và Tên'].tolist())
    if pick_n:
        idx = st.session_state.db[st.session_state.db['Họ và Tên'] == pick_n].index[0]
        st.session_state.db.at[idx, 'Job Detail'] = st.text_area("Nội dung ghi chú:", value=st.session_state.db.at[idx, 'Job Detail'], height=250, key="detail_area")

# Hỗ trợ cuộn ngang
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
