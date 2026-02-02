import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="PVD Cloud System", layout="wide", page_icon="🚢")

st.title("🚢 HỆ THỐNG QUẢN LÝ PVD - CLOUD 2026")

# Kết nối Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # Đọc dữ liệu và bỏ qua các lỗi định dạng ban đầu
    return conn.read(spreadsheet=st.secrets["gsheet_url"], ttl=0)

try:
    df = load_data()
    
    # Nếu sheet chưa có dữ liệu hoặc lỗi tiêu đề, tạo khung mặc định
    expected_cols = ["MSNV", "Họ Tên", "Đơn vị", "Chức danh", "Ngày vào làm", "Ghi chú"]
    if df.empty or len(df.columns) < 2:
        df = pd.DataFrame(columns=expected_cols)

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
                # Tạo hàng mới đúng cấu trúc
                new_row = pd.DataFrame([[msnv, ho_ten, don_vi, chuc_danh, str(ngay_vao), ghi_chu]], 
                                     columns=df.columns[:6] if not df.empty else expected_cols)
                
                updated_df = pd.concat([df, new_row], ignore_index=True)
                
                # Lưu đè lên Google Sheet
                conn.update(spreadsheet=st.secrets["gsheet_url"], data=updated_df)
                
                st.success("✅ Đã lưu thành công lên Cloud!")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("⚠️ Vui lòng điền MSNV và Họ Tên!")

    with tab2:
        st.subheader("📊 Dữ liệu trực tuyến")
        search = st.text_input("🔍 Tìm kiếm nhanh:")
        if not df.empty:
            df_filter = df if not search else df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
            st.dataframe(df_filter, use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có dữ liệu trên hệ thống.")

    with tab3:
        st.subheader("📤 Xuất dữ liệu")
        if not df.empty:
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 TẢI FILE EXCEL (.CSV)", data=csv, file_name='PVD_Data_Cloud.csv')

except Exception as e:
    st.error(f"❌ Lỗi kết nối: {e}")
    st.info("Mẹo: Hãy thử đổi tên Sheet ở dưới cùng thành 'Sheet1' và kiểm tra lại quyền Editor.")
