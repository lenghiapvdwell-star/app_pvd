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
    .stButton>button {width: 100%; border-radius: 5px;}
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

# --- 3. DANH MỤC CỐ ĐỊNH ---
COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
DEFAULT_RIGS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

# --- 4. KẾT NỐI & QUẢN LÝ DỮ LIỆU CẤU HÌNH ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5, show_spinner=False) # Giảm TTL để cập nhật nhanh hơn
def get_data_cached(wks_name):
    try:
        df = conn.read(worksheet=wks_name, ttl=0)
        return df if not df.empty else pd.DataFrame()
    except: return pd.DataFrame()

# Gọi danh sách Tên từ tab 'nhansu' cột '999s'
def load_config_names():
    df = get_data_cached("nhansu")
    if not df.empty and "999s" in df.columns:
        # Lọc bỏ giá trị trống và trả về list
        return [str(n).strip() for n in df["999s"].dropna().tolist() if str(n).strip()]
    return ["Bui Anh Phuong", "Le Thai Viet"] # Dự phòng

def load_config_rigs():
    df = get_data_cached("config")
    if not df.empty and "GIANS" in df.columns:
        return [str(g).strip().upper() for g in df["GIANS"].dropna().tolist() if str(g).strip()]
    return DEFAULT_RIGS

def save_config_names(name_list):
    df_save = pd.DataFrame({"999s": name_list})
    conn.update(worksheet="nhansu", data=df_save)
    st.cache_data.clear()

def save_config_rigs(rig_list):
    df_save = pd.DataFrame({"GIANS": rig_list})
    conn.update(worksheet="config", data=df_save)
    st.cache_data.clear()

# --- 5. ENGINE TÍNH TOÁN ---
def apply_logic(df, curr_m, curr_y, rigs):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    df_calc = df.copy()
    rigs_up = [r.upper() for r in rigs]
    date_cols = [c for c in df_calc.columns if "/" in c and "(" in c]

    for idx, row in df_calc.iterrows():
        if not str(row.get('Họ và Tên', '')).strip(): continue
        accrued = 0.0
        for col in date_cols:
            try:
                val = str(row.get(col, "")).strip().upper()
                if not val or val in ["NAN", "NONE", ""]: continue
                d_num = int(col[:2])
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

# --- 6. KHỞI TẠO BIẾN (SESSION STATE) ---
# Quan trọng: Load tên từ Google Sheet ngay khi mở app
if "NAMES" not in st.session_state:
    st.session_state.NAMES = load_config_names()
if "GIANS" not in st.session_state:
    st.session_state.GIANS = load_config_rigs()
if "store" not in st.session_state:
    st.session_state.store = {}

# --- 7. CHỌN THỜI GIAN ---
_, mc, _ = st.columns([3, 2, 3])
with mc: wd = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_name = wd.strftime("%m_%Y")
curr_m, curr_y = wd.month, wd.year
days_in_m = calendar.monthrange(curr_y, curr_m)[1]
DATE_COLS = [f"{d:02d}/{wd.strftime('%b')} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_y,curr_m,d).weekday()]})" for d in range(1, days_in_m+1)]

# --- 8. TẢI DỮ LIỆU & ĐỒNG BỘ NHÂN SỰ ---
if sheet_name not in st.session_state.store:
    with st.spinner(f"Đang đồng bộ dữ liệu {sheet_name}..."):
        df_month = get_data_cached(sheet_name)
        config_names = st.session_state.NAMES # Danh sách tên từ tab 'nhansu'
        
        if df_month.empty:
            # Tạo bảng mới dựa trên danh sách tên trong tab 'nhansu'
            df_month = pd.DataFrame({'STT': range(1, len(config_names)+1), 'Họ và Tên': config_names})
            df_month['Công ty'] = 'PVDWS'; df_month['Chức danh'] = 'Casing crew'; df_month['Tồn cũ'] = 0.0
            for c in DATE_COLS: df_month[c] = ""
            
            # Lấy tồn cũ tháng trước
            prev_date = wd.replace(day=1) - timedelta(days=1)
            prev_df = get_data_cached(prev_date.strftime("%m_%Y"))
            if not prev_df.empty:
                bals = prev_df.set_index('Họ và Tên')['Tổng CA'].to_dict()
                for idx, row in df_month.iterrows():
                    if row['Họ và Tên'] in bals: df_month.at[idx, 'Tồn cũ'] = bals[row['Họ và Tên']]
        else:
            # Đồng bộ: Nếu có tên mới ở tab 'nhansu' mà trong sheet tháng chưa có -> Thêm vào
            current_in_sheet = df_month['Họ và Tên'].dropna().tolist()
            new_people = [n for n in config_names if n not in current_in_sheet]
            if new_people:
                new_rows = pd.DataFrame({'Họ và Tên': new_people})
                new_rows['Công ty'] = 'PVDWS'; new_rows['Chức danh'] = 'Casing crew'; new_rows['Tồn cũ'] = 0.0
                for c in DATE_COLS: new_rows[c] = ""
                df_month = pd.concat([df_month, new_rows], ignore_index=True)
            
            # Sắp xếp lại STT
            df_month['STT'] = range(1, len(df_month) + 1)

        st.session_state.store[sheet_name] = apply_logic(df_month, curr_m, curr_y, st.session_state.GIANS)

