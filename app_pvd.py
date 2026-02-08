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
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=180)
    else:
        st.markdown("### 🔴 PVD WELL")

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. QUẢN LÝ DANH SÁCH GIÀN ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

with st.sidebar:
    st.header("⚙️ QUẢN LÝ GIÀN")
    new_gian = st.text_input("Tên giàn mới:")
    if st.button("➕ Thêm Giàn"):
        if new_gian and new_gian not in st.session_state.GIANS:
            st.session_state.GIANS.append(new_gian)
            st.rerun()
    
    selected_gian_del = st.selectbox("Chọn giàn để xóa:", st.session_state.GIANS)
    if st.button("❌ Xóa Giàn"):
        if selected_gian_del in st.session_state.GIANS:
            st.session_state.GIANS.remove(selected_gian_del)
            st.rerun()

# --- 4. CHỌN THÁNG ---
_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today(), key="main_date_picker")

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b") 

conn = st.connection("gsheets", type=GSheetsConnection)

if "current_sheet" not in st.session_state or st.session_state.current_sheet != sheet_name:
    st.session_state.current_sheet = sheet_name
    if 'db' in st.session_state: del st.session_state.db

# --- 5. DANH SÁCH NHÂN SỰ (FIXED 66 NAMES) ---
NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong"]
COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]

# --- 6. TẢI DỮ LIỆU & FIX LỖI LENGTH ---
if 'db' not in st.session_state:
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        if df_load is not None and not df_load.empty:
            st.session_state.db = df_load
        else: raise Exception
    except:
        # Đảm bảo tất cả các list có cùng độ dài là 66
        st.session_state.db = pd.DataFrame({
            'STT': list(range(1, 67)), 
            'Họ và Tên': NAMES_66, 
            'Công ty': ['PVDWS'] * 66, 
            'Chức danh': ['Casing crew'] * 66, 
            'Job Detail': [''] * 66, 
            'CA Tháng Trước': [0.0] * 66,
            'Quỹ CA Tổng': [0.0] * 66
        })

num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
for col in DATE_COLS:
    if col not in st.session_state.db.columns: st.session_state.db[col] = ""

# --- 7. LOGIC TÍNH CA ---
def calculate_pvd_logic(df):
    hols = [date(2026,1,1), date(2026,4,30), date(2026,5,1), date(2026,9,2),
            date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19)]
    df_calc = df.copy()
    now = datetime.now()
    today_day = now.day

    for idx, row in df_calc.iterrows():
        accrued = 0.0
        last_status = ""
        for col in DATE_COLS:
            d_int = int(col[:2])
            val = str(df_calc.at[idx, col]).strip().upper()
            curr_v = val if val not in ["", "NAN", "NONE"] else (last_status if (d_int < today_day or (d_int == today_day and now.hour >= 7)) else "")
            last_status = curr_v if curr_v else last_status

            if curr_v:
                try:
                    dt = date(curr_year, curr_month, d_int)
                    is_we, is_ho = dt.weekday() >= 5, dt in hols
                    if any(g.upper() in curr_v for g in st.session_state.GIANS):
                        accrued += 2.0 if is_ho else (1.0 if is_we else 0.5)
                    elif curr_v == "CA" and not is_we and not is_ho:
                        accrued -= 1.0
                except: pass
        df_calc.at[idx, 'Quỹ CA Tổng'] = (pd.to_numeric(row['CA Tháng Trước'], errors='coerce') or 0.0) + accrued
    return df_calc

st.session_state.db = calculate_pvd_logic(st.session_state.db)

# --- 8. GIAO DIỆN ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ"])

