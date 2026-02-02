import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="PVD Personnel Management 2026", layout="wide")

# Hàm tạo tên cột ngày tháng
def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/Feb {days_vn[d.weekday()]}"

# 2. KHỞI TẠO BỘ NHỚ
if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

# Danh sách 64 nhân sự ban đầu
INITIAL_NAMES = [
    "Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang",
    "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong",
    "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia",
    "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin",
    "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang",
    "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu",
    "Do Duc Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong",
    "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh",
    "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy",
    "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh",
    "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung",
    "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat",
    "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"
]

if 'db' not in st.session_state:
    df = pd.DataFrame({
        'STT': range(1, len(INITIAL_NAMES) + 1),
        'Họ và Tên': INITIAL_NAMES,
        'Công ty': 'PVD',
        'Chức danh': 'Kỹ sư',
        'Nghỉ Ca Còn Lại': 0.0,
        'Job Detail': ''
    })
    for d in range(1, 29):
        df[get_col_name(d)] = ""
    st.session_state.db = df

# 3. LOGIC QUÉT DỮ LIỆU
def scan_balance():
    tet_2026 = [17, 18, 19, 20, 21]
    df_tmp = st.session_state.db.copy()
    for index, row in df_tmp.iterrows():
        balance = 0.0
        for d in range(1, 29):
            col = get_col_name(d)
            if col in df_tmp.columns:
                val = row[col]
                d_obj = date(2026, 2, d)
                if val in st.session_state.list_gian:
                    if d in tet_2026: balance += 2.0
                    elif d_obj.weekday() >= 5: balance += 1.0
                    else: balance += 0.5
                elif val == "CA":
                    balance -= 1.0
        df_tmp.at[index, 'Nghỉ Ca Còn Lại'] = float(balance)
    st.session_state.db = df_tmp

# 4. GIAO DIỆN
col_logo, col_text = st.columns([1, 5])
with col_logo:
    try:
        st.image("logo_pvd.png", width=100)
    except:
        st.write("Logo PVD")

with col_text:
    st.title("🚢 PVD PERSONNEL MANAGEMENT 2026")

tabs = st.tabs(["🚀 Điều Động", "👤 Thêm Nhân Viên", "✍️ Chỉnh Sửa Tay", "🔍 Quét Số Dư", "🏗️ Quản Lý Giàn"])

# TAB 1: NHẬP ĐIỀU ĐỘNG
with tabs[0]:
    c1, c2, c3 = st.columns([2, 1, 1.5])
    staff_options = st.session_state.db['Họ và Tên'].tolist()
    sel_staff = c1.multiselect("Chọn nhân viên:", staff_options)
    status = c2.selectbox("Trạng thái:", ["Đi Biển", "Nghỉ Ca (CA)", "Làm Xưởng (WS)", "Nghỉ Phép (NP)"])
    
    val_to_fill = ""
    if status == "Đi Biển":
        val_to_fill = c2.selectbox("Chọn Giàn:", st.session_state.list_gian)
    else:
        mapping = {"Nghỉ Ca (CA)": "CA", "Làm Xưởng (WS)": "WS", "Nghỉ Phép (NP)": "NP"}
        val_to_fill = mapping.get(status, status)
    
    dates = c3.date_input("Khoảng ngày (Tính cả ngày đi & về):", value=(date(2026, 2, 1), date(2026, 2, 3)))

    if st.button("XÁC NHẬN CẬP NHẬT", type="primary"):
        if isinstance(dates, tuple) and len(dates) == 2:
            for d in range(dates[0].day, dates[1].day + 1):
                col = get_col_name(d)
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col] = val_to_fill
            st.success("Đã cập nhật lịch trình!")
            st.rerun()

# TAB 2: THÊM NHÂN VIÊN MỚI
with tabs[1]:
    st.subheader("➕ Thêm nhân sự mới vào danh sách")
    with st.form("add_staff_form"):
        new_name = st.text_input("Họ và Tên nhân viên mới:")
        new_corp = st.text_input("Công ty:", value="PVD")
        new_pos = st.text_input("Chức danh:", value="Kỹ sư")
        submit_new = st.form_submit_button("Thêm vào danh sách")
        
        if submit_new and new_name:
            new_stt = len(st.session_state.db) + 1
            new_row = {
                'STT': new_stt,
                'Họ và Tên': new_name,
                'Công ty': new_corp,
                'Chức danh': new_pos,
                'Nghỉ Ca Còn Lại': 0.0,
                'Job Detail': ''
            }
            for d in range(1, 29):
                new_row[get_col_name(d)] = ""
            
            st.session_state.db = pd.concat([st.
