import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import time
import plotly.express as px
import os

# --- 1. CẤU HÌNH & STYLE (GIỮ NGUYÊN) ---
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

# --- 2. LOGO (GIỮ NGUYÊN) ---
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

# --- 4. KẾT NỐI & QUẢN LÝ DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300, show_spinner=False)
def get_data_cached(wks_name):
    try:
        df = conn.read(worksheet=wks_name, ttl=0)
        return df if not df.empty else pd.DataFrame()
    except: return pd.DataFrame()

def load_config_names():
    df = get_data_cached("nhansu")
    if not df.empty:
        df.columns = [str(c).strip() for c in df.columns]
        if "999s" in df.columns:
            return [str(n).strip() for n in df["999s"].dropna().tolist() if str(n).strip()]
        else:
            return [str(n).strip() for n in df.iloc[:, 0].dropna().tolist() if str(n).strip()]
    return [] 

def save_config_names(name_list):
    try:
        df_save = pd.DataFrame({"999s": name_list})
        conn.update(worksheet="nhansu", data=df_save)
        st.cache_data.clear()
        return True
    except: return False

def load_config_rigs():
    df = get_data_cached("config")
    if not df.empty:
        df.columns = [str(c).strip() for c in df.columns]
        if "GIANS" in df.columns:
            return [str(g).strip().upper() for g in df["GIANS"].dropna().tolist() if str(g).strip()]
    return DEFAULT_RIGS

def save_config_rigs(rig_list):
    try:
        df_save = pd.DataFrame({"GIANS": rig_list})
        conn.update(worksheet="config", data=df_save)
        st.cache_data.clear()
        return True
    except: return False

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
                if not val or val == "NAN": continue
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

# --- 6. HÀM CẬP NHẬT DÂY CHUYỀN ---
def push_balances_to_future(start_date, start_df, rigs):
    current_df = start_df.copy()
    current_date = start_date
    for i in range(1, 13 - current_date.month):
        next_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)
        next_sheet = next_date.strftime("%m_%Y")
        try:
            time.sleep(2.5) 
            next_df = get_data_cached(next_sheet)
            if next_df.empty: continue
            balances = current_df.set_index('Họ và Tên')['Tổng CA'].to_dict()
            for idx, row in next_df.iterrows():
                name = row['Họ và Tên']
                if name in balances: next_df.at[idx, 'Tồn cũ'] = balances[name]
            next_df = apply_logic(next_df, next_date.month, next_date.year, rigs)
            conn.update(worksheet=next_sheet, data=next_df)
            current_df = next_df
            current_date = next_date
        except: break

# --- 7. KHỞI TẠO DỮ LIỆU ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = load_config_rigs()
if "NAMES" not in st.session_state:
    st.session_state.NAMES = load_config_names()
if "store" not in st.session_state:
    st.session_state.store = {}

col_date1, col_date2, col_date3 = st.columns([3, 2, 3])
with col_date2: wd = st.date_input("📅 CHỌN THÁNG:", value=date.today())

sheet_name = wd.strftime("%m_%Y")
curr_m, curr_y = wd.month, wd.year
days_in_m = calendar.monthrange(curr_y, curr_m)[1]
DATE_COLS = [f"{d:02d}/{wd.strftime('%b')} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_y,curr_m,d).weekday()]})" for d in range(1, days_in_m+1)]

