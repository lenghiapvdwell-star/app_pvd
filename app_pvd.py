import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date

# 1. CẤU HÌNH
st.set_page_config(page_title="PVD Crew Management 2026", layout="wide")

# Khởi tạo bộ nhớ
if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

# Danh sách nhân sự
NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong"]

def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/Feb\n{days_vn[d.weekday()]}"

# Khởi tạo Database
if 'db' not in st.session_state:
    df = pd.DataFrame({'Họ và Tên': NAMES})
    df['Chức danh'] = 'Kỹ sư'
    df['Job Detail'] = ''
    df['Nghỉ Ca Còn Lại'] = 0.0 # Cột này có thể chỉnh tay
    for d in range(1, 29):
        df[get_col_name(d)] = "" # Xóa sạch chữ CA mặc định
    st.session_state.db = df

# 2. LOGIC TÍNH TOÁN
def scan_and_calculate_balance():
    tet_2026 = [17, 18, 19, 20, 21]
    for index, row in st.session_state.db.iterrows():
        new_balance = 0.0
        for d in range(1, 29):
            col = get_col_name(d)
            val = row[col]
            d_obj = date(2026, 2, d)
            
            if val in st.session_state.list_gian: # Đi biển
                if d in tet_2026: new_balance += 2.0
                elif d_obj.weekday() >= 5: new_balance += 1.0
                else: new_balance += 0.5
            elif val == "CA": # Nghỉ ca
                new_balance -= 1.0
            # WS và NP không làm thay đổi quỹ nghỉ ca tích lũy (hoặc theo quy định cty bạn)
        
        st.session_state.db.at[index, 'Nghỉ Ca Còn Lại'] = new_balance

# 3. GIAO DIỆN
st.sidebar.image("https://raw.githubusercontent.com/lenghiapvdwell-star/app_pvd/main/424911181_712854060938641_6819448166542158882_n.jpg", width=150)
st.title("🚢 PVD PERSONNEL MANAGEMENT")

tab_work, tab_edit, tab_scan = st.tabs(["🚀 Nhập Điều Động", "✍️ Chỉnh Sửa Tay", "🔍 Quét & Chốt Tháng"])

with tab_work:
    c1, c2, c3 = st.columns([2, 1, 1.5])
    with c1: sel_staff = st.multiselect("Nhân viên:", NAMES)
    with c2:
        status = st.selectbox("Trạng thái:", ["Đi Biển", "Nghỉ Ca (CA)", "Làm Xưởng (WS)", "Nghỉ Phép (NP)"])
        val = st.selectbox("Giàn:", st.session_state.list_gian) if status == "Đi Biển" else status.split("(")[1].replace(")", "")
    with c3:
        dates = st.date_input("Khoảng ngày:", value=(date(2026, 2, 1), date(2026, 2, 7)), min_value=date(2026, 2, 1), max_value=date(2026, 2, 28))

    if st.button("XÁC NHẬN CẬP NHẬT", type="primary"):
        if isinstance(dates, tuple) and len(dates) == 2:
            for d in range(dates[0].day, dates[1].day + 1):
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), get_col_name(d)] = val
            st.success("Đã cập nhật dữ liệu lịch!")
            st.rerun()

with tab_edit:
    st.subheader("✍️ Chỉnh sửa thông tin bổ sung")
    edited_df = st.data_editor(
        st.session_state.db[['Họ và Tên', 'Chức danh', 'Job Detail', 'Nghỉ Ca Còn Lại']],
        hide_index=True,
        use_container_width=True
    )
    if st.button("LƯU THAY ĐỔI TAY"):
        st.session_state.db.update(edited_df)
        st.success("Đã lưu các thay đổi chỉnh tay!")

with tab_scan:
    st.info("Nhấn nút dưới đây để hệ thống tự động tính toán 'Nghỉ Ca Còn Lại' dựa trên lịch tháng này.")
    if st.button("🚀 QUÉT & TÍNH TOÁN CUỐI THÁNG"):
        scan_and_calculate_balance()
        st.balloons()
        st.success("Đã tính toán xong dựa trên lịch trình thực tế!")
        st.rerun()

# 4. HIỂN THỊ BẢNG TỔNG
st.markdown("---")
def style_cells(val):
    if val in st.session_state.list_gian: return 'background-color: #00558F; color: white;'
    if val == "CA": return 'background-color: #E74C3C; color: white;'
    if val == "WS": return 'background-color: #F1C40F; color: black;'
    if val == "NP": return 'background-color: #9B59B6; color: white;'
    return ''

# Sắp xếp hiển thị: Tên, Chức danh, Nghỉ Ca Còn Lại, Job Detail rồi đến các ngày
cols = st.session_state.db.columns.tolist()
display_order = ['Họ và Tên', 'Nghỉ Ca Còn Lại', 'Job Detail'] + cols[4:]

st.subheader("📅 Bảng Tổng Hợp Tháng 02/2026")
st.dataframe(
    st.session_state.db[display_order].style.applymap(style_cells, subset=cols[4:]),
    use_container_width=True, height=500
)

# 5. XUẤT EXCEL
output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    st.session_state.db.to_excel(writer, index=False)
st.download_button("📥 XUẤT FILE BÁO CÁO EXCEL", data=output.getvalue(), file_name="PVD_Monthly_Report.xlsx")
