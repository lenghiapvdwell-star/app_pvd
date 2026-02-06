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
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; 
        font-size: 50px !important; 
        font-weight: bold !important;
        text-align: center !important; 
        text-shadow: 3px 3px 6px #000 !important;
        font-family: 'Arial Black', sans-serif !important;
    }
    .stMetric { 
        background-color: #0e1117; 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #31333f;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER & CHỌN THÁNG ---
st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today(), key="main_date_picker")

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b")

# Reset state khi đổi tháng
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
        st.session_state.db = df_load if (df_load is not None and not df_load.empty) else pd.DataFrame()
    except: st.session_state.db = pd.DataFrame()

# --- 4. HÀM THỐNG KÊ CHI TIẾT ---
def get_detailed_stats(target_person):
    full_year_records = []
    # Danh sách lễ tết 2026
    holidays = [date(2026,1,1), date(2026,4,30), date(2026,5,1), date(2026,9,2),
                date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19)]
    
    for m in range(1, 13):
        s_idx = f"{m:02d}_{curr_year}"
        try:
            df = conn.read(worksheet=s_idx, ttl=0)
            if df is not None and target_person in df['Họ và Tên'].values:
                row = df[df['Họ và Tên'] == target_person].iloc[0]
                m_abbr = date(curr_year, m, 1).strftime("%b")
                for col in df.columns:
                    if "/" in col and m_abbr in col:
                        val = str(row[col]).strip().upper()
                        if not val or val == "NAN": continue
                        
                        d_num = int(col[:2])
                        dt_obj = date(curr_year, m, d_num)
                        
                        cat = None
                        if any(g.upper() in val for g in GIANS):
                            cat = "Lễ Tết" if dt_obj in holidays else "Đi Biển"
                        elif val == "CA": cat = "Nghỉ CA"
                        elif val == "WS": cat = "Làm Bờ"
                        elif val == "NP": cat = "Nghỉ Phép"
                        elif val == "ỐM": cat = "Nghỉ Ốm"
                        
                        if cat: full_year_records.append({"Tháng": f"T{m}", "Loại": cat, "Ngày": 1})
        except: continue
    return pd.DataFrame(full_year_records)

# --- 5. GIAO DIỆN CHÍNH ---
tab1, tab2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 THỐNG KÊ NHÂN SỰ"])

with tab1:
    # Nút chức năng
    c1, c2, _ = st.columns([1.5, 1.5, 5])
    with c1:
        if st.button("📤 LƯU CLOUD", use_container_width=True, type="primary"):
            conn.update(worksheet=sheet_name, data=st.session_state.db)
            st.success("Đã lưu!")
    with c2:
        buffer = io.BytesIO()
        if not st.session_state.db.empty:
            st.session_state.db.to_excel(buffer, index=False)
            st.download_button("📥 XUẤT EXCEL", buffer, file_name=f"PVD_{sheet_name}.xlsx", use_container_width=True)

    # Hiển thị bảng Editor
    if not st.session_state.db.empty:
        # Tự động tính cột Quỹ CA (logic cũ của bạn)
        st.data_editor(st.session_state.db, use_container_width=True, height=550, hide_index=True, key=f"ed_{sheet_name}")
    else:
        st.warning("Chưa có dữ liệu cho tháng này. Vui lòng kiểm tra Google Sheets.")

with tab2:
    if not st.session_state.db.empty:
        names = sorted(st.session_state.db['Họ và Tên'].unique())
        selected = st.selectbox("🔍 Chọn nhân sự để xem báo cáo năm:", names)
        
        with st.spinner(f"Đang tổng hợp dữ liệu cho {selected}..."):
            stats_df = get_detailed_stats(selected)
            
            if not stats_df.empty:
                st.markdown(f"### 📊 Báo cáo hoạt động năm {curr_year}")
                st.markdown(f"**Nhân sự:** {selected}")
                
                # Hiển thị Metrics với chữ "Ngày" đầy đủ và rõ ràng
                m1, m2, m3, m4, m5 = st.columns(5)
                
                # Tính toán tổng số ngày cho từng loại
                sea_total = stats_df[stats_df['Loại']=='Đi Biển']['Ngày'].sum()
                ca_total = stats_df[stats_df['Loại']=='Nghỉ CA']['Ngày'].sum()
                ws_total = stats_df[stats_df['Loại']=='Làm Bờ']['Ngày'].sum()
                np_total = stats_df[stats_df['Loại']=='Nghỉ Phép']['Ngày'].sum()
                holiday_total = stats_df[stats_df['Loại']=='Lễ Tết']['Ngày'].sum()

                m1.metric("🌊 ĐI BIỂN", f"{int(sea_total)} Ngày")
                m2.metric("🏠 NGHỈ CA", f"{int(ca_total)} Ngày")
                m3.metric("🛠️ LÀM BỜ", f"{int(ws_total)} Ngày")
                m4.metric("🌴 NGHỈ PHÉP", f"{int(np_total)} Ngày")
                m5.metric("🧧 LỄ TẾT", f"{int(holiday_total)} Ngày")

                # Vẽ biểu đồ với chú thích rõ ràng
                fig = px.bar(
                    stats_df, x="Tháng", y="Ngày", color="Loại",
                    labels={"Ngày": "Tổng số ngày trong tháng", "Loại": "Trạng thái công việc"},
                    color_discrete_map={
                        "Đi Biển": "#00CC96", "Nghỉ CA": "#EF553B", "Làm Bờ": "#FECB52",
                        "Nghỉ Phép": "#636EFA", "Nghỉ Ốm": "#AB63FA", "Lễ Tết": "#FFA15A"
                    },
                    category_orders={"Tháng": [f"T{i}" for i in range(1, 13)]},
                    height=500
                )
                
                fig.update_layout(
                    legend_title_text='Chú thích màu sắc:',
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)', 
                    font_color="white"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nhân sự này chưa có dữ liệu hoạt động trong năm.")

                # Biểu đồ Plotly
                fig = px.bar(
                    stats_df, x="Tháng", y="Ngày", color="Loại",
                    color_discrete_map={
                        "Đi Biển": "#00CC96", "Nghỉ CA": "#EF553B", "Làm Bờ": "#FECB52",
                        "Nghỉ Phép": "#636EFA", "Nghỉ Ốm": "#AB63FA", "Lễ Tết": "#FFA15A"
                    },
                    category_orders={"Tháng": [f"T{i}" for i in range(1, 13)]},
                    height=500
                )
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nhân sự này chưa có dữ liệu hoạt động được ghi nhận.")
    else:
        st.error("Không thể tải danh sách nhân sự.")
