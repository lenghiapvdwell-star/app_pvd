import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Cấu hình trang
st.set_page_config(page_title="PVD Check Connect", layout="wide")

st.title("KIỂM TRA KẾT NỐI PVD")

try:
    # Kết nối trực tiếp bằng cách đọc mục [connections.gsheets] trong Secrets
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Thử đọc dữ liệu từ Sheet
    df = conn.read(worksheet="PVD_Data", ttl=0)
    
    st.success("✅ KẾT NỐI THÀNH CÔNG!")
    st.write("Dữ liệu tìm thấy:")
    st.dataframe(df)
    
except Exception as e:
    st.error(f"❌ LỖI KẾT NỐI: {e}")
    st.info("Gợi ý: Hãy kiểm tra xem nút SAVE trong Secrets đã được nhấn chưa.")
