import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Cấu hình trang
st.set_page_config(page_title="PVD Management Pro", layout="wide")

st.title("🚢 HỆ THỐNG QUẢN LÝ NHÂN SỰ PVD 2026")
st.markdown("---")

# 2. Kết nối Google Sheets
# Lưu ý: Bạn cần dán link Google Sheet (quyền Editor) vào Secrets với tên: gsheets_url
conn = st.connection("gsheets", type=GSheetsConnection)

# Đọc dữ liệu hiện có
df = conn.read(spreadsheet=st.secrets["gsheets_url"], worksheet="PVD_Data")

# 3. GIAO DIỆN NHẬP LIỆU (FORM)
with st.expander("➕ THÊM NHÂN SỰ MỚI", expanded=False):
    with st.form("input_form"):
        col1, col2 = st.columns(2)
        with col1:
            msnv = st.text_input("Mã số nhân viên (MSNV)*")
            ho_ten = st.text_input("Họ và Tên*")
            don_vi = st.selectbox("Đơn vị", ["PVD Drilling", "PVD Well Services", "PVD Logging", "Khác"])
        with col2:
            chuc_danh = st.text_input("Chức danh")
            ngay_vao = st.date_input("Ngày vào làm")
            ghi_chu = st.text_area("Ghi chú")
        
        submit_button = st.form_submit_button(label="💾 LƯU VÀO HỆ THỐNG")

    if submit_button:
        if msnv and ho_ten:
            # Tạo dòng dữ liệu mới
            new_data = pd.DataFrame([{
                "MSNV": msnv,
                "Họ Tên": ho_ten,
                "Đơn vị": don_vi,
                "Chức danh": chuc_danh,
                "Ngày vào làm": str(ngay_vao),
                "Ghi chú": ghi_chu
            }])
            # Nối vào dữ liệu cũ
            updated_df = pd.concat([df, new_data], ignore_index=True)
            # Ghi đè lên Google Sheets
            conn.update(spreadsheet=st.secrets["gsheets_url"], data=updated_df, worksheet="PVD_Data")
            st.success("✅ Đã lưu dữ liệu lên mạng thành công!")
            st.cache_data.clear() # Xóa cache để hiển thị dữ liệu mới
            st.rerun()
        else:
            st.warning("⚠️ Vui lòng nhập đủ MSNV và Họ Tên.")

# 4. GIAO DIỆN HIỂN THỊ VÀ XUẤT FILE
st.write("### 📊 DANH SÁCH NHÂN SỰ HIỆN TẠI")

# Bộ lọc tìm kiếm
search = st.text_input("🔍 Tìm kiếm nhanh...")
if search:
    display_df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
else:
    display_df = df

st.dataframe(display_df, use_container_width=True, hide_index=True)

# NÚT XUẤT EXCEL
col_down, _ = st.columns([1, 3])
with col_down:
    csv = display_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 XUẤT FILE EXCEL (CSV)",
        data=csv,
        file_name='PVD_Personnel_Report.csv',
        mime='text/csv',
    )

st.markdown("---")
st.caption("Dữ liệu được đồng bộ hóa thời gian thực trên Cloud")
