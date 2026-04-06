import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import plotly.express as px

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="PVD MANAGEMENT SYSTEM", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 1rem;}
    .main-title {
        color: #007BFF !important; font-size: 32px !important; font-weight: bold !important;
        text-align: center !important; margin-bottom: 20px !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
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
st.markdown('<h1 class="main-title">QUẢN LÝ NHÂN SỰ PVD WELL SERVICES</h1>', unsafe_allow_html=True)

# --- 3. KẾT NỐI DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data_safe(wks, ttl=0):
    try:
        df = conn.read(worksheet=wks, ttl=ttl)
        if df is not None and not df.empty:
            df.columns = [str(c).strip() for c in df.columns]
            for col in df.columns:
                if "/" in str(col): 
                    df[col] = df[col].astype(str).replace(['nan', 'None', 'NaN'], '')
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

def load_settings():
    # Load Giàn từ "config gians"
    df_c = get_data_safe("config gians")
    col_rig = "GIANS" if not df_c.empty and "GIANS" in df_c.columns else (df_c.columns[0] if not df_c.empty else None)
    rigs = [str(g).strip().upper() for g in df_c[col_rig].dropna().tolist()] if col_rig else ["PVD 11", "HK 14", "SDP"]
    
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

# --- 4. LOGIC TÍNH CA ---
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

# --- 5. XỬ LÝ THỜI GIAN ---
_, mc, _ = st.columns([3, 2, 3])
with mc: wd = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_name = wd.strftime("%m_%Y")
mm, yy = wd.month, wd.year
DATE_HEADERS = [f"{d:02d}/{wd.strftime('%b')}" for d in range(1, calendar.monthrange(yy, mm)[1] + 1)]

df_main = get_data_safe(sheet_name)

if df_main.empty:
    df_main = pd.DataFrame({'STT': range(1, len(st.session_state.NAMES)+1), 'Họ và Tên': st.session_state.NAMES, 'Tồn cũ': 0.0, 'Tổng CA': 0.0})
    for c in DATE_HEADERS: df_main[c] = ""
    # Lấy tồn tháng trước
    prev_m = (wd.replace(day=1) - timedelta(days=1)).strftime("%m_%Y")
    df_prev = get_data_safe(prev_m)
    if not df_prev.empty:
        df_main['Tồn cũ'] = df_main['Họ và Tên'].map(df_prev.set_index('Họ và Tên')['Tổng CA']).fillna(0.0)
else:
    for c in DATE_HEADERS:
        if c not in df_main.columns: df_main[c] = ""

current_df = apply_pvd_logic(df_main, mm, yy, st.session_state.GIANS)

# --- 6. GIAO DIỆN TAB ---
t1, t2 = st.tabs(["📋 BẢNG ĐIỀU ĐỘNG", "📊 THỐNG KÊ TỒN CA"])

with t1:
    with st.expander("🛠️ CÔNG CỤ NHẬP NHANH (QUICK FILL)"):
        col_n, col_d = st.columns(2)
        p_names = col_n.multiselect("Chọn anh em:", st.session_state.NAMES)
        p_dates = col_d.date_input("Khoảng ngày:", value=(date(yy,mm,1), date(yy,mm,1)))
        col_m, col_v = st.columns(2)
        p_mode = col_m.selectbox("Trạng thái:", ["Đi Biển", "Nghỉ CA", "Xưởng/Phép", "Xóa"])
        p_val = col_v.selectbox("Chọn Giàn:", st.session_state.GIANS) if p_mode == "Đi Biển" else {"Nghỉ CA":"CA", "Xưởng/Phép":"WS", "Xóa":""}[p_mode]
        
        if st.button("✅ THỰC THI"):
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
        st.success("Đã đồng bộ lên Cloud!")
        st.rerun()
    with c3:
        out = io.BytesIO(); current_df.to_excel(out, index=False)
        st.download_button("📤 XUẤT FILE EXCEL", out.getvalue(), f"PVD_{sheet_name}.xlsx")

    cols_to_show = ['STT', 'Họ và Tên', 'Tồn cũ', 'Tổng CA'] + [c for c in DATE_HEADERS if c in current_df.columns]
    edited_df = st.data_editor(current_df[cols_to_show], use_container_width=True, height=600, hide_index=True)

    if not edited_df.equals(current_df[cols_to_show]):
        for c in cols_to_show: current_df[c] = edited_df[c]
        current_df = apply_pvd_logic(current_df, mm, yy, st.session_state.GIANS)
        conn.update(worksheet=sheet_name, data=current_df)
        st.rerun()

with t2:
    st.subheader(f"Biểu đồ Tồn CA - Tháng {mm}/{yy}")
    if not current_df.empty:
        # Sử dụng Plotly để vẽ biểu đồ cột đẹp và rõ ràng hơn
        fig = px.bar(
            current_df, 
            x='Họ và Tên', 
            y='Tổng CA',
            text='Tổng CA',
            color='Tổng CA',
            color_continuous_scale='Blues',
            labels={'Tổng CA': 'Số CA tồn dồn', 'Họ và Tên': 'Nhân viên'}
        )
        # Tự động xoay chữ nếu tên quá dài để không bị dính lẹo
        fig.update_layout(xaxis_tickangle=-45, height=600)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Chưa có dữ liệu để hiển thị biểu đồ.")

# --- 7. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ CÀI ĐẶT HỆ THỐNG")
    with st.expander("👤 QUẢN LÝ NHÂN SỰ"):
        n_add = st.text_input("Thêm nhân viên:")
        if st.button("Thêm") and n_add:
            st.session_state.NAMES.append(n_add)
            conn.update(worksheet="nhansu", data=pd.DataFrame({"Họ và Tên": st.session_state.NAMES}))
            st.rerun()
        n_del = st.selectbox("Xóa nhân viên:", [""] + st.session_state.NAMES)
        if st.button("Xóa") and n_del:
            st.session_state.NAMES.remove(n_del)
            conn.update(worksheet="nhansu", data=pd.DataFrame({"Họ và Tên": st.session_state.NAMES}))
            st.rerun()

    with st.expander("🏗️ QUẢN LÝ GIÀN"):
        g_add = st.text_input("Thêm giàn mới:").upper()
        if st.button("Thêm Giàn") and g_add:
            st.session_state.GIANS.append(g_add)
            conn.update(worksheet="config gians", data=pd.DataFrame({"GIANS": st.session_state.GIANS}))
            st.rerun()
        g_del = st.selectbox("Xóa giàn:", [""] + st.session_state.GIANS)
        if st.button("Xóa Giàn") and g_del:
            st.session_state.GIANS.remove(g_del)
            conn.update(worksheet="config gians", data=pd.DataFrame({"GIANS": st.session_state.GIANS}))
            st.rerun()

    if st.button("🔄 LÀM MỚI DỮ LIỆU"):
        st.cache_data.clear()
        st.rerun()
