import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="PVD MANAGEMENT SYSTEM", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 1rem;}
    .main-title {
        color: #007BFF !important; 
        font-size: 38px !important; 
        font-weight: bold !important;
        text-align: center !important; 
        margin-top: -10px !important;
        margin-bottom: 20px !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    .stButton>button {width: 100%; border-radius: 5px;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO PVD ---
def display_pvd_logo():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        logo_path = os.path.join(current_dir, f"logo_pvd{ext}")
        if os.path.exists(logo_path):
            col1, col2, col3 = st.columns([4, 2, 4])
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
            # Ép kiểu String cho các cột ngày tháng để tránh lỗi TypeError
            for col in df.columns:
                if "/" in str(col):
                    df[col] = df[col].astype(str).replace(['nan', 'None', 'NaN'], '')
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

def load_all_settings():
    # 1. Đọc Giàn từ sheet "config gians"
    df_c = get_data_safe("config gians")
    # Giả sử cột chứa tên giàn là cột đầu tiên hoặc cột có tên "GIANS"
    col_rig = "GIANS" if not df_c.empty and "GIANS" in df_c.columns else (df_c.columns[0] if not df_c.empty else None)
    rigs = [str(g).strip().upper() for g in df_c[col_rig].dropna().tolist()] if col_rig else ["PVD 8", "HK 11", "SDP"]
    
    # 2. Đọc Nhân sự từ "nhansu" hoặc "999s"
    names = []
    for s_name in ["nhansu", "999s"]:
        df_n = get_data_safe(s_name)
        if not df_n.empty:
            col_name = "Họ và Tên" if "Họ và Tên" in df_n.columns else df_n.columns[0]
            names = [str(n).strip() for n in df_n[col_name].dropna().tolist() if str(n).strip()]
            if names: break
    
    # Nếu cả 2 sheet đều trống, dùng danh sách mặc định
    if not names:
        names = ["Bui Anh Phuong", "Le Trong Nghia", "Nguyen Van Manh", "Le Thai Viet"] # Rút gọn demo
        
    return rigs, names

if "GIANS" not in st.session_state or "NAMES" not in st.session_state:
    st.session_state.GIANS, st.session_state.NAMES = load_all_settings()

# --- 4. LOGIC TÍNH TOÁN ---
def apply_pvd_logic(df, mm, yy, rigs):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    df_res = df.copy()
    date_cols = [c for c in df_res.columns if "/" in str(c)]
    rigs_up = [r.upper() for r in rigs]
    
    for idx, row in df_res.iterrows():
        if not str(row.get('Họ và Tên', '')).strip(): continue
        acc = 0.0
        for col in date_cols:
            val = str(row.get(col, "")).strip().upper()
            if not val or val in ["NAN", "NONE", ""]: continue
            try:
                d_idx = int(str(col)[:2])
                dt = date(yy, mm, d_idx)
                is_we = dt.weekday() >= 5
                is_ho = dt in hols
                if any(r in val for r in rigs_up):
                    if is_ho: acc += 2.0
                    elif is_we: acc += 1.0
                    else: acc += 0.5
                elif val == "CA":
                    if not is_we and not is_ho: acc -= 1.0
            except: continue
        t_cu = pd.to_numeric(row.get('Tồn cũ', 0), errors='coerce')
        df_res.at[idx, 'Tổng CA'] = round(float(t_cu if not pd.isna(t_cu) else 0.0) + acc, 1)
    return df_res

# --- 5. XỬ LÝ DỮ LIỆU ---
_, mc, _ = st.columns([3, 2, 3])
with mc: wd = st.date_input("📅 CHỌN THÁNG:", value=date.today())

sheet_now = wd.strftime("%m_%Y")
mm, yy = wd.month, wd.year
days_in_m = calendar.monthrange(yy, mm)[1]
DATE_HEADERS = [f"{d:02d}/{wd.strftime('%b')} ({['T2','T3','T4','T5','T6','T7','CN'][date(yy,mm,d).weekday()]})" for d in range(1, days_in_m+1)]

df_main = get_data_safe(sheet_now)

if df_main.empty:
    df_main = pd.DataFrame({'STT': range(1, len(st.session_state.NAMES)+1), 'Họ và Tên': st.session_state.NAMES, 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Tồn cũ': 0.0, 'Tổng CA': 0.0})
    for c in DATE_HEADERS: df_main[c] = ""
    prev_s = (wd.replace(day=1) - timedelta(days=1)).strftime("%m_%Y")
    df_p = get_data_safe(prev_s)
    if not df_p.empty:
        df_main['Tồn cũ'] = df_main['Họ và Tên'].map(df_p.set_index('Họ và Tên')['Tổng CA']).fillna(0.0)

current_df = apply_pvd_logic(df_main, mm, yy, st.session_state.GIANS)

# --- 6. GIAO DIỆN ---
tab1, tab2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 THỐNG KÊ"])

with tab1:
    with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH"):
        c_n, c_d = st.columns([1, 1])
        sel_names = c_n.multiselect("Nhân sự:", st.session_state.NAMES)
        date_range = c_d.date_input("Ngày áp dụng:", value=(date(yy, mm, 1), date(yy, mm, 1)))
        r1, r2 = st.columns(2)
        mode = r1.selectbox("Loại:", ["Đi Biển", "Nghỉ CA", "Làm Xưởng (WS)", "Nghỉ Phép", "Xóa"])
        val_f = r2.selectbox("Chọn Giàn:", st.session_state.GIANS) if mode == "Đi Biển" else {"Nghỉ CA":"CA", "Làm Xưởng (WS)":"WS", "Nghỉ Phép":"NP", "Xóa":""}[mode]
        
        if st.button("✅ ÁP DỤNG"):
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
                st.success("Đã áp dụng tạm thời!")

    b1, b2, b3 = st.columns([2, 2, 4])
    if b1.button("📤 LƯU LÊN CLOUD", type="primary"):
        conn.update(worksheet=sheet_now, data=current_df)
        st.success("Đã lưu!")
        st.rerun()
    with b3:
        out = io.BytesIO(); current_df.to_excel(out, index=False)
        st.download_button("📥 XUẤT EXCEL", out.getvalue(), f"PVD_{sheet_now}.xlsx")

    show_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Tồn cũ', 'Tổng CA'] + DATE_HEADERS
    edited = st.data_editor(current_df[show_cols], use_container_width=True, height=600, hide_index=True)
    if not edited.equals(current_df[show_cols]):
        for c in show_cols: current_df[c] = edited[c]
        current_df = apply_pvd_logic(current_df, mm, yy, st.session_state.GIANS)
        conn.update(worksheet=sheet_now, data=current_df)
        st.rerun()

# --- 7. SIDEBAR QUẢN LÝ ---
with st.sidebar:
    st.header("⚙️ CÀI ĐẶT")
    # Nhân sự lưu vào sheet "nhansu"
    with st.expander("👤 NHÂN SỰ"):
        n_add = st.text_input("Tên mới:")
        if st.button("Thêm") and n_add:
            st.session_state.NAMES.append(n_add)
            conn.update(worksheet="nhansu", data=pd.DataFrame({"Họ và Tên": st.session_state.NAMES}))
            st.rerun()
        n_del = st.selectbox("Xóa nhân sự:", st.session_state.NAMES)
        if st.button("Xóa"):
            st.session_state.NAMES.remove(n_del)
            conn.update(worksheet="nhansu", data=pd.DataFrame({"Họ và Tên": st.session_state.NAMES}))
            st.rerun()

    # Giàn lưu vào sheet "config gians"
    with st.expander("🏗️ GIÀN KHOAN"):
        g_add = st.text_input("Tên giàn mới:").upper()
        if st.button("Thêm Giàn") and g_add:
            st.session_state.GIANS.append(g_add)
            conn.update(worksheet="config gians", data=pd.DataFrame({"GIANS": st.session_state.GIANS}))
            st.rerun()
        g_del = st.selectbox("Xóa giàn:", st.session_state.GIANS)
        if st.button("Xóa Giàn"):
            st.session_state.GIANS.remove(g_del)
            conn.update(worksheet="config gians", data=pd.DataFrame({"GIANS": st.session_state.GIANS}))
            st.rerun()
            
    if st.button("🔄 REFRESH"):
        st.cache_data.clear()
        st.rerun()
