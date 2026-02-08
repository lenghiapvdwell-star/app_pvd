import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import time

# --- 1. CẤU HÌNH & STYLE ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; font-size: 38px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 2px 2px 4px #000 !important;
    }
    .stButton>button {border-radius: 5px; height: 3em;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER & LOGO ---
c_logo, _ = st.columns([1, 4])
with c_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=160)
    else:
        st.markdown("<h2 style='color:red;'>🔴 PVD WELL</h2>", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. DỮ LIỆU CỐ ĐỊNH ---
NAMES_65 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong"]
HOLIDAYS_2026 = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,2,21), date(2026,4,25), date(2026,4,30), date(2026,5,1), date(2026,9,2)]

# --- 4. KẾT NỐI ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_gians():
    try:
        df_config = conn.read(worksheet="CONFIG", ttl=1)
        return df_config.iloc[:, 0].dropna().astype(str).tolist()
    except:
        return ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

if "gians_list" not in st.session_state:
    st.session_state.gians_list = load_gians()

# --- 5. CHỌN THÁNG ---
_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b")

# --- 6. HÀM LOGIC (AUTOFILL & TÍNH CA) ---
def apply_pvd_logic(df):
    num_days = calendar.monthrange(curr_year, curr_month)[1]
    date_cols = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
    
    df_new = df.copy()
    for idx, row in df_new.iterrows():
        # A. Autofill: Ngày sau lấy ngày trước
        last_val = ""
        for col in date_cols:
            if col not in df_new.columns: df_new[col] = ""
            curr_v = str(df_new.at[idx, col]).strip()
            if curr_v == "" or curr_v.upper() in ["NAN", "NONE"]:
                df_new.at[idx, col] = last_val
            else:
                last_val = curr_v

        # B. Tính CA
        acc_month = 0.0
        for col in date_cols:
            v = str(df_new.at[idx, col]).strip().upper()
            if not v or v in ["WS", "NP", "ỐM"]: continue
            try:
                dt = date(curr_year, curr_month, int(col[:2]))
                is_off = any(g.upper() in v for g in st.session_state.gians_list)
                if is_off:
                    if dt in HOLIDAYS_2026: acc_month += 2.0
                    elif dt.weekday() >= 5: acc_month += 1.0
                    else: acc_month += 0.5
                elif v == "CA":
                    if dt.weekday() < 5 and dt not in HOLIDAYS_2026: acc_month -= 1.0
            except: continue
        
        old_val = pd.to_numeric(df_new.at[idx, 'CA Tháng Trước'], errors='coerce') or 0.0
        df_new.at[idx, 'Quỹ CA Tổng'] = old_val + acc_month
    return df_new

# --- 7. TẢI DỮ LIỆU ---
if 'db' not in st.session_state or st.session_state.get('active_sheet') != sheet_name:
    try:
        st.session_state.db = conn.read(worksheet=sheet_name, ttl=0)
    except:
        st.session_state.db = pd.DataFrame({
            'STT': range(1, 66), 'Họ và Tên': NAMES_65, 
            'CA Tháng Trước': 0.0, 'Quỹ CA Tổng': 0.0
        })
    st.session_state.active_sheet = sheet_name

# --- 8. TAB CÔNG CỤ (ĐÃ KHÔI PHỤC) ---
with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH & QUẢN LÝ GIÀN KHOAN"):
    t_bulk, t_rig = st.tabs(["⚡ Đổ dữ liệu nhanh", "⚓ Quản lý danh sách giàn"])
    
    with t_bulk:
        c1, c2, c3 = st.columns(3)
        f_staff = c1.multiselect("Nhân sự:", st.session_state.db['Họ và Tên'].tolist())
        f_date = c2.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, 2)))
        f_status = c3.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm"])
        f_val = c3.selectbox("Chọn giàn:", st.session_state.gians_list) if f_status == "Đi Biển" else f_status
        if st.button("🚀 ÁP DỤNG LÊN BẢNG"):
            if f_staff and len(f_date) == 2:
                for name in f_staff:
                    idx = st.session_state.db.index[st.session_state.db['Họ và Tên'] == name][0]
                    for i in range((f_date[1] - f_date[0]).days + 1):
                        d = f_date[0] + timedelta(days=i)
                        col_n = [c for c in st.session_state.db.columns if c.startswith(f"{d.day:02d}/")]
                        if col_n: st.session_state.db.at[idx, col_n[0]] = f_val
                st.rerun()

    with t_rig:
        ra, rb = st.columns([3, 1])
        new_r = ra.text_input("Tên giàn mới:")
        if rb.button("➕ Thêm"):
            if new_r:
                st.session_state.gians_list.append(new_r.upper())
                conn.update(worksheet="CONFIG", data=pd.DataFrame({"Giàn": st.session_state.gians_list}))
                st.rerun()
        st.markdown("---")
        da, db = st.columns([3, 1])
        r_del = da.selectbox("Chọn giàn cần xóa:", ["-- Chọn --"] + st.session_state.gians_list)
        if db.button("🗑️ Xóa"):
            if r_del != "-- Chọn --":
                st.session_state.gians_list.remove(r_del)
                conn.update(worksheet="CONFIG", data=pd.DataFrame({"Giàn": st.session_state.gians_list}))
                st.rerun()

# --- 9. ĐIỀU KHIỂN CHÍNH ---
cc1, cc2, _ = st.columns([2, 2, 5])
if cc1.button("💾 LƯU & ĐỒNG BỘ CLOUD", type="primary", use_container_width=True):
    with st.spinner("Đang lưu..."):
        final_df = apply_pvd_logic(st.session_state.db)
        conn.update(worksheet=sheet_name, data=final_df)
        st.session_state.db = final_df
        st.success("Đã đồng bộ thành công!")
        st.rerun()

buf = io.BytesIO()
st.session_state.db.to_excel(buf, index=False)
cc2.download_button("📥 XUẤT EXCEL", buf, f"PVD_{sheet_name}.xlsx", use_container_width=True)

# --- 10. BẢNG NHẬP LIỆU ---
st.markdown("---")
display_df = apply_pvd_logic(st.session_state.db)

# Đảm bảo thứ tự cột: STT, Tên, CA Trước, Các ngày..., Quỹ CA Tổng
cols = list(display_df.columns)
main_cols = ['STT', 'Họ và Tên', 'CA Tháng Trước']
date_cols = [c for c in cols if '/' in c]
final_cols = main_cols + date_cols + ['Quỹ CA Tổng']
display_df = display_df[final_cols]

edited_df = st.data_editor(
    display_df,
    use_container_width=True,
    height=600,
    hide_index=True,
    key=f"pvd_final_editor_{sheet_name}"
)

if not edited_df.equals(display_df):
    st.session_state.db = edited_df
    st.rerun()