if sheet_name not in st.session_state.store:
    with st.spinner(f"Đang đồng bộ danh sách nhân sự từ Google Sheets..."):
        df_raw = get_data_cached(sheet_name)
        current_config_names = load_config_names()
        st.session_state.NAMES = current_config_names
        
        if df_raw.empty:
            df_raw = pd.DataFrame({'STT': range(1, len(current_config_names)+1), 'Họ và Tên': current_config_names})
            df_raw['Công ty'] = 'PVDWS'; df_raw['Chức danh'] = 'Casing crew'; df_raw['Tồn cũ'] = 0.0
            for c in DATE_COLS: df_raw[c] = ""
            prev_date = wd.replace(day=1) - timedelta(days=1)
            prev_df = get_data_cached(prev_date.strftime("%m_%Y"))
            if not prev_df.empty:
                balances = prev_df.set_index('Họ và Tên')['Tổng CA'].to_dict()
                for idx, row in df_raw.iterrows():
                    if row['Họ và Tên'] in balances: df_raw.at[idx, 'Tồn cũ'] = balances[row['Họ và Tên']]
        else:
            existing_names = df_raw['Họ và Tên'].dropna().tolist()
            new_names = [n for n in current_config_names if n not in existing_names]
            if new_names:
                new_df = pd.DataFrame({'Họ và Tên': new_names})
                new_df['Công ty'] = 'PVDWS'; new_df['Chức danh'] = 'Casing crew'; new_df['Tồn cũ'] = 0.0
                for c in DATE_COLS: new_df[c] = ""
                df_raw = pd.concat([df_raw, new_df], ignore_index=True)
            df_raw['STT'] = range(1, len(df_raw)+1)

        # Chống lỗi kiểu dữ liệu cho STT
        df_raw['STT'] = pd.to_numeric(df_raw['STT'], errors='coerce').fillna(0).astype(int)

        now = datetime.now()
        if sheet_name == now.strftime("%m_%Y") and now.hour >= 6 and now.day > 1:
            p_day, c_day = f"{(now.day-1):02d}/", f"{now.day:02d}/"
            col_p = [c for c in DATE_COLS if c.startswith(p_day)]
            col_c = [c for c in DATE_COLS if c.startswith(c_day)]
            if col_p and col_c:
                mask = (df_raw[col_c[0]].isna() | (df_raw[col_c[0]] == "")) & (df_raw[col_p[0]].notna() & (df_raw[col_p[0]] != ""))
                if mask.any():
                    df_raw.loc[mask, col_c[0]] = df_raw.loc[mask, col_p[0]]
                    df_raw = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)
                    conn.update(worksheet=sheet_name, data=df_raw)

        st.session_state.store[sheet_name] = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)

# --- 8. GIAO DIỆN CHÍNH ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ TỔNG HỢP"])

with t1:
    db = st.session_state.store[sheet_name]
    c1, c2, c3 = st.columns([2, 2, 4])
    
    if c1.button("📤 LƯU & CẬP NHẬT CẢ NĂM", type="primary", use_container_width=True):
        with st.spinner("Đang chốt tồn và đẩy sang các tháng kế tiếp..."):
            db = apply_logic(db, curr_m, curr_y, st.session_state.GIANS)
            conn.update(worksheet=sheet_name, data=db)
            push_balances_to_future(wd, db, st.session_state.GIANS)
            st.cache_data.clear()
            st.session_state.store.clear()
            st.success("Hoàn tất quy trình Pro!")
            time.sleep(1)
            st.rerun()

    with c3:
        buf = io.BytesIO()
        db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf.getvalue(), f"PVD_{sheet_name}.xlsx", use_container_width=True)

    with st.expander("🛠️ CÔNG CỤ NHẬP NHANH"):
        names_sel = st.multiselect("Nhân sự:", st.session_state.NAMES)
        dr = st.date_input("Khoảng ngày:", value=(date(curr_y, curr_m, 1), date(curr_y, curr_m, 5)))
        r1, r2, r3, r4 = st.columns(4)
        stt_list = ["Đi Biển", "CA", "WS", "NP", "Ốm", "Xóa"]
        stt = r1.selectbox("Trạng thái:", stt_list)
        rig = r2.selectbox("Tên Giàn:", st.session_state.GIANS) if stt == "Đi Biển" else stt
        co = r3.selectbox("Công ty:", ["Giữ nguyên"] + COMPANIES)
        ti = r4.selectbox("Chức danh:", ["Giữ nguyên"] + TITLES)
        if st.button("✅ ÁP DỤNG", use_container_width=True):
            if names_sel and len(dr) == 2:
                for n in names_sel:
                    idx_list = db.index[db['Họ và Tên'] == n].tolist()
                    if idx_list:
                        idx = idx_list[0]
                        if co != "Giữ nguyên": db.at[idx, 'Công ty'] = co
                        if ti != "Giữ nguyên": db.at[idx, 'Chức danh'] = ti
                        sd, ed = dr
                        while sd <= ed:
                            if sd.month == curr_m:
                                m_cols = [c for c in DATE_COLS if c.startswith(f"{sd.day:02d}/")]
                                if m_cols: db.at[idx, m_cols[0]] = "" if stt == "Xóa" else rig
                            sd += timedelta(days=1)
                st.session_state.store[sheet_name] = apply_logic(db, curr_m, curr_y, st.session_state.GIANS)
                st.rerun()

    # --- 10. CẤU HÌNH CỘT VÀ MÀU SẮC (SỬA LỖI TẠI ĐÂY) ---
    col_config = {
        "STT": st.column_config.NumberColumn("STT", width="min", pinned=True, format="%d"),
        "Họ và Tên": st.column_config.TextColumn("Họ và Tên", width="medium", pinned=True),
        "Công ty": st.column_config.SelectboxColumn("Công ty", options=COMPANIES, width="small"),
        "Chức danh": st.column_config.SelectboxColumn("Chức danh", options=TITLES, width="small"),
        "Tồn cũ": st.column_config.NumberColumn("Tồn cũ", format="%.1f", width="small"),
        "Tổng CA": st.column_config.NumberColumn("Tổng CA", format="%.1f", width="small"),
    }
    
    # Tạo danh sách trạng thái để gán màu trong Selectbox
    status_options = st.session_state.GIANS + ["CA", "WS", "NP", "ỐM", ""]
    
    for c in DATE_COLS:
        col_config[c] = st.column_config.SelectboxColumn(c, options=status_options, width="small")

    all_col = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Tồn cũ', 'Tổng CA'] + DATE_COLS
    available_cols = [c for c in all_col if c in db.columns]

    ed_db = st.data_editor(
        db[available_cols], 
        use_container_width=True, 
        height=600, 
        hide_index=True,
        column_config=col_config,
        key=f"editor_{sheet_name}"
    )
    
    if not ed_db.equals(db[available_cols]):
        st.session_state.store[sheet_name].update(ed_db)
        st.session_state.store[sheet_name] = apply_logic(st.session_state.store[sheet_name], curr_m, curr_y, st.session_state.GIANS)
        st.rerun()

