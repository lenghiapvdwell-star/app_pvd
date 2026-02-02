import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. Khởi tạo
st.set_page_config(page_title="PVD Personnel 2026", layout="wide")

@st.cache_resource
def get_credentials():
    # Đọc từng biến từ Secrets
    return {
        "type": st.secrets["type"],
        "project_id": st.secrets["project_id"],
        "private_key_id": st.secrets["private_key_id"],
        "private_key": st.secrets["private_key"],
        "client_email": st.secrets["client_email"],
        "token_uri": st.secrets["token_uri"],
    }

st.title("🚢 PVD PERSONNEL CLOUD 2026")

try:
    info = get_credentials()
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    gc = gspread.authorize(creds)
    
    # Mở Sheet
    sh = gc.open_by_key("1mNVM-Gq6JkF41Yz7JDRiiLtWOtoQHnXwyp3LTRGt-2E")
    ws = sh.worksheet("PVD_Data")
    
    df = pd.DataFrame(ws.get_all_records())
    
    if not df.empty:
        st.success("✅ KẾT NỐI THÀNH CÔNG!")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("⚠️ Kết nối OK nhưng Tab 'PVD_Data' đang trống.")

except Exception as e:
    st.error(f"❌ LỖI: {e}")
