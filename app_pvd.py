import streamlit as st
import pandas as pd
from datetime import datetime, date
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import os

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="PVD Management 2026", layout="wide")

# CSS để bảng hiển thị đẹp và rõ ràng hơn
st.markdown("""
    <style>
        [data-testid="stStatusWidget"] {display: none !important;}
        .stButton button {border-radius: 8px; font-weight: bold; height: 3em; border: 1px solid #00f2ff; background-color: #1a1c24; color: #00f2ff;}
        [data-testid="stDataEditor"] { border: 2px solid #00f2ff; border-radius: 10px; }
        .stDataFrame { font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. DỮ LIỆU NHÂN VIÊN GỐC (Dùng khi Sheet trống) ---
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/02\n{days_vn[d.weekday()]}"

DATE_COLS = [get_col_name(d) for d in range(1, 29)]

# --- 3. KẾT NỐI VÀ QUẢN LÝ BỘ NHỚ (SESSION STATE) ---
conn = st.connection("gsheets", type=GSheetsConnection)

# CHỈ TẢI DỮ LIỆU MỘT LẦN DUY NHẤT KHI MỞ APP
if 'db' not in st.session_state:
    try:
        # Thử đọc từ Google Sheets
        df_cloud = conn.read(worksheet="Sheet1")
        if df_cloud.empty or 'Họ và Tên' not in df_cloud.columns:
            # Tạo mới nếu Sheets trống
            df = pd.DataFrame({'STT': range(1, 65), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': '', 'Nghỉ Ca Còn Lại': 0.0})
            for c in DATE_COLS: df[c] = ""
            st.session_state.db = df
        else:
            # Nếu có dữ liệu, gán vào bộ nhớ tạm
            st.session_state.db = df_cloud
    except:
        # Nếu lỗi kết nối, dùng dữ liệu mặc định
        df = pd.DataFrame({'STT': range(1, 65), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': '', 'Nghỉ Ca Còn Lại': 0.0})
        for c in DATE_COLS: df[c] = ""
        st.session_state.db = df

if 'gians' not in st.session_state:
    try:
        g_raw = conn.read(worksheet="Gians")
        st.session_state.gians = g_raw['TenGian'].dropna().astype(str).tolist()
    except:
        st.session_state.gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

# Hàm lưu tập trung
def save_data():
    try:
        conn.update(worksheet="Sheet1", data=st.session_state.db)
        conn.update(worksheet="Gians", data=pd.DataFrame({"TenGian": st.session_state.gians}))
        st.success("✅ Đã lưu dữ liệu lên Google Sheets thành công!")
    except Exception as e:
        st.error("❌ Không tìm thấy Sheet1 hoặc Gians trên Google Sheets. Vui lòng kiểm tra tên Sheet.")

# --- 4. GIAO DIỆN LOGO & TIÊU ĐỀ ---
c_logo, c_title = st.columns([1, 5])
with c_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=120)
with c_title:
    st.markdown('<h1 style="color: #00f2ff; text-align: left; margin-bottom: 20px;">PVD WELL SERVICES - 2026</h1>', unsafe_allow_html=True)

# --- 5. HỆ THỐNG TABS ---
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG & TỔNG HỢP", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "📝 CHI TIẾT"])

with tabs[0]: # TAB ĐIỀU ĐỘNG
    # Nút lưu nằm ngay trong tab
    col_btn1, col_btn2 = st.columns([5, 1])
    with col_btn2:
        if st.button("💾 LƯU CLOUD", key="btn_save_1"):
            save_data()

    # Dùng FORM để gom các thay đổi, tránh bị reset khi đang chọn
    with st.form("input_form"):
        st.subheader("🚀 NHẬP DỮ LIỆU NHANH")
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1.5])
        
        sel_staff = c1.multiselect("CHỌN NHÂN VIÊN:", st.session_state.db['Họ và Tên'].tolist())
        status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "CA", "WS", "NP"])
        gian_val = c3.selectbox("CHỌN GIÀN:", st.session_state.gians) if status == "Đi Biển" else status
        dates = c4.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))
        
        submitted = st.form_submit_button("✅ XÁC NHẬN NHẬP")
        if submitted:
            if isinstance(dates, tuple) and len(dates) == 2 and sel_staff:
                for d in range(dates[0].day, dates[1].day + 1):
                    col = get_col_name(d)
                    st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col] = gian_val
                st.toast("Đã cập nhật bảng tạm!")

    st.divider()
    
    # Cấu hình hiển thị cột đầy đủ thông tin
    col_cfg = {
        "STT": st.column_config.NumberColumn(width=50),
        "Họ và Tên": st.column_config.TextColumn("Họ và Tên", width=220),
        "Công ty": st.column_config.TextColumn("Công ty", width=100),
        "Chức danh": st.column_config.TextColumn("Chức danh", width=150),
        "Job Detail": st.column_config.TextColumn("Job Detail", width=300),
        "Nghỉ Ca Còn Lại": st.column_config.NumberColumn("Nghỉ Ca", width=80),
    }
    for c in DATE_COLS: 
        col_cfg[c] = st.column_config.TextColumn(c, width=85)

    # BẢNG TỔNG HỢP - Gán trực tiếp kết quả edit vào db để ko bao giờ mất dữ liệu
    st.session_state.db = st.data_editor(
        st.session_state.db,
        column_config=col_cfg,
        use_container_width=True,
        height=600,
        num_rows="dynamic",
        key="main_table_key" # Khóa này giúp bảng giữ trạng thái
    )

with tabs[1]: # TAB GIÀN KHOAN
    col_btn_g1, col_btn_g2 = st.columns([5, 1])
    with col_btn_g2:
        if st.button("💾 LƯU CLOUD", key="btn_save_2"): save_data()
            
    st.subheader("🏗️ Quản lý Giàn Khoan")
    g_df = pd.DataFrame({"TenGian": st.session_state.gians}).astype(str)
    edited_g = st.data_editor(g_df, num_rows="dynamic", use_container_width=True, key="rig_table_key")
    if st.button("ĐỒNG BỘ TÊN GIÀN"):
        st.session_state.gians = edited_g['TenGian'].dropna().tolist()
        st.success("Đã đồng bộ danh sách Giàn!")

with tabs[2]: # TAB NHÂN VIÊN
    col_btn_s1, col_btn_s2 = st.columns([5, 1])
    with col_btn_s2:
        if st.button("💾 LƯU CLOUD", key="btn_save_3"): save_data()

    st.subheader("👤 Quản lý Nhân sự")
    s_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail']
    edited_s = st.data_editor(st.session_state.db[s_cols], num_rows="dynamic", use_container_width=True, key="staff_table_key")
    if st.button("ĐỒNG BỘ NHÂN VIÊN"):
        # Lấy các cột ngày tháng hiện tại
        others = [c for c in st.session_state.db.columns if c not in s_cols]
        # Hợp nhất dữ liệu mới sửa với các cột ngày tháng cũ
        st.session_state.db = pd.concat([edited_s.reset_index(drop=True), st.session_state.db[others].reset_index(drop=True)], axis=1)
        st.success("Đã đồng bộ thông tin nhân viên vào bảng chính!")

with tabs[3]: # TAB CHI TIẾT
    st.subheader("📝 Ghi chú Job Detail")
    pick_n = st.selectbox("Chọn nhân viên để xem/sửa chi tiết:", st.session_state.db['Họ và Tên'].tolist())
    if pick_n:
        idx = st.session_state.db[st.session_state.db['Họ và Tên'] == pick_n].index[0]
        # Sửa trực tiếp vào db
        st.session_state.db.at[idx, 'Job Detail'] = st.text_area("Nội dung ghi chú:", value=st.session_state.db.at[idx, 'Job Detail'], height=300)
        if st.button("Lưu nhanh Job Detail"):
            save_data()

# JS Hỗ trợ cuộn ngang
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
