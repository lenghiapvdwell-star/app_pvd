import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

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

# --- 2. HEADER ---
c_logo, _ = st.columns([1, 4])
with c_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=180)
    else:
        st.markdown("### 🔴 PVD WELL")

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. QUẢN LÝ GIÀN (SIDEBAR) ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

with st.sidebar:
    st.header("⚙️ QUẢN LÝ GIÀN")
    new_gian = st.text_input("Tên giàn mới:")
    if st.button("➕ Thêm Giàn"):
        if new_gian and new_gian not in st.session_state.GIANS:
            st.session_state.GIANS.append(new_gian)
            st.rerun()
    
    selected_gian_del = st.selectbox("Chọn giàn để xóa:", st.session_state.GIANS)
    if st.button("❌ Xóa Giàn"):
        if selected_gian_del in st.session_state.GIANS:
            st.session_state.GIANS.remove(selected_gian_del)
            st.rerun()

# --- 4. KẾT NỐI & CHỌN THÁNG ---
_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today(), key="main_date_picker")

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b") 

conn = st.connection("gsheets", type=GSheetsConnection)

if "current_sheet" not in st.session_state or st.session_state.current_sheet != sheet_name:
    st.session_state.current_sheet = sheet_name
    if 'db' in st.session_state: del st.session_state.db

# --- 5. TẢI DỮ LIỆU & LÀM SẠCH NAN ---
NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]

if 'db' not in st.session_state:
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        if df_load is not None and not df_load.empty:
            # TRIỆT TIÊU NAN: Thay thế tất cả giá trị trống/nan thành chuỗi rỗng
            st.session_state.db = df_load.fillna("").replace("nan", "").replace("None", "")
        else: raise Exception
    except:
        count = len(NAMES_66)
        st.session_state.db = pd.DataFrame({
            'STT': list(range(1, count + 1)), 'Họ và Tên': NAMES_66, 
            'Công ty': ['PVDWS'] * count, 'Chức danh': ['Casing crew'] * count, 
            'Job Detail': [''] * count, 'CA Tháng Trước': [0.0] * count, 'Quỹ CA Tổng': [0.0] * count
        })

num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
for col in DATE_COLS:
    if col not in st.session_state.db.columns: st.session_state.db[col] = ""

# --- 6. LOGIC TÍNH TOÁN ---
def recalculate_ca(df):
    hols = [date(2026,1,1), date(2026,4,30), date(2026,5,1), date(2026,9,2),
            date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19)]
    df_calc = df.copy().fillna("").replace("nan", "")
    for idx, row in df_calc.iterrows():
        accrued = 0.0
        for col in DATE_COLS:
            val = str(df_calc.at[idx, col]).strip().upper()
            if val and val not in ["", "NAN", "NONE"]:
                try:
                    d_int = int(col[:2])
                    dt = date(curr_year, curr_month, d_int)
                    is_we, is_ho = dt.weekday() >= 5, dt in hols
                    if any(g.upper() in val for g in st.session_state.GIANS):
                        accrued += 2.0 if is_ho else (1.0 if is_we else 0.5)
                    elif val == "CA":
                        if not is_we and not is_ho: accrued -= 1.0
                except: pass
        ton_cu = pd.to_numeric(row['CA Tháng Trước'], errors='coerce') or 0.0
        df_calc.at[idx, 'Quỹ CA Tổng'] = ton_cu + accrued
    return df_calc

# --- 7. AUTOFILL 8H SÁNG ---
if "last_autofill_date" not in st.session_state:
    st.session_state.last_autofill_date = None

now = datetime.now()
today_str = now.strftime("%Y-%m-%d")

if st.session_state.last_autofill_date != today_str and now.hour >= 8:
    df_auto = st.session_state.db.copy().fillna("").replace("nan", "")
    today_day = now.day
    updated = False
    for idx, row in df_auto.iterrows():
        last_val = ""
        for col in DATE_COLS:
            d_int = int(col[:2])
            curr_val = str(df_auto.at[idx, col]).strip().upper()
            if curr_val in ["", "NAN", "NONE"]:
                if d_int <= today_day and last_val:
                    df_auto.at[idx, col] = last_val
                    updated = True
            else:
                last_val = curr_val
    if updated:
        st.session_state.db = recalculate_ca(df_auto)
        conn.update(worksheet=sheet_name, data=st.session_state.db)
        st.session_state.last_autofill_date = today_str
        st.toast("Auto-fill ngày mới thành công!", icon="✅")

