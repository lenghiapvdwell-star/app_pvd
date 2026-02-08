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

# --- 2. KẾT NỐI & DỮ LIỆU CẤU HÌNH ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_gians():
    try:
        df_config = conn.read(worksheet="CONFIG", ttl=10)
        return df_config.iloc[:, 0].dropna().astype(str).tolist()
    except:
        return ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

if "gians_list" not in st.session_state:
    st.session_state.gians_list = load_gians()

# --- 3. CHỌN THÁNG ---
_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b")

# --- 4. LOAD DỮ LIỆU & SỬA LỖI KEYERROR ---
if 'db' not in st.session_state or st.session_state.get('active_sheet') != sheet_name:
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        if df_load.empty: raise ValueError
        st.session_state.db = df_load
    except:
        NAMES_BASE = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong"]
        st.session_state.db = pd.DataFrame({'STT': range(1, len(NAMES_BASE)+1), 'Họ và Tên': NAMES_BASE})
    st.session_state.active_sheet = sheet_name

# --- BƯỚC QUAN TRỌNG: KIỂM TRA VÀ BÙ CỘT THIẾU ---
num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr}" for d in range(1, num_days+1)]
fixed_info = ['STT', 'Họ và Tên', 'Tên Công Ty', 'Chức Danh', 'Job Detail', 'CA Tháng Trước']
required_cols = fixed_info + DATE_COLS + ['Quỹ CA Tổng']

# Nếu thiếu cột nào trong list required_cols, tự thêm cột đó vào DataFrame
for col in required_cols:
    if col not in st.session_state.db.columns:
        if col in ['STT', 'CA Tháng Trước', 'Quỹ CA Tổng']:
            st.session_state.db[col] = 0.0
        else:
            st.session_state.db[col] = ""

# Sắp xếp lại thứ tự cột chính xác
st.session_state.db = st.session_state.db[required_cols]

# --- 5. LOGIC AUTO-FILL & TÍNH CA ---
def process_data(df, use_autofill=True):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,2,21), date(2026,4,25), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    df_new = df.copy()
    
    for idx, row in df_new.iterrows():
        if not str(row.get('Họ và Tên', '')).strip(): continue
        
        if use_autofill:
            last_val = ""
            for col in DATE_COLS:
                curr = str(df_new.at[idx, col]).strip()
                if curr == "" or curr.upper() in ["NAN", "NONE"]:
                    df_new.at[idx, col] = last_val
                else:
                    last_val = curr

        accrued = 0.0
        ca_truoc = pd.to_numeric(row.get('CA Tháng Trước', 0), errors='coerce')
        if pd.isna(ca_truoc): ca_truoc = 0.0
        
        for col in DATE_COLS:
            v = str(df_new.at[idx, col]).strip().upper()
            if not v or v in ["NP", "ỐM", "WS"]: continue
            
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
                    if not is_weekend and not is_holiday: accrued -= 1.0
            except: continue
            
        df_new.at[idx, 'Quỹ CA Tổng'] = ca_truoc + accrued
    return df_new

# --- 6. GIAO DIỆN ---
c1, c2, c3 = st.columns([2, 2, 4])
if c1.button("💾 LƯU & AUTO-FILL", type="primary", use_container_width=True):
    st.session_state.db = process_data(st.session_state.db, use_autofill=True)
    conn.update(worksheet=sheet_name, data=st.session_state.db)
    st.toast("Đã lưu dữ liệu!")
    time.sleep(0.5)
    st.rerun()

buf = io.BytesIO()
st.session_state.db.to_excel(buf, index=False)
c2.download_button("📥 XUẤT EXCEL", buf, f"PVD_{sheet_name}.xlsx", use_container_width=True)

# --- 7. CÔNG CỤ QUẢN LÝ ---
with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH & QUẢN LÝ GIÀN"):
    tab_bulk, tab_rig = st.tabs(["⚡ Đổ dữ liệu hàng loạt", "⚓ Quản lý Giàn khoan"])
    with tab_bulk:
        ca, cb, cc = st.columns(3)
        sel_staff = ca.multiselect("Nhân sự:", st.session_state.db['Họ và Tên'].tolist())
        sel_dates = cb.date_input("Khoảng ngày:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, 2)))
        sel_status = cc.selectbox("Trạng thái:", ["Đi Biển", "CA", "NP", "Ốm", "WS"])
        sel_val = cc.selectbox("Chọn giàn:", st.session_state.gians_list) if sel_status == "Đi Biển" else sel_status
        if st.button("🚀 ÁP DỤNG"):
            if sel_staff and len(sel_dates) == 2:
                for name in sel_staff:
                    idx = st.session_state.db.index[st.session_state.db['Họ và Tên'] == name][0]
                    s_d, e_d = sel_dates
                    for i in range((e_d - s_d).days + 1):
                        d = s_d + timedelta(days=i)
                        if d.month == curr_month:
                            col_n = f"{d.day:02d}/{month_abbr}"
                            st.session_state.db.at[idx, col_n] = sel_val
                st.session_state.db = process_data(st.session_state.db, use_autofill=False)
                st.rerun()
    with tab_rig:
        c_add, c_del = st.columns(2)
        with c_add:
            new_r = st.text_input("Thêm giàn mới:")
            if st.button("➕ Thêm"):
                if new_r and new_r.upper() not in st.session_state.gians_list:
                    st.session_state.gians_list.append(new_r.upper())
                    conn.update(worksheet="CONFIG", data=pd.DataFrame({"Giàn": st.session_state.gians_list}))
                    st.rerun()
        with c_del:
            del_r = st.selectbox("Xóa giàn:", ["-- Chọn --"] + st.session_state.gians_list)
            if st.button("🗑️ Xóa"):
                if del_r != "-- Chọn --":
                    st.session_state.gians_list.remove(del_r)
                    conn.update(worksheet="CONFIG", data=pd.DataFrame({"Giàn": st.session_state.gians_list}))
                    st.rerun()

# --- 8. BẢNG NHẬP LIỆU ---
st.markdown("---")
edited_df = st.data_editor(
    st.session_state.db, 
    use_container_width=True, 
    height=600, 
    hide_index=True,
    key=f"pvd_editor_{sheet_name}"
)
st.session_state.db = edited_df
