import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CẤU HÌNH & STYLE ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 0.5rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; font-size: 45px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 3px 3px 6px #000 !important;
        font-family: 'Arial Black', sans-serif !important;
    }
    [data-testid="stDataEditor"] div[data-testid="column-6"] {
        background-color: #004c4c !important; color: #00f2ff !important; font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER ---
c_logo, _ = st.columns([1, 4])
with c_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=180)
    else:
        st.markdown("### 🔴 PVD WELL")

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. CHỌN THÁNG ---
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

# --- 4. KẾT NỐI & DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)
GIANS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]
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

# --- 5. LOGIC SIÊU AUTOFILL & TÍNH CA ---
def process_autofill_and_calc(df):
    # Quy ước ngày lễ 2026
    hols = [date(2026,1,1), date(2026,4,30), date(2026,5,1), date(2026,9,2),
            date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19)]
    
    df_new = df.copy()
    
    for idx, row in df_new.iterrows():
        # A. AUTOFILL "CHẢY": Lấy giá trị ngày trước điền cho ngày sau nếu trống
        last_valid_status = ""
        for col in DATE_COLS:
            current_val = str(df_new.at[idx, col]).strip()
            if current_val == "" or current_val.upper() in ["NAN", "NONE"]:
                df_new.at[idx, col] = last_valid_status
            else:
                last_valid_status = current_val

        # B. TÍNH QUỸ CA (CHỈ BIỂN CỘNG, CHỈ CA TRỪ, WS/NP/ỐM GIỮ NGUYÊN)
        accrued = 0.0
        for col in DATE_COLS:
            status = str(df_new.at[idx, col]).strip().upper()
            if not status or status in ["NAN", "NONE"]: continue
            
            try:
                dt = date(curr_year, curr_month, int(col[:2]))
                is_we = dt.weekday() >= 5
                is_ho = dt in hols
                
                is_offshore = any(g.upper() in status for g in GIANS)
                if is_offshore:
                    if is_ho: accrued += 2.0
                    elif is_we: accrued += 1.0
                    else: accrued += 0.5
                elif status == "CA":
                    if not is_we and not is_ho: 
                        accrued -= 1.0
            except: continue
            
        ton_cu = pd.to_numeric(df_new.at[idx, 'CA Tháng Trước'], errors='coerce') or 0.0
        df_new.at[idx, 'Quỹ CA Tổng'] = ton_cu + accrued
        
    return df_new

# Áp dụng Autofill và tính toán trước khi hiển thị
st.session_state.db = process_autofill_and_calc(st.session_state.db)

# --- 6. GIAO DIỆN ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ"])

with t1:
    bc1, bc2, _ = st.columns([1.5, 1.5, 5])
    with bc1:
        if st.button("📤 LƯU CLOUD", type="primary", use_container_width=True):
            conn.update(worksheet=sheet_name, data=st.session_state.db)
            st.success("Dữ liệu đã được đồng bộ Cloud!")
            st.cache_data.clear()

    with bc2:
        buf = io.BytesIO()
        st.session_state.db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf, f"PVD_{sheet_name}.xlsx", use_container_width=True)

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
                            if d.month == curr_month:
                                col_n = [c for c in DATE_COLS if c.startswith(f"{d.day:02d}/")][0]
                                st.session_state.db.at[idx, col_n] = f_val
                st.rerun()

    cols_order = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail', 'CA Tháng Trước', 'Quỹ CA Tổng'] + DATE_COLS
    config = {
        "STT": st.column_config.NumberColumn(disabled=True),
        "Họ và Tên": st.column_config.TextColumn(disabled=True),
        "CA Tháng Trước": st.column_config.NumberColumn("Tồn Cũ", format="%.1f"),
        "Quỹ CA Tổng": st.column_config.NumberColumn("Tổng ca", format="%.1f", disabled=True),
    }
    
    ed_df = st.data_editor(st.session_state.db[cols_order], column_config=config, use_container_width=True, height=600, hide_index=True, key=f"ed_{sheet_name}")
    
    if not ed_df.equals(st.session_state.db[cols_order]):
        st.session_state.db.update(ed_df)
        st.rerun()

with t2:
    st.subheader("📊 Phân tích tích lũy & Trạng thái")
    sel_name = st.selectbox("🔍 Chọn nhân sự xem biểu đồ:", NAMES_64)
    
    # Lấy dữ liệu dòng của nhân sự được chọn
    person_row = st.session_state.db[st.session_state.db['Họ và Tên'] == sel_name].iloc[0]
    
    # Tạo dataframe cho biểu đồ
    chart_data = []
    for col in DATE_COLS:
        val = str(person_row[col]).upper()
        status_group = "Khác"
        if any(g in val for g in GIANS): status_group = "Đi Biển"
        elif "CA" in val: status_group = "Nghỉ CA"
        elif "WS" in val: status_group = "Tại Xưởng"
        elif "NP" in val: status_group = "Nghỉ Phép"
        elif "ỐM" in val: status_group = "Nghỉ Ốm"
        
        chart_data.append({"Ngày": col[:5], "Trạng thái": status_group, "Giá trị": 1})

    df_chart = pd.DataFrame(chart_data)
    
    fig = px.bar(df_chart, x="Ngày", y="Giá trị", color="Trạng thái", 
                 title=f"Lịch trình tháng {sheet_name} của {sel_name}",
                 color_discrete_map={
                     "Đi Biển": "#00CC96", "Nghỉ CA": "#EF553B", 
                     "Tại Xưởng": "#636EFA", "Nghỉ Phép": "#FECB52", "Nghỉ Ốm": "#AB63FA", "Khác": "#C0C0C0"
                 })
    fig.update_layout(showlegend=True, yaxis_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
    st.plotly_chart(fig, use_container_width=True)

    # Thống kê nhanh
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng ngày Biển", len(df_chart[df_chart['Trạng thái']=="Đi Biển"]))
    c2.metric("Tổng ngày CA", len(df_chart[df_chart['Trạng thái']=="Nghỉ CA"]))
    c3.metric("Quỹ CA hiện tại", f"{person_row['Quỹ CA Tổng']:.1f}")
