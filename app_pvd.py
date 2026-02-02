import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="PVD Personnel Cloud", layout="wide", page_icon="🚢")

st.title("🚢 HỆ THỐNG QUẢN LÝ NHÂN SỰ PVD - CLOUD 2026")

# Kiểm tra xem Secrets đã được thiết lập đúng chưa
if "sheet_url" not in st.secrets or "form_url" not in st.secrets:
    st.error("❌ Thiếu cấu hình trong Secrets! Vui lòng kiểm tra lại 'sheet_url' và 'form_url'.")
    st.stop()

# Hàm tải dữ liệu
@st.cache_data(ttl=10)
def load_data():
    try:
        # Thêm biến thời gian để buộc Google cung cấp dữ liệu mới nhất
        url = st.secrets["sheet_url"] + "&cache_bust=" + str(time.time())
        return pd.read_csv(url)
    except Exception as e:
        return None

# Giao diện chính
tab1, tab2 = st.tabs(["📝 NHẬP LIỆU & TRA CỨU", "📥 XUẤT BÁO CÁO EXCEL"])

with tab1:
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.subheader("📝 Form Nhập Liệu")
        # Nhúng Google Form từ Secrets
        st.components.v1.iframe(st.secrets["form_url"], height=700, scrolling=True)

    with col_right:
        st.subheader("📊 Danh sách từ Cloud")
        if st.button("🔄 Cập nhật dữ liệu mới"):
            st.cache_data.clear()
            st.rerun()
            
        df = load_data()
        if df is not None:
            search = st.text_input("🔍 Tìm nhân viên:")
            if search:
                df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning("Đang kết nối đến Google Sheets...")

with tab2:
    st.subheader("📤 Xuất file Excel")
    df_export = load_data()
    if df_export is not None:
        csv = df_export.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 TẢI FILE EXCEL (.CSV)", data=csv, file_name='PVD_Data.csv')
