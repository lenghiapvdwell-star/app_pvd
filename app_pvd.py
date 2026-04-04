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

# --- 3. KẾT NỐI & DANH MỤC ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data_safe(wks_name, ttl=0):
    try:
        df = conn.read(worksheet=wks_name, ttl=ttl)
        return df if (df is not None and not df.empty) else pd.DataFrame()
    except: return pd.DataFrame()

# Tải danh sách Giàn và Nhân sự từ sheet config
def load_config():
    df = get_data_safe("config", ttl=0)
    rigs = [str(g).strip().upper() for g in df["GIANS"].dropna().tolist()] if not df.empty and "GIANS" in df.columns else ["PVD 8", "HK 11"]
    names = [str(n).strip() for n in df["NAMES"].dropna().tolist()] if not df.empty and "NAMES" in df.columns else ["Nguyen Van A"]
    return rigs, names

def save_config(rig_list, name_list):
    df_save = pd.DataFrame({
        "GIANS": pd.Series(rig_list),
        "NAMES": pd.Series(name_list)
    })
    conn.update(worksheet="config", data=df_save)
    st.cache_data.clear()

if "GIANS" not in st.session_state or "NAMES" not in st.session_state:
    st.session_state.GIANS, st.session_state.NAMES = load_config()

# --- 4. ENGINE TÍNH TOÁN ---
def apply_logic(df, curr_m, curr_y, rigs):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    df_calc = df.copy()
    rigs_up = [r.upper() for r in rigs]
    date_cols = [c for c in df_calc.columns if "/" in str(c) and "(" in str(c)]

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

def push_balances_to_future(start_date, start_df, rigs):
    current_df = start_df.copy()
    current_date = start_date
    for _ in range(1, 12):
        days_in_m = calendar.monthrange(current_date.year, current_date.month)[1]
        next_date = current_date.replace(day=1) + timedelta(days=days_in_m)
        next_sheet = next_date.strftime("%m_%Y")
        next_df = get_data_safe(next_sheet)
        if next_df.empty: break
        balances = current_df.set_index('Họ và Tên')['Tổng CA'].to_dict()
        for idx, row in next_df.iterrows():
            name = row['Họ và Tên']
            if name in balances: next_df.at[idx, 'Tồn cũ'] = balances[name]
        next_df = apply_logic(next_df, next_date.month, next_date.year, rigs)
        conn.update(worksheet=next_sheet, data=next_df)
        current_df = next_df
        current_date = next_date

# --- 5. KHỞI TẠO DỮ LIỆU ---
_, mc, _ = st.columns([3, 2, 3])
with mc: wd = st.date_input("📅 CHỌN THÁNG:", value=date.today())

sheet_name = wd.strftime("%m_%Y")
curr_m, curr_y = wd.month, wd.year
days_in_m = calendar.monthrange(curr_y, curr_m)[1]
DATE_COLS = [f"{d:02d}/{wd.strftime('%b')} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_y,curr_m,d).weekday()]})" for d in range(1, days_in_m+1)]

df_raw = get_data_safe(sheet_name)

# Nếu tháng chưa tồn tại
if df_raw.empty:
    df_raw = pd.DataFrame({'STT': range(1, len(st.session_state.NAMES)+1), 'Họ và Tên': st.session_state.NAMES, 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Tồn cũ': 0.0, 'Tổng CA': 0.0})
    for c in DATE_COLS: df_raw[c] = ""
    prev_date = wd.replace(day=1) - timedelta(days=1)
    prev_df = get_data_safe(prev_date.strftime("%m_%Y"))
    if not prev_df.empty:
        balances = prev_df.set_index('Họ và Tên')['Tổng CA'].to_dict()
        df_raw['Tồn cũ'] = df_raw['Họ và Tên'].map(balances).fillna(0.0)

# --- AUTO-FILL NÂNG CẤP (Xuyên ngày & Xuyên tháng) ---
now = datetime.now()
if sheet_name == now.strftime("%m_%Y") and now.hour >= 6:
    changed = False
    # TRƯỜNG HỢP 1: Ngày đầu tháng (01) -> Lấy từ ngày cuối tháng trước
    if now.day == 1:
        col_01 = [c for c in DATE_COLS if c.startswith("01/")]
        if col_01 and (df_raw[col_01[0]].isna() | (df_raw[col_01[0]] == "")).all():
            prev_date = wd.replace(day=1) - timedelta(days=1)
            prev_df = get_data_safe(prev_date.strftime("%m_%Y"))
            if not prev_df.empty:
                last_cols = [c for c in prev_df.columns if "/" in str(c)]
                if last_cols:
                    # Lấy trạng thái ngày cuối cùng của tháng trước
                    status_map = prev_df.set_index('Họ và Tên')[last_cols[-1]].to_dict()
                    df_raw[col_01[0]] = df_raw['Họ và Tên'].map(status_map).fillna("")
                    changed = True

    # TRƯỜNG HỢP 2: Các ngày còn lại trong tháng -> Lấy từ ngày hôm trước
    elif now.day > 1:
        p_day, c_day = f"{(now.day-1):02d}/", f"{now.day:02d}/"
        col_p = [c for c in DATE_COLS if c.startswith(p_day)]
        col_c = [c for c in DATE_COLS if c.startswith(c_day)]
        if col_p and col_c:
            cp, cc = col_p[0], col_c[0]
            mask = (df_raw[cc].isna() | (df_raw[cc] == "")) & (df_raw[cp].notna() & (df_raw[cp] != ""))
            if mask.any():
                df_raw.loc[mask, cc] = df_raw.loc[mask, cp]
                changed = True

    if changed:
        df_raw = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)
        conn.update(worksheet=sheet_name, data=df_raw)
        st.toast("⚡ Tự động nối dữ liệu ngày mới!", icon="✅")

current_db = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)

