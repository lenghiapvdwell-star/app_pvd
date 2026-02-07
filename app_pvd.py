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

# --- 3. KẾT NỐI & HÀM BỔ TRỢ ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_gians_from_sheets():
    try:
        df_config = conn.read(worksheet="CONFIG", ttl=0)
        if df_config is not None and not df_config.empty:
            return df_config.iloc[:, 0].dropna().astype(str).tolist()
    except:
        pass
    return ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

def save_to_cloud_with_retry(worksheet_name, df):
    max_retries = 3
    for i in range(max_retries):
        try:
            conn.update(worksheet=worksheet_name, data=df)
            return True
        except:
            if i < max_retries - 1:
                time.sleep(1.5)
                continue
    return False

# --- 4. KHỞI TẠO DỮ LIỆU ---
if "gians_list" not in st.session_state:
    st.session_state.gians_list = load_gians_from_sheets()

COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong"]

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
        st.session_state.db = df_load
    except:
        st.session_state.db = pd.DataFrame({
            'STT': range(1, 66), 'Họ và Tên': NAMES_64[:65], 
            'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 
            'Job Detail': '', 'CA Tháng Trước': 0.0, 'Quỹ CA Tổng': 0.0
        })
    st.session_state.active_sheet = sheet_name

num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
for col in DATE_COLS:
    if col not in st.session_state.db.columns: st.session_state.db[col] = ""

# --- 6. LOGIC TÍNH CA ---
def calculate_pvd_logic(df):
    hols = [date(2026,1,1), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    def row_calc(row):
        accrued = 0.0
        for col in DATE_COLS:
            v = str(row.get(col, "")).strip().upper()
            if not v or v in ["NAN", "NONE"]: continue
            try:
                dt = date(curr_year, curr_month, int(col[:2]))
                is_we, is_ho = dt.weekday() >= 5, dt in hols
                if any(g.upper() in v for g in st.session_state.gians_list):
                    accrued += 2.0 if is_ho else (1.0 if is_we else 0.5)
                elif v == "CA" and not (is_we or is_ho): accrued -= 1.0
            except: continue
        return accrued
    df['Quỹ CA Tổng'] = df['CA Tháng Trước'].fillna(0) + df.apply(row_calc, axis=1)
    return df

st.session_state.db = calculate_pvd_logic(st.session_state.db)

# --- 7. GIAO DIỆN TABS ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ"])

with t1:
    bc1, bc2, _ = st.columns([1.5, 1.5, 5])
    with bc1:
        if st.button("📤 LƯU CLOUD", type="primary", use_container_width=True):
            with st.spinner("Đang lưu..."):
                if save_to_cloud_with_retry(sheet_name, st.session_state.db):
                    st.success("Đã lưu!")
                    st.cache_data.clear()
                else: st.error("Lỗi kết nối Cloud.")
    with bc2:
        buf = io.BytesIO()
        st.session_state.db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf, f"PVD_{sheet_name}.xlsx", use_container_width=True)

    with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH & QUẢN LÝ GIÀN"):
        st.markdown("##### ⚓ Quản lý giàn (Sheet CONFIG)")
        c_add1, c_add2, c_del = st.columns([2, 1, 1])
        new_rig = c_add1.text_input("Tên giàn mới:")
        if c_add2.button("➕ Thêm", use_container_width=True):
            if new_rig and new_rig not in st.session_state.gians_list:
                st.session_state.gians_list.append(new_rig)
                conn.update(worksheet="CONFIG", data=pd.DataFrame({"Giàn": st.session_state.gians_list}))
                st.rerun()
        
        del_rig = c_del.selectbox("Xóa giàn:", ["-- Chọn --"] + st.session_state.gians_list)
        if del_rig != "-- Chọn --" and st.button(f"🗑️ Xóa {del_rig}"):
            st.session_state.gians_list.remove(del_rig)
            conn.update(worksheet="CONFIG", data=pd.DataFrame({"Giàn": st.session_state.gians_list}))
            st.rerun()

        st.divider()
        c1, c2 = st.columns([2, 1])
        f_staff = c1.multiselect("Nhân sự:", NAMES_64)
        f_date = c2.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, num_days)))
        r2_1, r2_2, r2_3, r2_4 = st.columns(4)
        f_status = r2_1.selectbox("Trạng thái:", ["Không đổi", "Đi Biển", "CA", "WS", "NP", "Ốm"])
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

    ed_df = st.data_editor(st.session_state.db, use_container_width=True, height=600, hide_index=True, key=f"ed_{sheet_name}")
    if not ed_df.equals(st.session_state.db):
        st.session_state.db = ed_df
        st.rerun()

