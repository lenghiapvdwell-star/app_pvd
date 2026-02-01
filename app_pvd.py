import streamlit as st
import pandas as pd
from io import BytesIO
import random
from datetime import datetime

# 1. Cấu hình trang
st.set_page_config(page_title="PVD Management 2026", layout="wide", initial_sidebar_state="collapsed")

# 2. KHỞI TẠO DỮ LIỆU BAN ĐẦU
if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

if 'rig_colors' not in st.session_state:
    st.session_state.rig_colors = {
        "PVD I": "#00558F", "PVD II": "#1E8449", 
        "PVD III": "#8E44AD", "PVD VI": "#D35400", "PVD 11": "#2E4053"
    }

# Hàm lấy thứ trong tuần bằng tiếng Việt
def get_vn_weekday(day):
    # Tháng 2/2026 bắt đầu ngày 01 là Chủ Nhật (CN)
    d = datetime(2026, 2, day)
    weekday = d.weekday()
    days = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d} {days[weekday]}"

NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Duc Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manu Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

if 'db' not in st.session_state:
    df = pd.DataFrame({'Họ và Tên': NAMES})
    df['Chức danh'] = 'Kỹ sư'
    df['Công ty'] = 'PVD'
    # Tạo 28 ngày cho tháng 2/2026
    for d in range(1, 29):
        df[get_vn_weekday(d)] = "CA"
    st.session_state.db = df

# 3. CSS LOGO VÀ GIAO DIỆN
st.markdown(
    """
    <style>
    [data-testid="collapsedControl"] { display: none; }
    .pvd-logo { position: fixed; top: 15px; left: 15px; z-index: 99999; width: 90px; background: white; padding: 5px; border-radius: 5px; }
    .main .block-container { padding-left: 120px; padding-right: 20px; }
    .main-header { color: #00558F; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    </style>
    <img src="https://www.pvdrilling.com.vn/images/logo.png" class="pvd-logo">
    """,
    unsafe_allow_html=True
)

st.markdown("<div class='main-header'>HỆ THỐNG ĐIỀU PHỐI NHÂN SỰ PVD 2026</div>", unsafe_allow_html=True)

# 4. TABS CHỨC NĂNG
tab_rig, tab_info, tab_manage = st.tabs(["🚀 Chấm công & Đi biển", "📝 Nhập Chức danh / Công ty", "🏗️ Quản lý Giàn"])

# TAB 1: CHẤM CÔNG
with tab_rig:
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        sel_staff = st.multiselect("Nhân viên:", NAMES, key="staff_rig")
    with c2:
        status_opt = st.selectbox("Trạng thái:", ["Đi Biển", "Nghỉ CA (CA)", "Làm Việc (WS)", "Nghỉ Phép (P)", "Nghỉ Ốm (S)"])
        final_val = st.selectbox("Chọn Giàn:", st.session_state.list_gian) if status_opt == "Đi Biển" else {"Nghỉ CA (CA)": "CA", "Làm Việc (WS)": "WS", "Nghỉ Phép (P)": "P", "Nghỉ Ốm (S)": "S"}[status_opt]
    with c3:
        d_range = st.slider("Từ ngày đến ngày (Tháng 2):", 1, 28, (1, 14))
    
    if st.button("🔥 CẬP NHẬT CHẤM CÔNG", type="primary"):
        for d in range(d_range[0], d_range[1] + 1):
            col_name = get_vn_weekday(d)
            st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col_name] = final_val
        st.success("Đã cập nhật!")

# TAB 2: NHẬP CHỨC DANH & CÔNG TY
with tab_info:
    st.info("Chọn nhân viên và nhập thông tin để cập nhật hồ sơ hàng loạt.")
    c_staff, c_role, c_corp = st.columns([2, 1, 1])
    with c_staff:
        info_staff = st.multiselect("Chọn nhân viên:", NAMES, key="staff_info")
    with c_role:
        new_role = st.text_input("Chức danh mới:", placeholder="VD: Kỹ sư cơ khí")
    with c_corp:
        new_corp = st.text_input("Công ty mới:", placeholder="VD: PVD Offshore")
    
    if st.button("💾 LƯU HỒ SƠ"):
        if new_role: st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(info_staff), 'Chức danh'] = new_role
        if new_corp: st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(info_staff), 'Công ty'] = new_corp
        st.success("Hồ sơ đã được cập nhật!")

# TAB 3: QUẢN LÝ GIÀN
with tab_manage:
    ca, cb = st.columns(2)
    with ca:
        new_rig = st.text_input("Tên Giàn mới:")
        if st.button("Thêm Giàn"):
            if new_rig and new_rig not in st.session_state.list_gian:
                st.session_state.list_gian.append(new_rig)
                st.session_state.rig_colors[new_rig] = "#%06x" % random.randint(0, 0xFFFFFF)
                st.rerun()
    with cb:
        rig_del = st.selectbox("Xóa Giàn:", st.session_state.list_gian)
        if st.button("Xóa"):
            st.session_state.list_gian.remove(rig_del)
            st.rerun()

# 5. HIỂN THỊ BẢNG
st.subheader("📅 Bảng chi tiết Tháng 02/2026")

def style_cells(val):
    if val in st.session_state.rig_colors:
        color = st.session_state.rig_colors[val]
        return f'color: {color}; font-weight: bold; background-color: #f0f8ff;'
    styles = {"P": 'background-color: #FADBD8; color: #7B241C;', "S": 'background-color: #E8DAEF; color: #512E5F;', "WS": 'background-color: #FCF3CF; color: #7D6608;'}
    return styles.get(val, 'color: #BDC3C7;')

# Sắp xếp cột Chức danh và Công ty lên đầu
cols = list(st.session_state.db.columns)
df_display = st.session_state.db[[cols[0], 'Chức danh', 'Công ty'] + cols[3:]]

st.dataframe(df_display.style.applymap(style_cells, subset=df_display.columns[3:]), use_container_width=True, height=500)

# XUẤT EXCEL
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.download_button("📥 XUẤT BÁO CÁO EXCEL", data=to_excel(st.session_state.db), file_name="PVD_2026.xlsx")
