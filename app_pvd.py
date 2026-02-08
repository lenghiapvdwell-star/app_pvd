import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import time

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 0.5rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; font-size: 45px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 3px 3px 6px #000 !important;
        font-family: 'Arial Black', sans-serif !important;
        margin-bottom: 15px;
    }
    .stButton>button {border-radius: 5px; height: 3em;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER & LOGO ---
c_logo, _ = st.columns([1, 4])
with c_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=180)
    else:
        st.markdown("<h2 style='color:red;'>🔴 PVD WELL</h2>", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. KẾT NỐI & DANH SÁCH GIÀN ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_gians():
    try:
        df_config = conn.read(worksheet="CONFIG", ttl=10)
        return df_config.iloc[:, 0].dropna().astype(str).tolist()
    except:
        return ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

if "gians_list" not in st.session_state:
    st.session_state.gians_list = load_gians()

# Danh sách nhân sự mặc định
NAMES_BASE = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong"]

# --- 4. CHỌN THÁNG ---
_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b")

# --- 5. QUẢN LÝ DỮ LIỆU TẠM THỜI (SESSION STATE) ---
if 'db' not in st.session_state or st.session_state.get('active_sheet') != sheet_name:
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        st.session_state.db = df_load
    except:
        st.session_state.db = pd.DataFrame({'STT': range(1, len(NAMES_BASE)+1), 'Họ và Tên': NAMES_BASE})
    st.session_state.active_sheet = sheet_name

# Đảm bảo có đủ cột ngày
num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr}" for d in range(1, num_days+1)]
for col in DATE_COLS:
    if col not in st.session_state.db.columns: st.session_state.db[col] = ""

# --- 6. HÀM XỬ LÝ (CHỈ CHẠY KHI NHẤN NÚT LƯU) ---
def run_autofill_and_calc(df):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,2,21), date(2026,4,25), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    df_new = df.copy()
    for idx, row in df_new.iterrows():
        if not str(row.get('Họ và Tên', '')).strip(): continue
        
        # Autofill quy tắc ngày trước cho ngày sau
        last_val = ""
        for col in DATE_COLS:
            current_val = str(df_new.at[idx, col]).strip()
            if current_val == "" or current_val.upper() == "NAN":
                df_new.at[idx, col] = last_val
            else:
                last_val = current_val

        # Tính toán Quỹ CA
        acc = 0.0
        for col in DATE_COLS:
            v = str(df_new.at[idx, col]).strip().upper()
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
        df_new.at[idx, 'Quỹ CA Tổng'] = acc
    return df_new

# --- 7. GIAO DIỆN ĐIỀU KHIỂN ---
c1, c2, c3 = st.columns([2.5, 2, 4])

# NÚT QUAN TRỌNG NHẤT: LƯU TỔNG THỂ
if c1.button("☁️ LƯU & ĐỒNG BỘ CLOUD (AUTOFILL)", type="primary", use_container_width=True):
    with st.status("🔄 Đang xử lý Autofill & Đồng bộ Google Sheets...", expanded=False):
        # Chạy Autofill + Tính toán trước khi gửi lên Cloud
        st.session_state.db = run_autofill_and_calc(st.session_state.db)
        conn.update(worksheet=sheet_name, data=st.session_state.db)
        st.success("Đã đồng bộ thành công!")
        time.sleep(1)
        st.rerun()

buf = io.BytesIO()
st.session_state.db.to_excel(buf, index=False)
c2.download_button("📥 XUẤT EXCEL (Tạm thời)", buf, f"PVD_{sheet_name}.xlsx", use_container_width=True)

# --- 8. CÔNG CỤ (CHỈ THAY ĐỔI TẠM THỜI TRÊN MÀN HÌNH) ---
with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH & QUẢN LÝ GIÀN KHOAN"):
    tab_bulk, tab_rig = st.tabs(["⚡ Đổ dữ liệu nhanh", "⚓ Quản lý danh sách giàn"])
    
    with tab_bulk:
        col_a, col_b, col_c = st.columns(3)
        f_staff = col_a.multiselect("Chọn nhân sự:", st.session_state.db['Họ và Tên'].tolist())
        f_date = col_b.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, 2)))
        f_status = col_c.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm"])
        f_val = col_c.selectbox("Chọn giàn:", st.session_state.gians_list) if f_status == "Đi Biển" else f_status
        
        if st.button("🚀 ÁP DỤNG LÊN BẢNG"):
            if f_staff and len(f_date) == 2:
                for name in f_staff:
                    idx = st.session_state.db.index[st.session_state.db['Họ và Tên'] == name][0]
                    for i in range((f_date[1] - f_date[0]).days + 1):
                        d = f_date[0] + timedelta(days=i)
                        col_n = f"{d.day:02d}/{month_abbr}"
                        if col_n in st.session_state.db.columns:
                            st.session_state.db.at[idx, col_n] = f_val
                st.toast("Đã áp dụng lên bảng (Chưa lưu Cloud)")
                time.sleep(0.5)
                st.rerun()

    with tab_rig:
        ra, rb = st.columns([3, 1])
        new_r = ra.text_input("Tên giàn mới:")
        if rb.button("➕ Thêm", use_container_width=True):
            if new_r:
                st.session_state.gians_list.append(new_r.upper())
                conn.update(worksheet="CONFIG", data=pd.DataFrame({"Giàn": st.session_state.gians_list}))
                st.rerun()
        
        del_r = st.selectbox("Xóa giàn khoan:", ["-- Chọn giàn cần xóa --"] + st.session_state.gians_list)
        if st.button("🗑️ Xác nhận xóa"):
            if del_r != "-- Chọn giàn cần xóa --":
                st.session_state.gians_list.remove(del_r)
                conn.update(worksheet="CONFIG", data=pd.DataFrame({"Giàn": st.session_state.gians_list}))
                st.rerun()

# --- 9. BẢNG NHẬP LIỆU (SỬ DỤNG DATA EDITOR) ---
st.markdown("---")
st.info("💡 **QUY TRÌNH:** Nhập dữ liệu -> Kiểm tra trên bảng -> Nhấn **'LƯU & ĐỒNG BỘ CLOUD'** để Autofill và tính CA.")
edited_df = st.data_editor(
    st.session_state.db, 
    use_container_width=True, 
    height=600, 
    hide_index=True,
    key="pvd_editor_v5"
)
# Cập nhật thay đổi từ bảng vào session_state (chưa lưu Cloud)
st.session_state.db = edited_df
