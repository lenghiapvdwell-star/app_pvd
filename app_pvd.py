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

if 'db' not in st.session_state:
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        if df_load is not None and not df_load.empty:
            st.session_state.db = df_load
        else: raise Exception
    except:
        st.session_state.db = pd.DataFrame({
            'STT': range(1, 67), 
            'Họ và Tên': NAMES_64[:66], 
            'Công ty': 'PVDWS', 
            'Chức danh': 'Casing crew', 
            'Job Detail': '', 
            'CA Tháng Trước': 0.0,
            'Quỹ CA Tổng': 0.0
        })

num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
for col in DATE_COLS:
    if col not in st.session_state.db.columns: st.session_state.db[col] = ""

# --- 5. LOGIC AUTOFILL 7H SÁNG & TÍNH TOÁN CA ---
def process_logic(df):
    hols = [date(2026,1,1), date(2026,4,30), date(2026,5,1), date(2026,9,2),
            date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19)]
    
    df_calc = df.copy()
    now = datetime.now()
    # Xác định ngày hôm nay để so sánh mốc 7h sáng
    today_day = now.day

    for idx, row in df_calc.iterrows():
        accrued = 0.0
        last_status = ""
        
        for i, col in enumerate(DATE_COLS):
            d_int = int(col[:2])
            current_val = str(df_calc.at[idx, col]).strip().upper()
            
            # CHẾ ĐỘ AUTOFILL THÔNG MINH (Chỉ lấp ô trống nếu đã qua 7h sáng của ngày đó)
            if current_val in ["", "NAN", "NONE"]:
                # Nếu là ngày trong quá khứ HOẶC (là ngày hôm nay và đã sau 7h sáng)
                if d_int < today_day or (d_int == today_day and now.hour >= 7):
                    current_val = last_status
            
            last_status = current_status = current_val

            # QUY TẮC CỘNG/TRỪ CA
            if current_status:
                try:
                    dt = date(curr_year, curr_month, d_int)
                    is_we = dt.weekday() >= 5
                    is_ho = dt in hols
                    
                    # 1. Chỉ cộng khi ở Giàn
                    if any(g.upper() in current_status for g in GIANS):
                        if is_ho: accrued += 2.0
                        elif is_we: accrued += 1.0
                        else: accrued += 0.5
                    # 2. Chỉ trừ khi nghỉ CA (Ngày thường)
                    elif current_status == "CA":
                        if not is_we and not is_ho: accrued -= 1.0
                    # 3. WS, NP, ỐM -> KHÔNG TRỪ, KHÔNG CỘNG
                except: pass
            
        ton_cu = pd.to_numeric(row['CA Tháng Trước'], errors='coerce') or 0.0
        df_calc.at[idx, 'Quỹ CA Tổng'] = ton_cu + accrued
        
    return df_calc

# Luôn tính toán lại dựa trên dữ liệu thực tế và thời gian
st.session_state.db = process_logic(st.session_state.db)

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
        st.download_button("📥 XUẤT EXCEL", buf, f"PVD_{sheet_name}.xlsx", use_container_width=True)

    # Hiển thị bảng: Nhập ngày nào chỉ hiện chữ ngày đó
    cols_order = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail', 'CA Tháng Trước', 'Quỹ CA Tổng'] + DATE_COLS
    config = {
        "STT": st.column_config.NumberColumn(disabled=True),
        "Họ và Tên": st.column_config.TextColumn(disabled=True),
        "CA Tháng Trước": st.column_config.NumberColumn("Tồn Cũ", format="%.1f"),
        "Quỹ CA Tổng": st.column_config.NumberColumn("Tổng ca", format="%.1f", disabled=True),
        "Công ty": st.column_config.SelectboxColumn(options=COMPANIES),
        "Chức danh": st.column_config.SelectboxColumn(options=TITLES),
    }
    
    ed_df = st.data_editor(st.session_state.db[cols_order], column_config=config, use_container_width=True, height=600, hide_index=True, key=f"ed_{sheet_name}")
    
    if not ed_df.equals(st.session_state.db[cols_order]):
        st.session_state.db.update(ed_df)
        st.rerun()

with t2:
    st.subheader("📊 Phân tích & Thống kê năm")
    sel = st.selectbox("🔍 Chọn nhân sự:", NAMES_64)
    
    # Giả lập dữ liệu cả năm từ session (Trong thực tế sẽ load từ GSheets nhiều worksheet)
    # Ở đây biểu đồ sẽ quét qua các ngày của tháng hiện tại đã được Autofill ngầm
    person_data = st.session_state.db[st.session_state.db['Họ và Tên'] == sel].iloc[0]
    
    plot_recs = []
    last_v = ""
    for col in DATE_COLS:
        v = str(person_data[col]).strip().upper()
        # Autofill ngầm cho biểu đồ giống thực tế đi biển
        if v in ["", "NAN", "NONE"]: curr_v = last_v
        else: curr_v = v
        last_v = curr_v
        
        if curr_v:
            cat = "Đi Biển" if any(g.upper() in curr_v for g in GIANS) else curr_v
            if cat in ["Đi Biển", "CA", "WS", "NP", "ỐM"]:
                plot_recs.append({"Ngày": col[:5], "Loại": cat, "Số lượng": 1})

    if plot_recs:
        df_p = pd.DataFrame(plot_recs)
        df_sum = df_p.groupby(['Ngày', 'Loại']).sum().reset_index()
        
        # 1. Biểu đồ cột chồng hiện số ngày
        fig = px.bar(df_sum, x="Ngày", y="Số lượng", color="Loại", text="Số lượng",
                     color_discrete_map={"Đi Biển": "#00CC96", "CA": "#EF553B", "WS": "#FECB52", "NP": "#636EFA", "ỐM": "#AB63FA"})
        
        # 2. Biểu đồ nối (Tổng biển lũy kế)
        sea_df = df_p[df_p['Loại'] == "Đi Biển"].copy()
        if not sea_df.empty:
            sea_df['Lũy kế'] = range(1, len(sea_df) + 1)
            fig.add_trace(go.Scatter(x=sea_df["Ngày"], y=sea_df["Lũy kế"], name="Lũy kế Biển",
                                     line=dict(color="#00f2ff", width=3), mode="lines+markers"))

        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig, use_container_width=True)

        # 3. Thống kê tổng năm (Dựa trên tháng hiện tại - có thể mở rộng load các sheet khác)
        st.markdown("### 📈 Tổng hợp trong năm")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tổng đi biển", f"{len(df_p[df_p['Loại']=='Đi Biển'])} ngày")
        c2.metric("Tổng nghỉ CA", f"{len(df_p[df_p['Loại']=='CA'])} ngày")
        c3.metric("Tổng nghỉ phép", f"{len(df_p[df_p['Loại']=='NP'])} ngày")
        c4.metric("Tổng nghỉ ốm", f"{len(df_p[df_p['Loại']=='ỐM'])} ngày")
