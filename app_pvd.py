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
    .block-container {padding-top: 0.5rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; font-size: 45px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 3px 3px 6px #000 !important;
        font-family: 'Arial Black', sans-serif !important;
    }
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

# --- 3. KẾT NỐI & DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_gians():
    try:
        df_config = conn.read(worksheet="CONFIG", ttl=10)
        return df_config.iloc[:, 0].dropna().astype(str).tolist()
    except:
        return ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

if "gians_list" not in st.session_state:
    st.session_state.gians_list = load_gians()

NAMES_BASE = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong"]

# --- 4. CHỌN THÁNG ---
_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b")

if 'db' not in st.session_state or st.session_state.get('active_sheet') != sheet_name:
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        st.session_state.db = df_load
    except:
        st.session_state.db = pd.DataFrame({
            'STT': range(1, len(NAMES_BASE)+1), 
            'Họ và Tên': NAMES_BASE,
            'CA Tháng Trước': 0.0,
            'Quỹ CA Tổng': 0.0
        })
        for i in range(10):
            st.session_state.db.loc[len(st.session_state.db)] = [len(st.session_state.db)+1, "", 0.0, 0.0]
    st.session_state.active_sheet = sheet_name

num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr}" for d in range(1, num_days+1)]
for col in DATE_COLS:
    if col not in st.session_state.db.columns: st.session_state.db[col] = ""

fixed_cols = ['STT', 'Họ và Tên', 'CA Tháng Trước']
st.session_state.db = st.session_state.db[fixed_cols + DATE_COLS + ['Quỹ CA Tổng']]

# --- 5. LOGIC AUTO-FILL & TÍNH CA CHI TIẾT ---
def process_data(df, use_autofill=True):
    # Lễ 2026: Tết (16-21/2), Hùng Vương (25/4), 30/4, 1/5, 2/9...
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,2,21), date(2026,4,25), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    df_new = df.copy()
    df_new['CA Tháng Trước'] = pd.to_numeric(df_new['CA Tháng Trước'], errors='coerce').fillna(0.0)

    for idx, row in df_new.iterrows():
        if not str(row.get('Họ và Tên', '')).strip(): continue
        
        # 1. Autofill
        if use_autofill:
            last_val = ""
            for col in DATE_COLS:
                curr = str(df_new.at[idx, col]).strip()
                if curr == "" or curr.upper() == "NAN":
                    df_new.at[idx, col] = last_val
                else:
                    last_val = curr

        # 2. Tính CA
        accrued = 0.0
        for col in DATE_COLS:
            v = str(df_new.at[idx, col]).strip().upper()
            
            # QUY TẮC MỚI: Nếu là NP (Nghỉ phép) hoặc ỐM -> Bỏ qua, không tính toán gì cho ngày này
            if not v or v in ["NP", "ỐM", "WS"]: 
                continue
            
            try:
                dt = date(curr_year, curr_month, int(col[:2]))
                is_offshore = any(g.upper() in v for g in st.session_state.gians_list)
                is_holiday = dt in hols
                is_weekend = dt.weekday() >= 5
                
                if is_offshore:
                    if is_holiday: accrued += 2.0
                    elif is_weekend: accrued += 1.0
                    else: accrued += 0.5
                elif v == "CA":
                    # CHỈ TRỪ nếu là ngày thường và KHÔNG phải lễ
                    if not is_weekend and not is_holiday:
                        accrued -= 1.0
            except: continue
            
        df_new.at[idx, 'Quỹ CA Tổng'] = df_new.at[idx, 'CA Tháng Trước'] + accrued
    return df_new

# --- 6. GIAO DIỆN ĐIỀU KHIỂN ---
c1, c2, c3 = st.columns([2, 2, 4])
if c1.button("💾 LƯU & TÍNH TOÁN (AUTO-FILL)", type="primary", use_container_width=True):
    with st.status("🚀 Đang đồng bộ...", expanded=False):
        st.session_state.db = process_data(st.session_state.db, use_autofill=True)
        conn.update(worksheet=sheet_name, data=st.session_state.db)
        st.toast("Đã cập nhật lịch và Quỹ CA!")
        time.sleep(0.5)
        st.rerun()

buf = io.BytesIO()
st.session_state.db.to_excel(buf, index=False)
c2.download_button("📥 XUẤT EXCEL", buf, f"PVD_{sheet_name}.xlsx", use_container_width=True)

# --- 7. CÔNG CỤ CẬP NHẬT NHANH ---
with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH & QUẢN LÝ GIÀN"):
    t_bulk, t_rig = st.tabs(["⚡ Đổ dữ liệu hàng loạt", "⚓ Quản lý Giàn khoan"])
    with t_bulk:
        ca, cb, cc = st.columns(3)
        sel_staff = ca.multiselect("Nhân sự:", st.session_state.db['Họ và Tên'].tolist())
        sel_dates = cb.date_input("Khoảng ngày:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, 2)))
        sel_status = cc.selectbox("Trạng thái:", ["Đi Biển", "CA", "NP", "Ốm", "WS"])
        sel_rig = cc.selectbox("Chọn giàn:", st.session_state.gians_list) if sel_status == "Đi Biển" else sel_status
        if st.button("🚀 XÁC NHẬN ÁP DỤNG"):
            if sel_staff and len(sel_dates) == 2:
                for name in sel_staff:
                    idx = st.session_state.db.index[st.session_state.db['Họ và Tên'] == name][0]
                    s_d, e_d = sel_dates
                    for i in range((e_d - s_d).days + 1):
                        d = s_d + timedelta(days=i)
                        if d.month == curr_month:
                            col_n = f"{d.day:02d}/{month_abbr}"
                            st.session_state.db.at[idx, col_n] = sel_rig
                st.rerun()
    with t_rig:
        ra, rb = st.columns([3, 1])
        new_rig = ra.text_input("Thêm giàn:")
        if rb.button("➕"):
            if new_rig:
                st.session_state.gians_list.append(new_rig.upper())
                conn.update(worksheet="CONFIG", data=pd.DataFrame({"Giàn": st.session_state.gians_list}))
                st.rerun()

# --- 8. BẢNG NHẬP LIỆU CHÍNH ---
st.markdown("---")
st.warning("⚠️ **LƯU Ý:** Trạng thái 'NP' (Nghỉ phép) và 'ỐM' sẽ **không bị trừ** vào Quỹ CA của nhân sự.")
edited_df = st.data_editor(
    st.session_state.db, 
    use_container_width=True, 
    height=600, 
    hide_index=True,
    key="pvd_editor_v6"
)
st.session_state.db = edited_df
