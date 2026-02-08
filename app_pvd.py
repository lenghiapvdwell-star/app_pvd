import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import time
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; font-size: 45px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 3px 3px 6px #000 !important;
        font-family: 'Arial Black', sans-serif !important;
        margin-bottom: 20px;
    }
    [data-testid="stMetricValue"] { font-size: 32px !important; font-weight: bold !important; color: #00f2ff !important; }
    /* Hiệu ứng hover cho bảng */
    .stDataEditor { border: 1px solid #333 !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER ---
c_logo, _ = st.columns([1, 4])
with c_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=180)
    else:
        st.markdown("<h2 style='color:red;'>🔴 PVD WELL</h2>", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. KẾT NỐI ---
conn = st.connection("gsheets", type=GSheetsConnection)

def save_to_cloud_smart(worksheet_name, df):
    df_clean = df.fillna("").replace(["nan", "NaN", "None"], "")
    try:
        conn.update(worksheet=worksheet_name, data=df_clean)
        st.cache_data.clear() # Xóa cache toàn cục để nạp dữ liệu mới nhất
        return True
    except Exception as e:
        st.error(f"Lỗi Cloud: {e}")
        return False

# --- 4. SIDEBAR QUẢN LÝ GIÀN ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

with st.sidebar:
    st.header("⚙️ QUẢN LÝ GIÀN")
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

# --- 5. CHỌN THÁNG & LOGIC TẢI DỮ LIỆU ---
COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]

_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    # Key động dựa trên ngày giúp Streamlit nhận biết sự thay đổi ngay lập tức
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today(), key="date_selector")

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b")

# Giải quyết tồn CA từ tháng trước
prev_month_date = working_date.replace(day=1) - timedelta(days=1)
prev_sheet = prev_month_date.strftime("%m_%Y")

# GIẢI PHÁP PRO: Kiểm tra sự thay đổi của sheet_name trong session_state
if 'current_loaded_sheet' not in st.session_state or st.session_state.current_loaded_sheet != sheet_name:
    st.session_state.current_loaded_sheet = sheet_name
    # Force reload bằng cách xóa 'db' cũ khi đổi tháng
    if 'db' in st.session_state:
        del st.session_state.db

@st.cache_data(ttl=60) # Lưu cache ngắn 60s để tránh lỗi 429 nếu reload quá nhanh
def load_data_pro(s_name, p_name):
    try:
        # Đọc tháng trước lấy tồn
        df_p = conn.read(worksheet=p_name, ttl=0)
        b_map = dict(zip(df_p['Họ và Tên'], df_p['Quỹ CA Tổng']))
    except:
        b_map = {}
        
    try:
        # Đọc tháng hiện tại
        df_l = conn.read(worksheet=s_name, ttl=0)
        if df_l.empty or len(df_l) < 5: raise ValueError
        df_l = df_l.fillna("").replace(["nan", "NaN", "None"], "")
        # Cập nhật lại tồn tháng trước từ map mới nhất
        for idx, row in df_l.iterrows():
            name = row['Họ và Tên']
            if name in b_map:
                df_l.at[idx, 'CA Tháng Trước'] = float(b_map[name])
        return df_l
    except:
        # Tạo mới nếu không có data
        return pd.DataFrame({
            'STT': range(1, len(NAMES_66) + 1),
            'Họ và Tên': NAMES_66,
            'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Job Detail': '',
            'CA Tháng Trước': [float(b_map.get(n, 0.0)) for n in NAMES_66],
            'Quỹ CA Tổng': 0.0
        })

if 'db' not in st.session_state:
    st.session_state.db = load_data_pro(sheet_name, prev_sheet)

# Đảm bảo cột ngày luôn đủ
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
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ"])

