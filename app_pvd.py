import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 0.5rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; font-size: 45px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 3px 3px 6px #000 !important;
        font-family: 'Arial Black', sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER ---
c_logo, _ = st.columns([1, 4])
with c_logo:
    logo_path = "logo_pvd.png" 
    if os.path.exists(logo_path):
        st.image(logo_path, width=180)
    else:
        st.markdown("### 🔴 PVD WELL")

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. QUẢN LÝ DANH SÁCH GIÀN (LƯU TRONG SESSION) ---
# Khởi tạo danh sách giàn mặc định nếu chưa có
if "gians_list" not in st.session_state:
    st.session_state.gians_list = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

# --- 4. CHỌN THÁNG ---
_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today(), key="main_date_picker")

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b") 

prev_date = working_date.replace(day=1) - timedelta(days=1)
prev_sheet_name = prev_date.strftime("%m_%Y")

if "current_sheet" not in st.session_state: st.session_state.current_sheet = sheet_name
if st.session_state.current_sheet != sheet_name:
    for key in list(st.session_state.keys()):
        if key.startswith("ed_") or key == "db": del st.session_state[key]
    st.session_state.current_sheet = sheet_name
    st.rerun()

# --- 5. KẾT NỐI & DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)
COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong"]

def get_prev_ton_dau():
    try:
        df_prev = conn.read(worksheet=prev_sheet_name, ttl=0)
        if df_prev is not None and 'Quỹ CA Tổng' in df_prev.columns:
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
        prev_map = get_prev_ton_dau()
        st.session_state.db = pd.DataFrame({
            'STT': range(1, 66), 
            'Họ và Tên': NAMES_64[:65], 
            'Công ty': 'PVDWS', 
            'Chức danh': 'Casing crew', 
            'Job Detail': '', 
            'CA Tháng Trước': [prev_map.get(name, 0.0) for name in NAMES_64[:65]],
            'Quỹ CA Tổng': 0.0
        })

num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
for col in DATE_COLS:
    if col not in st.session_state.db.columns: st.session_state.db[col] = ""

# --- 6. LOGIC TÍNH CA ---
def calculate_pvd_logic(df):
    hols = [date(2026,1,1), date(2026,4,30), date(2026,5,1), date(2026,9,2),
            date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19)]
    
    def row_calc(row):
        accrued = 0.0
        for col in DATE_COLS:
            v = str(row.get(col, "")).strip().upper()
            if not v or v in ["NAN", "NONE"]: continue
            try:
                dt = date(curr_year, curr_month, int(col[:2]))
                is_we = dt.weekday() >= 5
                is_ho = dt in hols
                # Kiểm tra xem giá trị nhập vào có chứa bất kỳ tên giàn nào trong danh sách không
                if any(g.upper() in v for g in st.session_state.gians_list):
                    if is_ho: accrued += 2.0
                    elif is_we: accrued += 1.0
                    else: accrued += 0.5
                elif v == "CA":
                    if not is_we and not is_ho: accrued -= 1.0
            except: continue
        return accrued

    df['CA Tháng Trước'] = pd.to_numeric(df['CA Tháng Trước'], errors='coerce').fillna(0.0)
    df['Quỹ CA Tổng'] = df['CA Tháng Trước'] + df.apply(row_calc, axis=1)
    return df

st.session_state.db = calculate_pvd_logic(st.session_state.db)

# --- 7. CACHE BIỂU ĐỒ ---
@st.cache_data(ttl=300)
def load_year_data(year):
    all_data = {}
    for m in range(1, 13):
        try:
            name_m = f"{m:02d}_{year}"
            df_m = conn.read(worksheet=name_m, ttl=0)
            if df_m is not None and 'Họ và Tên' in df_m.columns:
                all_data[m] = df_m
        except: continue
    return all_data

# --- 8. GIAO DIỆN CHÍNH ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ"])

