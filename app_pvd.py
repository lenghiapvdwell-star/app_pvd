import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

# Cố định tháng 02/2026
YEAR, MONTH = 2026, 2
DATE_COLS = [f"{d:02d}/02" for d in range(1, 29)]
HOLIDAYS = [15, 16, 17, 18, 19]

# --- 2. DANH SÁCH 64 NHÂN SỰ ---
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

# --- 3. KẾT NỐI & KHỞI TẠO ---
conn = st.connection("gsheets", type=GSheetsConnection)

if 'db' not in st.session_state:
    try:
        df_load = conn.read(worksheet="Sheet1")
        if df_load is not None and not df_load.empty:
            st.session_state.db = df_load
        else: raise Exception
    except:
        df_init = pd.DataFrame({'STT': range(1, 65), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': ''})
        for c in DATE_COLS: df_init[c] = ""
        st.session_state.db = df_init

if 'gians' not in st.session_state:
    st.session_state.gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

# --- 4. LOGIC TÍNH QUỸ CA ---
def update_ca_logic(df):
    gians = st.session_state.gians
    def calc_row(row):
        total = 0.0
        for col in DATE_COLS:
            if col in row.index:
                val = str(row[col]).strip()
                if not val or val.lower() in ["nan", "none", ""]: continue
                day_num = int(col.split('/')[0])
                dt = date(YEAR, MONTH, day_num)
                is_weekend = dt.weekday() >= 5
                is_holiday = day_num in HOLIDAYS
                if val in gians:
                    if is_holiday: total += 2.0
                    elif is_weekend: total += 1.0
                    else: total += 0.5
                elif val.upper() == "CA":
                    if not is_weekend and not is_holiday: total -= 1.0
        return total
    df['Nghỉ Ca Còn Lại'] = df.apply(calc_row, axis=1)
    return df

# --- 5. GIAO DIỆN ---
c_logo, c_title = st.columns([1.5, 5])
with c_logo:
    if os.path.exists("logo_pvd.png"): st.image("logo_pvd.png", width=180)
    else: st.write("### PVD LOGO")
with c_title:
    st.markdown('<h1 style="color: #00f2ff; margin-top: 15px;">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# TÍNH TOÁN TRƯỚC KHI HIỂN THỊ
st.session_state.db = update_ca_logic(st.session_state.db)

tabs = st.tabs(["🚀 ĐIỀU ĐỘNG & CLOUD", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN"])

with tabs[0]:
    # Khu vực nút bấm quan trọng
    c_btn1, c_btn2, c_btn3 = st.columns([1, 1, 1])
    with c_btn1:
        # NÚT UPLOAD GOOGLE SHEETS
        if st.button("📤 ĐỒNG BỘ LÊN CLOUD (LƯU GG SHEETS)", use_container_width=True, type="primary"):
            try:
                conn.update(worksheet="Sheet1", data=st.session_state.db)
                st.success("✅ Đã gửi dữ liệu lên Google Sheets thành công!")
            except:
                st.error("❌ Lỗi! Hãy kiểm tra kết nối hoặc tên Tab 'Sheet1'.")
    
    with c_btn2:
        # XUẤT EXCEL
        buffer = io.BytesIO()
        st.session_state.db.to_excel(buffer, index=False)
        st.download_button("📥 TẢI FILE EXCEL (.xlsx)", data=buffer.getvalue(), file_name="PVD_Export.xlsx", use_container_width=True)

    # FORM NHẬP LIỆU (CHỐNG NHẢY TRANG)
    with st.form("input_form", clear_on_submit=True):
        st.write("### ➕ NHẬP DỮ LIỆU NHANH")
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        f_staff = c1.multiselect("Nhân viên:", st.session_state.db['Họ và Tên'].tolist())
        f_status = c2.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm"])
        f_gian = c3.selectbox("Chọn Giàn:", st.session_state.gians) if f_status == "Đi Biển" else f_status
        f_date = c4.date_input("Thời gian:", value=(date(YEAR, MONTH, 1), date(YEAR, MONTH, 2)))
        
        if st.form_submit_button("✅ CẬP NHẬT VÀO BẢNG TẠM", use_container_width=True):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                for d in range(f_date[0].day, f_date[1].day + 1):
                    col_name = f"{d:02d}/02"
                    if col_name in st.session_state.db.columns:
                        st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), col_name] = f_gian
                st.rerun()

    # BẢNG HIỂN THỊ CHÍNH
    cols = ['STT', 'Họ và Tên', 'Nghỉ Ca Còn Lại'] + [c for c in st.session_state.db.columns if c not in ['STT', 'Họ và Tên', 'Nghỉ Ca Còn Lại']]
    edited_df = st.data_editor(
        st.session_state.db[cols],
        column_config={
            "Nghỉ Ca Còn Lại": st.column_config.NumberColumn("Quỹ CA", format="%.1f", disabled=True),
            "Họ và Tên": st.column_config.TextColumn(pinned=True, width="medium")
        },
        use_container_width=True, height=550
    )
    # Ghi nhận thay đổi từ việc sửa trực tiếp trên bảng
    if not edited_df.equals(st.session_state.db[cols]):
        st.session_state.db.update(edited_df)

with tabs[1]:
    new_gians = st.data_editor(pd.DataFrame({"Giàn": st.session_state.gians}), num_rows="dynamic", use_container_width=True)
    if st.button("Lưu danh sách Giàn"):
        st.session_state.gians = new_gians["Giàn"].dropna().tolist()

with tabs[2]:
    staff_info = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail']
    new_staff = st.data_editor(st.session_state.db[staff_info], num_rows="dynamic", use_container_width=True)
    if st.button("Lưu thông tin Nhân sự"):
        st.session_state.db.update(new_staff)

# CUỘN NGANG
components.html("""
<script>
    setTimeout(() => {
        const el = window.parent.document.querySelector('div[data-testid="stDataEditor"] [role="grid"]');
        if (el) {
            let isDown = false; let startX, scrollLeft;
            el.addEventListener('mousedown', (e) => { isDown = true; startX = e.pageX - el.offsetLeft; scrollLeft = el.scrollLeft; });
            el.addEventListener('mouseleave', () => { isDown = false; });
            el.addEventListener('mouseup', () => { isDown = false; });
            el.addEventListener('mousemove', (e) => { if(!isDown) return; e.preventDefault(); const x = e.pageX - el.offsetLeft; el.scrollLeft = scrollLeft - (x - startX) * 2; });
        }
    }, 1000);
</script>
""", height=0)
