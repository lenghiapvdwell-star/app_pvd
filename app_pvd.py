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
        font-size: 35px !important; 
        font-weight: bold !important;
        text-align: center !important; 
        margin-bottom: 20px !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    .stButton>button {border-radius: 5px;}
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

# --- 4. KẾT NỐI & DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600, show_spinner=False)
def get_data_cached(wks_name):
    try:
        df = conn.read(worksheet=wks_name, ttl=0)
        return df if not df.empty else pd.DataFrame()
    except: return pd.DataFrame()

def load_config_rigs():
    df = get_data_cached("config")
    if not df.empty and "GIANS" in df.columns:
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
                if not val or val == "NAN" or val == "NONE": continue
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

def push_balances_to_future(start_date, start_df, rigs):
    current_df = start_df.copy()
    current_date = start_date
    for i in range(1, 13 - current_date.month):
        next_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)
        next_sheet = next_date.strftime("%m_%Y")
        try:
            time.sleep(2)
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

# --- 6. KHỞI TẠO ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = load_config_rigs()
if "store" not in st.session_state:
    st.session_state.store = {}

_, mc, _ = st.columns([3, 2, 3])
with mc: wd = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_name = wd.strftime("%m_%Y")
curr_m, curr_y = wd.month, wd.year
days_in_m = calendar.monthrange(curr_y, curr_m)[1]
DATE_COLS = [f"{d:02d}/{wd.strftime('%b')} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_y,curr_m,d).weekday()]})" for d in range(1, days_in_m+1)]

if sheet_name not in st.session_state.store:
    with st.spinner(f"Đang tải dữ liệu {sheet_name}..."):
        df_raw = get_data_cached(sheet_name)
        if df_raw.empty:
            df_raw = pd.DataFrame(columns=['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Tồn cũ', 'Tổng CA'] + DATE_COLS)
        st.session_state.store[sheet_name] = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)

# --- 7. GIAO DIỆN CHÍNH ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG & QUẢN LÝ", "📊 BÁO CÁO TỔNG HỢP"])

