import streamlit as st
import pandas as pd
from datetime import datetime, date
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import os

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="PVD Management 2026", layout="wide")

# CSS tối ưu giao diện
st.markdown("""
    <style>
        [data-testid="stStatusWidget"] {display: none !important;}
        .stButton button {border-radius: 8px; font-weight: bold; height: 3em; border: 1px solid #00f2ff; background-color: #1a1c24; color: #00f2ff;}
        .stButton button:hover {background-color: #00f2ff; color: #1a1c24;}
        div[data-testid="stExpander"] { border: 1px solid #333; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. KHỞI TẠO DỮ LIỆU GỐC ---
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/02\n{days_vn[d.weekday()]}"

DATE_COLS = [get_col_name(d) for d in range(1, 29)]

# --- 3. KẾT NỐI VÀ QUẢN LÝ BỘ NHỚ (SESSION STATE) ---
conn = st.connection("gsheets", type=GSheetsConnection)

# QUAN TRỌNG: Chỉ load dữ liệu 1 lần duy nhất khi mở App
if 'db' not in st.session_state:
    try:
        db_raw = conn.read(worksheet="Sheet1")
        if db_raw.empty or 'Họ và Tên' not in db_raw.columns:
            # Tạo mới nếu Sheets trống
            df = pd.DataFrame({'STT': range(1, 65), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': '', 'Nghỉ Ca Còn Lại': 0.0})
            for c in DATE_COLS: df[c] = ""
            st.session_state.db = df
        else:
            st.session_state.db = db_raw
    except:
        df = pd.DataFrame({'STT': range(1, 65), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': '', 'Nghỉ Ca Còn Lại': 0.0})
        for c in DATE_COLS: df[c] = ""
        st.session_state.db = df

if 'gians' not in st.session_state:
    try:
        g_raw = conn.read(worksheet="Gians")
        st.session_state.gians = g_raw['TenGian'].dropna().astype(str).tolist()
    except:
        st.session_state.gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

# --- 4. GIAO DIỆN LOGO & TIÊU ĐỀ ---
col_logo, col_title, col_save = st.columns([1, 4, 1.2])
with col_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=100)
with col_title:
    st.markdown('<h1 style="color: #00f2ff; text-align: center; margin-bottom:0;">PVD MANAGEMENT 2026</h1>', unsafe_allow_html=True)
with col_save:
    if st.button("💾 LƯU CLOUD", type="primary", use_container_width=True):
        conn.update(worksheet="Sheet1", data=st.session_state.db)
        conn.update(worksheet="Gians", data=pd.DataFrame({"TenGian": st.session_state.gians}))
        st.success("Đã đồng bộ!")

# --- 5. HỆ THỐNG TAB ---
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG & TỔNG HỢP", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "📝 CHI TIẾT"])

with tabs[0]:
    # Dùng FORM để ngăn chặn việc Rerun khi đang chọn dở
    with st.form("input_form"):
        st.subheader("🚀 NHẬP DỮ LIỆU NHANH")
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1.5])
        
        sel_staff = c1.multiselect("CHỌN NHÂN VIÊN:", st.session_state.db['Họ và Tên'].tolist())
        status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "CA", "WS", "NP"])
        
        # Nếu chọn Đi Biển thì hiện Giàn, không thì hiện trạng thái khác
        gian_val = c3.selectbox("CHỌN GIÀN:", st.session_state.gians) if status == "Đi Biển" else status
        
        dates = c4.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))
        
        submit = st.form_submit_button("✅ XÁC NHẬN NHẬP")
        if submit:
            if isinstance(dates, tuple) and len(dates) == 2 and sel_staff:
                for d in range(dates[0].day, dates[1].day + 1):
                    col = get_col_name(d)
                    st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col] = gian_val
                st.toast("Đã cập nhật bảng!")
                # Không dùng st.rerun ở đây để tránh mất trạng thái form

    st.divider()
    st.subheader("📊 BẢNG TỔNG HỢP CHI TIẾT")
    
    # Cấu hình độ rộng cột
    col_cfg = {
        "STT": st.column_config.NumberColumn(width=40),
        "Họ và Tên": st.column_config.TextColumn(width=180),
        "Công ty": st.column_config.TextColumn(width=70),
        "Job Detail": st.column_config.TextColumn(width=150),
        "Nghỉ Ca Còn Lại": st.column_config.NumberColumn(width=60),
    }
    for c in DATE_COLS: col_cfg[c] = st.column_config.TextColumn(width=55)

    # QUAN TRỌNG: Cập nhật trực tiếp vào session_state
    st.session_state.db = st.data_editor(
        st.session_state.db,
        column_config=col_cfg,
        use_container_width=True,
        height=550,
        num_rows="dynamic",
        key="main_table_editor" # Key này cực kỳ quan trọng để chống reset
    )

with tabs[1]: # GIÀN KHOAN
    st.subheader("🏗️ Quản lý Giàn Khoan")
    # Ép kiểu String để nhập được chữ
    g_df = pd.DataFrame({"TenGian": st.session_state.gians}).astype(str)
    edited_g = st.data_editor(g_df, num_rows="dynamic", use_container_width=True, key="rigs_editor")
    if st.button("Xác nhận đổi tên Giàn"):
        st.session_state.gians = edited_g['TenGian'].dropna().tolist()
        st.success("Đã cập nhật danh sách Giàn!")

with tabs[2]: # NHÂN VIÊN
    st.subheader("👤 Quản lý Nhân sự")
    staff_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail']
    # Chỉ sửa phần nhân sự
    edited_s = st.data_editor(st.session_state.db[staff_cols], num_rows="dynamic", use_container_width=True, key="staff_editor")
    
    if st.button("Cập nhật danh sách Nhân viên"):
        # Giữ nguyên lịch trình, chỉ đổi thông tin người
        other_cols = [c for c in st.session_state.db.columns if c not in staff_cols]
        st.session_state.db = pd.concat([edited_s.reset_index(drop=True), st.session_state.db[other_cols].reset_index(drop=True)], axis=1)
        st.session_state.db['Công ty'] = st.session_state.db['Công ty'].fillna('PVDWS').replace('', 'PVDWS')
        st.success("Đã đồng bộ nhân sự!")

with tabs[3]: # CHI TIẾT
    pick_n = st.selectbox("Chọn nhân viên:", st.session_state.db['Họ và Tên'].tolist())
    if pick_n:
        idx = st.session_state.db[st.session_state.db['Họ và Tên'] == pick_n].index[0]
        st.session_state.db.at[idx, 'Job Detail'] = st.text_area("Nội dung Job Detail:", value=st.session_state.db.at[idx, 'Job Detail'], height=300)

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
