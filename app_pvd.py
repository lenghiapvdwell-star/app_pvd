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
    # Sử dụng các màu rực rỡ để nổi bật trên nền tối
    st.session_state.rig_colors = {
        "PVD I": "#3498DB", "PVD II": "#2ECC71", "PVD III": "#F1C40F", "PVD VI": "#E67E22", "PVD 11": "#ECF0F1"
    }

def get_col_name(day):
    d = datetime(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    month_en = d.strftime('%b')
    return f"{day:02d}/{month_en}\n{days_vn[d.weekday()]}"

NAMES = ["Bùi Anh Phương", "Lê Thái Việt", "Lê Tùng Phong", "Nguyễn Tiến Dũng", "Nguyễn Văn Quang", "Phạm Hồng Minh", "Nguyễn Gia Khánh", "Nguyễn Hữu Lộc", "Nguyễn Tấn Đạt", "Chu Văn Trường", "Hồ Sỹ Đức", "Hoàng Thái Sơn", "Phạm Thái Bảo", "Cao Trung Nam", "Lê Trọng Nghĩa", "Nguyễn Văn Mạnh", "Nguyễn Văn Sơn", "Dương Mạnh Quyết", "Trần Quốc Huy", "Rusliy Saifuddin", "Đào Tiến Thành", "Đoàn Minh Quân", "Rawing Empanit", "Bùi Sỹ Xuân", "Cao Văn Thắng", "Cao Xuân Vinh", "Đàm Quang Trung", "Đào Văn Tám", "Đinh Duy Long", "Đinh Ngọc Hiếu", "Đỗ Đức Ngọc", "Đỗ Văn Tường", "Đồng Văn Trung", "Hà Viết Hùng", "Hồ Trọng Đông", "Hoàng Tùng", "Lê Hoài Nam", "Lê Hoài Phước", "Lê Minh Hoàng", "Lê Quang Minh", "Lê Quốc Duy", "Mai Nhân Dương", "Ngô Quỳnh Hải", "Ngô Xuân Điền", "Nguyễn Hoàng Quy", "Nguyễn Hữu Toàn", "Nguyễn Mạnh Cường", "Nguyễn Quốc Huy", "Nguyễn Tuấn Anh", "Nguyễn Tuấn Minh", "Nguyễn Văn Bảo Ngọc", "Nguyễn Văn Duẩn", "Nguyễn Văn Hưng", "Nguyễn Văn Võ", "Phan Tây Bắc", "Trần Văn Hoàn", "Trần Văn Hùng", "Trần Xuân Nhật", "Võ Hồng Thịnh", "Vũ Tuấn Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Trần Tuấn Dũng"]

if 'db' not in st.session_state:
    df = pd.DataFrame({'Họ và Tên': NAMES})
    df['Chức danh'] = 'Kỹ sư'
    df['Công ty'] = 'PVD'
    for d in range(1, 29):
        df[get_col_name(d)] = "CA"
    st.session_state.db = df

# 3. CSS: NỀN XANH BLUE VÀ PHÔNG CHỮ TRẮNG NỔI BẬT
st.markdown(
    """
    <style>
    /* Nền Xanh Blue đậm */
    .stApp {
        background-color: #1B2631 !important;
        color: #ECF0F1 !important;
    }
    
    [data-testid="collapsedControl"] { display: none; }
    
    /* Logo 225px ghim bên trái */
    .pvd-logo-fixed {
        position: fixed;
        top: 30px;
        left: 20px;
        z-index: 10000;
        width: 225px;
        background: rgba(255,255,255,0.1);
        padding: 10px;
        border-radius: 10px;
    }
    
    /* Nội dung chính dịch sang phải */
    .main .block-container {
        padding-left: 290px; 
        padding-right: 30px;
    }
    
    /* Tiêu đề trắng sáng */
    .main-header {
        color: #3498DB;
        font-size: 32px;
        font-weight: 800;
        margin-bottom: 25px;
        text-transform: uppercase;
        letter-spacing: 2px;
        border-bottom: 2px solid #3498DB;
    }

    /* Các Tab màu tối đồng nhất */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        color: #BDC3C7 !important;
    }
    .stTabs [aria-selected="true"] {
        color: #3498DB !important;
        border-bottom-color: #3498DB !important;
    }

    /* Bảng dữ liệu: Nền sáng để chữ màu nổi bật */
    thead tr th {
        background-color: #2C3E50 !important;
        color: #ECF0F1 !important;
        font-size: 13px !important;
        white-space: pre-wrap !important;
        border: 1px solid #34495E !important;
    }
    
    /* Input text màu trắng trên nền tối */
    input {
        color: white !important;
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
    st.sidebar.error("Thiếu file logo_pvd.png")

st.markdown("<div class='main-header'>PV DRILLING PERSONNEL SYSTEM 2026</div>", unsafe_allow_html=True)

# 4. TABS CHỨC NĂNG
tab_rig, tab_info, tab_manage = st.tabs(["📊 QUẢN LÝ ĐIỀU ĐỘNG", "📁 HỒ SƠ NHÂN VIÊN", "⚙️ CÀI ĐẶT HỆ THỐNG"])

with tab_rig:
    with st.container():
        c1, c2, c3 = st.columns([2, 1.5, 1.5])
        with c1:
            sel_staff = st.multiselect("CHỌN NHÂN VIÊN", NAMES)
        with c2:
            status_opt = st.selectbox("TRẠNG THÁI", ["Đi Biển", "Nghỉ CA (CA)", "Làm Việc (WS)", "Nghỉ Phép (P)", "Nghỉ Ốm (S)"])
            if status_opt == "Đi Biển":
                final_val = st.selectbox("CHỌN GIÀN", st.session_state.list_gian)
            else:
                final_val = {"Nghỉ CA (CA)": "CA", "Làm Việc (WS)": "WS", "Nghỉ Phép (P)": "P", "Nghỉ Ốm (S)": "S"}[status_opt]
        with c3:
            sel_dates = st.date_input("KHOẢNG NGÀY ĐIỀU ĐỘNG", 
                                      value=(date(2026, 2, 1), date(2026, 2, 7)),
                                      min_value=date(2026, 2, 1), 
                                      max_value=date(2026, 2, 28))

        if st.button("🚀 CẬP NHẬT HỆ THỐNG", type="primary", use_container_width=True):
            if isinstance(sel_dates, tuple) and len(sel_dates) == 2:
                start_d, end_d = sel_dates[0].day, sel_dates[1].day
                for d in range(start_d, end_d + 1):
                    col_name = get_col_name(d)
                    st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col_name] = final_val
                st.success("Dữ liệu đã được đồng bộ!")
                st.rerun()

with tab_info:
    # (Phần này giữ nguyên logic như cũ)
    c_s, c_r, c_c = st.columns([2, 1, 1])
    with c_s: i_staff = st.multiselect("Nhân sự:", NAMES, key="i_s")
    with c_r: n_role = st.text_input("Chức danh:")
    with c_corp: n_corp = st.text_input("Đơn vị:")
    if st.button("💾 CẬP NHẬT HỒ SƠ"):
        if n_role: st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(i_staff), 'Chức danh'] = n_role
        if n_corp: st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(i_staff), 'Công ty'] = n_corp
        st.rerun()

with tab_manage:
    ca, cb = st.columns(2)
    with ca:
        new_rig = st.text_input("Thêm Giàn:")
        if st.button("THÊM MỚI"):
            st.session_state.list_gian.append(new_rig)
            st.session_state.rig_colors[new_rig] = "#%06x" % random.randint(0, 0xFFFFFF)
            st.rerun()
    with cb:
        rig_del = st.selectbox("Xóa Giàn:", st.session_state.list_gian)
        if st.button("XÓA BỎ"):
            st.session_state.list_gian.remove(rig_del)
            st.rerun()

# 5. HIỂN THỊ BẢNG VỚI STYLE BLUE
st.subheader("BẢNG TỔNG HỢP CHI TIẾT 2026")

def style_cells(val):
    if val in st.session_state.list_gian:
        color = st.session_state.rig_colors.get(val, "#3498DB")
        return f'color: {color}; font-weight: 900; background-color: #FBFCFC; border: 1px solid #D5DBDB;'
    
    styles = {
        "P": 'background-color: #E74C3C; color: white; font-weight: bold;', # Đỏ cho phép
        "S": 'background-color: #9B59B6; color: white; font-weight: bold;', # Tím cho ốm
        "WS": 'background-color: #F1C40F; color: #1B2631; font-weight: bold;' # Vàng cho làm bờ
    }
    return styles.get(val, 'color: #7F8C8D; background-color: #FFFFFF;')

cols = list(st.session_state.db.columns)
df_display = st.session_state.db[[cols[0], 'Chức danh', 'Công ty'] + cols[3:]]

st.dataframe(df_display.style.applymap(style_cells, subset=df_display.columns[3:]), use_container_width=True, height=650)

# 6. XUẤT EXCEL
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.download_button("📥 TẢI BÁO CÁO EXCEL", data=to_excel(st.session_state.db), file_name="PVD_Blue_Report.xlsx", use_container_width=True)
