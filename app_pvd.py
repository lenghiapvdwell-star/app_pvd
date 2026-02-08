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
        df_config = conn.read(worksheet="CONFIG", ttl=600)
        if df_config is not None and not df_config.empty:
            return df_config.iloc[:, 0].dropna().astype(str).tolist()
    except: pass
    return ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

def save_to_cloud_smart(worksheet_name, df):
    df_clean = df.copy()
    for col in df_clean.columns:
        if df_clean[col].dtype == 'object':
            df_clean[col] = df_clean[col].fillna("")
        else:
            df_clean[col] = df_clean[col].fillna(0)
            
    retries = 3
    for i in range(retries):
        try:
            conn.update(worksheet=worksheet_name, data=df_clean)
            return True
        except Exception as e:
            if "429" in str(e):
                time.sleep(5)
                continue
            return False
    return False

# --- 4. KHỞI TẠO ---
if "gians_list" not in st.session_state:
    st.session_state.gians_list = load_gians_from_sheets()

COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
NAMES_BASE = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong"]

# --- 5. CHỌN THỜI GIAN & TẢI DỮ LIỆU ---
_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b")

if 'db' not in st.session_state or st.session_state.get('active_sheet') != sheet_name:
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=300)
        df_load['Họ và Tên'] = df_load['Họ và Tên'].fillna("").astype(str)
        filled_rows = df_load[df_load['Họ và Tên'].str.strip() != ""]
        
        new_empty_rows = pd.DataFrame([{
            'STT': len(filled_rows) + i + 1, 'Họ và Tên': "", 'Công ty': 'PVDWS',
            'Chức danh': 'Casing crew', 'Job Detail': '', 'CA Tháng Trước': 0.0, 'Quỹ CA Tổng': 0.0
        } for i in range(5)])
        
        st.session_state.db = pd.concat([filled_rows, new_empty_rows], ignore_index=True)
    except:
        all_names = NAMES_BASE + [""] * 5
        st.session_state.db = pd.DataFrame({
            'STT': range(1, len(all_names) + 1), 'Họ và Tên': all_names, 
            'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Job Detail': '', 
            'CA Tháng Trước': 0.0, 'Quỹ CA Tổng': 0.0
        })
    st.session_state.active_sheet = sheet_name

num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
for col in DATE_COLS:
    if col not in st.session_state.db.columns: st.session_state.db[col] = ""

# --- 6. LOGIC TÍNH CA ---
def calculate_pvd_logic(df):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,2,21), date(2026,4,25), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    def row_calc(row):
        accrued = 0.0
        name = str(row.get('Họ và Tên', '')).strip()
        if not name: return 0.0
        for col in DATE_COLS:
            v = str(row.get(col, "")).strip().upper()
            if not v or v in ["NAN", "NONE", "WS", "NP", "ỐM"]: continue
            try:
                dt = date(curr_year, curr_month, int(col[:2]))
                is_offshore = any(g.upper() in v for g in st.session_state.gians_list)
                if is_offshore:
                    if dt in hols: accrued += 2.0
                    elif dt.weekday() >= 5: accrued += 1.0
                    else: accrued += 0.5
                elif v == "CA":
                    if dt.weekday() < 5 and dt not in hols: accrued -= 1.0
            except: continue
        return accrued

    df_calc = df.copy()
    df_calc['CA Tháng Trước'] = pd.to_numeric(df_calc['CA Tháng Trước'], errors='coerce').fillna(0.0)
    df_calc['Quỹ CA Tổng'] = df_calc['CA Tháng Trước'] + df_calc.apply(row_calc, axis=1)
    return df_calc

# Chỉ tính toán lại khi hiển thị, không gán ngược liên tục làm trigger rerun
db_display = calculate_pvd_logic(st.session_state.db)

# --- 7. TABS ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ"])

with t1:
    bc1, bc2, _ = st.columns([1.5, 1.5, 5])
    with bc1:
        if st.button("📤 LƯU CLOUD", type="primary", use_container_width=True):
            with st.status("🚀 Đang đồng bộ...", expanded=False):
                if save_to_cloud_smart(sheet_name, st.session_state.db):
                    st.toast("Đã lưu thành công!")
                    time.sleep(0.5)
                    st.rerun()
    with bc2:
        buf = io.BytesIO()
        db_display.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf, f"PVD_{sheet_name}.xlsx", use_container_width=True)

    with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH & QUẢN LÝ GIÀN"):
        # Giữ nguyên các tính năng cũ
        c_add1, c_add2, c_del = st.columns([2, 1, 1])
        new_rig = c_add1.text_input("Tên giàn mới:")
        if c_add2.button("➕ Thêm"):
            if new_rig and new_rig.strip().upper() not in st.session_state.gians_list:
                st.session_state.gians_list.append(new_rig.strip().upper())
                save_to_cloud_smart("CONFIG", pd.DataFrame({"Giàn": st.session_state.gians_list}))
                st.rerun()
        
        st.divider()
        valid_names = [str(n) for n in st.session_state.db['Họ và Tên'].tolist() if str(n).strip() != ""]
        f_staff = st.multiselect("Nhân sự:", valid_names)
        f_date = st.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, num_days)))
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

    # HIỂN THỊ BẢNG (BỎ RERUN TỰ ĐỘNG)
    # Dữ liệu hiển thị lấy từ db_display (có tính Quỹ CA)
    # Dữ liệu gốc trong session_state sẽ được cập nhật âm thầm
    ed_df = st.data_editor(db_display, use_container_width=True, height=600, hide_index=True, key=f"ed_{sheet_name}")
    
    if not ed_df.equals(db_display):
        st.session_state.db = ed_df # Cập nhật dữ liệu vào bộ nhớ nhưng không rerun ngay

with t2:
    st.subheader("📊 Phân tích cường độ & Tổng hợp ngày biển")
    # Biểu đồ vẫn lấy dữ liệu từ bộ nhớ để hiển thị
    chart_names = [str(n) for n in st.session_state.db['Họ và Tên'].tolist() if str(n).strip() != ""]
    sel = st.selectbox("🔍 Chọn nhân sự:", chart_names) if chart_names else st.info("Chưa có dữ liệu.")
    
    if chart_names and sel:
        recs = []
        for m in range(1, 13):
            try:
                df_m = conn.read(worksheet=f"{m:02d}_{curr_year}", ttl=3600)
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
            fig = px.bar(summary, x="Tháng", y="Ngày", color="Loại", barmode="stack",
                         color_discrete_map={"Đi Biển": "#00CC96", "CA": "#EF553B", "WS": "#FECB52", "NP": "#636EFA", "ỐM": "#AB63FA"})
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig, use_container_width=True)
