import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import date

# 1. Cấu hình trang
st.set_page_config(page_title="PVD 2026", layout="wide")

# 2. Kết nối và làm sạch mã khóa (Dứt điểm lỗi PEM)
try:
    # Lấy thông tin từ mục Secrets
    conf = st.secrets["connections"]["gsheets"].to_dict()
    
    # Chuyển đổi các chữ \n thành lệnh xuống dòng thực sự cho Google hiểu
    if "private_key" in conf:
        conf["private_key"] = conf["private_key"].replace("\\n", "\n")
    
    # KẾT NỐI: Sử dụng tham số từ Secrets mà không lặp lại 'type'
    conn = st.connection("gsheets", **conf)
    
    st.success("✅ Hệ thống đã kết nối thành công với Google Sheets!")
except Exception as e:
    st.error(f"❌ Lỗi: {e}")
    st.stop()

# 3. Giao diện chính
st.title("PVD PERSONNEL CLOUD 2026")

try:
    # Thử đọc dữ liệu từ Tab PVD_Data
    df = conn.read(worksheet="PVD_Data", ttl=0)
    st.write("Dữ liệu hiện tại:")
    st.dataframe(df, use_container_width=True)
except Exception as e:
    st.warning("⚠️ Đã kết nối nhưng chưa thấy dữ liệu.")
    st.info("Hãy kiểm tra: 1. Đã share file cho Email Service Account chưa? 2. Tên Tab có đúng là 'PVD_Data' không?")
