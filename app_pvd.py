import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="PVD MANAGEMENT SYSTEM", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 1rem;}
    .main-title {
        color: #007BFF !important; font-size: 38px !important; font-weight: bold !important;
        text-align: center !important; margin-bottom: 20px !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO ---
def display_pvd_logo():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        logo_path = os.path.join(current_dir, f"logo_pvd{ext}")
        if os.path.exists(logo_path):
            _, col2, _ = st.columns([4, 2, 4])
            with col2: st.image(logo_path, use_container_width=True)
            return True
    return False

display_pvd_logo()
st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. KẾT NỐI & LOAD DATA ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data_safe(wks, ttl=0):
    try:
        df = conn.read(worksheet=wks, ttl=ttl)
        if df is not None and not df.empty:
            # Ép kiểu String cho toàn bộ để tránh lỗi so sánh
            df.columns = [str(c).strip() for c in df.columns]
            for col in df.columns:
                if "/" in str(col): 
                    df[col] = df[col].astype(str).replace(['nan', 'None', 'NaN'], '')
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

def load_settings():
    df_c = get_data_safe("config gians")
    col_rig = "GIANS" if not df_c.empty and "GIANS" in df_c.columns else (df_c.columns[0] if not df_c.empty else None)
    rigs = [str(g).strip().upper() for g in df_c[col_rig].dropna().tolist()] if col_rig else ["PVD 8", "HK 11", "SDP", "PVD 11"]
    
    names = []
    for s in ["nhansu", "999s"]:
        df_n = get_data_safe(s)
        if not df_n.empty:
            col_name = "Họ và Tên" if "Họ và Tên" in df_n.columns else df_n.columns[0]
            names = [str(n).strip() for n in df_n[col_name].dropna().tolist() if str(n).strip()]
            if names: break
    return rigs, names

if "GIANS" not in st.session_state:
    st.session_state.GIANS, st.session_state.NAMES = load_settings()

# --- 4. LOGIC TÍNH TOÁN CA ---
def apply_pvd_logic(df, mm, yy, rigs):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    df_res = df.copy()
    date_cols = [c for c in df_res.columns if "/" in str(c)]
    rigs_up = [r.upper() for r in rigs]
    
    for idx, row in df_res.iterrows():
        ca_phat_sinh = 0.0
        for col in date_cols:
            val = str(row.get(col, "")).strip().upper()
            if not val or val in ["", "NAN", "NONE"]: continue
            try:
                d_val = int(str(col)[:2])
                dt = date(yy, mm, d_val)
                is_weekend = dt.weekday() >= 5
                is_holiday = dt in hols
                
                if any(rig in val for rig in rigs_up):
                    if is_holiday: ca_phat_sinh += 2.0
                    elif is_weekend: ca_phat_sinh += 1.0
                    else: ca_phat_sinh += 0.5
                elif val == "CA":
                    if not is_weekend and not is_holiday: ca_phat_sinh -= 1.0
            except: continue
            
        ton_cu = pd.to_numeric(row.get('Tồn cũ', 0), errors='coerce')
        df_res.at[idx, 'Tổng CA'] = round((ton_cu if not pd.isna(ton_cu) else 0.0) + ca_phat_sinh, 1)
    return df_res

# --- 5. XỬ LÝ DỮ LIỆU ---
_, mc, _ = st.columns([3, 2, 3])
with mc: wd = st.date_input("📅 CHỌN THÁNG:", value=date.today())

sheet_name = wd.strftime("%m_%Y")
mm, yy = wd.month, wd.year
# Tạo danh sách cột ngày chuẩn cho tháng đã chọn
DATE_HEADERS = [f"{d:02d}/{wd.strftime('%b')}" for d in range(1, calendar.monthrange(yy, mm)[1] + 1)]

df_main = get_data_safe(sheet_name)

# Khởi tạo dữ liệu nếu sheet trống hoặc thiếu cột
if df_main.empty:
    df_main = pd.DataFrame({'STT': range(1, len(st.session_state.NAMES)+1), 'Họ và Tên': st.session_state.NAMES, 'Tồn cũ': 0.0, 'Tổng CA': 0.0})
    for c in DATE_HEADERS: df_main[c] = ""
    # Chuyển tồn từ tháng trước
    prev_m = (wd.replace(day=1) - timedelta(days=1)).strftime("%m_%Y")
    df_prev = get_data_safe(prev_m)
    if not df_prev.empty:
        df_main['Tồn cũ'] = df_main['Họ và Tên'].map(df_prev.set_index('Họ và Tên')['Tổng CA']).fillna(0.0)
else:
    # Đảm bảo các cột ngày phải có mặt trong DF để tránh KeyError
    for c in DATE_HEADERS:
        if c not in df_main.columns: df_main[c] = ""

# Tính toán
current_df = apply_pvd_logic(df_main, mm, yy, st.session_state.GIANS)

# --- 6. GIAO DIỆN ---
t1, t2 = st.tabs(["📋 BẢNG ĐIỀU ĐỘNG", "📈 THỐNG KÊ"])

with t1:
    with st.expander("⚡ CẬP NHẬT NHANH (QUICK FILL)"):
        col_n, col_d = st.columns(2)
        p_names = col_n.multiselect("Nhân viên:", st.session_state.NAMES)
        p_dates = col_d.date_input("Ngày áp dụng:", value=(date(yy,mm,1), date(yy,mm,1)))
        col_m, col_v = st.columns(2)
        p_mode = col_m.selectbox("Trạng thái:", ["Đi Biển", "Nghỉ CA", "Xưởng/Phép", "Xóa"])
        p_val = col_v.selectbox("Chọn Giàn:", st.session_state.GIANS) if p_mode == "Đi Biển" else {"Nghỉ CA":"CA", "Xưởng/Phép":"WS", "Xóa":""}[p_mode]
        
        if st.button("ÁP DỤNG"):
            if p_names and len(p_dates) == 2:
                d1, d2 = p_dates
                while d1 <= d2:
                    if d1.month == mm:
                        c_col = f"{d1.day:02d}/{wd.strftime('%b')}"
                        if c_col in current_df.columns:
                            for name in p_names:
                                current_df.loc[current_df['Họ và Tên'] == name, c_col] = str(p_val)
                    d1 += timedelta(days=1)
                current_df = apply_pvd_logic(current_df, mm, yy, st.session_state.GIANS)
                conn.update(worksheet=sheet_name, data=current_df)
                st.rerun()

    c1, c2, c3 = st.columns([2,2,4])
    if c1.button("💾 LƯU DỮ LIỆU", type="primary"):
        conn.update(worksheet=sheet_name, data=current_df)
        st.success("Đã lưu!")
        st.rerun()
    with c3:
        out = io.BytesIO(); current_df.to_excel(out, index=False)
        st.download_button("📤 XUẤT EXCEL", out.getvalue(), f"PVD_{sheet_name}.xlsx")

    # Hiển thị bảng Editor - Đã bảo vệ bằng DATE_HEADERS chuẩn
    cols_to_show = ['STT', 'Họ và Tên', 'Tồn cũ', 'Tổng CA'] + [c for c in DATE_HEADERS if c in current_df.columns]
    edited_df = st.data_editor(current_df[cols_to_show], use_container_width=True, height=600, hide_index=True)

    if not edited_df.equals(current_df[cols_to_show]):
        for c in cols_to_show: current_df[c] = edited_df[c]
        current_df = apply_pvd_logic(current_df, mm, yy, st.session_state.GIANS)
        conn.update(worksheet=sheet_name, data=current_df)
        st.rerun()

with t2:
    st.bar_chart(current_df.set_index('Họ và Tên')['Tổng CA'])

with st.sidebar:
    st.header("⚙️ QUẢN LÝ")
    with st.expander("👤 NHÂN SỰ"):
        n_add = st.text_input("Tên mới:")
        if st.button("Thêm NV") and n_add:
            st.session_state.NAMES.append(n_add)
            conn.update(worksheet="nhansu", data=pd.DataFrame({"Họ và Tên": st.session_state.NAMES}))
            st.rerun()
    with st.expander("🏗️ GIÀN"):
        g_add = st.text_input("Giàn mới:").upper()
        if st.button("Thêm Giàn") and g_add:
            st.session_state.GIANS.append(g_add)
            conn.update(worksheet="config gians", data=pd.DataFrame({"GIANS": st.session_state.GIANS}))
            st.rerun()
    if st.button("🔄 LÀM MỚI"):
        st.cache_data.clear()
        st.rerun()
