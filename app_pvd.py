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

# --- 2. LOGO PVD ---
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
            for col in df.columns:
                if "/" in str(col): df[col] = df[col].astype(str).replace(['nan', 'None', 'NaN'], '')
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

def load_settings():
    # Load Giàn từ "config gians"
    df_c = get_data_safe("config gians")
    col_rig = "GIANS" if not df_c.empty and "GIANS" in df_c.columns else (df_c.columns[0] if not df_c.empty else None)
    rigs = [str(g).strip().upper() for g in df_c[col_rig].dropna().tolist()] if col_rig else ["PVD 8", "HK 11", "SDP"]
    
    # Load Nhân sự từ "nhansu" hoặc "999s"
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

# --- 4. ENGINE TÍNH TOÁN QUY TẮC CA (QUAN TRỌNG) ---
def apply_pvd_logic(df, mm, yy, rigs):
    # Danh sách ngày lễ 2026
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    df_res = df.copy()
    date_cols = [c for c in df_res.columns if "/" in str(c)]
    rigs_up = [r.upper() for r in rigs]
    
    for idx, row in df_res.iterrows():
        if not str(row.get('Họ và Tên', '')).strip(): continue
        ca_thang_nay = 0.0
        
        for col in date_cols:
            val = str(row.get(col, "")).strip().upper()
            if not val or val in ["NAN", "NONE", ""]: continue
            
            try:
                d_idx = int(str(col)[:2])
                dt = date(yy, mm, d_idx)
                is_we = dt.weekday() >= 5 # Thứ 7, CN
                is_ho = dt in hols      # Ngày lễ
                
                # Quy tắc cộng:
                if any(r in val for r in rigs_up): # Đi giàn
                    if is_ho: ca_thang_nay += 2.0
                    elif is_we: ca_thang_nay += 1.0
                    else: ca_thang_nay += 0.5
                elif val == "CA": # Nghỉ CA
                    if not is_we and not is_ho: ca_thang_nay -= 1.0
            except: continue
            
        # Tổng CA = Tồn cũ + CA phát sinh tháng này
        ton_cu = pd.to_numeric(row.get('Tồn cũ', 0), errors='coerce')
        if pd.isna(ton_cu): ton_cu = 0.0
        df_res.at[idx, 'Tổng CA'] = round(ton_cu + ca_thang_nay, 1)
        
    return df_res

# --- 5. QUẢN LÝ THỜI GIAN & CHUYỂN TỒN ---
_, mc, _ = st.columns([3, 2, 3])
with mc: wd = st.date_input("📅 THÁNG LÀM VIỆC:", value=date.today())

sheet_now = wd.strftime("%m_%Y")
mm, yy = wd.month, wd.year
days_in_m = calendar.monthrange(yy, mm)[1]
DATE_HEADERS = [f"{d:02d}/{wd.strftime('%b')} ({['T2','T3','T4','T5','T6','T7','CN'][date(yy,mm,d).weekday()]})" for d in range(1, days_in_m+1)]

df_main = get_data_safe(sheet_now)

