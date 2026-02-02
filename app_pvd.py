import streamlit as st
import pandas as pd
from datetime import datetime, date
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import os

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="PVD Well Services 2026", layout="wide")

# Hiển thị Logo và Tiêu đề
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=120)
    else:
        st.info("Logo PVD")
with col_title:
    st.markdown('<h1 style="color: #00f2ff; text-align: center;">PVD WELL SERVICES MANAGEMENT 2026</h1>', unsafe_allow_html=True)

# 2. KHỞI TẠO KẾT NỐI
conn = st.connection("gsheets", type=GSheetsConnection)

def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/02\n{days_vn[d.weekday()]}"

DATE_COLS = [get_col_name(d) for d in range(1, 29)]
NGAY_LE_TET = [15, 16, 17, 18, 19, 20, 21] 

# DANH SÁCH 64 NHÂN VIÊN
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

# 3. HÀM TẢI DỮ LIỆU AN TOÀN (CHỐNG LỖI WORKSHEET NOT FOUND)
def safe_load():
    # Thử tải Tab chính
    try:
        db = conn.read(worksheet="Sheet1", ttl=0)
    except: db = pd.DataFrame()

    # Thử tải Tab Giàn
    try:
        gians = conn.read(worksheet="Gians", ttl=0)['TenGian'].dropna().tolist()
    except: gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

    # Thử tải Tab Nhân viên
    try:
        staffs = conn.read(worksheet="Staffs", ttl=0)
    except: staffs = pd.DataFrame()
    
    return db, gians, staffs

if 'db' not in st.session_state:
    db_r, gians_r, staffs_r = safe_load()
    
    if staffs_r.empty:
        st.session_state.staffs = pd.DataFrame({"STT": range(1, len(NAMES_64)+1), "Họ và Tên": NAMES_64, "Công ty": "PVD", "Chức danh": "Kỹ sư"})
    else:
        st.session_state.staffs = staffs_r

    if db_r.empty:
        init_db = st.session_state.staffs.copy()
        init_db["Nghỉ Ca Còn Lại"] = 0.0
        init_db["Job Detail"] = ""
        for c in DATE_COLS: init_db[c] = ""
        st.session_state.db = init_db
    else:
        st.session_state.db = db_r
        
    st.session_state.gians = gians_r

def save_all():
    try:
        conn.update(worksheet="Sheet1", data=st.session_state.db)
        # Chỉ lưu các tab phụ nếu chúng tồn tại (để tránh lỗi WorksheetNotFound)
        st.toast("✅ Đã lưu dữ liệu Sheet1", icon="☁️")
    except Exception as e:
        st.error(f"Lỗi lưu dữ liệu: {e}. Vui lòng tạo thêm tab Gians và Staffs trên Google Sheet.")

# 4. CSS TÔ MÀU
def get_rig_style():
    colors = ["#FF4B4B", "#45FF45", "#4B8BFF", "#FFFF45", "#FF45FF", "#45FFFF", "#FFA500", "#00FF7F"]
    style = "<style>"
    for i, gian in enumerate(st.session_state.gians):
        c = colors[i % len(colors)]
        style += f'div[data-testid="stDataEditor"] span:contains("{gian}") {{ background-color: {c} !important; color: black !important; font-weight: bold; border-radius: 4px; padding: 2px 4px; }}'
    style += "div[data-testid='stDataEditor'] th { height: 80px !important; white-space: pre !important; }</style>"
    return style

st.markdown(get_rig_style(), unsafe_allow_html=True)

# 5. GIAO DIỆN TABS
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 TỔNG HỢP", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "📝 JOB"])

with tabs[0]: # ĐIỀU ĐỘNG
    c1, c2, c3 = st.columns([2, 1, 1.5])
    sel_staff = c1.multiselect("NHÂN VIÊN:", st.session_state.db['Họ và Tên'].tolist())
    status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "CA", "WS", "NP"])
    val = c2.selectbox("GIÀN:", st.session_state.gians) if status == "Đi Biển" else status
    dates = c3.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))
    if st.button("XÁC NHẬN", use_container_width=True):
        if isinstance(dates, tuple) and len(dates) == 2:
            for d in range(dates[0].day, dates[1].day + 1):
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), get_col_name(d)] = val
            save_all()
            st.rerun()

with tabs[1]: # TỔNG HỢP
    if st.button("🚀 TÍNH TOÁN NGHỈ CA DỒN TÍCH", use_container_width=True):
        for idx, row in st.session_state.db.iterrows():
            bal = 0.0
            for d in range(1, 29):
                col = get_col_name(d); v = row[col]; d_obj = date(2026, 2, d); thu = d_obj.weekday()
                if v in st.session_state.gians:
                    if d in NGAY_LE_TET: bal += 2.0
                    elif thu >= 5: bal += 1.0
                    else: bal += 0.5
                elif v == "CA" and thu < 5 and d not in NGAY_LE_TET: bal -= 1.0
            st.session_state.db.at[idx, 'Nghỉ Ca Còn Lại'] = round(bal, 1)
        save_all()
        st.rerun()

    disp_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Nghỉ Ca Còn Lại', 'Job Detail'] + DATE_COLS
    edited_df = st.data_editor(st.session_state.db[disp_cols], use_container_width=True, height=550)
    if st.button("LƯU THAY ĐỔI BẢNG"):
        st.session_state.db.update(edited_df)
        save_all()

with tabs[2]: # GIÀN KHOAN
    rig = st.text_input("Tên giàn mới:")
    if st.button("Thêm"):
        st.session_state.gians.append(rig); save_all(); st.rerun()
    del_rig = st.selectbox("Xóa giàn:", st.session_state.gians)
    if st.button("Xóa"):
        st.session_state.gians.remove(del_rig); save_all(); st.rerun()

with tabs[4]: # JOB
    name = st.selectbox("Nhân viên:", st.session_state.db['Họ và Tên'].tolist())
    job = st.text_area("Nội dung:")
    if st.button("Cập nhật"):
        st.session_state.db.loc[st.session_state.db['Họ và Tên'] == name, 'Job Detail'] = job
        save_all(); st.success("Xong!")
