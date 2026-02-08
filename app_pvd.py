import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import time
import plotly.express as px

# --- 1. CẤU HÌNH & GIAO DIỆN ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

# CSS tinh chỉnh cho giao diện chuyên nghiệp hơn
st.markdown("""
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 1rem;}
    .main-title {
        color: #00f2ff !important; font-size: 42px !important; font-weight: 800 !important;
        text-align: center !important; text-shadow: 2px 2px 8px rgba(0,242,255,0.4) !important;
        margin-bottom: 25px;
    }
    /* Làm đẹp thẻ Metrics */
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(0, 242, 255, 0.2);
        border-radius: 12px;
        padding: 15px 10px;
        transition: all 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        border-color: #00f2ff;
        transform: translateY(-2px);
        background-color: rgba(0, 242, 255, 0.05);
    }
    [data-testid="stMetricValue"] { font-size: 32px !important; font-weight: bold !important; color: #00f2ff !important; }
    [data-testid="stMetricLabel"] { font-size: 16px !important; font-weight: 500 !important; color: #ffffff !important; }
    
    /* Bo góc Data Editor */
    .stDataEditor { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER ---
c_logo, c_title = st.columns([1, 5])
with c_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=160)
    else:
        st.markdown("<h2 style='color:#ff4b4b; margin:0;'>🔴 PVD WELL</h2>", unsafe_allow_html=True)
with c_title:
    st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. KẾT NỐI (Sử dụng Cache để mượt hơn) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def save_to_cloud_smart(worksheet_name, df):
    df_clean = df.fillna("").replace(["nan", "NaN", "None"], "")
    try:
        conn.update(worksheet=worksheet_name, data=df_clean)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Lỗi Cloud: {e}")
        return False

# --- 4. SIDEBAR ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

with st.sidebar:
    st.markdown("### ⚙️ QUẢN LÝ GIÀN")
    new_gian = st.text_input("Tên giàn mới:")
    if st.button("➕ Thêm Giàn", use_container_width=True):
        if new_gian and new_gian.strip().upper() not in st.session_state.GIANS:
            st.session_state.GIANS.append(new_gian.strip().upper())
            st.rerun()
    
    st.divider()
    del_gian = st.selectbox("Xóa giàn:", ["-- Chọn --"] + st.session_state.GIANS)
    if del_gian != "-- Chọn --" and st.button(f"🗑️ Xóa {del_gian}", use_container_width=True):
        st.session_state.GIANS.remove(del_gian)
        st.rerun()

# --- 5. LOGIC DỮ LIỆU ---
COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]

_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b")

# Tính toán tháng trước để lấy tồn CA
prev_sheet = (working_date.replace(day=1) - timedelta(days=1)).strftime("%m_%Y")

if 'active_sheet' not in st.session_state or st.session_state.active_sheet != sheet_name:
    st.session_state.active_sheet = sheet_name
    if 'db' in st.session_state: del st.session_state.db

if 'db' not in st.session_state:
    try:
        df_prev = conn.read(worksheet=prev_sheet, ttl=0)
        balance_map = dict(zip(df_prev['Họ và Tên'], df_prev['Quỹ CA Tổng']))
    except:
        balance_map = {}
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        if df_load.empty or len(df_load) < 5: raise ValueError
        df_final = df_load.fillna("").replace(["nan", "NaN", "None"], "")
        for idx, row in df_final.iterrows():
            name = row['Họ và Tên']
            if name in balance_map: df_final.at[idx, 'CA Tháng Trước'] = float(balance_map[name])
        st.session_state.db = df_final
    except:
        st.session_state.db = pd.DataFrame({
            'STT': range(1, len(NAMES_66) + 1),
            'Họ và Tên': NAMES_66,
            'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Job Detail': '',
            'CA Tháng Trước': [float(balance_map.get(n, 0.0)) for n in NAMES_66],
            'Quỹ CA Tổng': 0.0
        })

num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
for col in DATE_COLS:
    if col not in st.session_state.db.columns: st.session_state.db[col] = ""

# --- 6. HÀM TÍNH TOÁN ---
def recalculate_ca(df):
    hols = [date(2026,1,1), date(2026,4,30), date(2026,5,1), date(2026,9,2),
            date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19)]
    df_calc = df.copy()
    df_calc['CA Tháng Trước'] = pd.to_numeric(df_calc['CA Tháng Trước'], errors='coerce').fillna(0.0)
    for idx, row in df_calc.iterrows():
        accrued = 0.0
        for col in DATE_COLS:
            val = str(row.get(col, "")).strip().upper()
            if not val or val in ["NAN", "NONE", "WS", "NP", "ỐM"]: continue
            try:
                dt = date(curr_year, curr_month, int(col[:2]))
                is_we, is_ho = dt.weekday() >= 5, dt in hols
                if any(g.upper() in val for g in st.session_state.GIANS):
                    accrued += 2.0 if is_ho else (1.0 if is_we else 0.5)
                elif val == "CA":
                    if not is_we and not is_ho: accrued -= 1.0
            except: pass
        df_calc.at[idx, 'Quỹ CA Tổng'] = row['CA Tháng Trước'] + accrued
    return df_calc

# --- 7. TABS ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ HOẠT ĐỘNG"])

with t1:
    c_btn1, c_btn2, c_btn3 = st.columns([1, 1, 1])
    with c_btn1:
        if st.button("📤 LƯU LÊN CLOUD", type="primary", use_container_width=True):
            st.session_state.db = recalculate_ca(st.session_state.db)
            if save_to_cloud_smart(sheet_name, st.session_state.db):
                st.success(f"Đã đồng bộ tháng {sheet_name}!"); time.sleep(1); st.rerun()
    with c_btn2:
        if st.button("🔄 LÀM MỚI DỮ LIỆU", use_container_width=True):
            st.cache_data.clear()
            if 'db' in st.session_state: del st.session_state.db
            st.rerun()
    with c_btn3:
        buf = io.BytesIO()
        st.session_state.db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT FILE EXCEL", buf.getvalue(), f"PVD_{sheet_name}.xlsx", use_container_width=True)

    with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH"):
        c1, c2 = st.columns([2, 1])
        f_staff = c1.multiselect("Chọn nhân sự:", NAMES_66)
        f_date = c2.date_input("Chọn khoảng ngày:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, num_days)))
        r2_1, r2_2, r2_3, r2_4 = st.columns(4)
        f_status = r2_1.selectbox("Trạng thái:", ["Xóa trắng", "Đi Biển", "CA", "WS", "NP", "Ốm"])
        f_val = r2_2.selectbox("Chọn Giàn:", st.session_state.GIANS) if f_status == "Đi Biển" else f_status
        f_co = r2_3.selectbox("Công ty:", ["Không đổi"] + COMPANIES)
        f_ti = r2_4.selectbox("Chức danh:", ["Không đổi"] + TITLES)
        if st.button("✅ ÁP DỤNG THAY ĐỔI", use_container_width=True):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                for person in f_staff:
                    idx = st.session_state.db.index[st.session_state.db['Họ và Tên'] == person][0]
                    for i in range((f_date[1] - f_date[0]).days + 1):
                        d = f_date[0] + timedelta(days=i)
                        if d.month == curr_month:
                            col_n = [c for c in DATE_COLS if c.startswith(f"{d.day:02d}/")][0]
                            st.session_state.db.at[idx, col_n] = "" if f_status == "Xóa trắng" else f_val
                    if f_co != "Không đổi": st.session_state.db.at[idx, 'Công ty'] = f_co
                    if f_ti != "Không đổi": st.session_state.db.at[idx, 'Chức danh'] = f_ti
                st.session_state.db = recalculate_ca(st.session_state.db); st.rerun()

    st.markdown("---")
    ordered_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail', 'CA Tháng Trước', 'Quỹ CA Tổng'] + DATE_COLS
    display_df = st.session_state.db[ordered_cols].fillna("")
    ed_df = st.data_editor(display_df, use_container_width=True, height=580, hide_index=True,
                           column_config={
                               "CA Tháng Trước": st.column_config.NumberColumn("Tồn CA", format="%.1f"),
                               "Quỹ CA Tổng": st.column_config.NumberColumn("Tổng CA", format="%.1f", disabled=True),
                           })
    if not ed_df.equals(display_df):
        st.session_state.db.update(ed_df); st.session_state.db = recalculate_ca(st.session_state.db); st.rerun()

with t2:
    st.markdown(f"### 📈 Phân tích nhân sự năm {curr_year}")
    sel_name = st.selectbox("🔍 Tìm kiếm tên nhân sự:", NAMES_66)
    recs = []
    
    # Hiển thị spinner khi quét dữ liệu cả năm
    with st.spinner('Đang tổng hợp dữ liệu 12 tháng...'):
        for m in range(1, 13):
            m_sheet = f"{m:02d}_{curr_year}"
            try:
                df_m = conn.read(worksheet=m_sheet, ttl=0)
                if not df_m.empty and sel_name in df_m['Họ và Tên'].values:
                    row_p = df_m[df_m['Họ và Tên'] == sel_name].iloc[0]
                    m_label = date(curr_year, m, 1).strftime("%b")
                    for col in df_m.columns:
                        if "/" in col and m_label in col:
                            v = str(row_p[col]).strip().upper()
                            if v and v not in ["", "NAN", "NONE"]:
                                if any(g.upper() in v for g in st.session_state.GIANS): cat = "Đi Biển"
                                elif v == "CA": cat = "CA"
                                elif v == "WS": cat = "WS"
                                elif v == "NP": cat = "NP"
                                elif v == "ỐM": cat = "ỐM"
                                else: continue
                                recs.append({"Tháng": f"T{m}", "Loại": cat, "Ngày": 1})
            except: continue
        
    if recs:
        pdf = pd.DataFrame(recs)
        summary = pdf.groupby(['Tháng', 'Loại']).size().reset_index(name='Ngày')
        
        # Biểu đồ Plotly tinh chỉnh
        fig = px.bar(summary, x="Tháng", y="Ngày", color="Loại", text="Ngày", barmode="stack",
                     category_orders={"Tháng": [f"T{i}" for i in range(1, 13)]},
                     color_discrete_map={"Đi Biển":"#00f2ff","CA":"#ff4b4b","WS":"#ffd700","NP":"#00ff00","ỐM":"#ff00ff"},
                     template="plotly_dark")
        fig.update_traces(textposition='inside', textfont_size=14, marker_line_width=0)
        fig.update_layout(xaxis_title="", yaxis_title="Số ngày", height=450, 
                          hovermode="x unified",
                          margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
        
        # --- PHẦN TỔNG KẾT (Bỏ bảng, giữ khung số đẹp) ---
        st.markdown("<br><h4 style='text-align: center; color: #00f2ff;'>📋 TỔNG KẾT HOẠT ĐỘNG CẢ NĂM</h4>", unsafe_allow_html=True)
        total_sum = pdf.groupby('Loại')['Ngày'].sum().to_dict()
        
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("🚢 ĐI BIỂN", f"{total_sum.get('Đi Biển', 0)} day")
        m2.metric("🏠 NGHỈ CA", f"{total_sum.get('CA', 0)} day")
        m3.metric("🛠️ LÀM WS", f"{total_sum.get('WS', 0)} day")
        m4.metric("🏖️ NGHỈ NP", f"{total_sum.get('NP', 0)} day")
        m5.metric("🏥 NGHỈ ỐM", f"{total_sum.get('ỐM', 0)} day")
    else:
        st.info(f"Chưa có dữ liệu hoạt động của {sel_name} trong năm {curr_year}.")
