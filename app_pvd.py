import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

# 1. Cấu hình trang
st.set_page_config(page_title="PVD Cloud Management", layout="wide", initial_sidebar_state="collapsed")

# 2. Kết nối Google Sheets (Sử dụng cấu hình từ Secrets)
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # Đọc dữ liệu từ sheet "PVD_Data" (Bạn hãy đặt tên tab trong Google Sheets là PVD_Data nhé)
        df = conn.read(worksheet="PVD_Data", ttl="0")
        return df
    except Exception as e:
        return None

# 3. Khởi tạo dữ liệu
if 'db' not in st.session_state:
    existing_data = load_data()
    if existing_data is not None and not existing_data.empty:
        st.session_state.db = existing_data
    else:
        # Nếu chưa có dữ liệu trên Cloud, tạo mới danh sách 64 người
        NAMES = ["Bùi Anh Phương", "Lê Thái Việt", "Lê Tùng Phong", "Nguyễn Tiến Dũng", "Nguyễn Văn Quang", "Phạm Hồng Minh", "Nguyễn Gia Khánh", "Nguyễn Hữu Lộc", "Nguyễn Tấn Đạt", "Chu Văn Trường", "Hồ Sỹ Đức", "Hoàng Thái Sơn", "Phạm Thái Bảo", "Cao Trung Nam", "Lê Trọng Nghĩa", "Nguyễn Văn Mạnh", "Nguyễn Văn Sơn", "Dương Mạnh Quyết", "Trần Quốc Huy", "Rusliy Saifuddin", "Đào Tiến Thành", "Đoàn Minh Quân", "Rawing Empanit", "Bùi Sỹ Xuân", "Cao Văn Thắng", "Cao Xuân Vinh", "Đàm Quang Trung", "Đào Văn Tám", "Đinh Duy Long", "Đinh Ngọc Hiếu", "Đỗ Đức Ngọc", "Đỗ Văn Tường", "Đồng Văn Trung", "Hà Viết Hùng", "Hồ Trọng Đông", "Hoàng Tùng", "Lê Hoài Nam", "Lê Hoài Phước", "Lê Minh Hoàng", "Lê Quang Minh", "Lê Quốc Duy", "Mai Nhân Dương", "Ngô Quỳnh Hải", "Ngô Xuân Điền", "Nguyễn Hoàng Quy", "Nguyễn Hữu Toàn", "Nguyễn Mạnh Cường", "Nguyễn Quốc Huy", "Nguyễn Tuấn Anh", "Nguyễn Tuấn Minh", "Nguyễn Văn Bảo Ngọc", "Nguyễn Văn Duẩn", "Nguyễn Văn Hưng", "Nguyễn Văn Võ", "Phan Tây Bắc", "Trần Văn Hoàn", "Trần Văn Hùng", "Trần Xuân Nhật", "Võ Hồng Thịnh", "Vũ Tuấn Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Trần Tuấn Dũng"]
        df = pd.DataFrame({'Họ và Tên': NAMES, 'Chức danh': 'Kỹ sư', 'Công ty': 'PVD'})
        # Giả định tháng 2/2026 có 28 ngày
        days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
        for d in range(1, 29):
            dt = datetime(2026, 2, d)
            col_name = f"{d:02d}/{dt.strftime('%b')}\n{days_vn[dt.weekday()]}"
            df[col_name] = ""
        st.session_state.db = df

# 4. Giao diện (CSS Blue Ocean)
st.markdown(
    """
    <style>
    .stApp { background-color: #0A192F !important; color: #E6F1FF !important; }
    .pvd-logo-fixed { position: fixed; top: 25px; left: 20px; z-index: 10000; width: 225px; }
    .main .block-container { padding-left: 290px; padding-right: 30px; }
    .main-header { color: #64FFDA; font-size: 30px; font-weight: 800; border-bottom: 2px solid #64FFDA; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True
)

st.image("logo_pvd.png", width=225)
st.markdown("<div class='main-header'>PVD CLOUD DISPATCHING SYSTEM 2026</div>", unsafe_allow_html=True)

# 5. Các Tab chức năng (Giữ nguyên logic cập nhật của bạn)
# ... (Phần code multiselect, date_input, tab_info bạn copy từ bản trước vào đây)

# 6. NÚT ĐỒNG BỘ "PRO"
st.divider()
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("🌐 LƯU DỮ LIỆU LÊN CLOUD", type="primary", use_container_width=True):
        try:
            # Ghi đè dữ liệu lên Google Sheets
            conn.update(worksheet="PVD_Data", data=st.session_state.db)
            st.success("✅ Đã lưu! Đồng nghiệp mở link sẽ thấy dữ liệu này ngay.")
        except Exception as e:
            st.error(f"Lỗi: Hãy đảm bảo bạn đã tạo Tab tên 'PVD_Data' trong Google Sheet.")

with col_btn2:
    if st.button("🔄 TẢI DỮ LIỆU MỚI NHẤT", use_container_width=True):
        st.session_state.db = load_data()
        st.rerun()

# 7. Hiển thị bảng (Chữ CA nổi bật)
def style_cells(val):
    if val == "CA": return 'color: #FFFFFF; font-weight: bold; background-color: #1B2631;'
    # ... (Các style khác cho Giàn, P, S)
    return 'background-color: #0A192F;'

st.dataframe(st.session_state.db.style.applymap(style_cells), use_container_width=True, height=600)
