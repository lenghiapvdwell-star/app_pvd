import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="PVD Personnel 2026", layout="wide")

@st.cache_resource
def get_gspread_client():
    # Lấy thông tin từ secrets và xử lý ký tự xuống dòng
    creds_dict = {
        "type": st.secrets["type"],
        "project_id": st.secrets["project_id"],
        "private_key_id": st.secrets["private_key_id"],
        "private_key": st.secrets["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets["client_email"],
        "token_uri": st.secrets["token_uri"],
    }
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

st.title("🚢 PVD PERSONNEL CLOUD 2026")

try:
    client = get_gspread_client()
    # ID bảng tính của bạn
    spreadsheet_id = "1mNVM-Gq6JkF41Yz7JDRiiLtWOtoQHnXwyp3LTRGt-2E"
    sheet = client.open_by_key(spreadsheet_id)
    worksheet = sheet.worksheet("PVD_Data")
    
    # Hiển thị dữ liệu
    df = pd.DataFrame(worksheet.get_all_records())
    st.success("✅ KẾT NỐI DỮ LIỆU ĐÁM MÂY THÀNH CÔNG!")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"❌ LỖI: {e}")
