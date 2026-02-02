import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="PVD Personnel 2026", layout="wide")

# Hàm tạo tên cột an toàn
def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    # Trả về tên cột dạng "01/Feb T2" (Dùng 1 dòng để tránh lỗi Key khi Pandas xử lý xuống dòng)
    return f"{day:02d}/Feb {days_vn[d.weekday()]}"

# 2. KHỞI TẠO DỮ LIỆU
NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", 
         "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong",
         "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia"]

if 'db' not in st.session_state:
    df = pd.DataFrame({'Họ và Tên': NAMES})
    df['Chức danh'] = 'Kỹ sư'
    df['Nghỉ Ca Còn Lại'] = 0.0
    df['Job Detail'] = ''
    # Khởi tạo 28 ngày trống
    for d in range(1, 29):
        df[get_col_name(d)] = ""
    st.session_state.db = df

if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

# 3. LOGIC QUÉT DỮ LIỆU
def scan_balance():
    tet_2026 = [17, 18, 19, 20, 21]
    df = st.session_state.db.copy()
    for index, row in df.iterrows():
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
        df.at[index, 'Nghỉ Ca Còn Lại'] = balance
    st.session_state.db = df

# 4. GIAO DIỆN
col_logo, col_text = st.columns([1, 5])
with col_logo:
    st.image("https://raw.githubusercontent.com/lenghiapvdwell-star/app_pvd/main/424911181_712854060938641_6819448166542158882_n.jpg", width=110)
with col_text:
    st.title("🚢 PVD PERSONNEL MANAGEMENT")

tab_input, tab_edit, tab_scan = st.tabs(["🚀 Nhập Điều Động", "✍️ Chỉnh Sửa Tay", "🔍 Quét & Chốt Tháng"])

with tab_input:
    c1, c2, c3 = st.columns([2, 1, 1.5])
    sel_staff = c1.multiselect("Nhân viên:", NAMES)
    status = c2.selectbox("Trạng thái:", ["Đi Biển", "Nghỉ Ca (CA)", "Làm Xưởng (WS)", "Nghỉ Phép (NP)"])
    
    val_to_fill = ""
    if status == "Đi Biển":
        val_to_fill = c2.selectbox("Chọn Giàn:", st.session_state.list_gian)
    else:
        # Lấy ký hiệu trong ngoặc (CA, WS, NP)
        mapping = {"Nghỉ Ca (CA)": "CA", "Làm Xưởng (WS)": "WS", "Nghỉ Phép (NP)": "NP"}
        val_to_fill = mapping.get(status, status)
    
    dates = c3.date_input("Chọn khoảng ngày:", value=(date(2026, 2, 1), date(2026, 2, 7)), 
                          min_value=date(2026, 2, 1), max_value=date(2026, 2, 28))

    if st.button("XÁC NHẬN CẬP NHẬT", type="primary"):
        if isinstance(dates, tuple) and len(dates) == 2:
            start_d, end_d = dates[0].day, dates[1].day
            for d in range(start_d, end_d + 1):
                col = get_col_name(d)
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col] = val_to_fill
            st.success("Đã cập nhật lịch trình!")
            st.rerun()

with tab_edit:
    st.subheader("✍️ Chỉnh sửa bổ sung")
    # Chỉ lấy các cột hồ sơ để chỉnh sửa tay
    edit_cols = ['Họ và Tên', 'Chức danh', 'Nghỉ Ca Còn Lại', 'Job Detail']
    existing_edit_cols = [c for c in edit_cols if c in st.session_state.db.columns]
    
    edited_df = st.data_editor(st.session_state.db[existing_edit_cols], hide_index=True, use_container_width=True)
    
    if st.button("LƯU THAY ĐỔI TAY"):
        st.session_state.db.update(edited_df)
        st.success("Đã lưu!")

with tab_scan:
    st.info("Nhấn nút để tính: Biển (T2-T6:+0.5, T7-CN:+1, Tết:+2) | CA:-1 | WS & NP: 0")
    if st.button("🚀 QUÉT & CHỐT SỐ DƯ"):
        scan_balance()
        st.balloons()
        st.rerun()

# 5. HIỂN THỊ BẢNG TỔNG
st.markdown("---")
st.subheader("📅 Bảng Tổng Hợp Tháng 02/2026")

# Tự động lấy các cột ngày tháng hiện có trong DB
date_cols = [c for c in st.session_state.db.columns if "/Feb" in c]
# Cột hồ sơ hiển thị
info_cols = ['Họ và Tên', 'Nghỉ Ca Còn Lại', 'Job Detail']
# Tổng hợp cột hiển thị (Chỉ lấy những cột thực sự tồn tại để tránh KeyError)
display_order = [c for c in info_cols if c in st.session_state.db.columns] + date_cols

def style_cells(val):
    if val in st.session_state.list_gian: return 'background-color: #00558F; color: white;'
    if val == "CA": return 'background-color: #E74C3C; color: white;'
    if val == "WS": return 'background-color: #F1C40F; color: black;'
    if val == "NP": return 'background-color: #9B59B6; color: white;'
    return ''

# Render DataFrame
try:
    st.dataframe(
        st.session_state.db[display_order].style.applymap(style_cells, subset=date_cols),
        use_container_width=True, height=550
    )
except Exception as e:
    st.error(f"Lỗi hiển thị: {e}. Vui lòng nhấn F5 hoặc Refresh lại trang.")

# 6. XUẤT EXCEL
output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    st.session_state.db.to_excel(writer, index=False)
st.download_button("📥 XUẤT EXCEL", data=output.getvalue(), file_name="PVD_Report_2026.xlsx")
