import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import time
import plotly.express as px
import os

# --- 1. CẤU HÌNH & STYLE ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 1rem;}
    .main-title {
        color: #007BFF !important; 
        font-size: 39px !important; 
        font-weight: bold !important;
        text-align: center !important; 
        margin-bottom: 20px !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO ---
def display_main_logo():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        logo_path = os.path.join(current_dir, f"logo_pvd{ext}")
        if os.path.exists(logo_path):
            col1, col2, col3 = st.columns([4, 2, 4])
            with col2: st.image(logo_path, use_container_width=True)
            return True
    return False

display_main_logo()
st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. KẾT NỐI & HÀM ĐỌC/GHI CẤU HÌNH ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data_safe(wks_name, ttl=0):
    try:
        df = conn.read(worksheet=wks_name, ttl=ttl)
        return df if (df is not None and not df.empty) else pd.DataFrame()
    except: return pd.DataFrame()

def load_settings():
    # Đọc danh sách Giàn từ sheet config
    df_conf = get_data_safe("config", ttl=0)
    rigs = [str(g).strip().upper() for g in df_conf["GIANS"].dropna().tolist()] if not df_conf.empty and "GIANS" in df_conf.columns else ["PVD 8", "HK 11", "SDP"]
    
    # Đọc danh sách Nhân sự từ sheet nhansu 999s
    df_ns = get_data_safe("nhansu 999s", ttl=0)
    if not df_ns.empty and "Họ và Tên" in df_ns.columns:
        names = [str(n).strip() for n in df_ns["Họ và Tên"].dropna().tolist() if str(n).strip()]
    else:
        # Danh sách dự phòng nếu sheet trống
        names = ["Bui Anh Phuong", "Le Trong Nghia", "Nguyen Van Manh"] 
    return rigs, names

# Khởi tạo session state để lưu danh sách tạm thời
if "GIANS" not in st.session_state or "NAMES" not in st.session_state:
    st.session_state.GIANS, st.session_state.NAMES = load_settings()

# --- 4. ENGINE TÍNH TOÁN ---
def apply_logic(df, curr_m, curr_y, rigs):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    df_calc = df.copy()
    rigs_up = [r.upper() for r in rigs]
    date_cols = [c for c in df_calc.columns if "/" in str(c)]

    for idx, row in df_calc.iterrows():
        if not str(row.get('Họ và Tên', '')).strip(): continue
        accrued = 0.0
        for col in date_cols:
            try:
                val = str(row.get(col, "")).strip().upper()
                if not val or val == "NAN": continue
                d_num = int(str(col)[:2])
                target_date = date(curr_y, curr_m, d_num)
                is_we = target_date.weekday() >= 5
                is_ho = target_date in hols
                if any(g in val for g in rigs_up):
                    if is_ho: accrued += 2.0
                    elif is_we: accrued += 1.0
                    else: accrued += 0.5
                elif val == "CA":
                    if not is_we and not is_ho: accrued -= 1.0
            except: continue
        ton_cu = pd.to_numeric(row.get('Tồn cũ', 0), errors='coerce')
        df_calc.at[idx, 'Tổng CA'] = round(float(ton_cu if not pd.isna(ton_cu) else 0.0) + accrued, 1)
    return df_calc

# --- 5. KHỞI TẠO DỮ LIỆU THÁNG ---
_, mc, _ = st.columns([3, 2, 3])
with mc: wd = st.date_input("📅 CHỌN THÁNG:", value=date.today())

sheet_name = wd.strftime("%m_%Y")
curr_m, curr_y = wd.month, wd.year
days_in_m = calendar.monthrange(curr_y, curr_m)[1]
DATE_COLS = [f"{d:02d}/{wd.strftime('%b')} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_y,curr_m,d).weekday()]})" for d in range(1, days_in_m+1)]

df_raw = get_data_safe(sheet_name, ttl=0)

if df_raw.empty:
    df_raw = pd.DataFrame({'STT': range(1, len(st.session_state.NAMES)+1), 'Họ và Tên': st.session_state.NAMES, 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Tồn cũ': 0.0, 'Tổng CA': 0.0})
    for c in DATE_COLS: df_raw[c] = ""
    prev_date = wd.replace(day=1) - timedelta(days=1)
    prev_df = get_data_safe(prev_date.strftime("%m_%Y"))
    if not prev_df.empty:
        df_raw['Tồn cũ'] = df_raw['Họ và Tên'].map(prev_df.set_index('Họ và Tên')['Tổng CA']).fillna(0.0)

# --- 6. AUTO-FILL NGÀY MỚI & THÁNG MỚI ---
now = datetime.now()
if sheet_name == now.strftime("%m_%Y") and now.hour >= 6:
    changed = False
    if now.day == 1: # Ngày đầu tháng
        col_01 = [c for c in DATE_COLS if c.startswith("01/")]
        if col_01 and (df_raw[col_01[0]].isna() | (df_raw[col_01[0]] == "")).all():
            prev_date = wd.replace(day=1) - timedelta(days=1)
            prev_df = get_data_safe(prev_date.strftime("%m_%Y"))
            if not prev_df.empty:
                last_cols = [c for c in prev_df.columns if "/" in str(c)]
                status_map = prev_df.set_index('Họ và Tên')[last_cols[-1]].to_dict()
                df_raw[col_01[0]] = df_raw['Họ và Tên'].map(status_map).fillna("")
                changed = True
    elif now.day > 1: # Các ngày trong tháng
        p_day, c_day = f"{(now.day-1):02d}/", f"{now.day:02d}/"
        col_p = [c for c in DATE_COLS if c.startswith(p_day)]
        col_c = [c for c in DATE_COLS if c.startswith(c_day)]
        if col_p and col_c:
            mask = (df_raw[col_c[0]].isna() | (df_raw[col_c[0]] == "")) & (df_raw[col_p[0]].notna() & (df_raw[col_p[0]] != ""))
            if mask.any():
                df_raw.loc[mask, col_c[0]] = df_raw.loc[mask, col_p[0]]
                changed = True
    if changed:
        df_raw = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)
        conn.update(worksheet=sheet_name, data=df_raw)

current_db = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)

# --- 7. GIAO DIỆN CHÍNH ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BÁO CÁO"])

with t1:
    c1, c2, c3 = st.columns([2, 2, 4])
    if c1.button("📤 LƯU DỮ LIỆU", type="primary", use_container_width=True):
        conn.update(worksheet=sheet_name, data=current_db)
        st.success("Đã lưu!")
        st.rerun()
    with c3:
        buf = io.BytesIO(); current_db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf.getvalue(), f"PVD_{sheet_name}.xlsx", use_container_width=True)

    all_col = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Tồn cũ', 'Tổng CA'] + DATE_COLS
    st.data_editor(current_db[all_col], use_container_width=True, height=550, hide_index=True)

