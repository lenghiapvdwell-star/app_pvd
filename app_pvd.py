import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="PV Drilling Management 2026", layout="wide")

# --- LOGO & SIDEBAR ---
with st.sidebar:
    try:
        st.image("logo_pvd.png", width=200)
    except:
        st.markdown("### 🔵 PV DRILLING")
    
    st.title("Hệ thống Điều phối 2026")
    
    # Quản lý danh sách Giàn
    if 'list_gian' not in st.session_state:
        st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]
    
    st.subheader("🏗️ Quản lý Tên Giàn")
    new_rig = st.text_input("Nhập tên Giàn mới:")
    if st.button("Thêm vào danh sách"):
        if new_rig and new_rig not in st.session_state.list_gian:
            st.session_state.list_gian.append(new_rig)
            st.success(f"Đã thêm {new_rig}")
            st.rerun()

# --- KHỞI TẠO DỮ LIỆU ---
NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Duc Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

if 'db' not in st.session_state:
    df = pd.DataFrame({'Họ và Tên': NAMES})
    df['Chức danh'] = 'Chưa nhập'
    df['Công ty'] = 'PV Drilling'
    for d in range(1, 29):
        df[f"{d}/02/2026"] = "Nghỉ ca"
    st.session_state.db = df

# --- GIAO DIỆN CẬP NHẬT ---
st.header("🚢 BẢNG ĐIỀU ĐỘNG NHÂN SỰ PV DRILLING")

tab1, tab2 = st.tabs(["🚀 Điều động nhanh", "📝 Chỉnh sửa Chức danh & Công ty"])

with tab1:
    with st.container(border=True):
        c1, c2, c3 = st.columns([2,1,1])
        with c1:
            staff_sel = st.multiselect("Chọn nhân viên:", NAMES, key="st_rig")
        with c2:
            status_sel = st.selectbox("Đi Giàn / Trạng thái:", st.session_state.list_gian + ["Làm bờ", "Nghỉ phép", "Nghỉ ca"])
        with c3:
            d_from, d_to = st.slider("Từ ngày đến ngày (Tháng 2):", 1, 28, (1, 7))
        
        if st.button("XÁC NHẬN ĐIỀU ĐỘNG", type="primary"):
            for d in range(d_from, d_to + 1):
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(staff_sel), f"{d}/02/2026"] = status_sel
            st.success("Đã cập nhật lịch trình!")

with tab2:
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            staff_info_sel = st.multiselect("Chọn nhân viên để cập nhật hồ sơ:", NAMES, key="st_info")
        with c2:
            new_role = st.text_input("Nhập Chức danh (ví dụ: Kỹ sư, Thợ hàn...):")
        with c3:
            new_corp = st.text_input("Nhập Tên Công ty:")
        
        if st.button("CẬP NHẬT HỒ SƠ"):
            if new_role:
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(staff_info_sel), 'Chức danh'] = new_role
            if new_corp:
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(staff_info_sel), 'Công ty'] = new_corp
            st.success("Đã cập nhật thông tin nhân sự!")

# --- HIỂN THỊ BẢNG DỮ LIỆU ---
st.subheader("📅 Chi tiết chấm công tháng 02/2026")
# Sắp xếp lại cột để Chức danh và Công ty hiện lên đầu
cols = list(st.session_state.db.columns)
new_col_order = [cols[0], 'Chức danh', 'Công ty'] + cols[3:]
st.session_state.db = st.session_state.db[new_col_order]

edited_df = st.data_editor(st.session_state.db, height=500, use_container_width=True)
st.session_state.db = edited_df

# --- XUẤT EXCEL ---
def to_excel(df):
    output = BytesIO()
    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='PVD_2026')
        return output.getvalue()
    except Exception as e:
        return None

excel_data = to_excel(edited_df)
if excel_data:
    st.download_button("📥 TẢI FILE EXCEL BÁO CÁO", data=excel_data, file_name="Bao_cao_PVD_2026.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.error("Lỗi xuất Excel: Vui lòng kiểm tra file requirements.txt trên GitHub (cần có xlsxwriter)")
