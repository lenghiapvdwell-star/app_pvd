import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH & THỜI GIAN ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

now = datetime.now()
current_month_year = now.strftime("%m_%Y") 
month_days = calendar.monthrange(now.year, now.month)[1]
DATE_COLS = [f"{d:02d}/{now.strftime('%m')}" for d in range(1, month_days + 1)]
HOLIDAYS = [15, 16, 17, 18, 19]

# --- 2. DANH SÁCH 64 NHÂN SỰ MẶC ĐỊNH ---
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

# --- 3. KHỞI TẠO KẾT NỐI & DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

if 'gians' not in st.session_state:
    st.session_state.gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

if 'db' not in st.session_state:
    try:
        # Thử đọc tab tháng hiện tại
        df_load = conn.read(worksheet=current_month_year)
        if df_load is None or df_load.empty:
            raise ValueError
        st.session_state.db = df_load
    except:
        # Nếu lỗi hoặc không thấy tab, tạo mới 64 người
        df_init = pd.DataFrame({
            'STT': range(1, 65), 
            'Họ và Tên': NAMES_64, 
            'Công ty': 'PVDWS', 
            'Chức danh': 'Kỹ sư', 
            'Job Detail': ''
        })
        for c in DATE_COLS: df_init[c] = ""
        st.session_state.db = df_init

if 'v_key' not in st.session_state:
    st.session_state.v_key = 0

# --- 4. HÀM TÍNH TOÁN QUỸ CA ---
def apply_pvd_logic(df):
    gians = st.session_state.gians
    def calc_row(row):
        total = 0.0
        for col in DATE_COLS:
            if col in row.index:
                val = str(row[col]).strip()
                if not val or val.lower() in ["nan", "none", ""]: continue
                day_num = int(col.split('/')[0])
                dt = date(now.year, now.month, day_num)
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

st.session_state.db = apply_pvd_logic(st.session_state.db)

# --- 5. GIAO DIỆN ---
c_logo, c_title = st.columns([1.5, 5])
with c_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=180)
    else:
        st.write("### PVD LOGO")

with c_title:
    header_html = f'''<h1 style="color: #00f2ff; margin-top: 15px; font-family: sans-serif;">PVD WELL SERVICES MANAGEMENT - {now.strftime("%m/%Y")}</h1>'''
    st.markdown(header_html, unsafe_allow_html=True)

tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "🏗️ QUẢN LÝ GIÀN", "👤 NHÂN VIÊN", "⚙️ HỆ THỐNG"])

# --- TAB 1: ĐIỀU ĐỘNG ---
with tabs[0]:
    with st.expander("➕ NHẬP DỮ LIỆU NHANH", expanded=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        f_staff = c1.multiselect("Nhân viên:", st.session_state.db['Họ và Tên'].tolist())
        f_status = c2.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm"])
        f_gian = c3.selectbox("Chọn Giàn:", st.session_state.gians) if f_status == "Đi Biển" else f_status
        f_date = c4.date_input("Thời gian:", value=(date(now.year, now.month, 1), date(now.year, now.month, 2)))
        
        if st.button("✅ CẬP NHẬT VÀO BẢNG", use_container_width=True):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                for d in range(f_date[0].day, f_date[1].day + 1):
                    col_name = f"{d:02d}/{now.strftime('%m')}"
                    if col_name in st.session_state.db.columns:
                        st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), col_name] = f_gian
                st.session_state.v_key += 1
                st.rerun()

    cols = ['STT', 'Họ và Tên', 'Nghỉ Ca Còn Lại'] + [c for c in st.session_state.db.columns if c not in ['STT', 'Họ và Tên', 'Nghỉ Ca Còn Lại']]
    edited_df = st.data_editor(st.session_state.db[cols], column_config={"Nghỉ Ca Còn Lại": st.column_config.NumberColumn("Quỹ CA", format="%.1f", disabled=True), "Họ và Tên": st.column_config.TextColumn(pinned=True)}, use_container_width=True, height=550, key=f"pvd_ed_{st.session_state.v_key}")
    if not edited_df.equals(st.session_state.db[cols]):
        st.session_state.db.update(edited_df)
        st.rerun()

# --- TAB 2: QUẢN LÝ GIÀN ---
with tabs[1]:
    st.subheader("🏗️ Cấu hình Giàn khoan")
    df_g = pd.DataFrame({"Tên Giàn": st.session_state.gians})
    new_gians = st.data_editor(df_g, num_rows="dynamic", use_container_width=True)
    if st.button("Lưu cấu hình Giàn"):
        st.session_state.gians = new_gians["Tên Giàn"].dropna().tolist()
        st.success("Đã cập nhật danh sách giàn!")

# --- TAB 3: NHÂN VIÊN ---
with tabs[2]:
    st.subheader("👤 Quản lý nhân sự")
    staff_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail']
    df_staff_edit = st.data_editor(st.session_state.db[staff_cols], num_rows="dynamic", use_container_width=True)
    if st.button("Cập nhật danh sách Nhân viên"):
        st.session_state.db.update(df_staff_edit)
        st.success("Đã lưu danh sách!")

# --- TAB 4: HỆ THỐNG ---
with tabs[3]:
    st.subheader("⚙️ Lưu trữ Google Sheets")
    target_sheet = st.text_input("Tên Tab muốn lưu (Ví dụ: Sheet1 hoặc 02_2026):", value=current_month_year)
    st.warning("Lưu ý: Bạn phải tạo sẵn Tab này trên Google Sheets trước khi bấm lưu.")
    
    if st.button("💾 LƯU LÊN CLOUD", use_container_width=True):
        try:
            conn.update(worksheet=target_sheet, data=st.session_state.db)
            st.success(f"Đã lưu thành công vào tab {target_sheet}!")
        except Exception as e:
            st.error(f"Lỗi: Không tìm thấy tab '{target_sheet}'. Hãy tạo tab mới trên Google Sheets với tên này.")

    buffer = io.BytesIO()
    st.session_state.db.to_excel(buffer, index=False)
    st.download_button("📥 TẢI EXCEL", data=buffer.getvalue(), file_name=f"PVD_{current_month_year}.xlsx", use_container_width=True)

# Script cuộn ngang
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
