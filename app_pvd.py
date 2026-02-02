import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date

# 1. CẤU HÌNH
st.set_page_config(page_title="PVD Personnel Pro 2026", layout="wide")

# Hàm lấy tên cột Ngày/Tháng/Thứ
def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/Feb\n{days_vn[d.weekday()]}"

# Khởi tạo dữ liệu
NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", 
         "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong"]

if 'db' not in st.session_state:
    df = pd.DataFrame({'Họ và Tên': NAMES})
    df['Chức danh'] = 'Kỹ sư'
    df['Job Detail'] = ''
    df['Nghỉ Ca Còn Lại'] = 0.0
    for d in range(1, 29):
        df[get_col_name(d)] = ""
    st.session_state.db = df

if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

# 2. LOGIC QUÉT DỮ LIỆU
def scan_balance():
    tet_2026 = [17, 18, 19, 20, 21]
    temp_df = st.session_state.db.copy()
    for index, row in temp_df.iterrows():
        balance = 0.0
        for d in range(1, 29):
            col = get_col_name(d)
            val = row[col]
            d_obj = date(2026, 2, d)
            if val in st.session_state.list_gian:
                if d in tet_2026: balance += 2.0
                elif d_obj.weekday() >= 5: balance += 1.0
                else: balance += 0.5
            elif val == "CA":
                balance -= 1.0
        temp_df.at[index, 'Nghỉ Ca Còn Lại'] = balance
    st.session_state.db = temp_df

# 3. GIAO DIỆN
col_l, col_r = st.columns([1, 5])
with col_l:
    st.image("https://raw.githubusercontent.com/lenghiapvdwell-star/app_pvd/main/424911181_712854060938641_6819448166542158882_n.jpg", width=100)
with col_r:
    st.title("🚢 PVD PERSONNEL MANAGEMENT")

tab_input, tab_edit, tab_scan = st.tabs(["🚀 Nhập Điều Động", "✍️ Chỉnh Sửa Tay", "🔍 Quét & Chốt Tháng"])

with tab_input:
    c1, c2, c3 = st.columns([2, 1, 1.5])
    sel_staff = c1.multiselect("Nhân viên:", NAMES)
    status = c2.selectbox("Trạng thái:", ["Đi Biển", "Nghỉ Ca (CA)", "Làm Xưởng (WS)", "Nghỉ Phép (NP)"])
    if status == "Đi Biển":
        val_to_fill = c2.selectbox("Giàn:", st.session_state.list_gian)
    else:
        val_to_fill = status.split("(")[1].replace(")", "") if "(" in status else status
    
    dates = c3.date_input("Khoảng ngày:", value=(date(2026, 2, 1), date(2026, 2, 7)), 
                          min_value=date(2026, 2, 1), max_value=date(2026, 2, 28))

    if st.button("XÁC NHẬN CẬP NHẬT", type="primary"):
        if isinstance(dates, tuple) and len(dates) == 2:
            for d in range(dates[0].day, dates[1].day + 1):
                col = get_col_name(d)
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col] = val_to_fill
            st.success("Đã cập nhật lịch trình!")
            st.rerun()

with tab_edit:
    st.subheader("✍️ Chỉnh sửa thông tin bổ sung")
    # Lấy danh sách cột hiện có để tránh lỗi KeyError
    cols_to_edit = [c for c in ['Họ và Tên', 'Chức danh', 'Job Detail', 'Nghỉ Ca Còn Lại'] if c in st.session_state.db.columns]
    
    edited_data = st.data_editor(
        st.session_state.db[cols_to_edit],
        hide_index=True, use_container_width=True
    )
    if st.button("LƯU THAY ĐỔI"):
        st.session_state.db.update(edited_data)
        st.success("Đã lưu chỉnh sửa tay!")

with tab_scan:
    st.info("Hệ thống sẽ tính: Biển (T2-T6:+0.5, T7-CN:+1, Tết:+2) | CA:-1 | WS & NP: 0")
    if st.button("🚀 QUÉT & TÍNH TOÁN"):
        scan_balance()
        st.balloons()
        st.rerun()

# 4. HIỂN THỊ BẢNG TỔNG
st.markdown("---")
def style_cells(val):
    if val in st.session_state.list_gian: return 'background-color: #00558F; color: white; text-align: center;'
    if val == "CA": return 'background-color: #E74C3C; color: white; text-align: center;'
    if val == "WS": return 'background-color: #F1C40F; color: black; text-align: center;'
    if val == "NP": return 'background-color: #9B59B6; color: white; text-align: center;'
    return 'text-align: center;'

# Cấu trúc hiển thị
all_cols = st.session_state.db.columns.tolist()
display_order = ['Họ và Tên', 'Nghỉ Ca Còn Lại', 'Job Detail'] + [c for c in all_cols if "/Feb" in c]

st.subheader("📅 Bảng Tổng Hợp Tháng 02/2026")
st.dataframe(
    st.session_state.db[display_order].style.applymap(style_cells, subset=[c for c in display_order if "/Feb" in c]),
    use_container_width=True, height=500
)

# 5. XUẤT EXCEL
output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    st.session_state.db.to_excel(writer, index=False)
st.download_button("📥 TẢI BÁO CÁO EXCEL", data=output.getvalue(), file_name="PVD_Report.xlsx")
