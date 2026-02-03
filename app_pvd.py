import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH & THỜI GIAN ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

now = datetime.now()
current_sheet = now.strftime("%m_%Y")  # Ví dụ: "02_2026"
# Tính tháng trước để lấy số dư
last_month_date = (now.replace(day=1) - pd.Timedelta(days=1))
last_sheet = last_month_date.strftime("%m_%Y")

month_days = calendar.monthrange(now.year, now.month)[1]
DATE_COLS = [f"{d:02d}/{now.strftime('%m')}" for d in range(1, month_days + 1)]

# --- 2. KHỞI TẠO DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

if 'db' not in st.session_state:
    try:
        # 1. Đọc sheet tháng hiện tại
        df = conn.read(worksheet=current_sheet)
        
        # 2. Nếu sheet tháng hiện tại chưa có, khởi tạo mới và lấy dư đầu kỳ
        if df is None or df.empty:
            # Thử đọc sheet tháng trước để lấy số dư cuối kỳ
            try:
                df_last = conn.read(worksheet=last_sheet)
                last_balances = df_last[['Họ và Tên', 'Nghỉ Ca Còn Lại']].rename(columns={'Nghỉ Ca Còn Lại': 'Dư Đầu Kỳ'})
            except:
                last_balances = pd.DataFrame(columns=['Họ và Tên', 'Dư Đầu Kỳ'])

            # Tạo khung dữ liệu tháng mới
            NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang"] # Thêm đủ 64 người của bạn ở đây
            df = pd.DataFrame({
                'STT': range(1, len(NAMES)+1), 
                'Họ và Tên': NAMES, 
                'Công ty': 'PVDWS', 
                'Chức danh': 'Kỹ sư', 
                'Job Detail': ''
            })
            # Gộp số dư từ tháng trước vào
            df = pd.merge(df, last_balances, on='Họ và Tên', how='left').fillna(0)
        
        # 3. Đảm bảo có đủ cột ngày và cột tính toán (Tránh KeyError)
        if 'Dư Đầu Kỳ' not in df.columns: df['Dư Đầu Kỳ'] = 0.0
        for c in DATE_COLS:
            if c not in df.columns: df[c] = ""
            
        st.session_state.db = df
    except Exception as e:
        st.error(f"Lỗi khởi tạo: {e}")
        st.session_state.db = pd.DataFrame()

# --- 3. HÀM TÍNH TOÁN QUY ƯỚC ---
def calculate_pvd_offshore(row):
    # Dùng .get() hoặc kiểm tra để an toàn tuyệt đối
    accrued = float(row.get('Dư Đầu Kỳ', 0))
    rigs = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]
    holidays = [15, 16, 17, 18, 19] # Cập nhật ngày lễ theo tháng
    
    for col in DATE_COLS:
        if col in row.index:
            val = str(row[col]).strip() if pd.notna(row[col]) else ""
            if not val: continue
            
            day_val = int(col.split('/')[0])
            d_obj = date(now.year, now.month, day_val)
            weekday = d_obj.weekday()
            
            if val in rigs:
                if day_val in holidays: accrued += 2.0
                elif weekday >= 5: accrued += 1.0
                else: accrued += 0.5
            elif val == "CA":
                if weekday < 5 and day_val not in holidays: accrued -= 1.0
    return round(accrued, 2)

# Cập nhật quỹ nghỉ ca
st.session_state.db['Nghỉ Ca Còn Lại'] = st.session_state.db.apply(calculate_pvd_offshore, axis=1)

# --- 4. GIAO DIỆN ---
c_logo, c_title = st.columns([1, 4])
with c_logo:
    if os.path.exists("logo_pvd.png"): st.image("logo_pvd.png", width=150)
with c_title:
    st.markdown(f'<h1 style="color: #00f2ff;">PVD WELL SERVICES - THÁNG {now.strftime("%m/%Y")}</h1>', unsafe_allow_html=True)

# Nút thao tác
c1, c2, c3 = st.columns([2, 1, 1])
with c2:
    if st.button("💾 LƯU CLOUD (SHEET " + current_sheet + ")", use_container_width=True):
        conn.update(worksheet=current_sheet, data=st.session_state.db)
        st.success("Đã lưu!")

# Bảng dữ liệu
st.data_editor(
    st.session_state.db,
    column_config={
        "Dư Đầu Kỳ": st.column_config.NumberColumn("Dư Tháng Trước", format="%.1f", disabled=True),
        "Nghỉ Ca Còn Lại": st.column_config.NumberColumn("Quỹ CA Hiện Tại", format="%.1f", disabled=True)
    },
    use_container_width=True,
    height=600,
    key=f"editor_{now.month}"
)
