import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Cấu hình trang Pro
st.set_page_config(page_title="PVD Cloud System", layout="wide", page_icon="🚢")

st.title("🚢 HỆ THỐNG QUẢN LÝ PVD - DỮ LIỆU ĐÁM MÂY")
st.info("Dữ liệu được lưu trữ trực tuyến. Mọi thay đổi sẽ được cập nhật cho toàn bộ người dùng.")

# 2. Kết nối với Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Đọc dữ liệu hiện có từ Sheet
    df = conn.read(spreadsheet=st.secrets["gsheet_url"])

    # 3. GIAO DIỆN CHIA TAB PRO
    tab1, tab2, tab3 = st.tabs(["➕ NHẬP LIỆU", "🔍 TRA CỨU", "📥 XUẤT BÁO CÁO"])

    with tab1:
        st.subheader("Ghi nhận thông tin mới")
        with st.form("input_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                msnv = st.text_input("Mã số nhân viên *")
                ho_ten = st.text_input("Họ và Tên *")
                don_vi = st.selectbox("Đơn vị", ["PVD Drilling", "PVD Well Services", "PVD Logging", "Khác"])
            with c2:
                chuc_danh = st.text_input("Chức danh")
                ngay_vao = st.date_input("Ngày vào làm")
            
            ghi_chu = st.text_area("Ghi chú bổ sung")
            submit = st.form_submit_button("💾 LƯU LÊN BỘ NHỚ ĐÁM MÂY")

        if submit:
            if msnv and ho_ten:
                # Tạo hàng dữ liệu mới
                new_row = pd.DataFrame([{
                    "MSNV": msnv,
                    "Họ Tên": ho_ten,
                    "Đơn vị": don_vi,
                    "Chức danh": chuc_danh,
                    "Ngày vào làm": str(ngay_vao),
                    "Ghi chú": ghi_chu
                }])
                # Cộng gộp và gửi lên Cloud
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(spreadsheet=st.secrets["gsheet_url"], data=updated_df)
                
                st.success("✅ Đã lưu! Dữ liệu đã được đồng bộ lên không gian mạng.")
                st.balloons()
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("⚠️ Vui lòng điền đầy đủ MSNV và Họ Tên.")

    with tab2:
        st.subheader("Danh sách nhân sự trực tuyến")
        search = st.text_input("🔍 Nhập thông tin cần tìm (Tên, MSNV...):")
        
        df_filter = df if not search else df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        st.dataframe(df_filter, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Kết xuất báo cáo Excel")
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 TẢI FILE EXCEL (CSV) BẢN MỚI NHẤT",
            data=csv,
            file_name='PVD_Data_Cloud.csv',
            mime='text/csv'
        )

except Exception as e:
    st.error(f"Lỗi kết nối bộ nhớ Cloud: {e}")
    st.info("Hãy đảm bảo bạn đã Share quyền 'Editor' cho file Google Sheet.")
