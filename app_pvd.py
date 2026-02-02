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
    conf["private_key"] = conf["private_key"].replace("\\n", "\n")
    
    # Kết nối thủ công
    conn = st.connection("gsheets", type=GSheetsConnection, **conf)
    
    st.success("✅ Hệ thống đã kết nối thành công với Google Sheets!")
except Exception as e:
    st.error(f"❌ Lỗi cấu hình Secrets: {e}")
    st.info("Kiểm tra lại xem bạn đã nhấn SAVE trong mục Secrets chưa.")
    st.stop()

# 3. Thử đọc dữ liệu
st.title("PVD PERSONNEL CLOUD 2026")
try:
    # Đọc dữ liệu từ Sheet có tên là PVD_Data
    df = conn.read(worksheet="PVD_Data", ttl=0)
    st.write("Dữ liệu hiện tại trên Cloud:")
    st.dataframe(df, use_container_width=True)
except Exception as e:
    st.warning("⚠️ Đã kết nối nhưng chưa tìm thấy Tab 'PVD_Data' hoặc Sheet đang trống.")
    st.info("Hãy đảm bảo bạn đã đặt tên Tab trong Google Sheet là: PVD_Data")
