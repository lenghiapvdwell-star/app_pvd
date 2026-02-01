import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, date

# 1. Cấu hình trang
st.set_page_config(page_title="PVD Pro Cloud 2026", layout="wide", initial_sidebar_state="collapsed")

# 2. Kết nối Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def get_col_name(day):
    d = datetime(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/{d.strftime('%b')}\n{days_vn[d.weekday()]}"

NAMES = ["Bùi Anh Phương", "Lê Thái Việt", "Lê Tùng Phong", "Nguyễn Tiến Dũng", "Nguyễn Văn Quang", "Phạm Hồng Minh", "Nguyễn Gia Khánh", "Nguyễn Hữu Lộc", "Nguyễn Tấn Đạt", "Chu Văn Trường", "Hồ Sỹ Đức", "Hoàng Thái Sơn", "Phạm Thái Bảo", "Cao Trung Nam", "Lê Trọng Nghĩa", "Nguyễn Văn Mạnh", "Nguyễn Văn Sơn", "Dương Mạnh Quyết", "Trần Quốc Huy", "Rusliy Saifuddin", "Đào Tiến Thành", "Đoàn Minh Quân", "Rawing Empanit", "Bùi Sỹ Xuân", "Cao Văn Thắng", "Cao Xuân Vinh", "Đàm Quang Trung", "Đào Văn Tám", "Đinh Duy Long", "Đinh Ngọc Hiếu", "Đỗ Đức Ngọc", "Đỗ Văn Tường", "Đồng Văn Trung", "Hà Viết Hùng", "Hồ Trọng Đông", "Hoàng Tùng", "Lê Hoài Nam", "Lê Hoài Phước", "Lê Minh Hoàng", "Lê Quang Minh", "Lê Quốc Duy", "Mai Nhân Dương", "Ngô Quỳnh Hải", "Ngô Xuân Điền", "Nguyễn Hoàng Quy", "Nguyễn Hữu Toàn", "Nguyễn Mạnh Cường", "Nguyễn Quốc Huy", "Nguyễn Tuấn Anh", "Nguyễn Tuấn Minh", "Nguyễn Văn Bảo Ngọc", "Nguyễn Văn Duẩn", "Nguyễn Văn Hưng", "Nguyễn Văn Võ", "Phan Tây Bắc", "Trần Văn Hoàn", "Trần Văn Hùng", "Trần Xuân Nhật", "Võ Hồng Thịnh", "Vũ Tuấn Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Trần Tuấn Dũng"]

# 3. Khởi tạo dữ liệu (Sửa lỗi thụt lề tại đây)
if 'db' not in st.session_state:
    try:
        # Thử đọc từ Cloud trước
        df_cloud = conn.read(worksheet="PVD_Data", ttl=0)
        if df_cloud is not None and not df_cloud.empty:
            st.session_state.db = df_cloud
        else:
            raise ValueError("Sheet trống")
    except Exception as e:
        # Nếu lỗi hoặc trống, tạo mới bảng 64 người
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
    .pvd-logo-fixed { position: fixed; top: 25px; left: 20px; z-index: 10000; width: 225px; }
    .main .block-container { padding-left: 290px; padding-right: 30px; }
    </style>
    """, unsafe_allow_html=True
)

st.image("logo_pvd.png", width=225)
st.markdown("<div class='main-header'>PVD PERSONNEL CLOUD SYSTEM 2026</div>", unsafe_allow_html=True)

# 5. Các Tab chức năng
tab1, tab2, tab3 = st.tabs(["🚀 CHẤM CÔNG", "📝 HỒ SƠ", "🌐 ĐỒNG BỘ CLOUD"])

with tab1:
    c1, c2, c3 = st.columns([2, 1.5, 1.5])
    with c1: s_staff = st.multiselect("Nhân viên:", NAMES)
    with c2:
        opt = st.selectbox("Trạng thái:", ["Đi Biển", "Nghỉ CA (CA)", "Làm Việc (WS)", "Nghỉ Phép (P)", "Nghỉ Ốm (S)"])
        val = st.selectbox("Giàn:", st.session_state.list_gian) if opt == "Đi Biển" else ("CA" if opt == "Nghỉ CA (CA)" else {"Làm Việc (WS)": "WS", "Nghỉ Phép (P)": "P", "Nghỉ Ốm (S)": "S"}[opt])
    with c3: dates = st.date_input("Chọn ngày:", value=(date(2026, 2, 1), date(2026, 2, 7)), min_value=date(2026, 2, 1), max_value=date(2026, 2, 28))
    
    if st.button("🔥 CẬP NHẬT DỮ LIỆU", type="primary", use_container_width=True):
        if isinstance(dates, tuple) and len(dates) == 2:
            for d in range(dates[0].day, dates[1].day + 1):
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(s_staff), get_col_name(d)] = val
            st.rerun()

with tab3:
    st.info("Nhấn nút dưới đây để lưu vĩnh viễn dữ liệu lên Google Sheets.")
    if st.button("🌐 LƯU LÊN GOOGLE SHEETS", use_container_width=True):
        try:
            conn.update(worksheet="PVD_Data", data=st.session_state.db)
            st.success("✅ Đã lưu thành công lên Cloud!")
        except Exception as e:
            st.error(f"Lỗi lưu Cloud: {e}. Hãy kiểm tra lại Secrets và quyền Editor của Sheet.")

# 6. Hiển thị bảng
def style_cells(v):
    if v == "CA": return 'color: #FFFFFF; font-weight: bold; background-color: #1B2631;'
    if v in st.session_state.list_gian: return 'color: #64FFDA; font-weight: bold; background-color: #112240;'
    styles = {"P": 'background-color: #F44336;', "S": 'background-color: #9C27B0;', "WS": 'background-color: #FFEB3B; color: black;'}
    return styles.get(v, 'background-color: #0A192F;')

st.subheader("BẢNG TỔNG HỢP CHI TIẾT")
# Subset từ cột thứ 3 trở đi để tô màu (bỏ qua Tên, Chức danh, Công ty)
st.dataframe(st.session_state.db.style.map(style_cells, subset=st.session_state.db.columns[3:]), use_container_width=True, height=600)
