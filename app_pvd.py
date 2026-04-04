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

# --- 3. KẾT NỐI & CACHING (GIẢM TẢI API) ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300) # Lưu bộ nhớ đệm 5 phút để tránh lỗi 429
def get_data_cached(wks_name):
    try:
        df = conn.read(worksheet=wks_name, ttl=0)
        return df if (df is not None and not df.empty) else pd.DataFrame()
    except:
        return pd.DataFrame()

def load_config():
    # Thử đọc config
    df_conf = get_data_cached("config")
    rigs = [str(g).strip().upper() for g in df_conf["GIANS"].dropna().tolist()] if not df_conf.empty and "GIANS" in df_conf.columns else ["PVD 8", "HK 11", "SDP"]
    
    # Đọc nhân sự
    df_ns = get_data_cached("nhansu 999s")
    if not df_ns.empty and "Họ và Tên" in df_ns.columns:
        names = [str(n).strip() for n in df_ns["Họ và Tên"].dropna().tolist() if str(n).strip()]
    else:
        names = ["Bui Anh Phuong", "Le Trong Nghia", "Nguyen Van Manh"] # List rút gọn nếu lỗi
        
    return rigs, names

if "GIANS" not in st.session_state or "NAMES" not in st.session_state:
    st.session_state.GIANS, st.session_state.NAMES = load_config()

# --- 4. ENGINE TÍNH TOÁN ---
def apply_logic(df, curr_m, curr_y, rigs):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    df_calc = df.copy()
    rigs_up = [r.upper() for r in rigs]
    date_cols = [c for c in df_calc.columns if "/" in str(c)]

    for idx, row in df_calc.iterrows():
        if "Họ và Tên" not in row or not str(row.get('Họ và Tên', '')).strip(): continue
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

# --- 5. XỬ LÝ DỮ LIỆU THÁNG ---
_, mc, _ = st.columns([3, 2, 3])
with mc: wd = st.date_input("📅 CHỌN THÁNG:", value=date.today())

sheet_name = wd.strftime("%m_%Y")
curr_m, curr_y = wd.month, wd.year
days_in_m = calendar.monthrange(curr_y, curr_m)[1]
theoretical_cols = [f"{d:02d}/{wd.strftime('%b')} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_y,curr_m,d).weekday()]})" for d in range(1, days_in_m+1)]

# Đọc dữ liệu (Sử dụng cache)
df_raw = get_data_cached(sheet_name)

if df_raw.empty:
    df_raw = pd.DataFrame({'STT': range(1, len(st.session_state.NAMES)+1), 'Họ và Tên': st.session_state.NAMES, 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Tồn cũ': 0.0, 'Tổng CA': 0.0})
    for c in theoretical_cols: df_raw[c] = ""
    # Lấy tồn từ tháng trước
    prev_sheet = (wd.replace(day=1) - timedelta(days=1)).strftime("%m_%Y")
    df_prev = get_data_cached(prev_sheet)
    if not df_prev.empty:
        df_raw['Tồn cũ'] = df_raw['Họ và Tên'].map(df_prev.set_index('Họ và Tên')['Tổng CA']).fillna(0.0)

# --- AUTO-FILL (CHỈ CHẠY 1 LẦN KHI CẦN) ---
now = datetime.now()
if sheet_name == now.strftime("%m_%Y") and now.hour >= 6:
    changed = False
    if now.day == 1:
        c01 = [c for c in df_raw.columns if str(c).startswith("01/")]
        if c01 and not any(str(x).strip() for x in df_raw[c01[0]]):
            prev_sheet = (wd.replace(day=1) - timedelta(days=1)).strftime("%m_%Y")
            df_p = get_data_cached(prev_sheet)
            if not df_p.empty:
                last_col = [c for c in df_p.columns if "/" in str(c)][-1]
                df_raw[c01[0]] = df_raw['Họ và Tên'].map(df_p.set_index('Họ và Tên')[last_col]).fillna("")
                changed = True
    elif now.day > 1:
        p_day, c_day = f"{(now.day-1):02d}/", f"{now.day:02d}/"
        cp = [c for c in df_raw.columns if str(c).startswith(p_day)]
        cc = [c for c in df_raw.columns if str(c).startswith(c_day)]
        if cp and cc and not any(str(x).strip() for x in df_raw[cc[0]]):
            df_raw[cc[0]] = df_raw[cp[0]]
            changed = True
    
    if changed:
        df_raw = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)
        conn.update(worksheet=sheet_name, data=df_raw)
        st.cache_data.clear() # Xóa cache để nạp lại dữ liệu mới vừa cập nhật

current_db = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)

# --- 6. GIAO DIỆN ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BÁO CÁO"])

with t1:
    c1, c2, c3 = st.columns([2, 2, 4])
    if c1.button("📤 LƯU DỮ LIỆU", type="primary", use_container_width=True):
        with st.spinner("Đang gửi dữ liệu lên Google..."):
            conn.update(worksheet=sheet_name, data=current_db)
            st.cache_data.clear()
            st.success("Đã lưu!")
            time.sleep(1)
            st.rerun()

    with c3:
        buf = io.BytesIO(); current_db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf.getvalue(), f"PVD_{sheet_name}.xlsx", use_container_width=True)

    # EDITOR CHI TIẾT
    base = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Tồn cũ', 'Tổng CA']
    d_cols = [c for c in current_db.columns if "/" in str(c)]
    ed_db = st.data_editor(current_db[base + d_cols], use_container_width=True, height=550, hide_index=True)
    
    if not ed_db.equals(current_db[base + d_cols]):
        for col in (base + d_cols): current_db[col] = ed_db[col]
        current_db = apply_logic(current_db, curr_m, curr_y, st.session_state.GIANS)
        conn.update(worksheet=sheet_name, data=current_db)
        st.cache_data.clear()
        st.rerun()

with t2:
    person = st.selectbox("🔍 Xem báo cáo cá nhân:", st.session_state.NAMES)
    if person:
        # Giới hạn chỉ đọc tháng hiện tại và 1-2 tháng lân cận để tránh lỗi Quota
        st.info("Báo cáo đang lấy dữ liệu từ cache 5 phút để bảo vệ hệ thống.")
        m_df = current_db[current_db['Họ và Tên'] == person]
        if not m_df.empty:
            row = m_df.iloc[0]
            # (Phần này anh giữ nguyên logic vẽ biểu đồ cũ của anh)
            st.write(f"Tồn cuối tháng hiện tại của {person}: **{row['Tổng CA']}**")

with st.sidebar:
    st.header("⚙️ QUẢN LÝ")
    if st.button("🔄 LÀM MỚI DỮ LIỆU (CLEAR CACHE)"):
        st.cache_data.clear()
        st.rerun()
    # (Các phần Thêm/Xóa nhân sự giữ nguyên)
