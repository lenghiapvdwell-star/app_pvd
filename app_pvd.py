import streamlit as st
import pandas as pd
from io import BytesIO
import random

# 1. Cấu hình trang
st.set_page_config(page_title="PVD Management 2026", layout="wide", initial_sidebar_state="collapsed")

# 2. Tự động tạo màu cho các Giàn
if 'rig_colors' not in st.session_state:
    # Danh sách màu chữ đậm, dễ nhìn
    colors = ['#00558F', '#1E8449', '#8E44AD', '#D35400', '#2E4053', '#C0392B', '#16A085']
    st.session_state.rig_colors = {
        "PVD I": "#00558F",
        "PVD II": "#1E8449",
        "PVD III": "#8E44AD",
        "PVD VI": "#D35400",
        "PVD 11": "#2E4053"
    }

# 3. CSS: Ghim Logo bên trái ngoài cùng và định dạng màu sắc
st.markdown(
    f"""
    <style>
    [data-testid="collapsedControl"] {{ display: none; }}
    
    .pvd-logo {{
        position: fixed;
        top: 20px;
        left: 15px;
        z-index: 10000;
        width: 100px;
    }}
    
    .main .block-container {{
        padding-left: 130px;
        padding-right: 30px;
    }}
    
    .main-header {{
        color: #00558F;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    </style>
    <img src="https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/logo_pvd.png" class="pvd-logo">
    """,
    unsafe_allow_html=True
)

# 4. DANH SÁCH NHÂN SỰ (64 người)
NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Duc Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

if 'db' not in st.session_state:
    df = pd.DataFrame({'Họ và Tên': NAMES})
    df['Chức danh'] = 'Kỹ sư/Công nhân'
    df['Công ty'] = 'PV Drilling'
    for d in range(1, 32):
        df[f"{d}/01/2026"] = "CA"
    st.session_state.db = df

if 'list_gian' not in st.session_state:
    st.session_state.list_gian = list(st.session_state.rig_colors.keys())

# 5. GIAO DIỆN CHÍNH
st.markdown("<h1 class='main-header'>HỆ THỐNG ĐIỀU PHỐI NHÂN SỰ PVD 2026</h1>", unsafe_allow_html=True)

# QUẢN LÝ TÊN GIÀN
with st.expander("🏗️ Quản lý Danh sách Tên Giàn"):
    c_a, c_b = st.columns([3, 2])
    with c_a:
        new_rig = st.text_input("Nhập tên Giàn mới:")
        if st.button("Thêm Giàn"):
            if new_rig and new_rig not in st.session_state.list_gian:
                st.session_state.list_gian.append(new_rig)
                # Gán màu ngẫu nhiên cho giàn mới
                random_color = "#%06x" % random.randint(0, 0xFFFFFF)
                st.session_state.rig_colors[new_rig] = random_color
                st.rerun()
    with c_b:
        rig_del = st.selectbox("Xóa giàn nếu viết sai:", st.session_state.list_gian)
        if st.button("Xóa Giàn"):
            st.session_state.list_gian.remove(rig_del)
            st.rerun()

# CẬP NHẬT TRẠNG THÁI
with st.container(border=True):
    st.subheader("🚀 Cập nhật nhanh")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        sel_staff = st.multiselect("Nhân viên:", NAMES)
    with col2:
        option = st.selectbox("Trạng thái:", ["Đi Biển", "Nghỉ CA (CA)", "Làm Việc (WS)", "Nghỉ Phép (P)", "Nghỉ Ốm (S)"])
        val = ""
        if option == "Đi Biển":
            val = st.selectbox("Chọn Giàn:", st.session_state.list_gian)
        else:
            mapping = {"Nghỉ CA (CA)": "CA", "Làm Việc (WS)": "WS", "Nghỉ Phép (P)": "P", "Nghỉ Ốm (S)": "S"}
            val = mapping[option]
    with col3:
        days = st.slider("Ngày:", 1, 31, (1, 15))

    if st.button("XÁC NHẬN", type="primary"):
        for d in range(days[0], days[1] + 1):
            st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), f"{d}/01/2026"] = val
        st.success("Cập nhật thành công!")

# 6. HIỂN THỊ BẢNG VỚI MÀU CHỮ RIÊNG BIỆT CHO GIÀN
st.subheader("📅 Chi tiết chấm công 2026")

def apply_custom_style(val):
    # Nếu là Giàn -> Lấy màu từ bộ nhớ, in đậm
    if val in st.session_state.rig_colors:
        color = st.session_state.rig_colors[val]
        return f'color: {color}; font-weight: bold; background-color: #f0f8ff;'
    # Các ký hiệu khác
    styles = {
        "P": 'background-color: #FADBD8; color: #7B241C;', # Đỏ
        "S": 'background-color: #E8DAEF; color: #512E5F;', # Tím
        "WS": 'background-color: #FCF3CF; color: #7D6608;', # Vàng
        "CA": 'color: #BDC3C7;' # Xám nhạt cho Nghỉ ca
    }
    return styles.get(val, '')

st.dataframe(st.session_state.db.style.applymap(apply_custom_style, subset=st.session_state.db.columns[3:]), use_container_width=True, height=500)

# XUẤT EXCEL
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.download_button("📥 TẢI EXCEL", data=to_excel(st.session_state.db), file_name="PVD_Management_2026.xlsx")
