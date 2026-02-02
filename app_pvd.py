import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Cấu hình trang
st.set_page_config(page_title="PVD Management 2026", layout="wide")

# 2. Xử lý khóa PEM thủ công để dứt điểm lỗi InvalidByte
if "connections" in st.secrets and "gsheets" in st.secrets.connections:
    # Lấy key từ secrets
    raw_key = st.secrets.connections.gsheets.private_key
    # Nếu key chứa chuỗi "\n" (dạng văn bản), chuyển nó thành ký tự xuống dòng thực sự
    clean_key = raw_key.replace("\\n", "\n")
    # Ghi đè lại vào bộ nhớ tạm của app
    st.secrets.connections.gsheets.private_key = clean_key

# 3. Kết nối theo cách chuẩn mực nhất của Streamlit
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    st.title("PVD PERSONNEL 2026")
    
    # Đọc dữ liệu (Hàm read lúc này cực kỳ đơn giản)
    df = conn.read(worksheet="PVD_Data", ttl=0)
    
    st.success("✅ KẾT NỐI CLOUD THÀNH CÔNG!")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"❌ LỖI: {e}")
    st.info("Gợi ý: Đảm bảo bạn đã Share file cho email pvd-sync@... và đặt tên Tab là PVD_Data")
