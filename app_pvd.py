import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. Cấu hình giao diện
st.set_page_config(page_title="PVD Personnel 2026", layout="wide")

@st.cache_resource
def connect_to_google():
    # Đọc chuỗi JSON từ secrets
    info = json.loads(st.secrets["service_account_json"])
    
    # Phạm vi truy cập
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # Kết nối
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds)

st.title("🚢 PVD PERSONNEL CLOUD 2026")

try:
    gc = connect_to_google()
    # Mở bằng ID file
    sh = gc.open_by_key("1mNVM-Gq6JkF41Yz7JDRiiLtWOtoQHnXwyp3LTRGt-2E")
    
    # Mở tab PVD_Data
    ws = sh.worksheet("PVD_Data")
    
    # Đọc và hiển thị
    data = ws.get_all_records()
    df = pd.DataFrame(data)
    
    if not df.empty:
        st.success("✅ KẾT NỐI THÀNH CÔNG!")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("⚠️ Đã kết nối nhưng Tab 'PVD_Data' chưa có dữ liệu.")

except Exception as e:
    st.error(f"❌ LỖI HỆ THỐNG: {e}")
    st.info("Hãy đảm bảo bạn đã dán đúng nội dung Secrets và Tab tên là 'PVD_Data'.")
