import streamlit as st
import pandas as pd
from io import BytesIO

# 1. Cấu hình trang (Phải là dòng đầu tiên)
st.set_page_config(page_title="PVD Management 2026", layout="wide", initial_sidebar_state="collapsed")

# 2. CSS: Logo cố định bên trái + Tô màu chữ xanh cho tên Giàn
st.markdown(
    """
    <style>
    [data-testid="collapsedControl"] { display: none; }
    
    .pvd-logo {
        position: fixed;
        top: 15px;
        left: 15px;
        z-index: 10000;
        width: 100px;
        background: white;
        padding: 5px;
        border-radius: 5px;
    }
    
    .main .block-container {
        padding-left: 130px;
        padding-right: 30px;
    }
    
    .main-header {
        color: #00558F;
        font-family: Arial, sans-serif;
    }
    </style>
    <img src="https://www.pvdrilling.com.vn/images/logo.png" class="pvd-logo">
    """,
    unsafe_allow_html=True
)

# 3. DANH SÁCH NHÂN SỰ
NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Duc Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

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

# QUẢN LÝ TÊN GIÀN
with st.expander("🏗️ Quản lý Danh sách Tên Giàn (Thêm/Xóa)"):
    c_a, c_b, c_c = st.columns([2, 2, 1])
    with c_a:
        new_rig = st.text_input("Nhập tên Giàn mới:")
        if st.button("Thêm Giàn"):
            if new_rig and new_rig not in st.session_state.list_gian:
                st.session_state.list_gian.append(new_rig)
                st.rerun()
    with c_b:
        rig_to_del = st.selectbox("Chọn giàn để xóa:", st.session_state.list_gian)
        if st.button("Xóa Giàn này"):
            st.session_state.list_gian.remove(rig_to_del)
            st.rerun()

# CẬP NHẬT TRẠNG THÁI
with st.container(border=True):
    st.subheader("🚀 Chấm công & Điều động")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        sel_staff = st.multiselect("Nhân viên:", NAMES)
    with col2:
        # Bổ sung Nghỉ phép (P) và Nghỉ ốm (S)
        option = st.selectbox("Trạng thái:", ["Đi Biển", "Nghỉ CA (CA)", "Làm Việc (WS)", "Nghỉ Phép (P)", "Nghỉ Ốm (S)"])
        val = ""
        if option == "Đi Biển":
            val = st.selectbox("Chọn Giàn:", st.session_state.list_gian)
        elif option == "Nghỉ CA (CA)": val = "CA"
        elif option == "Làm Việc (WS)": val = "WS"
        elif option == "Nghỉ Phép (P)": val = "P"
        else: val = "S"
    with col3:
        days = st.slider("Ngày:", 1, 31, (1, 15))

    if st.button("CẬP NHẬT", type="primary"):
        for d in range(days[0], days[1] + 1):
            st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), f"{d}/01/2026"] = val
        st.success(f"Đã cập nhật xong!")

# 5. HIỂN THỊ BẢNG VỚI TÔ MÀU XANH CHO TÊN GIÀN
st.subheader("📅 Bảng chi tiết 2026")

def apply_color(val):
    # Nếu giá trị nằm trong danh sách Giàn -> Chữ xanh dương đậm, nền xanh nhạt
    if val in st.session_state.list_gian:
        return 'color: #00558F; background-color: #D6EAF8; font-weight: bold'
    # Các trạng thái khác
    elif val == "P": return 'background-color: #FADBD8' # Đỏ nhạt cho phép
    elif val == "S": return 'background-color: #E8DAEF' # Tím nhạt cho ốm
    elif val == "WS": return 'background-color: #FCF3CF' # Vàng cho làm bờ
    return ''

st.dataframe(st.session_state.db.style.applymap(apply_color, subset=st.session_state.db.columns[3:]), use_container_width=True, height=500)

# XUẤT EXCEL
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.download_button("📥 TẢI EXCEL", data=to_excel(st.session_state.db), file_name="PVD_2026.xlsx")