with t1:
    bc1, bc2, bc3 = st.columns([1.5, 1.5, 5])
    with bc1:
        if st.button("📤 LƯU CLOUD", type="primary", use_container_width=True):
            try:
                conn.update(worksheet=sheet_name, data=st.session_state.db)
                st.success("Đã lưu!")
                st.cache_data.clear()
            except: st.error("Lỗi kết nối.")

    with bc2:
        buf = io.BytesIO()
        st.session_state.db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf, f"PVD_{sheet_name}.xlsx", use_container_width=True)

    # --- CÔNG CỤ CẬP NHẬT NHANH ---
    with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH & QUẢN LÝ GIÀN"):
        # Phần Thêm Giàn Mới
        st.markdown("##### ⚓ Thêm giàn khoan mới")
        c_add1, c_add2 = st.columns([3, 1])
        new_rig = c_add1.text_input("Nhập tên giàn mới (VD: PVD 11, HAKURYU 5...):", key="new_rig_input")
        if c_add2.button("➕ Thêm Giàn", use_container_width=True):
            if new_rig and new_rig not in st.session_state.gians_list:
                st.session_state.gians_list.append(new_rig)
                st.success(f"Đã thêm {new_rig}")
                st.rerun()
        
        st.divider()
        
        # Phần Nhập Dữ Liệu Nhanh
        st.markdown("##### 📝 Nhập dữ liệu nhanh")
        c1, c2 = st.columns([2, 1])
        f_staff = c1.multiselect("Nhân sự:", NAMES_64)
        f_date = c2.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, num_days)))
        r2_1, r2_2, r2_3, r2_4 = st.columns(4)
        f_status = r2_1.selectbox("Trạng thái:", ["Không đổi", "Đi Biển", "CA", "WS", "NP", "Ốm"])
        # Lấy danh sách giàn từ Session State
        f_val = r2_2.selectbox("Chọn giàn:", st.session_state.gians_list) if f_status == "Đi Biển" else f_status
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
                            if d.month == curr_month:
                                col_n = f"{d.day:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][d.weekday()]})"
                                if col_n in st.session_state.db.columns: st.session_state.db.at[idx, col_n] = f_val
                st.rerun()

    config = {
        "STT": st.column_config.NumberColumn(disabled=True),
        "Họ và Tên": st.column_config.TextColumn(disabled=True),
        "CA Tháng Trước": st.column_config.NumberColumn("Tồn Cũ", format="%.1f"),
        "Quỹ CA Tổng": st.column_config.NumberColumn("Tổng ca", format="%.1f", disabled=True),
    }
    ed_df = st.data_editor(st.session_state.db, column_config=config, use_container_width=True, height=600, hide_index=True, key=f"ed_{sheet_name}")
    if not ed_df.equals(st.session_state.db):
        st.session_state.db = ed_df
        st.rerun()

with t2:
    st.subheader("📊 Phân tích cường độ & Tổng hợp ngày biển")
    sel = st.selectbox("🔍 Chọn nhân sự:", NAMES_64)
    year_data = load_year_data(curr_year)
    
    recs = []
    if year_data:
        for m in range(1, 13):
            if m in year_data:
                df_m = year_data[m]
                if 'Họ và Tên' in df_m.columns and sel in df_m['Họ và Tên'].values:
                    row_p = df_m[df_m['Họ và Tên'] == sel].iloc[0]
                    m_label = date(curr_year, m, 1).strftime("%b")
                    for col in df_m.columns:
                        if "/" in col and m_label in col:
                            v = str(row_p[col]).strip().upper()
                            if v and v not in ["NAN", "NONE", ""]:
                                # Kiểm tra đi biển dựa trên danh sách giàn linh hoạt
                                cat = "Đi Biển" if any(g.upper() in v for g in st.session_state.gians_list) else v
                                if cat in ["Đi Biển", "CA", "WS", "NP", "ỐM"]:
                                    recs.append({"Tháng": f"T{m}", "Loại": cat, "Ngày": 1})

    if recs:
        pdf = pd.DataFrame(recs)
        summary = pdf.groupby(['Tháng', 'Loại']).sum().reset_index()
        
        sea_only = summary[summary['Loại'] == "Đi Biển"].copy()
        if not sea_only.empty:
            sea_only['MonthIdx'] = sea_only['Tháng'].str[1:].astype(int)
            sea_only = sea_only.sort_values('MonthIdx')
            sea_only['Lũy kế biển'] = sea_only['Ngày'].cumsum()

        fig = px.bar(summary, x="Tháng", y="Ngày", color="Loại", text="Ngày",
                     barmode="stack",
                     color_discrete_map={"Đi Biển": "#00CC96", "CA": "#EF553B", "WS": "#FECB52", "NP": "#636EFA", "ỐM": "#AB63FA"},
                     category_orders={"Tháng": [f"T{i}" for i in range(1, 13)]})

        if not sea_only.empty:
            fig.add_trace(go.Scatter(
                x=sea_only["Tháng"], y=sea_only["Lũy kế biển"],
                name="Tổng Biển Cộng Dồn", mode="lines+markers+text",
                text=sea_only["Lũy kế biển"], textposition="top center",
                line=dict(color="#00f2ff", width=3)
            ))

        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        c_m1, c_m2 = st.columns(2)
        c_m1.metric("Tổng ngày biển cả năm", f"{sea_only['Ngày'].sum() if not sea_only.empty else
