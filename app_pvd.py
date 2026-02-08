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

# --- 3. KẾT NỐI & SMART SAVE ---
conn = st.connection("gsheets", type=GSheetsConnection)

def save_to_cloud_smart(worksheet_name, df):
    df_clean = df.fillna("").replace(["nan", "NaN", "None"], "")
    try:
        conn.update(worksheet=worksheet_name, data=df_clean)
        return True
    except Exception as e:
        st.error(f"Lỗi Cloud: {e}")
        return False

# --- 4. KHỞI TẠO DỮ LIỆU ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]

# --- 5. CHỌN THÁNG ---
_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b")

if 'db' not in st.session_state or st.session_state.get('active_sheet') != sheet_name:
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        st.session_state.db = df_load.fillna("").replace(["nan", "NaN", "None"], "")
    except:
        count = len(NAMES_66)
        st.session_state.db = pd.DataFrame({
            'STT': range(1, count + 1), 'Họ và Tên': NAMES_66, 
            'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 
            'Job Detail': '', 'CA Tháng Trước': 0.0, 'Quỹ CA Tổng': 0.0
        })
    st.session_state.active_sheet = sheet_name

num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
for col in DATE_COLS:
    if col not in st.session_state.db.columns: st.session_state.db[col] = ""

# --- 6. LOGIC TÍNH CA ---
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
                day_int = int(col[:2])
                dt = date(curr_year, curr_month, day_int)
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
    bc1, bc2 = st.columns([1.5, 1.5])
    with bc1:
        if st.button("📤 LƯU CLOUD", type="primary", use_container_width=True):
            st.session_state.db = recalculate_ca(st.session_state.db)
            if save_to_cloud_smart(sheet_name, st.session_state.db):
                st.success("Đã lưu thành công!")
                time.sleep(1)
                st.rerun()
    with bc2:
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
                            st.session_state.db.at[idx, col_n] = "" if f_status == "Xóa trắng" else f_val
                    if f_co != "Không đổi": st.session_state.db.at[idx, 'Công ty'] = f_co
                    if f_ti != "Không đổi": st.session_state.db.at[idx, 'Chức danh'] = f_ti
                st.session_state.db = recalculate_ca(st.session_state.db)
                st.rerun()

    # HIỂN THỊ DỮ LIỆU
    display_df = st.session_state.db.fillna("").replace(["nan", "NaN"], "")
    ed_df = st.data_editor(display_df, use_container_width=True, height=600, hide_index=True,
                           column_config={"STT": st.column_config.NumberColumn(disabled=True),
                                         "Họ và Tên": st.column_config.TextColumn(disabled=True),
                                         "Quỹ CA Tổng": st.column_config.NumberColumn("Tổng ca", format="%.1f", disabled=True)})
    if not ed_df.equals(display_df):
        st.session_state.db.update(ed_df)
        st.session_state.db = recalculate_ca(st.session_state.db)
        st.rerun()

with t2:
    st.subheader(f"📊 Phân tích dữ liệu năm {curr_year}")
    sel_name = st.selectbox("🔍 Chọn nhân sự xem biểu đồ:", NAMES_66)
    
    recs = []
    with st.spinner("Đang tổng hợp dữ liệu 12 tháng..."):
        for m in range(1, 13):
            m_sheet = f"{m:02d}_{curr_year}"
            try:
                # ttl=3600 để tránh load lại từ cloud khi đổi nhân sự
                df_m = conn.read(worksheet=m_sheet, ttl=3600)
                if df_m is not None and sel_name in df_m['Họ và Tên'].values:
                    row_p = df_m[df_m['Họ và Tên'] == sel_name].iloc[0]
                    m_label = date(curr_year, m, 1).strftime("%b")
                    for col in df_m.columns:
                        if "/" in col and m_label in col:
                            v = str(row_p[col]).strip().upper()
                            if v and v not in ["", "NAN", "NONE"]:
                                cat = "Đi Biển" if any(g.upper() in v for g in st.session_state.GIANS) else v
                                if cat in ["Đi Biển", "CA", "WS", "NP", "ỐM"]:
                                    recs.append({"Tháng": f"T{m}", "Loại": cat, "Số ngày": 1})
            except: continue

    if recs:
        pdf = pd.DataFrame(recs)
        summary = pdf.groupby(['Tháng', 'Loại']).size().reset_index(name='Ngày')
        
        # Sắp xếp tháng theo đúng thứ tự T1 -> T12
        summary['MonthIdx'] = summary['Tháng'].str[1:].astype(int)
        summary = summary.sort_values('MonthIdx')

        # Tính lũy kế riêng cho Đi Biển
        sea_data = summary[summary['Loại'] == "Đi Biển"].copy()
        sea_data['Lũy kế biển'] = sea_data['Ngày'].cumsum()

        fig = px.bar(summary, x="Tháng", y="Ngày", color="Loại", text="Ngày",
                     barmode="stack", title=f"Thống kê hoạt động của {sel_name}",
                     color_discrete_map={"Đi Biển": "#00CC96", "CA": "#EF553B", "WS": "#FECB52", "NP": "#636EFA", "ỐM": "#AB63FA"},
                     category_orders={"Tháng": [f"T{i}" for i in range(1, 13)]})

        if not sea_data.empty:
            fig.add_trace(go.Scatter(x=sea_data["Tháng"], y=sea_data["Lũy kế biển"], name="Lũy kế Biển",
                                     mode="lines+markers+text", text=sea_data["Lũy kế biển"], 
                                     textposition="top center", line=dict(color="#00f2ff", width=3)))

        fig.update_layout(hovermode="x unified", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig, use_container_width=True)
        
        # Chỉ số Metric
        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🚢 Tổng Biển", f"{pdf[pdf['Loại']=='Đi Biển'].shape[0]} ngày")
        m2.metric("🏠 Tổng CA", f"{pdf[pdf['Loại']=='CA'].shape[0]} ngày")
        m3.metric("📅 Nghỉ Phép", f"{pdf[pdf['Loại']=='NP'].shape[0]} ngày")
        m4.metric("💊 Nghỉ Ốm", f"{pdf[pdf['Loại']=='ỐM'].shape[0]} ngày")
    else:
        st.info("Chưa tìm thấy dữ liệu hoạt động trong năm của nhân sự này.")
