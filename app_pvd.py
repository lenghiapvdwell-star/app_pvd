import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="PV Drilling - Quản lý Nhân sự 2026", layout="wide")

# --- CHÈN LOGO VÀ TIÊU ĐỀ BÊN TRÁI (SIDEBAR) ---
with st.sidebar:
    try:
        st.image("logo_pvd.png", width=200)
    except:
        st.error("Thiếu file logo_pvd.png")
    
    st.title("Hệ thống PV Drilling")
    st.info("Quản lý điều động nhân sự đi biển năm 2026")
    
    # Danh sách Giàn được lưu trữ
    if 'list_gian' not in st.session_state:
        st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]
    
    st.subheader("⚙️ Cài đặt hệ thống")
    new_rig = st.text_input("Thêm tên Giàn mới:")
    if st.button("Thêm Giàn"):
        if new_rig and new_rig not in st.session_state.list_gian:
            st.session_state.list_gian.append(new_rig)

# --- KHỞI TẠO DỮ LIỆU ---
NAMES = [
    "Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang",
    "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong",
    "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia",
    "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin",
    "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang",
    "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu",
    "Do Duc Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong",
    "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh",
    "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy",
    "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh",
    "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac",
    "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh",
    "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"
]

if 'db' not in st.session_state:
    df = pd.DataFrame({'Họ và Tên': NAMES})
    df['Chức danh'] = 'Kỹ sư/Công nhân'
    df['Công ty'] = 'PV Drilling'
    # Tạo cột ngày cho tháng 2/2026 (làm mẫu)
    for d in range(1, 29):
        df[f"{d}/02/2026"] = "Nghỉ ca"
    st.session_state.db = df

# --- GIAO DIỆN CHÍNH ---
st.header("📋 BẢNG CHẤM CÔNG & ĐIỀU ĐỘNG NHÂN SỰ 2026")

# Khu vực điều động nhanh
with st.expander("🚀 Cập nhật nhanh lịch trình (Nhiều người cùng lúc)"):
    col1, col2, col3 = st.columns(3)
    with col1:
        staff_select = st.multiselect("Chọn nhân viên:", NAMES)
    with col2:
        status_select = st.selectbox("Trạng thái/Giàn:", st.session_state.list_gian + ["Làm bờ", "Nghỉ phép", "Nghỉ ca"])
    with col3:
        day_range = st.slider("Từ ngày đến ngày (Tháng 2):", 1, 28, (1, 14))
    
    if st.button("CẬP NHẬT TRẠNG THÁI"):
        for d in range(day_range[0], day_range[1] + 1):
            col_name = f"{d}/02/2026"
            st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(staff_select), col_name] = status_select
        st.success("Đã cập nhật!")

# Bảng dữ liệu chính
st.subheader("Dữ liệu chi tiết")
edited_df = st.data_editor(st.session_state.db, height=500, use_container_width=True)
st.session_state.db = edited_df

# Xuất file
st.divider()
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.download_button("📥 XUẤT FILE EXCEL GỬI BÁO CÁO", data=to_excel(edited_df), file_name="PVD_Attendance_2026.xlsx")
