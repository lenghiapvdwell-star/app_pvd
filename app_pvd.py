import streamlit as st
import pandas as pd
from datetime import datetime, date
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import os

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="PVD Management", layout="wide")

st.markdown("""
    <style>
        [data-testid="stStatusWidget"] {display: none !important;}
        /* Nút xác nhận nhập màu xanh neon */
        .stButton button {border-radius: 8px; font-weight: bold; height: 3em;}
        /* Nút Lưu Cloud nổi bật hơn */
        div.stButton > button:first-child[key^="btn_save"] {
            background-color: #00f2ff !important;
            color: #1a1c24 !important;
            border: none;
        }
        [data-testid="stDataEditor"] { border: 2px solid #00f2ff; border-radius: 10px; }
        .stDataFrame { font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. DỮ LIỆU NHÂN VIÊN GỐC ---
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/02\n{days_vn[d.weekday()]}"

DATE_COLS = [get_col_name(d) for d in range(1, 29)]

# --- 3. QUẢN LÝ DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

if 'db' not in st.session_state:
    try:
        df_cloud = conn.read(worksheet="Sheet1")
        if df_cloud.empty or 'Họ và Tên' not in df_cloud.columns:
            df = pd.DataFrame({'STT': range(1, 65), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': '', 'Nghỉ Ca Còn Lại': 0.0})
            for c in DATE_COLS: df[c] = ""
            st.session_state.db = df
        else:
            st.session_state.db = df_cloud
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

def save_data():
    try:
        conn.update(worksheet="Sheet1", data=st.session_state.db)
        conn.update(worksheet="Gians", data=pd.DataFrame({"TenGian": st.session_state.gians}))
        st.success("✅ Dữ liệu đã được lưu an toàn lên Cloud!")
    except:
        st.error("❌ Lỗi: Hãy đảm bảo File Google Sheets có Sheet1 và Gians.")

# --- 4. GIAO DIỆN LOGO & TIÊU ĐỀ ---
c_logo, c_title = st.columns([1, 4])
with c_logo:
    # Logo to hơn 1.5 lần (180px)
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=180)
with c_title:
    st.markdown('<br><h1 style="color: #00f2ff; text-align: left;">PVD WELL SERVICES management</h1>', unsafe_allow_html=True)

# --- 5. HỆ THỐNG TABS ---
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG & TỔNG HỢP", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "📝 CHI TIẾT"])

with tabs[0]: 
    # Khung nhập liệu tích hợp nút Lưu
    with st.expander("📝 KHU VỰC THAO TÁC", expanded=True):
        with st.form("input_form"):
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1.5])
            sel_staff = c1.multiselect("CHỌN NHÂN VIÊN:", st.session_state.db['Họ và Tên'].tolist())
            status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "CA", "WS", "NP"])
            gian_val = c3.selectbox("CHỌN GIÀN:", st.session_state.gians) if status == "Đi Biển" else status
            dates = c4.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))
            
            # Hai nút nằm ngang cuối form
            cb1, cb2 = st.columns([1, 1])
            with cb1:
                submitted = st.form_submit_button("✅ XÁC NHẬN NHẬP", use_container_width=True)
            with cb2:
                # Nút lưu Cloud đặt ngay đây cho tiện
                save_btn = st.form_submit_button("💾 LƯU CLOUD (SAVE ALL)", use_container_width=True)
            
            if submitted:
                if isinstance(dates, tuple) and len(dates) == 2 and sel_staff:
                    for d in range(dates[0].day, dates[1].day + 1):
                        col = get_col_name(d)
                        st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col] = gian_val
                    st.toast("Đã cập nhật bảng tạm!")
            
            if save_btn:
                save_data()

    st.divider()
    col_cfg = {
        "STT": st.column_config.NumberColumn(width=50),
        "Họ và Tên": st.column_config.TextColumn("Họ và Tên", width=220),
        "Job Detail": st.column_config.TextColumn("Job Detail", width=300),
    }
    for c in DATE_COLS: col_cfg[c] = st.column_config.TextColumn(c, width=85)

    st.session_state.db = st.data_editor(
        st.session_state.db,
        column_config=col_cfg,
        use_container_width=True,
        height=600,
        num_rows="dynamic",
        key="main_table_key"
    )

with tabs[1]: # GIÀN KHOAN
    st.subheader("🏗️ Quản lý Giàn Khoan")
    cg1, cg2 = st.columns([3, 1])
    with cg1:
        g_df = pd.DataFrame({"TenGian": st.session_state.gians}).astype(str)
        edited_g = st.data_editor(g_df, num_rows="dynamic", use_container_width=True, key="rig_table_key")
    with cg2:
        if st.button("💾 LƯU CLOUD", key="btn_save_2", use_container_width=True):
            st.session_state.gians = edited_g['TenGian'].dropna().tolist()
            save_data()
        st.info("Nhập tên giàn mới vào bảng rồi nhấn Lưu.")

with tabs[2]: # NHÂN VIÊN
    st.subheader("👤 Quản lý Nhân sự")
    cs1, cs2 = st.columns([4, 1])
    with cs1:
        s_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail']
        edited_s = st.data_editor(st.session_state.db[s_cols], num_rows="dynamic", use_container_width=True, key="staff_table_key")
    with cs2:
        if st.button("💾 LƯU CLOUD", key="btn_save_3", use_container_width=True):
            others = [c for c in st.session_state.db.columns if c not in s_cols]
            st.session_state.db = pd.concat([edited_s.reset_index(drop=True), st.session_state.db[others].reset_index(drop=True)], axis=1)
            save_data()

with tabs[3]: # CHI TIẾT
    st.subheader("📝 Ghi chú Job Detail")
    pick_n = st.selectbox("Chọn nhân viên:", st.session_state.db['Họ và Tên'].tolist())
    if pick_n:
        idx = st.session_state.db[st.session_state.db['Họ và Tên'] == pick_n].index[0]
        st.session_state.db.at[idx, 'Job Detail'] = st.text_area("Nội dung ghi chú:", value=st.session_state.db.at[idx, 'Job Detail'], height=300)
        if st.button("💾 LƯU CLOUD", key="btn_save_4"):
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
