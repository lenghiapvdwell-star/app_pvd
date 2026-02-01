import streamlit as st
import pandas as pd
from io import BytesIO

# 1. Cấu hình trang (Phải là dòng đầu tiên)
st.set_page_config(page_title="PV Drilling Management 2026", layout="wide", initial_sidebar_state="collapsed")

# 2. CSS để ghim LOGO bên trái ngoài cùng và ẩn hoàn toàn Sidebar
st.markdown(
    """
    <style>
    /* Ẩn nút đóng mở Sidebar */
    [data-testid="collapsedControl"] { display: none; }
    
    /* Ghim logo góc trên bên trái ngoài cùng */
    .pvd-logo {
        position: fixed;
        top: 15px;
        left: 15px;
        z-index: 10000;
        width: 120px;
    }
    
    /* Đẩy toàn bộ nội dung chính sang phải để không bị logo đè */
    .main .block-container {
        padding-left: 150px;
        padding-right: 20px;
    }
    
    /* Định dạng tiêu đề */
    .main-header {
        color: #00558F;
        font-family: Arial, sans-serif;
        font-weight: bold;
    }
    </style>
    <img src="https://www.pvdrilling.com.vn/images/logo.png" class="pvd-logo">
    """,
    unsafe_allow_html=True
)

# 3. DANH SÁCH NHÂN SỰ
NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Duc Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

# Khởi tạo dữ liệu
if 'db' not in st.session_state:
    df = pd.DataFrame({'Họ và Tên': NAMES})
    df['Chức danh'] = 'Kỹ sư/Công nhân'
    df['Công ty'] = 'PV Drilling'
    for d in range(1, 32):
        df[f"{d}/01/2026"] = "CA"
    st.session_state.db = df

if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

# 4. GIAO DIỆN CHÍNH
st.markdown("<h1 class='main-header'>HỆ THỐNG ĐIỀU PHỐI NHÂN SỰ PVD 2026</h1>", unsafe_allow_html=True)

# KHU VỰC QUẢN LÝ TÊN GIÀN (Đã đưa ra ngoài)
with st.expander("🏗️ Quản lý Danh sách Tên Giàn"):
    col_a, col_b = st.columns([3, 1])
    with col_a:
        new_rig = st.text_input("Nhập tên Giàn muốn thêm:", placeholder="Ví dụ: PVD V...")
    with col_b:
        if st.button("Thêm Giàn"):
            if new_rig and new_rig not in st.session_state.list_gian:
                st.session_state.list_gian.append(new_rig)
                st.rerun()
    
    # Chức năng xóa tên giàn nếu viết sai
    st.write("---")
    st.write("Chọn giàn muốn xóa (nếu viết sai):")
    rig_to_delete = st.selectbox("Danh sách giàn hiện tại:", st.session_state.list_gian)
    if st.button("Xóa tên giàn này"):
        if rig_to_delete in st.session_state.list_gian:
            st.session_state.list_gian.remove(rig_to_delete)
            st.warning(f"Đã xóa giàn: {rig_to_delete}")
            st.rerun()

# KHU VỰC CHẤM CÔNG 3 OPTION
with st.container(border=True):
    st.subheader("🚀 Cập nhật trạng thái nhanh")
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        selected_staff = st.multiselect("Chọn nhân viên:", NAMES)
    with c2:
        mode = st.radio("Lựa chọn:", ["Đi Biển (Tên Giàn)", "Nghỉ CA (CA)", "Làm Việc (WS)"], horizontal=True)
        if "Biển" in mode:
            status_val = st.selectbox("Chọn Giàn từ danh sách:", st.session_state.list_gian)
        elif "CA" in mode:
            status_val = "CA"
        else:
            status_val = "WS"
    with c3:
        d_range = st.slider("Từ ngày đến ngày (Tháng 1):", 1, 31, (1, 15))
    
    if st.button("XÁC NHẬN CẬP NHẬT", type="primary"):
        for d in range(d_range[0], d_range[1] + 1):
            st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(selected_staff), f"{d}/01/2026"] = status_val
        st.success(f"Đã cập nhật trạng thái {status_val} thành công!")

# 5. BẢNG HIỂN THỊ VÀ XUẤT EXCEL
st.subheader("📅 Bảng chi tiết chấm công 2026")
edited_df = st.data_editor(st.session_state.db, use_container_width=True, height=500)
st.session_state.db = edited_df

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.download_button(
    label="📥 Tải Báo Cáo Excel (.xlsx)",
    data=to_excel(edited_df),
    file_name="Bao_cao_PVD_2026.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
