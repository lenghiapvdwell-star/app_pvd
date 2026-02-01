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
    st.session_state.rig_colors = {
        "PVD I": "#1A5276", "PVD II": "#196F3D", "PVD III": "#7D3C98", "PVD VI": "#A04000", "PVD 11": "#212F3D"
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

# 3. CSS TỐI ƯU TƯƠNG PHẢN & PHÔNG CHỮ
st.markdown(
    """
    <style>
    /* Nền màu Cream dịu mắt */
    .stApp {
        background-color: #FDF5E6 !important;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    [data-testid="collapsedControl"] { display: none; }
    
    /* Logo to 225px ghim trái */
    .pvd-logo-fixed {
        position: fixed;
        top: 30px;
        left: 20px;
        z-index: 10000;
        width: 225px;
    }
    
    /* Nội dung chính */
    .main .block-container {
        padding-left: 285px; 
        padding-right: 30px;
        color: #2C3E50; /* Màu chữ chính Charcoal */
    }
    
    /* Tiêu đề thanh lịch */
    .main-header {
        color: #004A99;
        font-size: 32px;
        font-weight: 800;
        margin-bottom: 20px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.05);
    }

    /* Định dạng bảng: Chữ đậm, dễ đọc */
    thead tr th {
        white-space: pre-wrap !important;
        text-align: center !important;
        background-color: #EAECEE !important;
        color: #1B2631 !important;
        font-weight: bold !important;
        border: 1px solid #D5DBDB !important;
    }
    
    /* Tab Menu */
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        color: #566573;
    }
    .stTabs [aria-selected="true"] {
        color: #004A99 !important;
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
    st.sidebar.error("Vui lòng kiểm tra file logo_pvd.png")

st.markdown("<div class='main-header'>PVD PERSONNEL DISPATCHING SYSTEM</div>", unsafe_allow_html=True)

# 4. TABS CHỨC NĂNG
tab_rig, tab_info, tab_manage = st.tabs(["📅 ĐIỀU ĐỘNG NHÂN SỰ", "👤 HỒ SƠ CHI TIẾT", "⚙️ CẤU HÌNH GIÀN"])

with tab_rig:
    with st.container():
        c1, c2, c3 = st.columns([2, 1.5, 1.5])
        with c1:
            sel_staff = st.multiselect("BƯỚC 1: CHỌN NHÂN VIÊN", NAMES)
        with c2:
            status_opt = st.selectbox("BƯỚC 2: TRẠNG THÁI", ["Đi Biển", "Nghỉ CA (CA)", "Làm Việc (WS)", "Nghỉ Phép (P)", "Nghỉ Ốm (S)"])
            if status_opt == "Đi Biển":
                final_val = st.selectbox("CHỌN GIÀN", st.session_state.list_gian)
            else:
                final_val = {"Nghỉ CA (CA)": "CA", "Làm Việc (WS)": "WS", "Nghỉ Phép (P)": "P", "Nghỉ Ốm (S)": "S"}[status_opt]
        with c3:
            sel_dates = st.date_input("BƯỚC 3: CHỌN KHOẢNG NGÀY", 
                                      value=(date(2026, 2, 1), date(2026, 2, 7)),
                                      min_value=date(2026, 2, 1), 
                                      max_value=date(2026, 2, 28))

        if st.button("🔥 XÁC NHẬN CẬP NHẬT", type="primary", use_container_width=True):
            if isinstance(sel_dates, tuple) and len(sel_dates) == 2:
                start_d, end_d = sel_dates[0].day, sel_dates[1].day
                for d in range(start_d, end_d + 1):
                    col_name = get_col_name(d)
                    st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col_name] = final_val
                st.success("Cập nhật dữ liệu thành công!")
                st.rerun()

with tab_info:
    c_s, c_r, c_c = st.columns([2, 1, 1])
    with c_s: i_staff = st.multiselect("Chọn nhân sự:", NAMES, key="info_s")
    with c_r: n_role = st.text_input("Chức danh mới:")
    with c_c: n_corp = st.text_input("Đơn vị mới:")
    if st.button("💾 LƯU THÔNG TIN"):
        if n_role: st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(i_staff), 'Chức danh'] = n_role
        if n_corp: st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(i_staff), 'Công ty'] = n_corp
        st.success("Hồ sơ đã được cập nhật!")

with tab_manage:
    ca, cb = st.columns(2)
    with ca:
        new_rig = st.text_input("Tên Giàn mới:")
        if st.button("THÊM VÀO DANH SÁCH"):
            st.session_state.list_gian.append(new_rig)
            st.session_state.rig_colors[new_rig] = "#%06x" % random.randint(0, 0xFFFFFF)
            st.rerun()
    with cb:
        rig_del = st.selectbox("Xóa Giàn:", st.session_state.list_gian)
        if st.button("XÓA KHỎI DANH SÁCH"):
            st.session_state.list_gian.remove(rig_del)
            st.rerun()

# 5. HIỂN THỊ BẢNG VỚI STYLE TƯƠNG THÍCH
st.subheader("BẢNG TỔNG HỢP ĐIỀU ĐỘNG THÁNG 02/2026")

def style_cells(val):
    if val in st.session_state.list_gian:
        color = st.session_state.rig_colors.get(val, "#00558F")
        return f'color: {color}; font-weight: 800; background-color: #FFFFFF; border: 0.5px solid #BDC3C7;'
    
    styles = {
        "P": 'background-color: #FADBD8; color: #943126; font-weight: bold; border: 0.5px solid #BDC3C7;',
        "S": 'background-color: #EBDEF0; color: #633974; font-weight: bold; border: 0.5px solid #BDC3C7;',
        "WS": 'background-color: #FEF9E7; color: #7D6608; font-weight: bold; border: 0.5px solid #BDC3C7;'
    }
    return styles.get(val, 'color: #7F8C8D; background-color: #FFFFFF; border: 0.5px solid #ECF0F1;')

# Hiển thị bảng dữ liệu
cols = list(st.session_state.db.columns)
df_display = st.session_state.db[[cols[0], 'Chức danh', 'Công ty'] + cols[3:]]

st.dataframe(df_display.style.applymap(style_cells, subset=df_display.columns[3:]), use_container_width=True, height=650)

# 6. XUẤT EXCEL
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.download_button("📥 TẢI BÁO CÁO CHI TIẾT (.XLSX)", data=to_excel(st.session_state.db), file_name="PVD_Report_2026.xlsx", use_container_width=True)