# Nếu tháng mới chưa có dữ liệu -> Tự tạo và lấy Tồn cũ từ tháng trước
if df_main.empty:
    df_main = pd.DataFrame({'STT': range(1, len(st.session_state.NAMES)+1), 'Họ và Tên': st.session_state.NAMES, 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Tồn cũ': 0.0, 'Tổng CA': 0.0})
    for c in DATE_HEADERS: df_main[c] = ""
    
    # Logic Lấy Tồn: Tìm sheet tháng liền trước
    prev_date = wd.replace(day=1) - timedelta(days=1)
    prev_sheet = prev_date.strftime("%m_%Y")
    df_prev = get_data_safe(prev_sheet)
    
    if not df_prev.empty:
        # Áp dụng nạp Tổng CA cũ -> Tồn cũ mới
        df_main['Tồn cũ'] = df_main['Họ và Tên'].map(df_prev.set_index('Họ và Tên')['Tổng CA']).fillna(0.0)

current_df = apply_pvd_logic(df_main, mm, yy, st.session_state.GIANS)

# --- 6. GIAO DIỆN ĐIỀU ĐỘNG ---
tab1, tab2 = st.tabs(["🚀 ĐIỀU ĐỘNG CHI TIẾT", "📊 THỐNG KÊ"])

with tab1:
    # Nhập nhanh
    with st.expander("🛠️ CÔNG CỤ NHẬP NHANH"):
        c1, c2 = st.columns(2)
        sel_names = c1.multiselect("Nhân sự:", st.session_state.NAMES)
        date_range = c2.date_input("Khoảng ngày:", value=(date(yy, mm, 1), date(yy, mm, 1)))
        r1, r2 = st.columns(2)
        mode = r1.selectbox("Loại hình:", ["Đi Biển", "Nghỉ CA", "Làm Xưởng (WS)", "Nghỉ Phép", "Xóa"])
        val_f = r2.selectbox("Chọn Giàn:", st.session_state.GIANS) if mode == "Đi Biển" else {"Nghỉ CA":"CA", "Làm Xưởng (WS)":"WS", "Nghỉ Phép":"NP", "Xóa":""}[mode]
        
        if st.button("✅ THỰC THI"):
            if sel_names and len(date_range) == 2:
                sd, ed = date_range
                while sd <= ed:
                    if sd.month == mm:
                        col_m = [c for c in current_df.columns if str(c).startswith(f"{sd.day:02d}/")]
                        if col_m:
                            for name in sel_names:
                                idxs = current_df.index[current_df['Họ và Tên'] == name].tolist()
                                if idxs: current_df.at[idxs[0], col_m[0]] = str(val_f)
                    sd += timedelta(days=1)
                st.success("Đã cập nhật tạm thời!")

    # Lưu và Xuất
    b1, b2, b3 = st.columns([2, 2, 4])
    if b1.button("📤 LƯU LÊN CLOUD (GOOGLE SHEET)", type="primary"):
        conn.update(worksheet=sheet_now, data=current_df)
        st.success("Đã đồng bộ tồn CA và lịch trình!")
        st.rerun()
    with b3:
        out = io.BytesIO(); current_df.to_excel(out, index=False)
        st.download_button("📥 XUẤT EXCEL", out.getvalue(), f"PVD_{sheet_now}.xlsx")

    # Bảng Data Editor
    show_cols = ['STT', 'Họ và Tên', 'Tồn cũ', 'Tổng CA'] + DATE_HEADERS
    edited = st.data_editor(current_df[show_cols], use_container_width=True, height=600, hide_index=True)
    
    if not edited.equals(current_df[show_cols]):
        for c in show_cols: current_df[c] = edited[c]
        current_df = apply_pvd_logic(current_df, mm, yy, st.session_state.GIANS)
        conn.update(worksheet=sheet_now, data=current_df)
        st.rerun()

with tab2:
    st.info("Thống kê tồn CA của anh em trong tháng này:")
    st.bar_chart(current_df.set_index('Họ và Tên')['Tổng CA'])

# --- 7. SIDEBAR QUẢN LÝ ---
with st.sidebar:
    st.header("⚙️ HỆ THỐNG")
    with st.expander("👤 NHÂN SỰ (Sheet: nhansu)"):
        n_add = st.text_input("Thêm tên:")
        if st.button("Thêm") and n_add:
            st.session_state.NAMES.append(n_add)
            conn.update(worksheet="nhansu", data=pd.DataFrame({"Họ và Tên": st.session_state.NAMES}))
            st.rerun()
        n_del = st.selectbox("Xóa tên:", st.session_state.NAMES)
        if st.button("Xóa"):
            st.session_state.NAMES.remove(n_del)
            conn.update(worksheet="nhansu", data=pd.DataFrame({"Họ và Tên": st.session_state.NAMES}))
            st.rerun()

    with st.expander("🏗️ GIÀN KHOAN (Sheet: config gians)"):
        g_add = st.text_input("Giàn mới:").upper()
        if st.button("Thêm Giàn") and g_add:
            st.session_state.GIANS.append(g_add)
            conn.update(worksheet="config gians", data=pd.DataFrame({"GIANS": st.session_state.GIANS}))
            st.rerun()
        g_del = st.selectbox("Xóa giàn:", st.session_state.GIANS)
        if st.button("Xóa Giàn"):
            st.session_state.GIANS.remove(g_del)
            conn.update(worksheet="config gians", data=pd.DataFrame({"GIANS": st.session_state.GIANS}))
            st.rerun()