with t1:
    db = st.session_state.store[sheet_name]
    
    # --- THANH CÔNG CỤ TRÊN CÙNG ---
    c1, c2, c3 = st.columns([2, 2, 4])
    if c1.button("📤 LƯU & CẬP NHẬT TOÀN NĂM", type="primary", use_container_width=True):
        with st.spinner("Đang chốt tồn và đồng bộ tháng tiếp theo..."):
            db = apply_logic(db, curr_m, curr_y, st.session_state.GIANS)
            conn.update(worksheet=sheet_name, data=db)
            push_balances_to_future(wd, db, st.session_state.GIANS)
            st.cache_data.clear()
            st.session_state.store.clear()
            st.success("Đã đồng bộ thành công!")
            st.rerun()

    with c3:
        buf = io.BytesIO()
        db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL THÁNG", buf.getvalue(), f"PVD_{sheet_name}.xlsx", use_container_width=True)

    # --- CÔNG CỤ TỔNG HỢP (NHÂN SỰ + GIÀN + NHẬP NHANH) ---
    with st.expander("🛠️ QUẢN LÝ DANH MỤC & NHẬP NHANH"):
        col_m1, col_m2 = st.columns(2)
        
        # 1. Quản lý Nhân sự
        with col_m1:
            st.markdown("##### 👤 QUẢN LÝ NHÂN SỰ")
            c_n1, c_n2 = st.columns([3, 1])
            new_worker = c_n1.text_input("Tên nhân viên mới:", key="add_worker_input")
            if c_n2.button("Thêm NV", use_container_width=True):
                if new_worker and new_worker not in db['Họ và Tên'].values:
                    new_row = pd.DataFrame([{
                        'STT': len(db) + 1, 'Họ và Tên': new_worker, 
                        'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 
                        'Tồn cũ': 0.0, 'Tổng CA': 0.0
                    }])
                    for c in DATE_COLS: new_row[c] = ""
                    db = pd.concat([db, new_row], ignore_index=True)
                    st.session_state.store[sheet_name] = db
                    st.success(f"Đã thêm {new_worker}")
                    st.rerun()
            
            del_worker = st.selectbox("Chọn nhân sự xóa:", [""] + db['Họ và Tên'].tolist(), key="del_worker_select")
            if st.button("❌ XÓA NHÂN SỰ KHỎI THÁNG NÀY", use_container_width=True) and del_worker:
                db = db[db['Họ và Tên'] != del_worker].reset_index(drop=True)
                db['STT'] = range(1, len(db) + 1)
                st.session_state.store[sheet_name] = db
                st.rerun()

        # 2. Quản lý Giàn khoan
        with col_m2:
            st.markdown("##### 🏗️ QUẢN LÝ GIÀN KHOAN")
            c_g1, c_g2 = st.columns([3, 1])
            new_rig = c_g1.text_input("Tên giàn mới:", key="add_rig_input").upper().strip()
            if c_g2.button("Thêm Giàn", use_container_width=True):
                if new_rig and new_rig not in st.session_state.GIANS:
                    st.session_state.GIANS.append(new_rig)
                    save_config_rigs(st.session_state.GIANS)
                    st.success(f"Đã thêm giàn {new_rig}")
                    st.rerun()
            
            del_rig = st.selectbox("Chọn giàn xóa:", [""] + st.session_state.GIANS, key="del_rig_select")
            if st.button("❌ XÓA GIÀN HỆ THỐNG", use_container_width=True) and del_rig:
                if len(st.session_state.GIANS) > 1:
                    st.session_state.GIANS.remove(del_rig)
                    save_config_rigs(st.session_state.GIANS)
                    st.rerun()

        st.markdown("---")
        
        # 3. Điều động nhanh
        st.markdown("##### 📅 ĐIỀU ĐỘNG NHANH THEO KHOẢNG NGÀY")
        names = st.multiselect("Chọn danh sách nhân sự:", db['Họ và Tên'].tolist())
        dr = st.date_input("Chọn khoảng ngày:", value=(date(curr_y, curr_m, 1), date(curr_y, curr_m, 5)))
        
        r1, r2, r3, r4 = st.columns(4)
        stt = r1.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm", "Xóa Trắng"])
        rig_sel = r2.selectbox("Tên Giàn:", st.session_state.GIANS) if stt == "Đi Biển" else stt
        co = r3.selectbox("Cập nhật Công ty:", ["Giữ nguyên"] + COMPANIES)
        ti = r4.selectbox("Cập nhật Chức danh:", ["Giữ nguyên"] + TITLES)
        
        if st.button("✅ ÁP DỤNG THAY ĐỔI NHANH", use_container_width=True, type="secondary"):
            if names and len(dr) == 2:
                for n in names:
                    idx_list = db.index[db['Họ và Tên'] == n].tolist()
                    if idx_list:
                        idx = idx_list[0]
                        if co != "Giữ nguyên": db.at[idx, 'Công ty'] = co
                        if ti != "Giữ nguyên": db.at[idx, 'Chức danh'] = ti
                        sd, ed = dr
                        while sd <= ed:
                            if sd.month == curr_m:
                                m_cols = [c for c in DATE_COLS if c.startswith(f"{sd.day:02d}/")]
                                if m_cols: db.at[idx, m_cols[0]] = "" if stt == "Xóa Trắng" else rig_sel
                            sd += timedelta(days=1)
                st.session_state.store[sheet_name] = apply_logic(db, curr_m, curr_y, st.session_state.GIANS)
                st.rerun()

    # --- BẢNG DỮ LIỆU CHI TIẾT ---
    st.markdown(f"### 📝 CHI TIẾT ĐIỀU ĐỘNG THÁNG {sheet_name}")
    all_col = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Tồn cũ', 'Tổng CA'] + DATE_COLS
    ed_db = st.data_editor(db[all_col], use_container_width=True, height=550, hide_index=True, key=f"editor_{sheet_name}")
    
    if not ed_db.equals(db[all_col]):
        for col in all_col:
            st.session_state.store[sheet_name][col] = ed_db[col].values
        st.session_state.store[sheet_name] = apply_logic(st.session_state.store[sheet_name], curr_m, curr_y, st.session_state.GIANS)
        st.rerun()

# --- 8. TAB BÁO CÁO ---
with t2:
    st.subheader(f"📊 Thống kê nhân sự năm {curr_y}")
    sel_name = st.selectbox("🔍 Chọn nhân sự báo cáo:", db['Họ và Tên'].tolist())
    if sel_name:
        yearly_data = []
        with st.spinner("Đang tính toán dữ liệu..."):
            for m in range(1, 13):
                m_sheet = f"{m:02d}_{curr_y}"
                m_df = get_data_cached(m_sheet)
                if not m_df.empty and sel_name in m_df['Họ và Tên'].values:
                    p_row = m_df[m_df['Họ và Tên'] == sel_name].iloc[0]
                    counts = {"Đi Biển": 0, "Nghỉ CA": 0, "Làm xưởng": 0, "Khác": 0}
                    for c in m_df.columns:
                        if "/" in c and "(" in c:
                            val = str(p_row[c]).strip().upper()
                            if any(g in val for g in st.session_state.GIANS): counts["Đi Biển"] += 1
                            elif val == "CA": counts["Nghỉ CA"] += 1
                            elif val == "WS": counts["Làm xưởng"] += 1
                            elif val in ["NP", "ỐM"]: counts["Khác"] += 1
                    for k, v in counts.items():
                        if v > 0: yearly_data.append({"Tháng": f"T{m}", "Loại": k, "Số ngày": v})
        
        if yearly_data:
            df_chart = pd.DataFrame(yearly_data)
            fig = px.bar(df_chart, x="Tháng", y="Số ngày", color="Loại", barmode="stack", text="Số ngày", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
            pv = df_chart.pivot_table(index='Loại', columns='Tháng', values='Số ngày', aggfunc='sum', fill_value=0).astype(int)
            pv['TỔNG CỘNG'] = pv.sum(axis=1)
            st.table(pv)
        else:
            st.info("Chưa có dữ liệu thống kê cho nhân sự này.")