# --- 9. GIAO DIỆN TABS ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 THỐNG KÊ"])

with t1:
    db = st.session_state.store[sheet_name]
    c1, c2, c3 = st.columns([2, 2, 4])
    
    if c1.button("📤 LƯU LẠI", type="primary"):
        with st.spinner("Đang lưu..."):
            db = apply_logic(db, curr_m, curr_y, st.session_state.GIANS)
            conn.update(worksheet=sheet_name, data=db)
            st.success("Đã lưu thành công!"); time.sleep(1); st.rerun()

    with c3:
        buf = io.BytesIO(); db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf.getvalue(), f"PVD_{sheet_name}.xlsx")

    # Bảng chỉnh sửa chính
    all_col = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Tồn cũ', 'Tổng CA'] + DATE_COLS
    ed_db = st.data_editor(db[all_col], use_container_width=True, height=600, hide_index=True)
    
    if not ed_db.equals(db[all_col]):
        st.session_state.store[sheet_name].update(ed_db)
        st.session_state.store[sheet_name] = apply_logic(st.session_state.store[sheet_name], curr_m, curr_y, st.session_state.GIANS)
        st.rerun()

with t2:
    # (Phần thống kê giữ nguyên như code cũ của bạn vì nó đã hoạt động tốt)
    st.subheader(f"📊 Thống kê nhân sự năm {curr_y}")
    sel_name = st.selectbox("🔍 Chọn nhân sự báo cáo:", st.session_state.NAMES)
    if sel_name:
        yearly_data = []
        rigs_up = [r.upper() for r in st.session_state.GIANS]
        for m in range(1, 13):
            m_df = get_data_cached(f"{m:02d}_{curr_y}")
            if not m_df.empty and sel_name in m_df['Họ và Tên'].values:
                p_row = m_df[m_df['Họ và Tên'] == sel_name].iloc[0]
                counts = {"Đi Biển": 0, "Nghỉ CA": 0, "Làm xưởng": 0, "Nghỉ/Ốm": 0}
                for c in m_df.columns:
                    if "/" in c and "(" in c:
                        val = str(p_row[c]).strip().upper()
                        if any(g in val for g in rigs_up) and val != "": counts["Đi Biển"] += 1
                        elif val == "CA": counts["Nghỉ CA"] += 1
                        elif val == "WS": counts["Làm xưởng"] += 1
                        elif val in ["NP", "ỐM"]: counts["Nghỉ/Ốm"] += 1
                for k, v in counts.items():
                    if v > 0: yearly_data.append({"Tháng": f"Tháng {m}", "Loại": k, "Số ngày": v})
        if yearly_data:
            df_chart = pd.DataFrame(yearly_data)
            fig = px.bar(df_chart, x="Tháng", y="Số ngày", color="Loại", barmode="stack", text="Số ngày", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            pv = df_chart.pivot_table(index='Loại', columns='Tháng', values='Số ngày', aggfunc='sum', fill_value=0).astype(int)
            pv['TỔNG NĂM'] = pv.sum(axis=1)
            st.table(pv)

# --- 10. SIDEBAR: QUẢN LÝ TỪ TAB NHANSU & CONFIG ---
with st.sidebar:
    st.header("⚙️ QUẢN LÝ DANH MỤC")
    
    # QUẢN LÝ NHÂN SỰ (Tab nhansu)
    with st.expander("👤 NHÂN VIÊN (Tab nhansu)", expanded=True):
        new_name = st.text_input("Tên NV mới:").strip()
        if st.button("➕ Thêm vào Google Sheets"):
            if new_name and new_name not in st.session_state.NAMES:
                st.session_state.NAMES.append(new_name)
                save_config_names(st.session_state.NAMES)
                st.success(f"Đã thêm {new_name}")
                st.session_state.store.clear(); st.rerun()
        
        st.markdown("---")
        del_name = st.selectbox("Xóa nhân viên:", [""] + st.session_state.NAMES)
        if st.button("❌ Xóa khỏi Google Sheets"):
            if del_name:
                st.session_state.NAMES.remove(del_name)
                save_config_names(st.session_state.NAMES)
                st.warning(f"Đã xóa {del_name}")
                st.session_state.store.clear(); st.rerun()

    # QUẢN LÝ GIÀN (Tab config)
    with st.expander("🏗️ GIÀN KHOAN (Tab config)"):
        ng = st.text_input("Tên giàn mới:").upper().strip()
        if st.button("➕ Thêm Giàn"):
            if ng and ng not in st.session_state.GIANS:
                st.session_state.GIANS.append(ng)
                save_config_rigs(st.session_state.GIANS)
                st.rerun()
        
        dg = st.selectbox("Xóa giàn:", st.session_state.GIANS)
        if st.button("❌ Xóa Giàn"):
            if len(st.session_state.GIANS) > 1:
                st.session_state.GIANS.remove(dg)
                save_config_rigs(st.session_state.GIANS)
                st.rerun()
