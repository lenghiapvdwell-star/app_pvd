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
current_month_year = now.strftime("%m_%Y") # Tên Sheet: 02_2026, 03_2026...
month_days = calendar.monthrange(now.year, now.month)[1]
DATE_COLS = [f"{d:02d}/{now.strftime('%m')}" for d in range(1, month_days + 1)]

# --- 2. KHỞI TẠO KẾT NỐI ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Tải danh sách Giàn
if 'gians' not in st.session_state:
    try:
        df_gians = conn.read(worksheet="Config_Gians")
        st.session_state.gians = df_gians['TenGian'].tolist()
    except:
        st.session_state.gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

# Tải dữ liệu chính theo tháng
if 'db' not in st.session_state:
    try:
        df_load = conn.read(worksheet=current_month_year)
        if df_load is None or df_load.empty: raise Exception
        st.session_state.db = df_load
    except:
        # Nếu chưa có tháng mới, lấy danh sách nhân sự từ Config_Staff
        try:
            df_staff = conn.read(worksheet="Config_Staff")
            df_init = df_staff.copy()
        except:
            NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang"]
            df_init = pd.DataFrame({'STT': range(1, len(NAMES_64)+1), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': ''})
        
        for c in DATE_COLS: df_init[c] = ""
        st.session_state.db = df_init

if 'v_key' not in st.session_state:
    st.session_state.v_key = 0

# --- 3. HÀM TÍNH TOÁN QUY ƯỚC ---
def apply_pvd_logic(df):
    gians = st.session_state.gians
    holidays = [15, 16, 17, 18, 19] # Có thể chuyển vào Config nếu cần
    
    def calc_row(row):
        total = 0.0
        for col in DATE_COLS:
            if col in row.index:
                val = str(row[col]).strip()
                if not val or val.lower() in ["nan", "none", ""]: continue
                day_num = int(col.split('/')[0])
                dt = date(now.year, now.month, day_num)
                is_weekend = dt.weekday() >= 5
                is_holiday = day_num in holidays
                
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

# --- 4. GIAO DIỆN (LOGO TO 1.5 LẦN) ---
col_l, col_r = st.columns([1.5, 5])
with col_l:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=180) # To lên 1.5 lần
    else:
        st.markdown("### PVD LOGO")
with col_r:
    st.markdown(f'<h1 style="color: #00f2ff; margin-top: 15px;">PVD MANAGEMENT - THÁNG {now.strftime("%m/%Y")}</h1>', unsafe_allow_html=True)

tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "🏗️ QUẢN LÝ GIÀN", "👤 NHÂN VIÊN", "📥 XUẤT FILE"])

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

    if st.button("💾 LƯU DỮ LIỆU THÁNG " + current_month_year, use_container_width=True):
        conn.update(worksheet=current_month_year, data=st.session_state.db)
        st.success("Đã lưu!")

    cols_order = ['STT', 'Họ và Tên', 'Nghỉ Ca Còn Lại'] + [c for c in st.session_state.db.columns if c not in ['STT', 'Họ và Tên', 'Nghỉ Ca Còn Lại']]
    st.session_state.db = st.session_state.db[cols_order]

    edited_df = st.data_editor(
        st.session_state.db,
        column_config={
            "Nghỉ Ca Còn Lại": st.column_config.NumberColumn("Quỹ CA", format="%.1f", disabled=True),
            "Họ và Tên": st.column_config.TextColumn(pinned=True)
        },
        use_container_width=True, height=500, key=f"pvd_ed_{st.session_state.v_key}"
    )
    if not edited_df.equals(st.session_state.db):
        st.session_state.db = edited_df
        st.rerun()

# --- TAB 2: QUẢN LÝ GIÀN ---
with tabs[1]:
    st.subheader("Cấu hình danh sách Giàn khoan")
    df_g = pd.DataFrame({"TenGian": st.session_state.gians})
    edited_gians = st.data_editor(df_g, num_rows="dynamic", use_container_width=True)
    if st.button("Lưu cấu hình Giàn"):
        st.session_state.gians = edited_gians['TenGian'].dropna().tolist()
        conn.update(worksheet="Config_Gians", data=pd.DataFrame({"TenGian": st.session_state.gians}))
        st.success("Đã cập nhật danh sách Giàn!")

# --- TAB 3: NHÂN VIÊN ---
with tabs[2]:
    st.subheader("Quản lý danh sách Nhân viên")
    # Lọc lấy các cột thông tin nhân viên
    staff_info_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail']
    df_staff_manage = st.session_state.db[staff_info_cols].copy()
    
    edited_staff = st.data_editor(df_staff_manage, num_rows="dynamic", use_container_width=True)
    
    if st.button("Lưu danh sách Nhân viên"):
        # Cập nhật lại db chính
        new_staff_df = edited_staff.dropna(subset=['Họ và Tên'])
        # Giữ lại các cột ngày cũ
        date_data = st.session_state.db[DATE_COLS]
        # (Lưu ý: Logic thêm/xóa nhân viên nâng cao sẽ cần merge dữ liệu tỉ mỉ hơn)
        conn.update(worksheet="Config_Staff", data=new_staff_df)
        st.success("Đã cập nhật danh sách nhân sự gốc!")

# --- TAB 4: XUẤT FILE ---
with tabs[3]:
    buffer = io.BytesIO()
    st.session_state.db.to_excel(buffer, index=False)
    st.download_button("📥 TẢI FILE EXCEL THÁNG", data=buffer.getvalue(), file_name=f"PVD_{current_month_year}.xlsx", use_container_width=True)

# Cuộn ngang
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
