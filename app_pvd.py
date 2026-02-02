import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. Cấu hình trang
st.set_page_config(page_title="PVD Personnel 2026", layout="wide")

@st.cache_resource
def get_gspread_client():
    # Lấy thông tin từ Secrets
    creds_dict = dict(st.secrets["gsheets_creds"])
    
    # Chỉ định quyền truy cập
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

st.title("🚢 PVD PERSONNEL CLOUD 2026")

try:
    client = get_gspread_client()
    # ID bảng tính (giữ nguyên từ file của bạn)
    spreadsheet_id = "1mNVM-Gq6JkF41Yz7JDRiiLtWOtoQHnXwyp3LTRGt-2E"
    sheet = client.open_by_key(spreadsheet_id)
    worksheet = sheet.worksheet("PVD_Data")
    
    # Đọc dữ liệu
    df = pd.DataFrame(worksheet.get_all_records())
    
    if not df.empty:
        st.success("✅ KẾT NỐI DỮ LIỆU ĐÁM MÂY THÀNH CÔNG!")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("⚠️ Đã kết nối nhưng không tìm thấy dữ liệu trong tab 'PVD_Data'.")

except Exception as e:
    st.error(f"❌ LỖI HỆ THỐNG: {e}")
