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
        font-size: 50px !important; 
        font-weight: bold !important;
        text-align: center !important; 
        text-shadow: 3px 3px 6px #000 !important;
        font-family: 'Arial Black', sans-serif !important;
    }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4259; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER ---
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
month_abbr = working_date.strftime("%b") 

# Quản lý trạng thái chuyển tháng
if "current_sheet" not in st.session_state: st.session_state.current_sheet = sheet_name
if st.session_state.current_sheet != sheet_name:
    for key in list(st.session_state.keys()):
        if key.startswith("editor_") or key == "db": del st.session_state[key]
    st.session_state.current_sheet = sheet_name
    st.rerun()

# --- 3. KẾT NỐI DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)
GIANS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

if 'db' not in st.session_state:
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        st.session_state.db = df_load if df_load is not None else pd.DataFrame()
    except: st.session_state.db = pd.DataFrame()

# --- 4. HÀM TỔNG HỢP DỮ LIỆU 12 THÁNG ---
def get_personal_stats(target_name):
    all_months_data = []
    # Các ngày lễ cố định để thống kê
    holidays_list = [date(curr_year, 1, 1), date(curr_year, 4, 30), date(curr_year, 5, 1), date(curr_year, 9, 2)]
    if curr_year == 2026: holidays_list += [date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19)]

    for m in range(1, 13):
        s_name = f"{m:02d}_{curr_year}"
        try:
            df = conn.read(worksheet=s_name, ttl=0)
            if df is not None and target_name in df['Họ và Tên'].values:
                row = df[df['Họ và Tên'] == target_name].iloc[0]
                m_abbr = date(curr_year, m, 1).strftime("%b")
                
                for col in df.columns:
                    if "/" in col and m_abbr in col:
                        val = str(row[col]).strip()
                        day_num = int(col[:2])
                        current_dt = date(curr_year, m, day_num)
                        
                        category = None
                        if val in GIANS:
                            if current_dt in holidays_list: category = "Lễ Tết"
                            else: category = "Đi biển"
                        elif val.upper() == "CA": category = "Nghỉ CA"
                        elif val.upper() == "WS": category = "Làm bờ"
                        elif val.upper() == "NP": category = "Nghỉ phép"
                        elif val.upper() == "ỐM": category = "Nghỉ ốm"
                        
                        if category:
                            all_months_data.append({"Tháng": f"T{m}", "Loại": category, "Số ngày": 1})
        except: continue
    return pd.DataFrame(all_months_data)

# --- 5. GIAO DIỆN TABS ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG & QUẢN LÝ", "📊 THỐNG KÊ CHI TIẾT"])

with t1:
    # (Phần Editor và Cập nhật nhanh giữ nguyên logic cũ của bạn)
    st.info(f"Đang hiển thị dữ liệu tháng: {sheet_name}")
    if not st.session_state.db.empty:
        st.data_editor(st.session_state.db, use_container_width=True, height=500, hide_index=True, key=f"ed_{sheet_name}")
    if st.button("📤 LƯU LÊN CLOUD"):
        conn.update(worksheet=sheet_name, data=st.session_state.db)
        st.success("Đã lưu!")

with t2:
    st.subheader("📊 Phân tích hiệu suất nhân sự (Toàn năm)")
    
    if not st.session_state.db.empty:
        staff_list = sorted(st.session_state.db['Họ và Tên'].unique().tolist())
        selected_person = st.selectbox("🔍 Chọn nhân sự cần xem thống kê:", staff_list)
        
        with st.spinner(f"Đang tính toán dữ liệu cho {selected_person}..."):
            person_df = get_personal_stats(selected_person)
            
            if not person_df.empty:
                # 1. Dashboard chỉ số nhanh
                st.markdown(f"#### 📈 Tổng quan cả năm: {selected_person}")
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("🌊 Đi biển", f"{person_df[person_df['Loại']=='Đi biển']['Số ngày'].sum()} ngày")
                m2.metric("🏠 Nghỉ CA", f"{person_df[person_df['Loại']=='Nghỉ CA']['Số ngày'].sum()} ngày")
                m3.metric("🛠️ Làm bờ", f"{person_df[person_df['Loại']=='Làm bờ']['Số ngày'].sum()} ngày")
                m4.metric("🌴 Nghỉ phép", f"{person_df[person_df['Loại']=='Nghỉ phép']['Số ngày'].sum()} ngày")
                m5.metric("🧧 Lễ Tết", f"{person_df[person_df['Loại']=='Lễ Tết']['Số ngày'].sum()} ngày")

                # 2. Biểu đồ cột chồng
                fig = px.bar(
                    person_df, x="Tháng", y="Số ngày", color="Loại",
                    title=f"Biểu đồ cường độ làm việc của {selected_person} trong năm {curr_year}",
                    color_discrete_map={
                        "Đi biển": "#00CC96", "Nghỉ CA": "#EF553B", "Làm bờ": "#FECB52",
                        "Nghỉ phép": "#636EFA", "Nghỉ ốm": "#AB63FA", "Lễ Tết": "#FFA15A"
                    },
                    category_orders={"Tháng": [f"T{i}" for i in range(1, 13)]}
                )
                fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Không tìm thấy dữ liệu hoạt động của nhân sự này trong năm nay.")
    else:
        st.error("Dữ liệu tháng hiện tại đang trống, không thể tải danh sách nhân sự.")