# --- 8. SIDEBAR: QUẢN LÝ NHÂN SỰ & GIÀN ---
with st.sidebar:
    st.header("⚙️ CÀI ĐẶT HỆ THỐNG")
    
    # Quản lý Nhân sự (Lưu vào nhansu 999s)
    with st.expander("👤 QUẢN LÝ NHÂN SỰ"):
        new_name = st.text_input("Tên nhân viên mới:")
        if st.button("➕ Thêm Nhân Viên"):
            if new_name and new_name not in st.session_state.NAMES:
                st.session_state.NAMES.append(new_name)
                # Cập nhật trực tiếp lên sheet nhansu 999s
                df_save_ns = pd.DataFrame({"STT": range(1, len(st.session_state.NAMES)+1), "Họ và Tên": st.session_state.NAMES})
                conn.update(worksheet="nhansu 999s", data=df_save_ns)
                st.success(f"Đã thêm {new_name}")
                st.rerun()
        
        del_name = st.selectbox("Chọn tên cần xóa:", st.session_state.NAMES)
        if st.button("❌ Xóa Nhân Viên"):
            st.session_state.NAMES.remove(del_name)
            df_save_ns = pd.DataFrame({"STT": range(1, len(st.session_state.NAMES)+1), "Họ và Tên": st.session_state.NAMES})
            conn.update(worksheet="nhansu 999s", data=df_save_ns)
            st.warning(f"Đã xóa {del_name}")
            st.rerun()

    # Quản lý Giàn (Lưu vào config)
    with st.expander("🏗️ QUẢN LÝ GIÀN"):
        new_rig = st.text_input("Tên giàn mới:").upper()
        if st.button("➕ Thêm Giàn"):
            if new_rig and new_rig not in st.session_state.GIANS:
                st.session_state.GIANS.append(new_rig)
                # Cập nhật sheet config, cột GIANS
                df_rigs = pd.DataFrame({"GIANS": st.session_state.GIANS})
                conn.update(worksheet="config", data=df_rigs)
                st.success(f"Đã thêm giàn {new_rig}")
                st.rerun()
        
        del_rig = st.selectbox("Chọn giàn cần xóa:", st.session_state.GIANS)
        if st.button("❌ Xóa Giàn"):
            st.session_state.GIANS.remove(del_rig)
            df_rigs = pd.DataFrame({"GIANS": st.session_state.GIANS})
            conn.update(worksheet="config", data=df_rigs)
            st.warning(f"Đã xóa giàn {del_rig}")
            st.rerun()

    if st.button("🔄 REFRESH APP"):
        st.cache_data.clear()
        st.rerun()