with t1:
    bc1, bc2, bc3 = st.columns([1.5, 1.5, 1.5])
    with bc1:
        if st.button("📤 LƯU CLOUD", type="primary", use_container_width=True):
            conn.update(worksheet=sheet_name, data=st.session_state.db)
            st.success("Đã lưu!")
    with bc2:
        if st.button("🔄 LÀM MỚI", use_container_width=True):
            del st.session_state.db
            st.rerun()

    with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH"):
        c1, c2 = st.columns([2, 1])
        f_staff = c1.multiselect("Nhân sự:", NAMES_66)
        f_date = c2.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, num_days)))
        r2_1, r2_2, r2_3, r2_4 = st.columns(4)
        f_status = r2_1.selectbox("Trạng thái:", ["Xóa dữ liệu cũ", "Đi Biển", "CA", "WS", "NP", "Ốm"])
        f_val = r2_2.selectbox("Giàn:", st.session_state.GIANS) if f_status == "Đi Biển" else f_status
        f_co = r2_3.selectbox("Cty:", ["Không đổi"] + COMPANIES)
        f_ti = r2_4.selectbox("Chức danh:", ["Không đổi"] + TITLES)
        if st.button("✅ ÁP DỤNG"):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                for person in f_staff:
                    idx = st.session_state.db.index[st.session_state.db['Họ và Tên'] == person][0]
                    for i in range((f_date[1] - f_date[0]).days + 1):
                        d = f_date[0] + timedelta(days=i)
                        if d.month == curr_month:
                            col_n = [c for c in DATE_COLS if c.startswith(f"{d.day:02d}/")][0]
                            st.session_state.db.at[idx, col_n] = "" if f_status == "Xóa dữ liệu cũ" else f_val
                    if f_co != "Không đổi": st.session_state.db.at[idx, 'Công ty'] = f_co
                    if f_ti != "Không đổi": st.session_state.db.at[idx, 'Chức danh'] = f_ti
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
    st.subheader("📊 Biểu đồ (Chỉ tính dữ liệu thực nhập)")
    sel = st.selectbox("🔍 Chọn nhân sự:", NAMES_66)
    
    @st.cache_data(ttl=10)
    def load_clean_year(year):
        data = {}
        for m in range(1, 13):
            try: data[m] = conn.read(worksheet=f"{m:02d}_{year}", ttl=0)
            except: pass
        return data

    year_data = load_clean_year(curr_year)
    recs = []
    if year_data:
        for m, df_m in year_data.items():
            if sel in df_m['Họ và Tên'].values:
                row_p = df_m[df_m['Họ và Tên'] == sel].iloc[0]
                m_label = date(curr_year, m, 1).strftime("%b")
                for col in df_m.columns:
                    if "/" in col and m_label in col:
                        v = str(row_p[col]).strip().upper()
                        if v and v not in ["NAN", "NONE", ""]:
                            cat = "Đi Biển" if any(g.upper() in v for g in st.session_state.GIANS) else v
                            if cat in ["Đi Biển", "CA", "WS", "NP", "ỐM"]:
                                recs.append({"Tháng": f"T{m}", "Loại": cat, "Ngày": 1})

    if recs:
        pdf = pd.DataFrame(recs)
        summary = pdf.groupby(['Tháng', 'Loại']).sum().reset_index()
        fig = px.bar(summary, x="Tháng", y="Ngày", color="Loại", text="Ngày", barmode="stack",
                     color_discrete_map={"Đi Biển": "#00CC96", "CA": "#EF553B", "WS": "#FECB52", "NP": "#636EFA", "ỐM": "#AB63FA"},
                     category_orders={"Tháng": [f"T{i}" for i in range(1, 13)]})
        sea_only = summary[summary['Loại'] == "Đi Biển"].copy()
        if not sea_only.empty:
            sea_only['MIdx'] = sea_only['Tháng'].str[1:].astype(int)
            sea_only = sea_only.sort_values('MIdx')
            sea_only['Lũy kế'] = sea_only['Ngày'].cumsum()
            fig.add_trace(go.Scatter(x=sea_only["Tháng"], y=sea_only["Lũy kế"], name="Cộng dồn Biển", mode="lines+markers+text", text=sea_only["Lũy kế"], textposition="top center", line=dict(color="#00f2ff", width=3)))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        vals = pdf['Loại'].value_counts().to_dict()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tổng Biển", f"{vals.get('Đi Biển', 0)} ngày")
        c2.metric("Tổng Nghỉ CA", f"{vals.get('CA', 0)} ngày")
        c3.metric("Tổng Phép", f"{vals.get('NP', 0)} ngày")
        c4.metric("Tổng Ốm", f"{vals.get('ỐM', 0)} ngày")
    else:
        st.info("Chưa có dữ liệu thực nhập.")