with t2:
    st.subheader("📊 Phân tích cường độ & Tổng hợp ngày biển")
    sel = st.selectbox("🔍 Chọn nhân sự:", NAMES_64)
    
    # Gom dữ liệu cả năm từ Cloud
    recs = []
    for m in range(1, 13):
        try:
            df_m = conn.read(worksheet=f"{m:02d}_{curr_year}", ttl=0)
            if df_m is not None and sel in df_m['Họ và Tên'].values:
                row_p = df_m[df_m['Họ và Tên'] == sel].iloc[0]
                m_lab = date(curr_year, m, 1).strftime("%b")
                for col in df_m.columns:
                    if "/" in col and m_lab in col:
                        v = str(row_p[col]).strip().upper()
                        if v and v not in ["NAN", "NONE", ""]:
                            cat = "Đi Biển" if any(g.upper() in v for g in st.session_state.gians_list) else v
                            if cat in ["Đi Biển", "CA", "WS", "NP", "ỐM"]:
                                recs.append({"Tháng": f"T{m}", "Loại": cat, "Ngày": 1})
        except: continue
    
    if recs:
        pdf = pd.DataFrame(recs)
        summary = pdf.groupby(['Tháng', 'Loại']).sum().reset_index()
        
        # Tính toán lũy kế ngày biển
        sea_only = summary[summary['Loại'] == "Đi Biển"].copy()
        if not sea_only.empty:
            sea_only['MonthIdx'] = sea_only['Tháng'].str[1:].astype(int)
            sea_only = sea_only.sort_values('MonthIdx')
            sea_only['Lũy kế biển'] = sea_only['Ngày'].cumsum()

        # Tạo biểu đồ Stack Bar với nhãn số liệu
        fig = px.bar(summary, x="Tháng", y="Ngày", color="Loại", text="Ngày",
                     barmode="stack",
                     color_discrete_map={"Đi Biển": "#00CC96", "CA": "#EF553B", "WS": "#FECB52", "NP": "#636EFA", "ỐM": "#AB63FA"},
                     category_orders={"Tháng": [f"T{i}" for i in range(1, 13)]})

        # Thêm đường line lũy kế biển
        if not sea_only.empty:
            fig.add_trace(go.Scatter(
                x=sea_only["Tháng"], y=sea_only["Lũy kế biển"],
                name="Lũy kế Biển", mode="lines+markers+text",
                text=sea_only["Lũy kế biển"], textposition="top center",
                line=dict(color="#00f2ff", width=3)
            ))

        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                          font_color="white", height=600, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        # Khối Metric hiển thị tổng kết
        cm1, cm2, cm3, cm4 = st.columns(4)
        total_sea = pdf[pdf['Loại'] == 'Đi Biển']['Ngày'].sum()
        total_ca = pdf[pdf['Loại'] == 'CA']['Ngày'].sum()
        total_np = pdf[pdf['Loại'] == 'NP']['Ngày'].sum()
        total_om = pdf[pdf['Loại'] == 'ỐM']['Ngày'].sum()
        
        cm1.metric("🚢 Tổng Biển (Năm)", f"{total_sea} ngày")
        cm2.metric("🏠 Tổng Nghỉ CA", f"{total_ca} ngày")
        cm3.metric("📅 Nghỉ Phép (NP)", f"{total_np} ngày")
        cm4.metric("💊 Nghỉ Ốm", f"{total_om} ngày")
    else:
        st.info("Chưa có dữ liệu cho nhân sự này trong năm nay.")
