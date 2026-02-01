import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, date

# 1. Cấu hình trang
st.set_page_config(page_title="PVD Management 2026", layout="wide", initial_sidebar_state="collapsed")

# 2. Kết nối an toàn với Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Lỗi cấu hình Secrets: {e}")
    st.stop()

def get_col_name(day):
    # Cố định tháng 2/2026
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/02\n{days_vn[d.weekday()]}"

NAMES = ["Bùi Anh Phương", "Lê Thái Việt", "Lê Tùng Phong", "Nguyễn Tiến Dũng", "Nguyễn Văn Quang", "Phạm Hồng Minh", "Nguyễn Gia Khánh", "Nguyễn Hữu Lộc", "Nguyễn Tấn Đạt", "Chu Văn Trường", "Hồ Sỹ Đức", "Hoàng Thái Sơn", "Phạm Thái Bảo", "Cao Trung Nam", "Lê Trọng Nghĩa", "Nguyễn Văn Mạnh", "Nguyễn Văn Sơn", "Dương Mạnh Quyết", "Trần Quốc Huy", "Rusliy Saifuddin", "Đào Tiến Thành", "Đoàn Minh Quân", "Rawing Empanit", "Bùi Sỹ Xuân", "Cao Văn Thắng", "Cao Xuân Vinh", "Đàm Quang Trung", "Đào Văn Tám", "Đinh Duy Long", "Đinh Ngọc Hiếu", "Đỗ Đức Ngọc", "Đỗ Văn Tường", "Đồng Văn Trung", "Hà Viết Hùng", "Hồ Trọng Đông", "Hoàng Tùng", "Lê Hoài Nam", "Lê Hoài Phước", "Lê Minh Hoàng", "Lê Quang Minh", "Lê Quốc Duy", "Mai Nhân Dương", "Ngô Quỳnh Hải", "Ngô Xuân Điền", "Nguyễn Hoàng Quy", "Nguyễn Hữu Toàn", "Nguyễn Mạnh Cường", "Nguyễn Quốc Huy", "Nguyễn Tuấn Anh", "Nguyễn Tuấn Minh", "Nguyễn Văn Bảo Ngọc", "Nguyễn Văn Duẩn", "Nguyễn Văn Hưng", "Nguyễn Văn Võ", "Phan Tây Bắc", "Trần Văn Hoàn", "Trần Văn Hùng", "Trần Xuân Nhật", "Võ Hồng Thịnh", "Vũ Tuấn Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Trần Tuấn Dũng"]

# 3. Khởi tạo dữ liệu
if 'db' not in st.session_state:
    try:
        # Thử tải dữ liệu từ Tab PVD_Data
        df_cloud = conn.read(worksheet="PVD_Data", ttl=0)
        if df_cloud is not None and not df_cloud.empty:
            st.session_state.db = df_cloud
        else:
            raise ValueError("Data empty")
    except:
        # Nếu chưa có trên Cloud, tạo bảng mẫu trắng 64 người
        df = pd.DataFrame({'Họ và Tên': NAMES, 'Chức danh': 'Kỹ sư', 'Công ty': 'PVD'})
        for d in range(1, 29):
            df[get_col_name(d)] = ""
        st.session_state.db = df

if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

# 4. Giao diện CSS
st.markdown(
    """
    <style>
    .stApp { background-color: #0A192F !important; color: #E6F1FF !important; }
    .main-header { color: #64FFDA; font-size: 32px; font-weight: 800; border-bottom: 2px solid #64FFDA; padding-bottom: 10px; }
    .main .block-container { padding-top: 2rem; }
    /* Style cho bảng DataFrame */
    div[data-testid="stDataFrame"] { border: 1px solid #64FFDA; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True
)

st.markdown("<div class='main-header'>PVD PERSONNEL CLOUD 2026</div>", unsafe_allow_html=True)

# 5. Các Tab chức năng
tab1, tab2 = st.tabs(["🚀 CHẤM CÔNG", "🌐 ĐỒNG BỘ CLOUD"])

with tab1:
    c1, c2, c3 = st.columns([2, 1, 1.5])
    with c1: s_staff = st.multiselect("Nhân viên:", NAMES)
    with c2:
        opt = st.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "P", "S"])
        val = st.selectbox("Giàn:", st.session_state.list_gian) if opt == "Đi Biển" else opt
    with c3: dates = st.date_input("Chọn ngày:", value=(date(2026, 2, 1), date(2026, 2, 7)), 
                                   min_value=date(2026, 2, 1), max_value=date(2026, 2, 28))
    
    if st.button("🔥 CẬP NHẬT DỮ LIỆU TẠM THỜI", type="primary", use_container_width=True):
        if isinstance(dates, tuple) and len(dates) == 2:
            start_d, end_d = dates[0].day, dates[1].day
            for d in range(start_d, end_d + 1):
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(s_staff), get_col_name(d)] = val
            st.success("Đã cập nhật vào bảng bên dưới. Hãy nhấn Tab 'ĐỒNG BỘ CLOUD' để lưu vĩnh viễn!")

with tab2:
    st.warning("⚠️ Chú ý: Dữ liệu trên Google Sheets sẽ bị ghi đè bởi bảng hiện tại.")
    if st.button("🌐 XÁC NHẬN LƯU LÊN CLOUD", use_container_width=True):
        try:
            # Lưu dữ liệu lên trang tính PVD_Data
            conn.update(worksheet="PVD_Data", data=st.session_state.db)
            st.success("✅ Đã đồng bộ thành công lên Google Sheets!")
        except Exception as e:
            st.error(f"Lỗi khi ghi dữ liệu: {e}")

# 6. Hiển thị bảng
def style_cells(v):
    if v == "CA": return 'color: #FFFFFF; font-weight: bold; background-color: #1B2631;'
    if v in st.session_state.list_gian: return 'color: #64FFDA; font-weight: bold; background-color: #112240;'
    styles = {"P": 'background-color: #F44336;', "S": 'background-color: #9C27B0;', "WS": 'background-color: #FFEB3B; color: black;'}
    return styles.get(v, '')

st.subheader("BẢNG TỔNG HỢP CHI TIẾT THÁNG 02/2026")
# Hiển thị bảng với màu sắc
st.dataframe(st.session_state.db.style.map(style_cells, subset=st.session_state.db.columns[3:]), 
             use_container_width=True, height=600)
