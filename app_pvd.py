import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="PVD Well Services 2026", layout="wide")

def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/02\n{days_vn[d.weekday()]}"

DATE_COLS = [get_col_name(d) for d in range(1, 29)]

# 2. KẾT NỐI GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data_from_gs():
    try:
        # ttl=0 để luôn lấy dữ liệu mới nhất từ Cloud
        return conn.read(ttl=0)
    except Exception as e:
        return None

def save_data_to_gs(df):
    try:
        # Worksheet mặc định thường là Sheet1
        conn.update(worksheet="Sheet1", data=df)
        st.toast("✅ Đã đồng bộ dữ liệu lên Cloud!", icon="☁️")
    except Exception as e:
        st.error(f"Lỗi lưu dữ liệu: {e}")

# 3. KHỞI TẠO HOẶC TẢI DỮ LIỆU
if 'db' not in st.session_state:
    existing_data = load_data_from_gs()
    if existing_data is not None and not existing_data.empty:
        # Kiểm tra nếu thiếu cột ngày (do đổi cấu hình) thì phải reset
        if get_col_name(1) not in existing_data.columns:
            st.warning("Cấu trúc cột cũ không khớp, đang khởi tạo lại...")
            st.session_state.db = None 
        else:
            st.session_state.db = existing_data
    
    if st.session_state.get('db') is None:
        NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]
        init_data = {'STT': range(1, len(NAMES) + 1), 'Họ và Tên': NAMES, 'Công ty': 'PVD', 'Chức danh': 'Kỹ sư', 'Nghỉ Ca Còn Lại': 0.0, 'Job Detail': ""}
        for col in DATE_COLS: init_data[col] = ""
        df_init = pd.DataFrame(init_data)
        st.session_state.db = df_init
        save_data_to_gs(df_init)

# 4. CSS VÀ GIAO DIỆN (GIỮ NGUYÊN)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .main-title-container { text-align: center; padding-bottom: 15px; border-bottom: 4px solid #00f2ff; margin-bottom: 30px; }
    .main-title-text { font-size: 38px !important; font-weight: 900; color: #00f2ff; }
    div[data-testid="stDataEditor"] th { height: 80px !important; white-space: pre !important; text-align: center !important; vertical-align: middle !important; color: #00f2ff !important; pointer-events: none; }
    div[data-testid="stDataEditor"] span:contains("None") { color: transparent !important; }
    </style>
    """, unsafe_allow_html=True)

# 5. HEADER
st.markdown('<div class="main-title-container"><p class="main-title-text">PVD WELL SERVICES MANAGEMENT 2026</p></div>', unsafe_allow_html=True)

# 6. TABS 
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "📝 JOB DETAIL", "📊 TỔNG HỢP"])

with tabs[0]: # ĐIỀU ĐỘNG
    c1, c2, c3 = st.columns([2, 1, 1.5])
    sel_staff = c1.multiselect("CHỌN NHÂN VIÊN:", st.session_state.db['Họ và Tên'].tolist())
    status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "Nghỉ Ca (CA)", "Làm Xưởng (WS)", "Nghỉ Phép (NP)"])
    list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]
    val_to_fill = c2.selectbox("CHỌN GIÀN:", list_gian) if status == "Đi Biển" else ({"Nghỉ Ca (CA)": "CA", "Làm Xưởng (WS)": "WS", "Nghỉ Phép (NP)": "NP"}.get(status))
    dates = c3.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))
    if st.button("XÁC NHẬN & ĐỒNG BỘ CLOUD", use_container_width=True):
        if isinstance(dates, tuple) and len(dates) == 2:
            for d in range(dates[0].day, dates[1].day + 1):
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), get_col_name(d)] = val_to_fill
            save_data_to_gs(st.session_state.db)
            st.rerun()

with tabs[1]: # JOB DETAIL
    st.write("Cập nhật nội dung Job tương tự...")

with tabs[2]: # BẢNG TỔNG HỢP
    st.write("### 📊 BẢNG TỔNG HỢP NHÂN SỰ")
    if st.button("🚀 TÍNH TOÁN & ĐỒNG BỘ SỐ DƯ NGHỈ CA", use_container_width=True):
        ngay_le_tet = [17, 18, 19, 20, 21]
        for idx, row in st.session_state.db.iterrows():
            bal = 0.0
            for d in range(1, 29):
                col = get_col_name(d); val = row[col]; d_obj = date(2026, 2, d)
                is_off_day = d_obj.weekday() >= 5 or d in ngay_le_tet
                if val in list_gian:
                    if d in ngay_le_tet: bal += 2.0
                    elif d_obj.weekday() >= 5: bal += 1.0
                    else: bal += 0.5
                elif val == "CA" and not is_off_day: bal -= 1.0
            st.session_state.db.at[idx, 'Nghỉ Ca Còn Lại'] = round(bal, 1)
        save_data_to_gs(st.session_state.db)
        st.rerun()

    display_order = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Nghỉ Ca Còn Lại', 'Job Detail'] + DATE_COLS
    all_opts = list_gian + ["CA", "WS", "NP"]
    col_cfg = {"STT": st.column_config.NumberColumn(width="small"), "Nghỉ Ca Còn Lại": st.column_config.NumberColumn(format="%.1f", width="small")}
    for c in DATE_COLS: col_cfg[c] = st.column_config.SelectboxColumn(width="small", options=all_opts)

    edited_df = st.data_editor(st.session_state.db[display_order], use_container_width=True, height=600, column_config=col_cfg, disabled=['STT', 'Nghỉ Ca Còn Lại'])
    
    if st.button("LƯU THAY ĐỔI TRỰC TIẾP TRÊN BẢNG"):
        st.session_state.db = edited_df
        save_data_to_gs(edited_df)

# JS KÉO CHUỘT (GIỮ NGUYÊN)
components.html("<script>...</script>", height=0)
