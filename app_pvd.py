import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="PVD Personnel Pro", layout="wide")

# Hàm tạo tên cột
def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/Feb {days_vn[d.weekday()]}"

# 2. KHỞI TẠO BỘ NHỚ
if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", 
         "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong",
         "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia"]

if 'db' not in st.session_state:
    df = pd.DataFrame({'Họ và Tên': NAMES})
    df['Chức danh'] = 'Kỹ sư'
    df['Nghỉ Ca Còn Lại'] = 0.0
    df['Job Detail'] = ''
    for d in range(1, 29):
        df[get_col_name(d)] = "" # Khởi tạo trống hoàn toàn
    st.session_state.db = df

# 3. LOGIC QUÉT DỮ LIỆU
def scan_balance():
    tet_2026 = [17, 18, 19, 20, 21]
    df_tmp = st.session_state.db.copy()
    for index, row in df_tmp.iterrows():
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
        df_tmp.at[index, 'Nghỉ Ca Còn Lại'] = balance
    st.session_state.db = df_tmp

# 4. GIAO DIỆN
col_logo, col_text = st.columns([1, 5])
with col_logo:
    st.image("https://raw.githubusercontent.com/lenghiapvdwell-star/app_pvd/main/424911181_712854060938641_6819448166542158882_n.jpg", width=100)
with col_text:
    st.title("🚢 PVD PERSONNEL MANAGEMENT")

tab_input, tab_edit, tab_scan, tab_rig = st.tabs(["🚀 Nhập Điều Động", "✍️ Chỉnh Sửa Tay", "🔍 Quét & Chốt Tháng", "🏗️ Quản Lý Giàn"])

with tab_input:
    c1, c2, c3 = st.columns([2, 1, 1.5])
    sel_staff = c1.multiselect("Nhân viên:", NAMES)
    status = c2.selectbox("Trạng thái:", ["Đi Biển", "Nghỉ Ca (CA)", "Làm Xưởng (WS)", "Nghỉ Phép (NP)"])
    
    val_to_fill = ""
    if status == "Đi Biển":
        val_to_fill = c2.selectbox("Chọn Giàn đang có:", st.session_state.list_gian)
    else:
        mapping = {"Nghỉ Ca (CA)": "CA", "Làm Xưởng (WS)": "WS", "Nghỉ Phép (NP)": "NP"}
        val_to_fill = mapping.get(status, status)
    
    dates = c3.date_input("Khoảng ngày:", value=(date(2026, 2, 1), date(2026, 2, 7)), 
                          min_value=date(2026, 2, 1), max_value=date(2026, 2, 28))

    if st.button("XÁC NHẬN CẬP NHẬT", type="primary"):
        if isinstance(dates, tuple) and len(dates) == 2:
            for d in range(dates[0].day, dates[1].day + 1):
                col = get_col_name(d)
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col] = val_to_fill
            st.rerun()

with tab_edit:
    st.subheader("✍️ Chỉnh sửa bổ sung (Chức danh, Job Detail, Số dư)")
    edit_cols = ['Họ và Tên', 'Chức danh', 'Nghỉ Ca Còn Lại', 'Job Detail']
    edited_df = st.data_editor(st.session_state.db[edit_cols], hide_index=True, use_container_width=True)
    if st.button("LƯU THAY ĐỔI TAY"):
        st.session_state.db.update(edited_df)
        st.success("Đã lưu!")

with tab_scan:
    if st.button("🚀 QUÉT & TÍNH TOÁN SỐ DƯ CUỐI THÁNG"):
        scan_balance()
        st.balloons()
        st.rerun()

with tab_rig:
    st.subheader("🏗️ Cấu trúc đội giàn khoan")
    c_rig1, c_rig2 = st.columns(2)
    with c_rig1:
        new_rig = st.text_input("Nhập tên giàn mới:")
        if st.button("Thêm Giàn"):
            if new_rig and new_rig not in st.session_state.list_gian:
                st.session_state.list_gian.append(new_rig)
                st.success(f"Đã thêm giàn {new_rig}")
                st.rerun()
    with c_rig2:
        del_rig = st.selectbox("Chọn giàn cần xóa (không còn ở VN):", st.session_state.list_gian)
        if st.button("Xóa Giàn"):
            st.session_state.list_gian.remove(del_rig)
            st.warning(f"Đã xóa giàn {del_rig}")
            st.rerun()

# 5. HIỂN THỊ BẢNG
st.markdown("---")
date_cols = [c for c in st.session_state.db.columns if "/Feb" in c]
display_order = ['Họ và Tên', 'Nghỉ Ca Còn Lại', 'Job Detail'] + date_cols

def style_cells(val):
    if not val or val == "": return ""
    if val in st.session_state.list_gian: return 'background-color: #00558F; color: white; font-weight: bold;'
    if val == "CA": return 'background-color: #E74C3C; color: white; font-weight: bold;'
    if val == "WS": return 'background-color: #F1C40F; color: black;'
    if val == "NP": return 'background-color: #9B59B6; color: white;'
    return ''

st.dataframe(
    st.session_state.db[display_order].style.applymap(style_cells, subset=date_cols),
    use_container_width=True, height=550
)

# 6. XUẤT EXCEL (Cần pip install xlsxwriter)
try:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        st.session_state.db.to_excel(writer, index=False)
    st.download_button("📥 XUẤT FILE EXCEL", data=output.getvalue(), file_name="PVD_Report.xlsx")
except Exception as e:
    st.error("Cần cài đặt xlsxwriter để xuất file. Vui lòng thêm xlsxwriter vào file requirements.txt")
