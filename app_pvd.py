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
    .block-container {padding-top: 0.5rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; 
        font-size: 60px !important; 
        font-weight: bold !important;
        text-align: center !important; 
        text-shadow: 3px 3px 6px #000 !important;
        font-family: 'Arial Black', sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER & CHỌN THÁNG ---
c_logo, c_title = st.columns([1, 4])
with c_logo:
    st.markdown("### 🔴 PVD WELL")
with c_title:
    st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today(), key="main_date_picker")

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year

# Hard Reset khi đổi tháng
if "current_sheet" not in st.session_state:
    st.session_state.current_sheet = sheet_name

if st.session_state.current_sheet != sheet_name:
    for key in list(st.session_state.keys()):
        if key.startswith("editor_") or key == "db":
            del st.session_state[key]
    st.session_state.current_sheet = sheet_name
    st.rerun()

# --- 3. KẾT NỐI DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)
month_abbr = working_date.strftime("%b") 

# Danh mục mặc định
GIANS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]
COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]

# Tải dữ liệu tháng hiện tại
if 'db' not in st.session_state:
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        st.session_state.db = df_load if df_load is not None else pd.DataFrame()
    except:
        st.session_state.db = pd.DataFrame()

# --- 4. HÀM TÍNH TOÁN (Lũy kế & Biểu đồ) ---
def get_all_year_data():
    """Quét dữ liệu 12 tháng để vẽ biểu đồ"""
    all_data = []
    with st.spinner("Đang tổng hợp dữ liệu 12 tháng..."):
        for m in range(1, 13):
            s_name = f"{m:02d}_{curr_year}"
            try:
                df = conn.read(worksheet=s_name, ttl=0)
                if df is not None:
                    # Đếm số ngày theo loại
                    for _, row in df.iterrows():
                        sea_days = 0
                        ca_days = 0
                        ws_days = 0
                        for col in df.columns:
                            val = str(row[col]).strip()
                            if val in GIANS: sea_days += 1
                            elif val.upper() == "CA": ca_days += 1
                            elif val.upper() == "WS": ws_days += 1
                        
                        all_data.append({"Tháng": f"T{m}", "Loại": "Đi biển", "Ngày": sea_days})
                        all_data.append({"Tháng": f"T{m}", "Loại": "Nghỉ CA", "Ngày": ca_days})
                        all_data.append({"Tháng": f"T{m}", "Loại": "Làm xưởng", "Ngày": ws_days})
            except: continue
    return pd.DataFrame(all_data)

# --- 5. GIAO DIỆN CHÍNH ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG & QUẢN LÝ", "📊 BIỂU ĐỒ THỐNG KÊ NĂM"])

with t1:
    # (Phần nút bấm và Cập nhật nhanh giữ nguyên như bản trước của bạn)
    bc1, bc2, _ = st.columns([1.5, 1.5, 5])
    with bc1:
        if st.button("📤 LƯU CLOUD", type="primary"):
            conn.update(worksheet=sheet_name, data=st.session_state.db)
            st.success("Đã lưu!")
    
    # Bảng Editor
    num_days = calendar.monthrange(curr_year, curr_month)[1]
    DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
    
    if not st.session_state.db.empty:
        st.data_editor(
            st.session_state.db,
            use_container_width=True,
            height=600,
            hide_index=True,
            key=f"editor_{sheet_name}"
        )

with t2:
    st.subheader(f"📊 Phân tích cường độ công việc năm {curr_year}")
    
    year_df = get_all_year_data()
    
    if not year_df.empty:
        # Vẽ biểu đồ Plotly
        fig = px.bar(
            year_df, 
            x="Tháng", 
            y="Ngày", 
            color="Loại",
            title="Tổng hợp cường độ hoạt động 12 tháng",
            color_discrete_map={
                "Đi biển": "#00CC96", # Xanh lá
                "Nghỉ CA": "#EF553B", # Đỏ
                "Làm xưởng": "#FECB52" # Vàng
            },
            barmode="stack"
        )
        
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Thêm bảng tóm tắt
        st.write("### 📝 Tóm tắt tổng số ngày trong năm")
        summary = year_df.groupby("Loại")["Ngày"].sum().reset_index()
        st.table(summary)
    else:
        st.warning("Chưa có dữ liệu trên Cloud để hiển thị biểu đồ. Hãy lưu dữ liệu các tháng trước!")
