import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import time

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 0.5rem;}
    .main-title {
        color: #00f2ff !important; font-size: 40px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 2px 2px 4px #000;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KẾT NỐI ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_gians():
    try:
        df = conn.read(worksheet="CONFIG", ttl=600)
        return df.iloc[:, 0].dropna().astype(str).tolist()
    except: return ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

# --- 3. KHỞI TẠO DỮ LIỆU ---
if "gians_list" not in st.session_state:
    st.session_state.gians_list = load_gians()

NAMES_BASE = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong"]

# --- 4. CHỌN THÁNG ---
_, c_mid, _ = st.columns([3, 2, 3])
working_date = c_mid.date_input("📅 THÁNG LÀM VIỆC:", value=date.today())
sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year

# Tải dữ liệu
if 'db' not in st.session_state or st.session_state.get('active_sheet') != sheet_name:
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        st.session_state.db = df_load
    except:
        st.session_state.db = pd.DataFrame({'STT': range(1, len(NAMES_BASE)+1), 'Họ và Tên': NAMES_BASE})
    st.session_state.active_sheet = sheet_name

# Tạo cột ngày nếu chưa có
num_days = calendar.monthrange(curr_year, curr_month)[1]
month_abbr = working_date.strftime("%b")
DATE_COLS = [f"{d:02d}/{month_abbr}" for d in range(1, num_days+1)]
for col in DATE_COLS:
    if col not in st.session_state.db.columns: st.session_state.db[col] = ""

# --- 5. LOGIC TÍNH TOÁN ---
def run_calculation(df):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,2,21)] # Rút gọn ví dụ
    def calc_row(row):
        acc = 0.0
        if not str(row.get('Họ và Tên','')).strip(): return 0.0
        for col in DATE_COLS:
            v = str(row.get(col, "")).strip().upper()
            if not v or v in ["WS", "NP", "ỐM"]: continue
            try:
                dt = date(curr_year, curr_month, int(col[:2]))
                is_offshore = any(g.upper() in v for g in st.session_state.gians_list)
                if is_offshore:
                    if dt in hols: acc += 2.0
                    elif dt.weekday() >= 5: acc += 1.0
                    else: acc += 0.5
                elif v == "CA":
                    if dt.weekday() < 5 and dt not in hols: acc -= 1.0
            except: continue
        return acc
    
    df['Quỹ CA Tổng'] = df.apply(calc_row, axis=1)
    return df

# --- 6. GIAO DIỆN CHÍNH ---
st.markdown(f'<h1 class="main-title">PVD WELL SERVICES - {sheet_name}</h1>', unsafe_allow_html=True)

# Hàng nút bấm
col_btn1, col_btn2, col_btn3 = st.columns([1.5, 1.5, 5])
if col_btn1.button("💾 LƯU & TÍNH TOÁN", type="primary", use_container_width=True):
    with st.spinner("Đang xử lý..."):
        st.session_state.db = run_calculation(st.session_state.db)
        conn.update(worksheet=sheet_name, data=st.session_state.db)
        st.success("Đã tính toán và lưu xong!")
        time.sleep(1)
        st.rerun()

buf = io.BytesIO()
st.session_state.db.to_excel(buf, index=False)
col_btn2.download_button("📥 XUẤT EXCEL", buf, f"PVD_{sheet_name}.xlsx", use_container_width=True)

# --- CÔNG CỤ NHẬP NHANH ---
with st.expander("🛠️ CÔNG CỤ NHẬP LIỆU NHANH (Đi biển hàng loạt, thêm giàn...)"):
    c1, c2, c3 = st.columns([2, 2, 2])
    f_staff = c1.multiselect("Nhân sự:", st.session_state.db['Họ và Tên'].tolist())
    f_date = c2.date_input("Khoảng ngày:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, 2)))
    f_status = c3.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP"])
    
    if st.button("🚀 ÁP DỤNG NGAY"):
        if f_staff and len(f_date) == 2:
            val = st.session_state.gians_list[0] if f_status == "Đi Biển" else f_status
            for name in f_staff:
                idx = st.session_state.db.index[st.session_state.db['Họ và Tên'] == name][0]
                for i in range((f_date[1] - f_date[0]).days + 1):
                    d = f_date[0] + timedelta(days=i)
                    col_n = f"{d.day:02d}/{month_abbr}"
                    if col_n in st.session_state.db.columns: st.session_state.db.at[idx, col_n] = val
            st.rerun()

# --- BẢNG NHẬP LIỆU CHÍNH ---
st.info("💡 Bạn có thể sửa trực tiếp vào bảng bên dưới. Sau khi sửa xong, hãy nhấn nút 'LƯU & TÍNH TOÁN' ở phía trên.")
edited_df = st.data_editor(st.session_state.db, use_container_width=True, height=600, hide_index=True)
st.session_state.db = edited_df
