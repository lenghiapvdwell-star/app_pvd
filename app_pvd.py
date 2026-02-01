import streamlit as st
import pandas as pd
from io import BytesIO

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="PV Drilling Management 2026", layout="wide")

# --- MẸO: ĐƯA LOGO RA NGOÀI SIDEBAR (FIXED POSITION) ---
st.markdown(
    """
    <style>
    [data-testid="stSidebarNav"] {
        padding-top: 120px;
    }
    .custom-logo {
        position: fixed;
        top: 10px;
        left: 10px;
        z-index: 999999;
        width: 120px;
    }
    </style>
    <img src="https://raw.githubusercontent.com/YOUR_GITHUB_USER/YOUR_REPO/main/logo_pvd.png" class="custom-logo">
    """,
    unsafe_allow_html=True
)
# Lưu ý: Thay link src bằng link ảnh thực tế trên GitHub của bạn hoặc dùng file nội bộ

# --- KHỞI TẠO DỮ LIỆU ---
NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Duc Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

if 'db' not in st.session_state:
    df = pd.DataFrame({'Họ và Tên': NAMES})
    df['Chức danh'] = 'Chưa nhập'
    df['Công ty'] = 'PV Drilling'
    for d in range(1, 32):
        df[f"{d}/01/2026"] = "CA" # Mặc định là Nghỉ ca (CA)
    st.session_state.db = df

if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

# --- SIDEBAR: QUẢN LÝ TÊN GIÀN ---
with st.sidebar:
    st.title("Thiết lập")
    new_rig = st.text_input("Thêm tên Giàn mới:")
    if st.button("Thêm Giàn"):
        if new_rig and new_rig not in st.session_state.list_gian:
            st.session_state.list_gian.append(new_rig)
            st.rerun()

# --- GIAO DIỆN CHÍNH ---
st.title("🚢 HỆ THỐNG ĐIỀU PHỐI NHÂN SỰ 2026")

tab1, tab2 = st.tabs(["🚀 Chấm công nhanh", "📝 Hồ sơ nhân sự"])

with tab1:
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            staff_sel = st.multiselect("Chọn nhân viên:", NAMES)
        with c2:
            # 3 Option chính của bạn
            status_sel = st.selectbox("Chọn trạng thái:", ["Tên Giàn (Chọn dưới)","WS (Làm bờ)", "CA (Nghỉ ca)"])
            rig_sel = st.selectbox("Nếu đi giàn, chọn tên:", st.session_state.list_gian)
        with c3:
            d_from, d_to = st.slider("Từ ngày đến ngày:", 1, 31, (1, 15))
        
        if st.button("CẬP NHẬT CHẤM CÔNG", type="primary"):
            final_status = rig_sel if "Tên Giàn" in status_sel else status_sel.split(" ")[0]
            for d in range(d_from, d_to + 1):
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(staff_sel), f"{d}/01/2026"] = final_status
            st.success(f"Đã cập nhật trạng thái {final_status}!")

with tab2:
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            staff_info_sel = st.multiselect("Chọn nhân viên:", NAMES, key="info_sel")
        with c2:
            new_role = st.text_input("Chức danh mới:")
        with c3:
            new_corp = st.text_input("Công ty mới:")
        
        if st.button("LƯU THÔNG TIN"):
            if new_role: st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(staff_info_sel), 'Chức danh'] = new_role
            if new_corp: st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(staff_info_sel), 'Công ty'] = new_corp
            st.rerun()

# --- BẢNG HIỂN THỊ ---
st.subheader("📅 Bảng chi tiết Tháng 01/2026")

# Tự động tô màu cho dễ nhìn
def color_coding(val):
    if val == "CA": color = "#e8f8f5" # Xanh nhạt
    elif val == "WS": color = "#fef9e7" # Vàng nhạt
    elif val in st.session_state.list_gian: color = "#ebf5fb" # Xanh dương nhạt
    else: color = "white"
    return f'background-color: {color}'

st.dataframe(st.session_state.db.style.applymap(color_coding, subset=st.session_state.db.columns[3:]), height=600)

# --- XUẤT EXCEL ---
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.download_button("📥 XUẤT FILE EXCEL", data=to_excel(st.session_state.db), file_name="PVD_Report_2026.xlsx")
