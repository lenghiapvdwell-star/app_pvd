import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import plotly.express as px

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .main-title {
        color: #00f2ff !important; font-size: 45px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 3px 3px 6px #000 !important;
        font-family: 'Arial Black', sans-serif !important;
    }
    .stMetric { background-color: #0e1117; padding: 15px; border-radius: 10px; border: 1px solid #31333f; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DANH SÁCH NHÂN SỰ CỐ ĐỊNH (65 NGƯỜI) ---
NAMES_LIST = [
    "Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", 
    "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", 
    "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", 
    "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", 
    "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", 
    "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", 
    "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", 
    "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", 
    "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", 
    "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", 
    "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong"
]

# --- 3. QUẢN LÝ THỜI GIAN ---
st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

_, c_mid, _ = st.columns([3, 2, 3])
with c_mid:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b")

# Reset Session khi đổi tháng
if "active_sheet" not in st.session_state:
    st.session_state.active_sheet = sheet_name

if st.session_state.active_sheet != sheet_name:
    for k in list(st.session_state.keys()):
        if k.startswith("ed_") or k == "db": del st.session_state[k]
    st.session_state.active_sheet = sheet_name
    st.rerun()

# --- 4. KẾT NỐI DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)
GIANS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

def get_transfer_ca():
    prev = date(curr_year, curr_month, 1) - timedelta(days=1)
    try:
        df_prev = conn.read(worksheet=prev.strftime("%m_%Y"), ttl=0)
        return df_prev.set_index('Họ và Tên')['Quỹ CA Tổng'].to_dict()
    except: return {}

if 'db' not in st.session_state:
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        if df_load is not None and not df_load.empty:
            st.session_state.db = df_load
        else: raise Exception
    except:
        # Tạo bảng mới nếu tháng chưa tồn tại
        df_new = pd.DataFrame({
            'STT': range(1, len(NAMES_LIST) + 1),
            'Họ và Tên': NAMES_LIST,
            'Công ty': 'PVDWS',
            'Chức danh': 'Casing crew',
            'Job Detail': '',
            'CA Tháng Trước': 0.0
        })
        # Lấy tồn từ tháng trước
        prev_ca = get_transfer_ca()
        df_new['CA Tháng Trước'] = df_new['Họ và Tên'].map(prev_ca).fillna(0.0)
        st.session_state.db = df_new

# --- 5. TÍNH TOÁN LŨY KẾ ---
def run_calculation(df):
    holidays = [date(curr_year,1,1), date(curr_year,4,30), date(curr_year,5,1), date(curr_year,9,2),
                date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19)]
    num_days = calendar.monthrange(curr_year, curr_month)[1]
    d_cols = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
    
    def calc_row(row):
        p_sinh = 0.0
        for col in d_cols:
            if col in row:
                val = str(row[col]).strip().upper()
                if val in [g.upper() for g in GIANS]:
                    dt = date(curr_year, curr_month, int(col[:2]))
                    if dt in holidays: p_sinh += 2.0
                    elif dt.weekday() >= 5: p_sinh += 1.0
                    else: p_sinh += 0.5
                elif val == "CA":
                    p_sinh -= 1.0
        return p_sinh

    df['CA Tháng Trước'] = pd.to_numeric(df['CA Tháng Trước'], errors='coerce').fillna(0.0)
    df['Quỹ CA Tổng'] = df['CA Tháng Trước'] + df.apply(calc_row, axis=1)
    return df, d_cols

st.session_state.db, current_date_cols = run_calculation(st.session_state.db)

# --- 6. GIAO DIỆN TABS ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG NHÂN SỰ", "📊 BIỂU ĐỒ THỐNG KÊ"])

with t1:
    c1, c2, _ = st.columns([1.5, 1.5, 5])
    if c1.button("📤 LƯU LÊN CLOUD", type="primary", use_container_width=True):
        conn.update(worksheet=sheet_name, data=st.session_state.db)
        st.success("Đã lưu!")
    
    if c2.button("📥 TẢI EXCEL", use_container_width=True):
        buf = io.BytesIO()
        st.session_state.db.to_excel(buf, index=False)
        st.download_button("Download", buf, f"PVD_{sheet_name}.xlsx")

    # Hiển thị bảng điều động
    st.data_editor(
        st.session_state.db,
        use_container_width=True,
        height=550,
        hide_index=True,
        key=f"ed_{sheet_name}"
    )

with t2:
    selected_name = st.selectbox("🔍 Chọn nhân sự xem báo cáo 12 tháng:", NAMES_LIST)
    
    # Logic quét dữ liệu 12 tháng cho biểu đồ
    all_year_data = []
    holidays_2026 = [date(2026,1,1), date(2026,4,30), date(2026,5,1), date(2026,9,2),
                     date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19)]
    
    with st.spinner("Đang tổng hợp dữ liệu..."):
        for m in range(1, 13):
            try:
                m_sheet = f"{m:02d}_{curr_year}"
                df_m = conn.read(worksheet=m_sheet, ttl=0)
                if df_m is not None and selected_name in df_m['Họ và Tên'].values:
                    row_m = df_m[df_m['Họ và Tên'] == selected_name].iloc[0]
                    m_label = date(curr_year, m, 1).strftime("%b")
                    for col in df_m.columns:
                        if "/" in col and m_label in col:
                            v = str(row_m[col]).strip().upper()
                            if v and v != "NAN":
                                dt_obj = date(curr_year, m, int(col[:2]))
                                cat = None
                                if any(g.upper() in v for g in GIANS):
                                    cat = "Lễ Tết" if dt_obj in holidays_2026 else "Đi Biển"
                                elif v == "CA": cat = "Nghỉ CA"
                                elif v == "WS": cat = "Làm Bờ"
                                elif v == "NP": cat = "Nghỉ Phép"
                                if cat: all_year_data.append({"Tháng": f"T{m}", "Loại": cat, "Ngày": 1})
            except: continue

    if all_year_data:
        pdf = pd.DataFrame(all_year_data)
        st.markdown(f"### 📈 Kết quả năm {curr_year}: {selected_name}")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🌊 ĐI BIỂN", f"{int(pdf[pdf['Loại']=='Đi Biển']['Ngày'].sum())} Ngày")
        m2.metric("🏠 NGHỈ CA", f"{int(pdf[pdf['Loại']=='Nghỉ CA']['Ngày'].sum())} Ngày")
        m3.metric("🛠️ LÀM BỜ", f"{int(pdf[pdf['Loại']=='Làm Bờ']['Ngày'].sum())} Ngày")
        m4.metric("🧧 LỄ TẾT", f"{int(pdf[pdf['Loại']=='Lễ Tết']['Ngày'].sum())} Ngày")

        
        fig = px.bar(
            pdf, x="Tháng", y="Ngày", color="Loại",
            color_discrete_map={"Đi Biển": "#00CC96", "Nghỉ CA": "#EF553B", "Làm Bờ": "#FECB52", "Lễ Tết": "#FFA15A", "Nghỉ Phép": "#636EFA"},
            category_orders={"Tháng": [f"T{i}" for i in range(1, 13)]},
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Chưa có dữ liệu hoạt động của nhân sự này trên hệ thống.")