with t1:
    bc1, bc2, bc3 = st.columns([1, 1, 1])
    with bc1:
        if st.button("📤 LƯU CLOUD", type="primary", key="btn_save", use_container_width=True):
            with st.spinner("Đang lưu..."):
                st.session_state.db = recalculate_ca(st.session_state.db)
                if save_to_cloud_smart(sheet_name, st.session_state.db):
                    st.toast(f"Đã lưu tháng {sheet_name}!", icon="✅")
                    time.sleep(1); st.rerun()
    with bc2:
        if st.button("🔄 LÀM MỚI (TẢI LẠI)", key="btn_refresh", use_container_width=True):
            st.cache_data.clear()
            if 'db' in st.session_state: del st.session_state.db
            st.rerun()
    with bc3:
        buf = io.BytesIO()
        st.session_state.db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf.getvalue(), f"PVD_{sheet_name}.xlsx", use_container_width=True)

    with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH"):
        c1, c2 = st.columns([2, 1])
        f_staff = c1.multiselect("Nhân sự:", NAMES_66)
        f_date = c2.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, num_days)))
        r2_1, r2_2, r2_3, r2_4 = st.columns(4)
        f_status = r2_1.selectbox("Trạng thái:", ["Xóa trắng", "Đi Biển", "CA", "WS", "NP", "Ốm"])
        f_val = r2_2.selectbox("Giàn:", st.session_state.GIANS) if f_status == "Đi Biển" else f_status
        f_co = r2_3.selectbox("Cty:", ["Không đổi"] + COMPANIES); f_ti = r2_4.selectbox("Chức danh:", ["Không đổi"] + TITLES)
        if st.button("✅ ÁP DỤNG", use_container_width=True):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                for person in f_staff:
                    idx = st.session_state.db.index[st.session_state.db['Họ và Tên'] == person][0]
                    for i in range((f_date[1] - f_date[0]).days + 1):
                        d = f_date[0] + timedelta(days=i)
                        if d.month == curr_month:
                            col_n = [c for c in DATE_COLS if c.startswith(f"{d.day:02d}/")][0]
                            st.session_state.db.at[idx, col_n] = "" if f_status == "Xóa trắng" else f_val
                st.session_state.db = recalculate_ca(st.session_state.db); st.rerun()

    st.markdown("---")
    basic_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail', 'CA Tháng Trước', 'Quỹ CA Tổng']
    ordered_cols = basic_cols + DATE_COLS
    
    # Key động cho data_editor để nó nạp lại hoàn toàn khi đổi tháng
    ed_df = st.data_editor(
        st.session_state.db[ordered_cols].fillna(""),
        use_container_width=True, height=600, hide_index=True,
        key=f"editor_{sheet_name}", 
        column_config={
            "CA Tháng Trước": st.column_config.NumberColumn("Tồn cũ", format="%.1f"),
            "Quỹ CA Tổng": st.column_config.NumberColumn("Tổng ca", format="%.1f", disabled=True),
        }
    )
    # So sánh và cập nhật
    if not ed_df.equals(st.session_state.db[ordered_cols].fillna("")):
        st.session_state.db.update(ed_df)
        st.session_state.db = recalculate_ca(st.session_state.db)
        st.rerun()

with t2:
    st.subheader(f"📊 Phân tích nhân sự năm {curr_year}")
    sel_name = st.selectbox("🔍 Chọn nhân sự xem biểu đồ:", NAMES_66)
    recs = []
    
    # Chỗ này Pro hơn: Quét dữ liệu nhanh hơn
    with st.spinner("Đang tổng hợp dữ liệu..."):
        for m in range(1, 13):
            m_sheet = f"{m:02d}_{curr_year}"
            try:
                df_m = conn.read(worksheet=m_sheet, ttl=600) # Biểu đồ cho phép cache lâu 10p
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
        
        fig = px.bar(summary, x="Tháng", y="Ngày", color="Loại", text="Ngày", barmode="stack",
                     category_orders={"Tháng": [f"T{i}" for i in range(1, 13)]},
                     color_discrete_map={"Đi Biển":"#00f2ff","CA":"#ff4b4b","WS":"#ffd700","NP":"#00ff00","ỐM":"#ff00ff"},
                     template="plotly_dark")
        fig.update_traces(textposition='inside', textfont_size=14)
        fig.update_layout(xaxis_title="Tháng", yaxis_title="Tổng số ngày", height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 📋 Tổng kết số ngày hoạt động trong năm")
        total_sum = pdf.groupby('Loại')['Ngày'].sum().to_dict()
        
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("🚢 Đi Biển", f"{total_sum.get('Đi Biển', 0)} day")
        m2.metric("🏠 Nghỉ CA", f"{total_sum.get('CA', 0)} day")
        m3.metric("🛠️ Làm WS", f"{total_sum.get('WS', 0)} day")
        m4.metric("🏖️ Nghỉ NP", f"{total_sum.get('NP', 0)} day")
        m5.metric("🏥 Nghỉ ỐM", f"{total_sum.get('ỐM', 0)} day")
    else:
        st.info(f"Không có dữ liệu cho nhân sự {sel_name} trong năm {curr_year}.")
