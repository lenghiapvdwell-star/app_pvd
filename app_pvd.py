import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="PVD Cloud System", layout="wide", page_icon="🚢")

st.title("🚢 HỆ THỐNG QUẢN LÝ PVD - CLOUD 2026")

# Kết nối Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Đọc dữ liệu từ Cloud
    df = conn.read(spreadsheet=st.secrets["gsheet_url"])
    
    # Nếu sheet hoàn toàn trống, tạo DataFrame mẫu để không bị lỗi
    if df.empty:
        df = pd.DataFrame(columns=["MSNV", "Họ Tên", "Đơn vị", "Chức danh", "Ngày vào làm", "Ghi chú"])

    tab1, tab2, tab3 = st.tabs(["➕ NHẬP LIỆU", "🔍 TRA CỨU", "📥 XUẤT BÁO CÁO"])

    with tab1:
        st.subheader("📝 Ghi nhận thông tin mới")
        with st.form("input_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            msnv = c1.text_input("Mã số nhân viên (MSNV) *")
            ho_ten = c1.text_input("Họ và Tên *")
            don_vi = c2.selectbox("Đơn vị", ["PVD Drilling", "PVD Well Services", "PVD Logging", "Khác"])
            chuc_danh = c2.text_input("Chức danh")
            ngay_vao = st.date_input("Ngày vào làm")
            ghi_chu = st.text_area("Ghi chú")
            
            submit = st.form_submit_button("💾 LƯU LÊN ĐÁM MÂY")

        if submit:
            if msnv and ho_ten:
                new_row = pd.DataFrame([{
                    "MSNV": msnv, "Họ Tên": ho_ten, "Đơn vị": don_vi,
                    "Chức danh": chuc_danh, "Ngày vào làm": str(ngay_vao), "Ghi chú": ghi_chu
                }])
                
                # Ghi đè dữ liệu mới lên Sheet
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(spreadsheet=st.secrets["gsheet_url"], data=updated_df)
                
                st.success("✅ Đã đồng bộ lên không gian mạng! Mọi người đều có thể thấy.")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("⚠️ Vui lòng điền MSNV và Họ Tên!")

    with tab2:
        st.subheader("📊 Dữ liệu nhân sự trực tuyến")
        search = st.text_input("🔍 Tìm kiếm nhanh:")
        df_filter = df if not search else df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        st.dataframe(df_filter, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("📤 Xuất dữ liệu Excel")
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 TẢI FILE EXCEL (.CSV)", data=csv, file_name='PVD_Data_Cloud.csv')

except Exception as e:
    st.error("❌ Lỗi cấu hình Sheet.")
    st.info("Hãy đảm bảo Hàng 1 của Sheet có đủ: MSNV, Họ Tên, Đơn vị, Chức danh, Ngày vào làm, Ghi chú")
