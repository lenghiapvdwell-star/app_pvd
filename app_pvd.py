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

@st.cache_data(ttl=600, show_spinner=False)
def get_data_cached(wks_name):
    try:
        df = conn.read(worksheet=wks_name, ttl=0)
        return df if not df.empty else pd.DataFrame()
    except: return pd.DataFrame()

# Lấy danh sách nhân sự từ tab 'nhansu' (Cột A)
def load_names_from_sheet():
    df = get_data_cached("nhansu")
    if not df.empty:
        return [str(n).strip() for n in df.iloc[:, 0].dropna().tolist() if str(n).strip()]
    return ["Bui Anh Phuong", "Le Thai Viet"] # Dự phòng nếu sheet trống

def save_names_to_sheet(name_list):
    try:
        df_save = pd.DataFrame(name_list)
        conn.update(worksheet="nhansu", data=df_save)
        st.cache_data.clear()
        return True
    except: return False

COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
DEFAULT_RIGS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

# --- 4. ENGINE TÍNH TOÁN ---
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
            current_df, current_date = next_df, next_date
        except: break

# --- 5. KHỞI TẠO ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = get_data_cached("config")["GIANS"].dropna().tolist() if not get_data_cached("config").empty else DEFAULT_RIGS
if "NAMES" not in st.session_state:
    st.session_state.NAMES = load_names_from_sheet()
if "store" not in st.session_state:
    st.session_state.store = {}

_, mc, _ = st.columns([3, 2, 3])
with mc: wd = st.date_input("📅 CHỌN THÁNG:", value=date.today())

sheet_name = wd.strftime("%m_%Y")
curr_m, curr_y = wd.month, wd.year
days_in_m = calendar.monthrange(curr_y, curr_m)[1]
DATE_COLS = [f"{d:02d}/{wd.strftime('%b')} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_y,curr_m,d).weekday()]})" for d in range(1, days_in_m+1)]