# --- 6. GIAO DIỆN ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ TỔNG HỢP"])

with t1:
    c1, c2, c3 = st.columns([2, 2, 4])
    if c1.button("📤 LƯU & CẬP NHẬT CẢ NĂM", type="primary", use_container_width=True):
        with st.spinner("Đang đồng bộ..."):
            conn.update(worksheet=sheet_name, data=current_db)
            push_balances_to_future(wd, current_db, st.session_state.GIANS)
            st.cache_data.clear()
            st.success("Hoàn tất!")
            time.sleep(1)
            st.rerun()

    with c3:
        buf = io.BytesIO(); current_db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf.getvalue(), f"PVD_{sheet_name}.xlsx", use_container_width=True)

    with st.expander("🛠️ CÔNG CỤ NHẬP NHANH"):
        names = st.multiselect("Chọn nhân sự:", st.session_state.NAMES)
        dr = st.date_input("Khoảng ngày:", value=(date(curr_y, curr_m, 1), date(curr_y, curr_m, 1)))
        r1, r2, r3, r4 = st.columns(4)
        stt = r1.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm", "Xóa"])
        rig = r2.selectbox("Tên Giàn:", st.session_state.GIANS) if stt == "Đi Biển" else stt
        co = r3.selectbox("Công ty:", ["Giữ nguyên", "PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"])
        ti = r4.selectbox("Chức danh:", ["Giữ nguyên", "Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"])
        if st.button("✅ ÁP DỤNG"):
            if names and len(dr) == 2:
                for n in names:
                    idx_list = current_db.index[current_db['Họ và Tên'] == n].tolist()
                    if idx_list:
                        idx = idx_list[0]
                        if co != "Giữ nguyên": current_db.at[idx, 'Công ty'] = co
                        if ti != "Giữ nguyên": current_db.at[idx, 'Chức danh'] = ti
                        sd, ed = dr
                        while sd <= ed:
                            if sd.month == curr_m:
                                match = [c for c in DATE_COLS if c.startswith(f"{sd.day:02d}/")]
                                if match: current_db.at[idx, match[0]] = "" if stt == "Xóa" else rig
                            sd += timedelta(days=1)
                st.rerun()

    all_col = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Tồn cũ', 'Tổng CA'] + DATE_COLS
    ed_db = st.data_editor(current_db[all_col], use_container_width=True, height=500, hide_index=True)
    if not ed_db.equals(current_db[all_col]):
        for c in all_col: current_db[c] = ed_db[c]
        current_db = apply_logic(current_db, curr_m, curr_y, st.session_state.GIANS)
        st.rerun()

with t2:
    st.subheader(f"📊 Báo cáo nhân sự {curr_y}")
    sel_name = st.selectbox("🔍 Tìm kiếm:", st.session_state.NAMES)
    if sel_name:
        yearly_data = []
        for m in range(1, 13):
            m_df = get_data_safe(f"{m:02d}_{curr_y}")
            if not m_df.empty and sel_name in m_df['Họ và Tên'].values:
                p_row = m_df[m_df['Họ và Tên'] == sel_name].iloc[0]
                counts = {"Đi Biển": 0, "Nghỉ CA": 0, "Làm xưởng": 0, "Vắng": 0}
                for c in m_df.columns:
                    if "/" in str(c) and "(" in str(c):
                        val = str(p_row[c]).strip().upper()
                        if any(g in val for g in [r.upper() for r in st.session_state.GIANS]) and val != "": counts["Đi Biển"] += 1
                        elif val == "CA": counts["Nghỉ CA"] += 1
                        elif val == "WS": counts["Làm xưởng"] += 1
                        elif val in ["NP", "ỐM"]: counts["Vắng"] += 1
                for k, v in counts.items():
                    if v > 0: yearly_data.append({"Tháng": f"Tháng {m}", "Loại": k, "Số ngày": v})
        if yearly_data:
            df_chart = pd.DataFrame(yearly_data)
            st.plotly_chart(px.bar(df_chart, x="Tháng", y="Số ngày", color="Loại", barmode="stack", template="plotly_dark"), use_container_width=True)

with st.sidebar:
    st.header("⚙️ QUẢN LÝ HỆ THỐNG")
    with st.expander("👤 QUẢN LÝ NHÂN SỰ"):
        new_n = st.text_input("Tên nhân sự mới:")
        if st.button("➕ Thêm Nhân Viên"):
            if new_n and new_n not in st.session_state.NAMES:
                st.session_state.NAMES.append(new_n)
                save_config(st.session_state.GIANS, st.session_state.NAMES)
                st.rerun()
        del_n = st.selectbox("Chọn tên muốn xóa:", st.session_state.NAMES)
        if st.button("❌ Xóa Nhân Viên"):
            st.session_state.NAMES.remove(del_n)
            save_config(st.session_state.GIANS, st.session_state.NAMES)
            st.rerun()

    with st.expander("🏗️ QUẢN LÝ GIÀN"):
        new_g = st.text_input("Tên giàn mới:").upper()
        if st.button("➕ Thêm Giàn"):
            if new_g and new_g not in st.session_state.GIANS:
                st.session_state.GIANS.append(new_g)
                save_config(st.session_state.GIANS, st.session_state.NAMES)
                st.rerun()
        del_g = st.selectbox("Chọn giàn muốn xóa:", st.session_state.GIANS)
        if st.button("❌ Xóa Giàn"):
            st.session_state.GIANS.remove(del_g)
            save_config(st.session_state.GIANS, st.session_state.NAMES)
            st.rerun()
