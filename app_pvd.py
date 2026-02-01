import streamlit as st
import pandas as pd
from io import BytesIO
import random

# 1. Cấu hình trang (Luôn đặt ở dòng đầu tiên)
st.set_page_config(page_title="PV Drilling 2026", layout="wide", initial_sidebar_state="collapsed")

# 2. KHỞI TẠO BỘ NHỚ (Để không bị mất tên giàn khi thêm mới)
if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

if 'rig_colors' not in st.session_state:
    # Gán màu cố định ban đầu cho các giàn mặc định
    st.session_state.rig_colors = {
        "PVD I": "#00558F", "PVD II": "#1E8449", 
        "PVD III": "#8E44AD", "PVD VI": "#D35400", "PVD 11": "#2E4053"
    }

# 3. CSS ĐƯA LOGO RA NGOÀI VÀ GHIM CỐ ĐỊNH
st.markdown(
    """
    <style>
    [data-testid="collapsedControl"] { display: none; }
    .pvd-logo {
        position: fixed;
        top: 15px;
        left: 15px;
        z-index: 99999;
        width: 100px;
        background: white;
        padding: 5px;
        border-radius: 5px;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
    }
    .main .block-container { padding-left: 130px; padding-right: 30px; }
    .main-header { color: #00558F; font-weight: bold; }
    </style>
    <img src="https://www.pvdrilling.com.vn/images/logo.png" class="pvd-logo">
    """,
    unsafe_allow_html=True
)

# 4. DANH SÁCH 64 NHÂN SỰ
NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Duc Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

if 'db' not in st.session_state:
    df = pd.DataFrame({'Họ và Tên': NAMES})
    df['Chức danh'] = 'Kỹ sư/Công nhân'
    df['Công ty'] = 'PV Drilling'
    for d in range(1, 32):
        df[f"{d}/01/2026"] = "CA"
    st.session_state.db = df

# 5. GIAO DIỆN CHÍNH
st.markdown("<h1 class='main-header'>HỆ THỐNG ĐIỀU PHỐI NHÂN SỰ PVD 2026</h1>", unsafe_allow_html=True)

# QUẢN LÝ TÊN GIÀN (Thêm/Xóa)
with st.expander("🏗️ Quản lý Danh sách Tên Giàn"):
    c_add, c_del = st.columns(2)
    with c_add:
        new_rig = st.text_input("Nhập tên Giàn mới:")
        if st.button("Lưu Giàn"):
            if new_rig and new_rig not in st.session_state.list_gian:
                st.session_state.list_gian.append(new_rig)
                st.session_state.rig_colors[new_rig] = "#%06x" % random.randint(0, 0xFFFFFF)
                st.rerun()
    with c_del:
        rig_to_del = st.selectbox("Xóa giàn viết sai:", st.session_state.list_gian)
        if st.button("Xóa ngay"):
            if rig_to_del in st.session_state.list_gian:
                st.session_state.list_gian.remove(rig_to_del)
                st.rerun()

# KHU VỰC CHẤM CÔNG NHANH
with st.container(border=True):
    st.subheader("🚀 Cập nhật trạng thái nhanh")
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        sel_staff = st.multiselect("Chọn nhân viên:", NAMES)
    with c2:
        status_opt = st.selectbox("Trạng thái:", ["Đi Biển", "Nghỉ CA (CA)", "Làm Việc (WS)", "Nghỉ Phép (P)", "Nghỉ Ốm (S)"])
        if status_opt == "Đi Biển":
            # Chỗ này quan trọng: Luôn lấy từ st.session_state.list_gian
            final_val = st.selectbox("Chọn Giàn cụ thể:", st.session_state.list_gian)
        else:
            mapping = {"Nghỉ CA (CA)": "CA", "Làm Việc (WS)": "WS", "Nghỉ Phép (P)": "P", "Nghỉ Ốm (S)": "S"}
            final_val = mapping[status_opt]
    with c3:
        d_range = st.slider("Từ ngày đến ngày (Tháng 1/2026):", 1, 31, (1, 15))

    if st.button("XÁC NHẬN CẬP NHẬT", type="primary"):
        for d in range(d_range[0], d_range[1] + 1):
            col_name = f"{d}/01/2026"
            st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col_name] = final_val
        st.success("Đã cập nhật dữ liệu!")

# 6. BẢNG HIỂN THỊ VÀ TÔ MÀU CHỮ
st.subheader("📅 Chi tiết bảng chấm công")

def style_cells(val):
    if val in st.session_state.rig_colors:
        color = st.session_state.rig_colors[val]
        return f'color: {color}; font-weight: bold; background-color: #f0f8ff;'
    elif val == "P": return 'background-color: #FADBD8; color: #7B241C;'
    elif val == "S": return 'background-color: #E8DAEF; color: #512E5F;'
    elif val == "WS": return 'background-color: #FCF3CF; color: #7D6608;'
    return 'color: #BDC3C7;' # Mặc định cho CA

st.dataframe(st.session_state.db.style.applymap(style_cells, subset=st.session_state.db.columns[3:]), use_container_width=True, height=500)

# XUẤT EXCEL
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.download_button("📥 TẢI EXCEL BÁO CÁO", data=to_excel(st.session_state.db), file_name="PVD_2026.xlsx")
