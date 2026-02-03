import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

# Thiết lập thời gian cố định cho tháng 02/2026 như bạn yêu cầu
YEAR = 2026
MONTH = 2
DATE_COLS = [f"{d:02d}/02" for d in range(1, 29)]
HOLIDAYS = [15, 16, 17, 18, 19]

# --- 2. DANH SÁCH 64 NHÂN SỰ MẶC ĐỊNH ---
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

# --- 3. KHỞI TẠO DỮ LIỆU TRONG SESSION STATE (ĐỂ KHÔNG MẤT KHI RESET) ---
conn = st.connection("gsheets", type=GSheetsConnection)

if 'db' not in st.session_state:
    try:
        # Ưu tiên đọc từ Google Sheets nếu đã có dữ liệu
        df_load = conn.read(worksheet="Sheet1")
        if df_load is not None and not df_load.empty:
            st.session_state.db = df_load
        else: raise Exception
    except:
        # Nếu không có, tạo mới từ danh sách 64 người
        df_init = pd.DataFrame({
            'STT': range(1, 65), 'Họ và Tên': NAMES_64, 
            'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': ''
        })
        for c in DATE_COLS: df_init[c] = ""
        st.session_state.db = df_init

if 'gians' not in st.session_state:
    st.session_state.gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

# --- 4. HÀM TÍNH TOÁN LOGIC ---
def apply_pvd_logic(df):
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

# Luôn tính toán lại quỹ CA trước khi hiển thị
st.session_state.db = apply_pvd_logic(st.session_state.db)

# --- 5. GIAO DIỆN (LOGO TO 1.5 LẦN) ---
col_logo, col_title = st.columns([1.5, 5])
with col_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=180)
    else:
        st.write("### PVD LOGO")

with col_title:
    st.markdown('<h1 style="color: #00f2ff; margin-top: 15px;">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "🏗️ QUẢN LÝ GIÀN", "👤 NHÂN VIÊN", "⚙️ HỆ THỐNG"])

# --- TAB 1: ĐIỀU ĐỘNG ---
with tabs[0]:
    # Sử dụng Form để ngăn việc reset trang khi đang chọn
    with st.form("input_form"):
        st.write("### ➕ NHẬP DỮ LIỆU ĐIỀU ĐỘNG")
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        f_staff = c1.multiselect("Nhân viên:", st.session_state.db['Họ và Tên'].tolist())
        f_status = c2.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm"])
        f_gian = c3.selectbox("Chọn Giàn:", st.session_state.gians) if f_status == "Đi Biển" else f_status
        f_date = c4.date_input("Thời gian:", value=(date(YEAR, MONTH, 1), date(YEAR, MONTH, 2)))
        
        submit_btn = st.form_submit_button("✅ XÁC NHẬN VÀO BẢNG", use_container_width=True)
        
        if submit_btn:
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                for d in range(f_date[0].day, f_date[1].day + 1):
                    col_name = f"{d:02d}/02"
                    if col_name in st.session_state.db.columns:
                        st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), col_name] = f_gian
                st.rerun()

    # Hiển thị bảng dữ liệu
    cols_display = ['STT', 'Họ và Tên', 'Nghỉ Ca Còn Lại'] + [c for c in st.session_state.db.columns if c not in ['STT', 'Họ và Tên', 'Nghỉ Ca Còn Lại']]
    
    edited_df = st.data_editor(
        st.session_state.db[cols_display],
        column_config={
            "Nghỉ Ca Còn Lại": st.column_config.NumberColumn("Quỹ CA", format="%.1f", disabled=True),
            "Họ và Tên": st.column_config.TextColumn(pinned=True, width="medium")
        },
        use_container_width=True, height=600
    )
    
    # Cập nhật từ bảng vào session state
    if not edited_df.equals(st.session_state.db[cols_display]):
        st.session_state.db.update(edited_df)

# --- TAB 2: QUẢN LÝ GIÀN ---
with tabs[1]:
    st.subheader("🏗️ Cấu hình danh sách Giàn")
    df_g = pd.DataFrame({"Tên Giàn": st.session_state.gians})
    new_gians = st.data_editor(df_g, num_rows="dynamic", use_container_width=True)
    if st.button("Lưu danh sách Giàn"):
        st.session_state.gians = new_gians["Tên Giàn"].dropna().tolist()
        st.success("Đã cập nhật!")

# --- TAB 3: NHÂN VIÊN ---
with tabs[2]:
    st.subheader("👤 Quản lý 64 nhân sự")
    staff_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail']
    df_staff_edit = st.data_editor(st.session_state.db[staff_cols], num_rows="dynamic", use_container_width=True)
    if st.button("Cập nhật thông tin nhân sự"):
        st.session_state.db.update(df_staff_edit)
        st.success("Đã lưu!")

# --- TAB 4: HỆ THỐNG (TAB QUAN TRỌNG ĐỂ LƯU) ---
with tabs[3]:
    st.header("⚙️ QUẢN TRỊ HỆ THỐNG")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("☁️ Google Sheets Cloud")
        sheet_name = st.text_input("Tên Tab trên Google Sheets:", value="Sheet1")
        if st.button("💾 ĐỒNG BỘ LÊN GOOGLE SHEETS", use_container_width=True, type="primary"):
            try:
                conn.update(worksheet=sheet_name, data=st.session_state.db)
                st.success(f"Đã lưu thành công lên Tab '{sheet_name}'!")
            except Exception as e:
                st.error("Lỗi kết nối! Hãy kiểm tra tên Tab trên Google Sheets có đúng là 'Sheet1' không.")

    with col2:
        st.subheader("📥 Xuất dữ liệu cục bộ")
        buffer = io.BytesIO()
        st.session_state.db.to_excel(buffer, index=False)
        st.download_button(
            label="📥 TẢI FILE EXCEL (.xlsx)",
            data=buffer.getvalue(),
            file_name=f"PVD_Data_{datetime.now().strftime('%d%m%Y')}.xlsx",
            use_container_width=True
        )

# Script cuộn ngang mượt mà
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
