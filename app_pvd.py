import streamlit as st
import pandas as pd
import time

# Cấu hình giao diện Pro
st.set_page_config(page_title="PVD Personnel Cloud", layout="wide", page_icon="🚢")

st.title("🚢 HỆ THỐNG QUẢN LÝ NHÂN SỰ PVD - CLOUD 2026")
st.markdown("---")

# Hàm đọc dữ liệu từ Google Sheets (Link CSV)
def load_data():
    try:
        # Thêm tham số thời gian để tránh Google trả về dữ liệu cũ (cache)
        url = st.secrets["sheet_url"] + "&cache_bust=" + str(time.time())
        data = pd.read_csv(url)
        return data
    except Exception as e:
        return None

# Chia Tab giao diện
tab1, tab2 = st.tabs(["📝 NHẬP LIỆU & TRA CỨU", "📥 XUẤT BÁO CÁO EXCEL"])

with tab1:
    col_form, col_data = st.columns([1, 2]) # Form bên trái, Bảng bên phải
    
    with col_form:
        st.subheader("📝 Nhập nhân sự")
        st.info("Sau khi nhấn 'Gửi' trên Form, hãy nhấn nút 'Làm mới bảng' bên cạnh.")
        # Nhúng Google Form
        st.components.v1.iframe(st.secrets["form_url"], height=600, scrolling=True)

    with col_data:
        st.subheader("📊 Danh sách trực tuyến")
        if st.button("🔄 Làm mới bảng dữ liệu"):
            st.cache_data.clear()
            st.rerun()

        df = load_data()
        if df is not None:
            # Ô tìm kiếm nhanh
            search = st.text_input("🔍 Tìm nhanh nhân viên (Tên, MSNV...):")
            if search:
                df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
            
            # Hiển thị bảng
            st.dataframe(df, use_container_width=True, hide_index=True, height=500)
        else:
            st.warning("⚠️ Đang chờ dữ liệu từ Cloud. Hãy đảm bảo bạn đã nhấn 'Xuất bản lên web' trên Google Sheet.")

with tab2:
    st.subheader("📤 Xuất dữ liệu ra file Excel")
    if df is not None:
        st.write(f"Tổng số nhân sự hiện tại: **{len(df)}**")
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 TẢI FILE EXCEL (.CSV) MỚI NHẤT",
            data=csv,
            file_name='PVD_Data_Cloud_Report.csv',
            mime='text/csv'
        )
    else:
        st.error("Chưa có dữ liệu để xuất file.")

# Chân trang
st.markdown("---")
st.caption("Hệ thống lưu trữ trên nền tảng Google Cloud Sync. Dữ liệu được bảo mật và cập nhật thời gian thực.")
