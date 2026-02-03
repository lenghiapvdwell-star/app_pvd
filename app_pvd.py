import streamlit as st
import pandas as pd
from datetime import datetime, date
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH & GIAO DIỆN ---
st.set_page_config(page_title="PVD Management 2026", layout="wide")

st.markdown("""
    <style>
        [data-testid="stStatusWidget"] {display: none !important;}
        .stButton button {border-radius: 8px; font-weight: bold; height: 3em; border: 1px solid #00f2ff;}
        [data-testid="stDataEditor"] { border: 2px solid #00f2ff; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. DỮ LIỆU GỐC 64 NHÂN VIÊN ---
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/02\n{days_vn[d.weekday()]}"

DATE_COLS = [get_col_name(d) for d in range(1, 29)]
REQUIRED_COLS = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail', 'Nghỉ Ca Còn Lại'] + DATE_COLS

# --- 3. KẾT NỐI & KHỞI TẠO DỮ LIỆU AN TOÀN ---
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
        # Kiểm tra nếu thiếu cột quan trọng thì reset về mặc định để tránh crash
        if db.empty or 'Họ và Tên' not in db.columns:
            db = create_default_db()
    except Exception:
        db = create_default_db()
    
    try:
        gians = conn.read(worksheet="Gians")['TenGian'].dropna().tolist()
    except Exception:
        gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]
    return db, gians

if 'db' not in st.session_state:
    st.session_state.db, st.session_state.gians = load_data()

# --- 4. GIAO DIỆN CHÍNH ---
col_logo, col_title, col_save = st.columns([1, 4, 1])
with col_title:
    st.markdown('<h1 style="color: #00f2ff; text-align: center; margin:0;">PVD MANAGEMENT 2026</h1>', unsafe_allow_html=True)
with col_save:
    if st.button("💾 LƯU CLOUD", type="primary", use_container_width=True):
        conn.update(worksheet="Sheet1", data=st.session_state.db)
        conn.update(worksheet="Gians", data=pd.DataFrame({"TenGian": st.session_state.gians}))
        st.success("Đã lưu!")

# TABS CHÍNH
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG & TỔNG HỢP", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "📝 CHI TIẾT"])

with tabs[0]: 
    st.subheader("🚀 THAO TÁC NHANH")
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1.5])
    
    # Kiểm tra an toàn trước khi lấy danh sách tên
    names_list = st.session_state.db['Họ và Tên'].dropna().tolist() if 'Họ và Tên' in st.session_state.db.columns else NAMES_64
    sel_staff = c1.multiselect("CHỌN NHÂN VIÊN:", names_list)
    
    status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "CA", "WS", "NP"])
    if status == "Đi Biển":
        val = c3.selectbox("CHỌN GIÀN:", st.session_state.gians)
    else:
        val = status
        c3.markdown(f"<br><p style='text-align:center; color:gray;'>{status}</p>", unsafe_allow_html=True)
    
    dates = c4.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))

    if st.button("✅ NHẬP DỮ LIỆU", use_container_width=True):
        if isinstance(dates, tuple) and len(dates) == 2:
            for d in range(dates[0].day, dates[1].day + 1):
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), get_col_name(d)] = val
            st.toast("Đã cập nhật!")

    st.divider()
    st.subheader("📊 BẢNG TỔNG HỢP")
    # Cho phép kéo/thả/copy như Excel
    st.session_state.db = st.data_editor(st.session_state.db, use_container_width=True, height=500, num_rows="dynamic")

with tabs[1]: # GIÀN KHOAN
    st.subheader("🏗️ Quản lý danh sách Giàn")
    edited_g = st.data_editor(pd.DataFrame({"TenGian": st.session_state.gians}), num_rows="dynamic", use_container_width=True)
    st.session_state.gians = edited_g['TenGian'].dropna().tolist()

with tabs[2]: # NHÂN VIÊN
    st.subheader("👤 Quản lý Nhân sự (Thêm/Xóa/Sửa)")
    staff_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail']
    # Lọc lấy các cột nhân sự để sửa nhanh
    if all(col in st.session_state.db.columns for col in staff_cols):
        edited_staff_df = st.data_editor(st.session_state.db[staff_cols], num_rows="dynamic", use_container_width=True)
        
        if st.button("XÁC NHẬN THAY ĐỔI"):
            # Cập nhật thông tin nhân sự và giữ nguyên các cột ngày tháng
            other_cols = [c for c in st.session_state.db.columns if c not in staff_cols]
            updated_db = pd.concat([edited_staff_df.reset_index(drop=True), st.session_state.db[other_cols].reset_index(drop=True)], axis=1)
            # Tự động điền PVDWS nếu cột Công ty bị bỏ trống
            updated_db['Công ty'] = updated_db['Công ty'].fillna('PVDWS').replace('', 'PVDWS')
            st.session_state.db = updated_db
            st.success("Đã đồng bộ danh sách!")
    else:
        st.error("Dữ liệu cột không hợp lệ. Vui lòng nhấn Lưu Cloud để khởi tạo lại.")

with tabs[3]: # CHI TIẾT
    st.subheader("📝 Ghi chú chi tiết")
    pick_n = st.selectbox("Chọn nhân viên:", names_list)
    if pick_n:
        idx_list = st.session_state.db[st.session_state.db['Họ và Tên'] == pick_n].index
        if not idx_list.empty:
            idx = idx_list[0]
            st.session_state.db.at[idx, 'Job Detail'] = st.text_area("Nội dung:", value=st.session_state.db.at[idx, 'Job Detail'], height=250)

# --- 5. HỖ TRỢ CUỘN NGANG ---
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
