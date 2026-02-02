import streamlit as st
import pandas as pd

st.set_page_config(page_title="PVD Management 2026", layout="wide", page_icon="🚢")

st.title("🚢 PVD PERSONNEL MANAGEMENT 2026")
st.markdown("---")

# Kiểm tra kết nối dữ liệu
if "sheet_url" not in st.secrets:
    st.error("❌ Bạn chưa lưu 'sheet_url' vào mục Secrets!")
    st.stop()

try:
    # Đọc dữ liệu từ link CSV đã xuất bản
    # Thêm tham số để ép Google cập nhật dữ liệu mới liên tục
    df = pd.read_csv(st.secrets["sheet_url"])

    # 1. PHẦN TRA CỨU
    search = st.text_input("🔍 Tìm kiếm nhân viên (Tên, MSNV, Đơn vị...):")
    if search:
        df_display = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
    else:
        df_display = df

    # 2. HIỂN THỊ BẢNG DỮ LIỆU
    st.write(f"### 📊 Danh sách nhân sự ({len(df_display)} người)")
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # 3. NÚT XUẤT EXCEL
    st.markdown("---")
    csv_data = df_display.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 TẢI FILE EXCEL BÁO CÁO",
        data=csv_data,
        file_name='PVD_Personnel_Report.csv',
        mime='text/csv'
    )

except Exception as e:
    st.warning("⚠️ Đang chờ dữ liệu từ Google Sheets...")
    st.info("Hãy đảm bảo bạn đã nhấn 'Xuất bản' (Publish) trên Google Sheets.")