if sheet_name not in st.session_state.store:
    df_raw = get_data_cached(sheet_name)
    if df_raw.empty:
        df_raw = pd.DataFrame({'STT': range(1, len(st.session_state.NAMES)+1), 'Họ và Tên': st.session_state.NAMES, 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Tồn cũ': 0.0, 'Tổng CA': 0.0})
        for c in DATE_COLS: df_raw[c] = ""
        prev_date = wd.replace(day=1) - timedelta(days=1)
        prev_df = get_data_cached(prev_date.strftime("%m_%Y"))
        if not prev_df.empty:
            balances = prev_df.set_index('Họ và Tên')['Tổng CA'].to_dict()
            df_raw['Tồn cũ'] = df_raw['Họ và Tên'].map(balances).fillna(0.0)

    # AUTO-FILL 6H SÁNG (BẢO VỆ DỮ LIỆU NHẬP TAY)
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

# --- 6. GIAO DIỆN ---
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

    # --- CÔNG CỤ NHẬP NHANH & QUẢN LÝ NHÂN SỰ ---
    with st.expander("🛠️ CÔNG CỤ NHẬP NHANH & QUẢN LÝ NHÂN SỰ"):
        # 1. Thêm nhân sự mới (Cơ chế giống thêm giàn)
        col_add1, col_add2 = st.columns([6, 2])
        new_worker = col_add1.text_input("👤 Tên nhân viên mới:", key="input_new_worker")
        if col_add2.button("➕ THÊM VÀO HỆ THỐNG", use_container_width=True):
            if new_worker and new_worker not in db['Họ và Tên'].values:
                # Tạo dòng mới
                new_row = pd.DataFrame([{
                    'STT': len(db) + 1, 'Họ và Tên': new_worker, 
                    'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 
                    'Tồn cũ': 0.0, 'Tổng CA': 0.0
                }])
                for c in DATE_COLS: new_row[c] = ""
                # Cập nhật vào dataframe hiện tại
                db = pd.concat([db, new_row], ignore_index=True)
                st.session_state.store[sheet_name] = db
                st.success(f"Đã thêm {new_worker}!")
                time.sleep(0.5)
                st.rerun()

        st.markdown("---")
        
        # 2. Điều động nhanh & Xóa khỏi bảng
        names = st.multiselect("Chọn nhân sự thao tác:", db['Họ và Tên'].tolist())
        
        # Nút xóa nhân sự (Chỉ xóa khỏi bảng tháng này)
        if st.button("❌ XÓA NHÂN SỰ KHỎI THÁNG NÀY", use_container_width=True):
            if names:
                db = db[~db['Họ và Tên'].isin(names)].reset_index(drop=True)
                db['STT'] = range(1, len(db) + 1)
                st.session_state.store[sheet_name] = db
                st.rerun()

        dr = st.date_input("Khoảng ngày:", value=(date(curr_y, curr_m, 1), date(curr_y, curr_m, 5)))
        r1, r2, r3, r4 = st.columns(4)
        stt = r1.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm", "Xóa Trắng"])
        rig = r2.selectbox("Tên Giàn:", st.session_state.GIANS) if stt == "Đi Biển" else stt
        co = r3.selectbox("Công ty:", ["Giữ nguyên"] + COMPANIES)
        ti = r4.selectbox("Chức danh:", ["Giữ nguyên"] + TITLES)
        
        if st.button("✅ ÁP DỤNG THAY ĐỔI", use_container_width=True, type="secondary"):
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
                                if m_cols: db.at[idx, m_cols[0]] = "" if stt == "Xóa Trắng" else rig
                            sd += timedelta(days=1)
                st.session_state.store[sheet_name] = apply_logic(db, curr_m, curr_y, st.session_state.GIANS)
                st.rerun()

    # --- HIỂN THỊ BẢNG DỮ LIỆU (PHẦN BẠN BỊ THIẾU) ---
    st.markdown("### 📝 BẢNG CHI TIẾT ĐIỀU ĐỘNG")
    all_col = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Tồn cũ', 'Tổng CA'] + DATE_COLS
    
    # Hiển thị bảng editor để sửa tay nếu cần
    ed_db = st.data_editor(
        db[all_col], 
        use_container_width=True, 
        height=600, 
        hide_index=True,
        key=f"editor_{sheet_name}" # Thêm key để tránh trùng lặp khi đổi tháng
    )
    
    # Kiểm tra nếu người dùng sửa trực tiếp trên bảng
    if not ed_db.equals(db[all_col]):
        # Cập nhật lại vào store
        for col in all_col:
            st.session_state.store[sheet_name][col] = ed_db[col].values
        # Tính toán lại logic (Tổng CA)
        st.session_state.store[sheet_name] = apply_logic(st.session_state.store[sheet_name], curr_m, curr_y, st.session_state.GIANS)
        st.rerun()

    with c3:
        buf = io.BytesIO()
        db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf.getvalue(), f"PVD_{sheet_name}.xlsx", use_container_width=True)

    with st.expander("🛠️ CÔNG CỤ NHẬP NHANH & QUẢN LÝ NHÂN SỰ"):
        # --- PHẦN 1: THÊM NHÂN VIÊN MỚI (GIỐNG THÊM GIÀN) ---
        c_add1, c_add2 = st.columns([6, 2])
        new_worker = c_add1.text_input("👤 Nhập tên nhân viên mới (Thêm vào hệ thống):", key="txt_new_worker")
        if c_add2.button("➕ THÊM NGAY", use_container_width=True):
            if new_worker and new_worker not in st.session_state.NAMES:
                # 1. Thêm vào danh sách tổng trong Session
                st.session_state.NAMES.append(new_worker)
                # 2. Lưu vào tab 'nhansu' trên Google Sheet
                save_names_to_sheet(st.session_state.NAMES)
                # 3. Tự động thêm luôn vào bảng điều động tháng hiện tại để chấm công
                new_row = pd.DataFrame([{
                    'STT': len(db) + 1, 
                    'Họ và Tên': new_worker, 
                    'Công ty': 'PVDWS', 
                    'Chức danh': 'Casing crew', 
                    'Tồn cũ': 0.0, 
                    'Tổng CA': 0.0
                }])
                for c in DATE_COLS: new_row[c] = ""
                db = pd.concat([db, new_row], ignore_index=True)
                st.session_state.store[sheet_name] = db
                st.success(f"Đã thêm {new_worker} vào hệ thống và bảng tháng {sheet_name}")
                time.sleep(1)
                st.rerun()

        st.markdown("---")

        # --- PHẦN 2: ĐIỀU ĐỘNG NHANH & XÓA ---
        names = st.multiselect("Chọn nhân sự để thao tác:", db['Họ và Tên'].tolist())
        
        # Nút xóa nhân sự khỏi bảng tháng này
        if st.button("❌ XÓA NHÂN SỰ KHỎI BẢNG THÁNG NÀY", use_container_width=True):
            if names:
                db = db[~db['Họ và Tên'].isin(names)].reset_index(drop=True)
                db['STT'] = range(1, len(db) + 1)
                st.session_state.store[sheet_name] = db
                st.rerun()

        dr = st.date_input("Khoảng ngày áp dụng:", value=(date(curr_y, curr_m, 1), date(curr_y, curr_m, 5)))
        r1, r2, r3, r4 = st.columns(4)
        stt = r1.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm", "Xóa Trắng"])
        rig = r2.selectbox("Tên Giàn:", st.session_state.GIANS) if stt == "Đi Biển" else stt
        co = r3.selectbox("Công ty:", ["Giữ nguyên"] + COMPANIES)
        ti = r4.selectbox("Chức danh:", ["Giữ nguyên"] + TITLES)
        
        if st.button("✅ ÁP DỤNG ĐIỀU ĐỘNG", type="primary", use_container_width=True):
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
                                if m_cols: db.at[idx, m_cols[0]] = "" if stt == "Xóa Trắng" else rig
                            sd += timedelta(days=1)
                st.session_state.store[sheet_name] = apply_logic(db, curr_m, curr_y, st.session_state.GIANS)
                st.rerun()

with t2:
    st.subheader(f"📊 Thống kê nhân sự năm {curr_y}")
    sel_name = st.selectbox("🔍 Chọn nhân sự báo cáo:", st.session_state.NAMES)
    if sel_name:
        yearly_data = []
        for m in range(1, 13):
            m_df = get_data_cached(f"{m:02d}_{curr_y}")
            if not m_df.empty and sel_name in m_df['Họ và Tên'].values:
                p_row = m_df[m_df['Họ và Tên'] == sel_name].iloc[0]
                counts = {"Đi Biển": 0, "Nghỉ CA": 0, "Làm xưởng": 0, "Nghỉ/Ốm": 0}
                for c in m_df.columns:
                    if "/" in c and "(" in c:
                        val = str(p_row[c]).strip().upper()
                        if any(g in val for g in [r.upper() for r in st.session_state.GIANS]) and val != "": counts["Đi Biển"] += 1
                        elif val == "CA": counts["Nghỉ CA"] += 1
                        elif val == "WS": counts["Làm xưởng"] += 1
                        elif val in ["NP", "ỐM"]: counts["Nghỉ/Ốm"] += 1
                for k, v in counts.items():
                    if v > 0: yearly_data.append({"Tháng": f"Tháng {m}", "Loại": k, "Số ngày": v})
        if yearly_data:
            df_chart = pd.DataFrame(yearly_data)
            st.plotly_chart(px.bar(df_chart, x="Tháng", y="Số ngày", color="Loại", barmode="stack", text="Số ngày", template="plotly_dark"), use_container_width=True)
            pv = df_chart.pivot_table(index='Loại', columns='Tháng', values='Số ngày', aggfunc='sum', fill_value=0).astype(int)
            pv['TỔNG NĂM'] = pv.sum(axis=1)
            st.table(pv)

with st.sidebar:
    st.header("⚙️ QUẢN LÝ HỆ THỐNG")
    # THÊM NHÂN VIÊN
    with st.expander("👤 QUẢN LÝ NHÂN SỰ"):
        new_name = st.text_input("Tên nhân viên mới:")
        if st.button("Thêm nhân viên"):
            if new_name and new_name not in st.session_state.NAMES:
                st.session_state.NAMES.append(new_name)
                save_names_to_sheet(st.session_state.NAMES)
                st.success(f"Đã thêm {new_name}")
                st.rerun()
    
    # THÊM GIÀN
    with st.expander("🏗️ QUẢN LÝ GIÀN"):
        ng = st.text_input("Tên giàn mới:").upper().strip()
        if st.button("Thêm giàn"):
            if ng and ng not in st.session_state.GIANS:
                st.session_state.GIANS.append(ng)
                conn.update(worksheet="config", data=pd.DataFrame({"GIANS": st.session_state.GIANS}))
                st.cache_data.clear()
                st.rerun()
