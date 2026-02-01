import streamlit as st
import pandas as pd
from io import BytesIO
import random
from datetime import datetime, date

# 1. Cấu hình trang
st.set_page_config(page_title="PVD Management 2026", layout="wide", initial_sidebar_state="collapsed")

# 2. KHỞI TẠO BỘ NHỚ
if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

if 'rig_colors' not in st.session_state:
    # Màu sắc rực rỡ để nổi bật trên nền xanh tối
    st.session_state.rig_colors = {
        "PVD I": "#00D4FF", "PVD II": "#39FF14", "PVD III": "#FFD700", "PVD VI": "#FF8C00", "PVD 11": "#FFFFFF"
    }

def get_col_name(day):
    d = datetime(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    month_en = d.strftime('%b')
    return f"{day:02d}/{month_en}\n{days_vn[d.weekday()]}"

NAMES = ["Bùi Anh Phương", "Lê Thái Việt", "Lê Tùng Phong", "Nguyễn Tiến Dũng", "Nguyễn Văn Quang", "Phạm Hồng Minh", "Nguyễn Gia Khánh", "Nguyễn Hữu Lộc", "Nguyễn Tấn Đạt", "Chu Văn Trường", "Hồ Sỹ Đức", "Hoàng Thái Sơn", "Phạm Thái Bảo", "Cao Trung Nam", "Lê Trọng Nghĩa", "Nguyễn Văn Mạnh", "Nguyễn Văn Sơn", "Dương Mạnh Quyết", "Trần Quốc Huy", "Rusliy Saifuddin", "Đào Tiến Thành", "Đoàn Minh Quân", "Rawing Empanit", "Bùi Sỹ Xuân", "Cao Văn Thăng", "Cao Xuân Vinh", "Đàm Quang Trung", "Đào Văn Tám", "Đinh Duy Long", "Đinh Ngọc Hiếu", "Đỗ Đức Ngọc", "Đỗ Văn Tường", "Đồng Văn Trung", "Hà Viết Hùng", "Hồ Trọng Đông", "Hoàng Tùng", "Lê Hoài Nam", "Lê Hoài Phước", "Lê Minh Hoàng", "Lê Quang Minh", "Lê Quốc Duy", "Mai Nhân Dương", "Ngô Quỳnh Hải", "Ngô Xuân Điền", "Nguyễn Hoàng Quy", "Nguyễn Hữu Toàn", "Nguyễn Mạnh Cường", "Nguyễn Quốc Huy", "Nguyễn Tuấn Anh", "Nguyễn Tuấn Minh", "Nguyễn Văn Bảo Ngọc", "Nguyễn Văn Duẩn", "Nguyễn Văn Hưng", "Nguyễn Văn Võ", "Phan Tây Bắc", "Trần Văn Hoàn", "Trần Văn Hùng", "Trần Xuân Nhật", "Võ Hồng Thịnh", "Vũ Tuấn Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Trần Tuấn Dũng"]

if 'db' not in st.session_state:
    df = pd.DataFrame({'Họ và Tên': NAMES})
    df['Chức danh'] = 'Kỹ sư'
    df['Công ty'] = 'PVD'
    for d in range(1, 29):
        df[get_col_name(d)] = "CA"
    st.session_state.db = df

# 3. CSS: NỀN XANH BLUE ĐẬM (DỊU MẮT NHƯNG NỔI BẬT)
st.markdown(
    """
    <style>
    /* Nền Xanh Blue đậm chất dầu khí */
    .stApp {
        background-color: #0A192F !important;
        color: #E6F1FF !important;
    }
    
    [data-testid="collapsedControl"] { display: none; }
    
    /* Logo to 225px ghim bên trái */
    .pvd-logo-fixed {
        position: fixed;
        top: 25px;
        left: 20px;
        z-index: 10000;
        width: 225px;
    }
    
    /* Đẩy nội dung chính */
    .main .block-container {
        padding-left: 290px; 
        padding-right: 30px;
    }
    
    .main-header {
        color: #64FFDA; /* Màu xanh ngọc nổi bật */
        font-size: 32px;
        font-weight: 800;
        border-bottom: 2px solid #64FFDA;
        padding-bottom: 10px;
    }

    /* Các Tab */
    .stTabs [data-baseweb="tab"] {
        color: #8892B0 !important;
    }
    .stTabs [aria-selected="true"] {
        color: #64FFDA !important;
        border-bottom-color: #64FFDA !important;
    }

    /* Bảng dữ liệu */
    thead tr th {
        background-color: #112240 !important;
        color: #CCD6F6 !important;
        white-space: pre-wrap !important;
        border: 1px solid #233554 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Hiển thị Logo
try:
    st.image("logo_pvd.png", width=225)
    st.markdown('<div class="pvd-logo-fixed"></div>', unsafe_allow_html=True)
except:
    st.sidebar.error("Lỗi: Không tìm thấy file logo_pvd.png")

st.markdown("<div class='main-header'>PV DRILLING PERSONNEL MANAGEMENT 2026</div>", unsafe_allow_html=True)

# 4. TABS CHỨC NĂNG
tab_rig, tab_info, tab_manage = st.tabs(["🚀 CHẤM CÔNG", "📝 HỒ SƠ", "🏗️ GIÀN"])

with tab_rig:
    c1, c2, c3 = st.columns([2, 1.5, 1.5])
    with c1:
        sel_staff = st.multiselect("Nhân viên:", NAMES)
    with c2:
        status_opt = st.selectbox("Trạng thái:", ["Đi Biển", "Nghỉ CA (CA)", "Làm Việc (WS)", "Nghỉ Phép (P)", "Nghỉ Ốm (S)"])
        final_val = st.selectbox("Giàn:", st.session_state.list_gian) if status_opt == "Đi Biển" else {"Nghỉ CA (CA)": "CA", "Làm Việc (WS)": "WS", "Nghỉ Phép (P)": "P", "Nghỉ Ốm (S)": "S"}[status_opt]
    with c3:
        sel_dates = st.date_input("Chọn ngày:", value=(date(2026, 2, 1), date(2026, 2, 7)), min_value=date(2026, 2, 1), max_value=date(2026, 2, 28))

    if st.button("🔥 CẬP NHẬT DỮ LIỆU", type="primary", use_container_width=True):
        if isinstance(sel_dates, tuple) and len(sel_dates) == 2:
            start_d, end_d = sel_dates[0].day, sel_dates[1].day
            for d in range(start_d, end_d + 1):
                col_name = get_col_name(d)
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col_name] = final_val
            st.rerun()

with tab_info:
    c_staff, c_role, c_corp = st.columns([2, 1, 1]) # Đã cố định tên biến c_corp ở đây
    with c_staff: i_staff = st.multiselect("Chọn nhân sự:", NAMES, key="info_staff_key")
    with c_role: n_role = st.text_input("Chức danh:")
    with c_corp: n_corp = st.text_input("Đơn vị:") # Đã khớp biến c_corp
    if st.button("💾 LƯU HỒ SƠ"):
        if n_role: st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(i_staff), 'Chức danh'] = n_role
        if n_corp: st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(i_staff), 'Công ty'] = n_corp
        st.success("Hồ sơ đã được lưu!")

with tab_manage:
    ca, cb = st.columns(2)
    with ca:
        new_rig = st.text_input("Thêm Giàn mới:")
        if st.button("THÊM"):
            st.session_state.list_gian.append(new_rig)
            st.session_state.rig_colors[new_rig] = "#%06x" % random.randint(0, 0xFFFFFF)
            st.rerun()
    with cb:
        rig_del = st.selectbox("Xóa Giàn:", st.session_state.list_gian)
        if st.button("XÓA"):
            st.session_state.list_gian.remove(rig_del)
            st.rerun()

# 5. HIỂN THỊ BẢNG (STYLE BLUE)
st.subheader("BẢNG TỔNG HỢP")

def style_cells(val):
    if val in st.session_state.list_gian:
        color = st.session_state.rig_colors.get(val, "#64FFDA")
        return f'color: {color}; font-weight: bold; background-color: #112240; border: 0.5px solid #233554;'
    
    styles = {
        "P": 'background-color: #F44336; color: white; font-weight: bold;',
        "S": 'background-color: #9C27B0; color: white; font-weight: bold;',
        "WS": 'background-color: #FFEB3B; color: #0A192F; font-weight: bold;'
    }
    return styles.get(val, 'color: #495670; background-color: #0A192F;')

cols = list(st.session_state.db.columns)
df_display = st.session_state.db[[cols[0], 'Chức danh', 'Công ty'] + cols[3:]]

st.dataframe(df_display.style.applymap(style_cells, subset=df_display.columns[3:]), use_container_width=True, height=650)

# 6. XUẤT EXCEL
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.download_button("📥 TẢI EXCEL", data=to_excel(st.session_state.db), file_name="PVD_Blue_Report.xlsx", use_container_width=True)
