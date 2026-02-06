import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import plotly.express as px

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 0.5rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; font-size: 50px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 3px 3px 6px #000 !important;
        font-family: 'Arial Black', sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER ---
c_logo, _ = st.columns([1, 4])
with c_logo:
    if os.path.exists("logo_pvd.png"): st.image("logo_pvd.png", width=220)
    else: st.markdown("### 🔴 PVD WELL")

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. CHỌN THÁNG ---
_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today(), key="main_date_picker")

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b") 

# Tính toán tên sheet tháng trước để lấy tồn
prev_date = working_date.replace(day=1) - timedelta(days=1)
prev_sheet_name = prev_date.strftime("%m_%Y")

# Reset khi đổi tháng
if "current_sheet" not in st.session_state: st.session_state.current_sheet = sheet_name
if st.session_state.current_sheet != sheet_name:
    for key in list(st.session_state.keys()):
        if key.startswith("ed_") or key == "db": del st.session_state[key]
    st.session_state.current_sheet = sheet_name
    st.rerun()

# --- 4. KẾT NỐI & DANH SÁCH NHÂN SỰ ---
conn = st.connection("gsheets", type=GSheetsConnection)
GIANS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]
COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong"]

# HÀM LẤY TỒN THÁNG TRƯỚC
def get_previous_month_ca():
    try:
        df_prev = conn.read(worksheet=prev_sheet_name, ttl=0)
        if df_prev is not None:
            return df_prev.set_index('Họ và Tên')['Quỹ CA Tổng'].to_dict()
    except: return {}
    return {}

if 'db' not in st.session_state:
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        if df_load is not None and not df_load.empty:
            st.session_state.db = df_load
        else: raise Exception
    except:
        # Nếu là sheet mới, tự động bốc tồn tháng trước sang
        prev_ca_map = get_previous_month_ca()
        st.session_state.db = pd.DataFrame({
            'STT': range(1, 66), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 
            'Chức danh': 'Casing crew', 'Job Detail': '', 
            'CA Tháng Trước': [prev_ca_map.get(name, 0.0) for name in NAMES_64],
            'Quỹ CA Tổng': 0.0
        })

num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
for col in DATE_COLS:
    if col not in st.session_state.db.columns: st.session_state.db[col] = ""

# --- 5. LOGIC TÍNH CA CỦA BẠN (KHÔNG ĐƯỢC SAI) ---
def calculate_pvd_logic(df):
    hols = [date(2026,1,1), date(2026,4,30), date(2026,5,1), date(2026,9,2),
            date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19)]
    
    def row_calc(row):
        accrued = 0.0
        for col in DATE_COLS:
            v = str(row.get(col, "")).strip().upper()
            if not v or v == "NAN": continue
            try:
                dt = date(curr_year, curr_month, int(col[:2]))
                is_we = dt.weekday() >= 5
                is_ho = dt in hols
                # CỘNG CA KHI ĐI BIỂN
                if any(g.upper() in v for g in GIANS):
                    if is_ho: accrued += 2.0
                    elif is_we: accrued += 1.0
                    else: accrued += 0.5
                # TRỪ CA (CHỈ TRỪ NGÀY THƯỜNG VÀ KHÔNG LỄ)
                elif v == "CA":
                    if not is_we and not is_ho: accrued -= 1.0
                # CÁC TRƯỜNG HỢP KHÁC: WS, NP, ỐM -> KHÔNG TRỪ
            except: continue
        return accrued

    df['CA Tháng Trước'] = pd.to_numeric(df['CA Tháng Trước'], errors='coerce').fillna(0.0)
    df['Quỹ CA Tổng'] = df['CA Tháng Trước'] + df.apply(row_calc, axis=1)
    return df

st.session_state.db = calculate_pvd_logic(st.session_state.db)

# --- 6. GIAO DIỆN ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ"])

with t1:
    bc1, bc2, _ = st.columns([1.5, 1.5, 5])
    with bc1:
        if st.button("📤 LƯU CLOUD", type="primary", use_container_width=True):
            conn.update(worksheet=sheet_name, data=st.session_state.db)
            st.success("Đã lưu!")
    with bc2:
        buf = io.BytesIO()
        st.session_state.db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf, f"PVD_{sheet_name}.xlsx")

    # CÔNG CỤ CẬP NHẬT NHANH
    with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH"):
        c1, c2 = st.columns([2, 1])
        f_staff = c1.multiselect("Nhân sự:", NAMES_64)
        f_date = c2.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, num_days)))
        r2_1, r2_2, r2_3, r2_4 = st.columns(4)
        f_status = r2_1.selectbox("Trạng thái:", ["Không đổi", "Đi Biển", "CA", "WS", "NP", "Ốm"])
        f_val = r2_2.selectbox("Giàn:", GIANS) if f_status == "Đi Biển" else f_status
        f_co = r2_3.selectbox("Cty:", ["Không đổi"] + COMPANIES)
        f_ti = r2_4.selectbox("Chức danh:", ["Không đổi"] + TITLES)
        if st.button("✅ ÁP DỤNG"):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                for person in f_staff:
                    idx = st.session_state.db.index[st.session_state.db['Họ và Tên'] == person][0]
                    if f_co != "Không đổi": st.session_state.db.at[idx, 'Công ty'] = f_co
                    if f_ti != "Không đổi": st.session_state.db.at[idx, 'Chức danh'] = f_ti
                    if f_status != "Không đổi":
                        for i in range((f_date[1] - f_date[0]).days + 1):
                            d = f_date[0] + timedelta(days=i)
                            col_n = f"{d.day:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][d.weekday()]})"
                            if col_n in st.session_state.db.columns: st.session_state.db.at[idx, col_n] = f_val
                st.rerun()

    config = {
        "STT": st.column_config.NumberColumn(disabled=True),
        "Họ và Tên": st.column_config.TextColumn(disabled=True),
        "Quỹ CA Tổng": st.column_config.NumberColumn("Tồn Cuối", format="%.1f", disabled=True),
        "CA Tháng Trước": st.column_config.NumberColumn("Tồn Đầu", format="%.1f"),
    }
    st.data_editor(st.session_state.db, column_config=config, use_container_width=True, height=600, hide_index=True, key=f"ed_{sheet_name}")

with t2:
    # Biểu đồ năm (Giữ nguyên tính năng quét 12 tháng của bạn)
    st.subheader("📊 Phân tích 12 tháng")
    sel = st.selectbox("🔍 Chọn nhân sự:", NAMES_64)
    recs = []
    with st.spinner("Đang tổng hợp..."):
        for m in range(1, 13):
            try:
                df_m = conn.read(worksheet=f"{m:02d}_{curr_year}", ttl=0)
                if df_m is not None and sel in df_m['Họ và Tên'].values:
                    row_p = df_m[df_m['Họ và Tên'] == sel].iloc[0]
                    m_label = date(curr_year, m, 1).strftime("%b")
                    for col in df_m.columns:
                        if "/" in col and m_label in col:
                            v = str(row_p[col]).strip().upper()
                            if v and v != "NAN":
                                cat = "Đi Biển" if any(g.upper() in v for g in GIANS) else v
                                if cat in ["Đi Biển", "CA", "WS", "NP", "ỐM"]:
                                    recs.append({"Tháng": f"T{m}", "Loại": cat, "Ngày": 1})
            except: continue
    if recs:
        pdf = pd.DataFrame(recs)
        fig = px.bar(pdf, x="Tháng", y="Ngày", color="Loại", barmode="stack",
                     category_orders={"Tháng": [f"T{i}" for i in range(1, 13)]})
        st.plotly_chart(fig, use_container_width=True)
