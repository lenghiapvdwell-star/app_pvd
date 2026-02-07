import streamlit as st
import pandas as pd
from datetime import date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io, os, time

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

# --- 2. KẾT NỐI ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. HÀM TỐI ƯU ---
def load_rigs():
    try:
        df = conn.read(worksheet="CONFIG", ttl=0)
        return df.iloc[:, 0].dropna().astype(str).tolist()
    except:
        return ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

# Hàm lưu Cloud có cơ chế tự động thử lại (Retry logic)
def save_to_cloud(worksheet_name, dataframe):
    max_retries = 3
    for i in range(max_retries):
        try:
            conn.update(worksheet=worksheet_name, data=dataframe)
            return True
        except Exception:
            if i < max_retries - 1:
                time.sleep(1) # Đợi 1 giây rồi thử lại
                continue
            else:
                return False

# --- 4. THIẾT LẬP THỜI GIAN ---
if "gians_list" not in st.session_state:
    st.session_state.gians_list = load_rigs()

working_date = st.date_input("📅 CHỌN THÁNG:", value=date.today())
sheet_name = working_date.strftime("%m_%Y")
month_abbr = working_date.strftime("%b")
curr_month, curr_year = working_date.month, working_date.year

# --- 5. TẢI DỮ LIỆU ---
if 'db' not in st.session_state or st.session_state.get('last_sheet') != sheet_name:
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        st.session_state.db = df_load
    except:
        # Tạo mới nếu chưa có sheet
        st.session_state.db = pd.DataFrame({
            'STT': range(1, 66),
            'Họ và Tên': ["Nhân viên " + str(i) for i in range(1, 66)], # Thay bằng NAMES_64 của bạn
            'Công ty': 'PVDWS',
            'Chức danh': 'Casing crew',
            'CA Tháng Trước': 0.0,
            'Quỹ CA Tổng': 0.0
        })
    st.session_state.last_sheet = sheet_name

# Tạo cột ngày nếu chưa có
num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr}" for d in range(1, num_days+1)]
for col in DATE_COLS:
    if col not in st.session_state.db.columns:
        st.session_state.db[col] = ""

# --- 6. LOGIC TÍNH TOÁN (Đã tinh gọn) ---
def update_logic(df):
    hols = [date(2026,1,1), date(2026,4,30), date(2026,5,1), date(2026,9,2)] # Rút gọn list lễ
    rigs_upper = [g.upper() for g in st.session_state.gians_list]
    
    def calc_row(row):
        acc = 0.0
        for col in DATE_COLS:
            val = str(row.get(col, "")).upper()
            if not val or val in ["NAN", "NONE"]: continue
            try:
                dt = date(curr_year, curr_month, int(col[:2]))
                is_special = dt.weekday() >= 5 or dt in hols
                if any(r in val for r in rigs_upper):
                    acc += 2.0 if dt in hols else (1.0 if dt.weekday() >= 5 else 0.5)
                elif val == "CA" and not is_special:
                    acc -= 1.0
            except: continue
        return acc

    df['Quỹ CA Tổng'] = df['CA Tháng Trước'].fillna(0) + df.apply(calc_row, axis=1)
    return df

st.session_state.db = update_logic(st.session_state.db)

# --- 7. GIAO DIỆN ---
st.title("PVD WELL MANAGEMENT")

col_btn1, col_btn2, _ = st.columns([1, 1, 4])
with col_btn1:
    if st.button("📤 LƯU CLOUD", type="primary", use_container_width=True):
        with st.spinner("Đang kết nối Cloud..."):
            success = save_to_cloud(sheet_name, st.session_state.db)
            if success:
                st.success("Đã lưu!")
                st.cache_data.clear()
            else:
                st.error("Lỗi kết nối. Vui lòng kiểm tra quyền Editor hoặc tab Sheet.")

with col_btn2:
    buf = io.BytesIO()
    st.session_state.db.to_excel(buf, index=False)
    st.download_button("📥 XUẤT EXCEL", buf, f"PVD_{sheet_name}.xlsx")

# --- 8. BẢNG DỮ LIỆU ---
config = {
    "Họ và Tên": st.column_config.TextColumn(width="medium", disabled=True),
    "Quỹ CA Tổng": st.column_config.NumberColumn(format="%.1f", disabled=True),
}

edited_df = st.data_editor(
    st.session_state.db,
    column_config=config,
    use_container_width=True,
    hide_index=True,
    height=500
)

if not edited_df.equals(st.session_state.db):
    st.session_state.db = edited_df
    st.rerun()