with t2:
    st.subheader(f"📊 Thống kê nhân sự năm {curr_y}")
    sel_name = st.selectbox("🔍 Chọn nhân sự báo cáo:", st.session_state.NAMES)
    if sel_name:
        yearly_data = []
        rigs_up = [r.upper() for r in st.session_state.GIANS]
        with st.spinner("Đang tổng hợp báo cáo..."):
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

# --- 9. SIDEBAR: QUẢN LÝ TỔNG HỢP ---
with st.sidebar:
    st.header("⚙️ QUẢN LÝ HỆ THỐNG")
    with st.expander("🏗️ Quản lý Giàn Khoan"):
        ng = st.text_input("➕ Thêm giàn mới:").upper().strip()
        if st.button("Thêm Giàn"):
            if ng and ng not in st.session_state.GIANS:
                st.session_state.GIANS.append(ng)
                if save_config_rigs(st.session_state.GIANS): st.rerun()
        st.markdown("---")
        dg = st.selectbox("❌ Xóa giàn:", st.session_state.GIANS)
        if st.button("Xóa Giàn"):
            if len(st.session_state.GIANS) > 1:
                st.session_state.GIANS.remove(dg) 
                if save_config_rigs(st.session_state.GIANS): st.rerun()

    st.markdown("---")
    with st.expander("👤 Quản lý Nhân Sự"):
        new_per = st.text_input("➕ Thêm nhân viên mới:").strip()
        if st.button("Thêm Nhân Viên"):
            if new_per and new_per not in st.session_state.NAMES:
                st.session_state.NAMES.append(new_per)
                if save_config_names(st.session_state.NAMES):
                    st.success(f"Đã thêm {new_per}")
                    st.session_state.store.clear()
                    st.rerun()
        st.markdown("---")
        del_per = st.selectbox("❌ Xóa nhân viên:", st.session_state.NAMES)
        if st.button("Xóa Nhân Viên"):
            if del_per:
                st.session_state.NAMES.remove(del_per)
                if save_config_names(st.session_state.NAMES):
                    st.warning(f"Đã xóa {del_per}")
                    st.session_state.store.clear()
                    st.rerun()
    
    if st.button("🔄 LÀM MỚI DANH SÁCH"):
        st.cache_data.clear()
        st.session_state.clear()
        st.rerun()
