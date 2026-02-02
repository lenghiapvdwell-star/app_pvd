import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import date

# 1. Cấu hình trang
st.set_page_config(page_title="PVD 2026", layout="wide")

# 2. Kết nối dứt điểm (Bản sửa lỗi Invalid connection)
try:
    # Bước A: Lấy dữ liệu từ Secrets
    # Chúng ta dùng "gsheets" làm tên kết nối
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    st.success("✅ Hệ thống đã kết nối thành công với Google Sheets!")
except Exception as e:
    st.error(f"❌ Lỗi: {e}")
    st.info("Nếu lỗi PEM quay lại, hãy kiểm tra kỹ mục Secrets.")
    st.stop()

# 3. Giao diện chính
st.title("PVD PERSONNEL CLOUD 2026")

try:
    # Đọc dữ liệu từ Tab PVD_Data
    df = conn.read(worksheet="PVD_Data", ttl=0)
    st.write("Dữ liệu hiện tại trên Google Sheets:")
    st.dataframe(df, use_container_width=True)
except Exception as e:
    st.warning("⚠️ Đã kết nối nhưng chưa thấy dữ liệu.")
    st.info("Kiểm tra: Bạn đã đặt tên Tab là 'PVD_Data' và Share file cho email service account chưa?")
