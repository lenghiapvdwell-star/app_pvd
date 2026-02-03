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
        /* Tăng cỡ chữ bảng một chút để dễ nhìn */
        .stDataFrame { font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. DANH SÁCH 64 NHÂN VIÊN ---
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/02\n{days_vn[d.weekday()]}"

DATE_COLS = [get_col_name(d) for d in range(1, 29)]

# --- 3. KẾT NỐI VÀ KIỂM TRA TÊN SHEET ---
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_load():
    # Mặc định khởi tạo bảng trống nếu Sheets có vấn đề
    default_df = pd.DataFrame({'STT': range(1, 65), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': '', 'Nghỉ Ca Còn Lại': 0.0})
    for c in DATE_COLS: default_df[c] = ""
    
    try:
        # Thử đọc Sheet1
        db = conn.read(worksheet="Sheet1")
        if db.empty or 'Họ và Tên' not in db.columns:
            db = default_df
    except:
        st.warning("⚠️ Không tìm thấy trang tính tên 'Sheet1'. App đang dùng dữ liệu tạm thời. Hãy đổi tên trang tính trên Google Sheets thành 'Sheet1'.")
        db = default_df
        
    try:
        gians = conn.read(worksheet="Gians")['TenGian'].dropna().astype(str).tolist()
    except:
        gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]
        
    return db, gians

if 'db' not in st.session_state:
    st.session_state.db, st.session_state.gians = safe_load()

# --- 4. GIAO DIỆN TIÊU ĐỀ ---
c_logo, c_title = st.columns([1, 5])
with c_logo:
    if os.path.exists("logo_pvd.png"): st.image("logo_pvd.png", width=120)
with c_title:
    st.markdown('<h1 style="color: #00f2ff; text-align: left;">PVD WELL SERVICES - 2026</h1>', unsafe_allow_html=True)

# --- 5. HỆ THỐNG TABS & NÚT LƯU ---
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG & TỔNG HỢP", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "📝 CHI TIẾT"])

# Hàm lưu dữ liệu tập trung
def save_to_cloud():
    try:
        conn.update(worksheet="Sheet1", data=st.session_state.db)
        conn.update(worksheet="Gians", data=pd.DataFrame({"TenGian": st.session_state.gians}))
        st.success("✅ Đã lưu dữ liệu lên Google Sheets thành công!")
    except Exception as e:
        st.error(f"❌ Lỗi lưu file: Hãy đảm bảo bạn có trang tính tên 'Sheet1' và 'Gians'.")
        st.info(f"Chi tiết lỗi: {e}")

with tabs[0]: # TAB CHÍNH
    # Khu vực nút Lưu nằm ngay trong Tab
    c_btn1, c_btn2 = st.columns([4, 1])
    with c_btn2:
        if st.button("💾 LƯU CLOUD (SAVE)", use_container_width=True, key="save_t1"):
            save_to_cloud()

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
                st.toast("Đã cập nhật bảng tạm thời!")

    st.divider()
    
    # CẤU HÌNH ĐỘ RỘNG CỘT (HIỆN ĐỦ THÔNG TIN)
    col_cfg = {
        "STT": st.column_config.NumberColumn(width=50),
        "Họ và Tên": st.column_config.TextColumn("Họ và Tên", width=220, help="Tên đầy đủ nhân viên"),
        "Công ty": st.column_config.TextColumn("Công ty", width=100),
        "Chức danh": st.column_config.TextColumn("Chức danh", width=150),
        "Job Detail": st.column_config.TextColumn("Job Detail", width=300),
        "Nghỉ Ca Còn Lại": st.column_config.NumberColumn("Nghỉ Ca", width=80),
    }
    # Tăng độ rộng cột ngày tháng để thấy rõ Thứ/Ngày
    for c in DATE_COLS: 
        col_cfg[c] = st.column_config.TextColumn(c, width=85)

    st.session_state.db = st.data_editor(
        st.session_state.db,
        column_config=col_cfg,
        use_container_width=True,
        height=600,
        num_rows="dynamic",
        key="main_editor_v2"
    )

with tabs[1]: # GIÀN KHOAN
    c_g1, c_g2 = st.columns([4, 1])
    with c_g2:
        if st.button("💾 LƯU CLOUD", key="save_t2", use_container_width=True): save_to_cloud()
    
    st.subheader("🏗️ Quản lý Giàn Khoan")
    g_df = pd.DataFrame({"TenGian": st.session_state.gians}).astype(str)
    edited_g = st.data_editor(g_df, num_rows="dynamic", use_container_width=True, key="rig_ed")
    st.session_state.gians = edited_g['TenGian'].dropna().tolist()

with tabs[2]: # NHÂN VIÊN
    c_s1, c_s2 = st.columns([4, 1])
    with c_s2:
        if st.button("💾 LƯU CLOUD", key="save_t3", use_container_width=True): save_to_cloud()
        
    st.subheader("👤 Quản lý Nhân sự")
    s_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail']
    edited_s = st.data_editor(st.session_state.db[s_cols], num_rows="dynamic", use_container_width=True, key="staff_ed")
    if st.button("ĐỒNG BỘ NHÂN VIÊN"):
        others = [c for c in st.session_state.db.columns if c not in s_cols]
        st.session_state.db = pd.concat([edited_s.reset_index(drop=True), st.session_state.db[others].reset_index(drop=True)], axis=1)
        st.success("Đã cập nhật danh sách vào bảng chính!")

with tabs[3]: # CHI TIẾT
    st.subheader("📝 Ghi chú Job Detail")
    pick_n = st.selectbox("Chọn nhân viên:", st.session_state.db['Họ và Tên'].tolist())
    if pick_n:
        idx = st.session_state.db[st.session_state.db['Họ và Tên'] == pick_n].index[0]
        st.session_state.db.at[idx, 'Job Detail'] = st.text_area("Nội dung:", value=st.session_state.db.at[idx, 'Job Detail'], height=300)
        if st.button("Lưu ghi chú"): save_to_cloud()

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
