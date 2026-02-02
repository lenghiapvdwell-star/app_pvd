import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="PVD Management 2026", layout="wide")

@st.cache_resource
def connect_gsheet():
    # Lấy thông tin từ các biến phẳng trong Secrets
    info = {
        "type": st.secrets["type"],
        "project_id": st.secrets["project_id"],
        "private_key_id": st.secrets["private_key_id"],
        "private_key": st.secrets["private_key"],
        "client_email": st.secrets["client_email"],
        "token_uri": st.secrets["token_uri"],
    }
    creds = Credentials.from_service_account_info(info, scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ])
    return gspread.authorize(creds)

st.title("🚢 PVD PERSONNEL CLOUD")

try:
    gc = connect_gsheet()
    # Mở sheet của bạn
    sh = gc.open_by_key("1mNVM-Gq6JkF41Yz7JDRiiLtWOtoQHnXwyp3LTRGt-2E")
    ws = sh.worksheet("PVD_Data")
    
    # Giao diện nhập liệu nhanh
    with st.expander("➕ NHẬP MỚI", expanded=True):
        with st.form("my_form"):
            msnv = st.text_input("MSNV")
            ten = st.text_input("Họ Tên")
            if st.form_submit_button("Lưu"):
                ws.append_row([msnv, ten])
                st.success("Đã lưu!")
                st.rerun()

    # Hiển thị dữ liệu
    df = pd.DataFrame(ws.get_all_records())
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi: {e}")