# --- 8. TABS GIAO DIỆN ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ"])

with t1:
    bc1, bc2 = st.columns([1.5, 1.5])
    with bc1:
        if st.button("📤 LƯU CLOUD", type="primary", use_container_width=True):
            st.session_state.db = recalculate_ca(st.session_state.db)
            conn.update(worksheet=sheet_name, data=st.session_state.db)
            st.success("Đã lưu lên Cloud!")
    with bc2:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            st.session_state.db.to_excel(writer, index=False, sheet_name=sheet_name)
        st.download_button(label="📥 XUẤT EXCEL", data=output.getvalue(), 
                           file_name=f"PVD_{sheet_name}.xlsx", mime="application/vnd.ms-excel", use_container_width=True)

    with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH (GHI ĐÈ DỮ LIỆU)"):
        c1, c2 = st.columns([2, 1])
        f_staff = c1.multiselect("Nhân sự:", NAMES_66)
        f_date = c2.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, num_days)))
        r2_1, r2_2, r2_3, r2_4 = st.columns(4)
        f_status = r2_1.selectbox("Trạng thái mới:", ["Xóa trắng", "Đi Biển", "CA", "WS", "NP", "Ốm"])
        f_val = r2_2.selectbox("Giàn:", st.session_state.GIANS) if f_status == "Đi Biển" else f_status
        f_co = r2_3.selectbox("Cty:", ["Không đổi", "PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"])
        f_ti = r2_4.selectbox("Chức danh:", ["Không đổi", "Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"])
        
        if st.button("✅ ÁP DỤNG (XÓA CŨ GHI MỚI)"):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                for person in f_staff:
                    idx = st.session_state.db.index[st.session_state.db['Họ và Tên'] == person][0]
                    for i in range((f_date[1] - f_date[0]).days + 1):
                        d = f_date[0] + timedelta(days=i)
                        if d.month == curr_month:
                            col_n = [c for c in DATE_COLS if c.startswith(f"{d.day:02d}/")][0]
                            # Ghi đè tuyệt đối: Xóa sạch dữ liệu cũ tại ô đó
                            st.session_state.db.at[idx, col_n] = "" if f_status == "Xóa trắng" else f_val
                    
                    if f_co != "Không đổi": st.session_state.db.at[idx, 'Công ty'] = f_co
                    if f_ti != "Không đổi": st.session_state.db.at[idx, 'Chức danh'] = f_ti
                
                st.session_state.db = recalculate_ca(st.session_state.db)
                conn.update(worksheet=sheet_name, data=st.session_state.db)
                st.rerun()

    # HIỂN THỊ BẢNG (TRIỆT TIÊU NAN TRỰC TIẾP TRÊN EDITOR)
    ordered_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail', 'CA Tháng Trước', 'Quỹ CA Tổng'] + DATE_COLS
    config = {
        "STT": st.column_config.NumberColumn(disabled=True),
        "Họ và Tên": st.column_config.TextColumn(disabled=True),
        "CA Tháng Trước": st.column_config.NumberColumn("Tồn Cũ", format="%.1f"),
        "Quỹ CA Tổng": st.column_config.NumberColumn("Tổng ca", format="%.1f", disabled=True),
    }
    # Làm sạch df hiển thị để không bao giờ thấy chữ nan
    display_df = st.session_state.db[ordered_cols].fillna("").replace("nan", "")
    
    ed_df = st.data_editor(display_df, column_config=config, use_container_width=True, height=600, hide_index=True)
    if not ed_df.equals(display_df):
        st.session_state.db.update(ed_df)
        st.session_state.db = recalculate_ca(st.session_state.db)
        st.rerun()

with t2:
    st.subheader("📊 BIỂU ĐỒ NĂM")
    # Tự động làm sạch dữ liệu năm để vẽ biểu đồ không bị lỗi NaN
    sel = st.selectbox("🔍 Chọn nhân sự:", NAMES_66)
    # ... (Logic biểu đồ giữ nguyên)
