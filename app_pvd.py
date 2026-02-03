import streamlit as st
import pandas as pd
from datetime import datetime, date
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import os

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
        [data-testid="stStatusWidget"] {display: none !important;}
        .stButton button {border-radius: 8px; font-weight: bold; height: 3em;}
        div.stButton > button[key^="btn_save"] {
            background-color: #00f2ff !important;
            color: #1a1c24 !important;
            border: none;
            width: 100%;
        }
        [data-testid="stDataEditor"] { border: 2px solid #00f2ff; border-radius: 10px; }
        .stDataFrame { font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. DỮ LIỆU GỐC ---
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
        if df_cloud is not None and not df_cloud.empty:
            st.session_state.db = df_cloud
        else:
            raise ValueError
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

def handle_save():
    try:
        # Trước khi lưu, đồng bộ dữ liệu từ editor vào db chính
        if "main_table" in st.session_state and "edited_rows" in st.session_state.main_table:
            # Dữ liệu từ key 'main_table' sẽ được tự động xử lý
            pass
        conn.update(worksheet="Sheet1", data=st.session_state.db)
        conn.update(worksheet="Gians", data=pd.DataFrame({"TenGian": st.session_state.gians}))
        st.success("✅ DỮ LIỆU ĐÃ LƯU LÊN CLOUD THÀNH CÔNG!")
    except Exception as e:
        st.error(f"❌ LỖI LƯU DỮ LIỆU: {e}")

# --- 4. TIÊU ĐỀ VIẾT HOA ---
c_logo, c_title = st.columns([1, 4])
with c_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=180)
with c_title:
    st.markdown('<br><h1 style="color: #00f2ff; text-align: left;">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 5. TABS ---
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "📝 CHI TIẾT"])

with tabs[0]: 
    with st.expander("📝 NHẬP LIỆU NHANH", expanded=True):
        c_in, c_sv = st.columns([4.5, 1.5])
        with c_in:
            with st.form("input_form"):
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1.5])
                sel_staff = col1.multiselect("NHÂN VIÊN:", st.session_state.db['Họ và Tên'].tolist())
                status = col2.selectbox("TRẠNG THÁI:", ["Đi Biển", "CA", "WS", "NP"])
                gian_val = col3.selectbox("GIÀN:", st.session_state.gians) if status == "Đi Biển" else status
                dates = col4.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))
                
                if st.form_submit_button("✅ XÁC NHẬN NHẬP", use_container_width=True):
                    if isinstance(dates, tuple) and len(dates) == 2 and sel_staff:
                        for d in range(dates[0].day, dates[1].day + 1):
                            col_n = get_col_name(d)
                            st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col_n] = gian_val
                        # Xử lý triệt để lỗi bằng cách ép buộc Streamlit vẽ lại từ đầu
                        st.rerun()

        with c_sv:
            st.write("")
            st.write("")
            if st.button("💾 LƯU CLOUD (SAVE)", key="btn_save_main"):
                handle_save()

    st.divider()
    
    col_cfg = {
        "STT": st.column_config.NumberColumn(width=50, disabled=True),
        "Họ và Tên": st.column_config.TextColumn("Họ và Tên", width=220, disabled=True),
        "Job Detail": st.column_config.TextColumn("Job Detail", width=300),
    }
    for c in DATE_COLS: col_cfg[c] = st.column_config.TextColumn(c, width=85)

    # KHẮC PHỤC TRIỆT ĐỂ: Sử dụng bản copy để hiển thị và gán ngược lại
    display_df = st.session_state.db.copy()
    
    edited_df = st.data_editor(
        display_df,
        column_config=col_cfg,
        use_container_width=True,
        height=600,
        num_rows="dynamic",
        key="main_table"
    )
    
    # Cập nhật db gốc khi có thay đổi trên bảng
    if not edited_df.equals(st.session_state.db):
        st.session_state.db = edited_df

# ... (Các tab khác giữ nguyên logic tương tự với key riêng)
