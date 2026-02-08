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

# --- 4. QUẢN LÝ GIÀN TRÊN SIDEBAR (SLIDE) ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

with st.sidebar:
    st.header("⚙️ QUẢN LÝ GIÀN")
    new_gian = st.text_input("Tên giàn mới:")
    if st.button("➕ Thêm Giàn", use_container_width=True):
        if new_gian and new_gian.strip().upper() not in st.session_state.GIANS:
            st.session_state.GIANS.append(new_gian.strip().upper())
            st.rerun()
    
    st.divider()
    del_gian = st.selectbox("Xóa giàn:", ["-- Chọn --"] + st.session_state.GIANS)
    if del_gian != "-- Chọn --":
        if st.button(f"🗑️ Xóa {del_gian}", use_container_width=True):
            st.session_state.GIANS.remove(del_gian)
            st.rerun()
    
    st.info("Danh sách giàn hiện tại: " + ", ".join(st.session_state.GIANS))

# --- 5. CHỌN THÁNG LÀM VIỆC ---
COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]

_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b")

# Tính toán tên sheet tháng trước
first_day_curr = working_date.replace(day=1)
last_month_date = first_day_curr - timedelta(days=1)
prev_sheet_name = last_month_date.strftime("%m_%Y")

# --- NÂNG CẤP: LOGIC TẢI DỮ LIỆU VÀ CHUYỂN TỒN ---
if 'active_sheet' in st.session_state and st.session_state.active_sheet != sheet_name:
    if 'db' in st.session_state: del st.session_state.db

if 'db' not in st.session_state:
    try:
        # 1. Đọc sheet hiện tại (ttl=0 để luôn lấy mới)
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        if df_load.empty: raise ValueError
        st.session_state.db = df_load.fillna("").replace(["nan", "NaN", "None"], "")
    except:
        # 2. Nếu sheet tháng mới chưa có, lấy tồn từ tháng cũ
        try:
            df_prev = conn.read(worksheet=prev_sheet_name, ttl=0)
            prev_balances = dict(zip(df_prev['Họ và Tên'], df_prev['Quỹ CA Tổng']))
        except:
            prev_balances = {}

        count = len(NAMES_66)
        new_data = {
            'STT': range(1, count + 1), 
            'Họ và Tên': NAMES_66, 
            'Công ty': 'PVDWS', 
            'Chức danh': 'Casing crew', 
            'Job Detail': '', 
            'CA Tháng Trước': [float(prev_balances.get(name, 0.0)) for name in NAMES_66], 
            'Quỹ CA Tổng': 0.0
        }
        st.session_state.db = pd.DataFrame(new_data)
    st.session_state.active_sheet = sheet_name

# Đảm bảo các cột ngày
num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
for col in DATE_COLS:
    if col not in st.session_state.db.columns: st.session_state.db[col] = ""

# --- 6. HÀM TÍNH TOÁN ---
def recalculate_ca(df):
    hols = [date(2026,1,1), date(2026,4,30), date(2026,5,1), date(2026,9,2),
            date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19)]
    df_calc = df.copy()
    df_calc['CA Tháng Trước'] = pd.to_numeric(df_calc.get('CA Tháng Trước', 0.0), errors='coerce').fillna(0.0)
    
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

# --- 7. TABS GIAO DIỆN ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ"])

with t1:
    bc1, bc2, bc3 = st.columns([1.5, 1.5, 1.5])
    with bc1:
        if st.button("📤 LƯU CLOUD (DÙNG KHI XONG)", type="primary", use_container_width=True):
            st.session_state.db = recalculate_ca(st.session_state.db)
            if save_to_cloud_smart(sheet_name, st.session_state.db):
                st.success(f"Đã lưu thành công dữ liệu {sheet_name}!")
                time.sleep(1)
                st.rerun()
    with bc2:
        # NÂNG CẤP: Nút làm mới dữ liệu thủ công
        if st.button("🔄 LÀM MỚI TỪ GOOGLE SHEET", use_container_width=True):
            if 'db' in st.session_state: del st.session_state.db
            st.rerun()
    with bc3:
        buf = io.BytesIO()
        st.session_state.db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf.getvalue(), f"PVD_{sheet_name}.xlsx", use_container_width=True)

    with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH (GHI ĐÈ)"):
        c1, c2 = st.columns([2, 1])
        f_staff = c1.multiselect("Nhân sự:", NAMES_66)
        f_date = c2.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, num_days)))
        r2_1, r2_2, r2_3, r2_4 = st.columns(4)
        f_status = r2_1.selectbox("Trạng thái:", ["Xóa trắng", "Đi Biển", "CA", "WS", "NP", "Ốm"])
        f_val = r2_2.selectbox("Giàn:", st.session_state.GIANS) if f_status == "Đi Biển" else f_status
        f_co = r2_3.selectbox("Cty:", ["Không đổi"] + COMPANIES)
        f_ti = r2_4.selectbox("Chức danh:", ["Không đổi"] + TITLES)
        
        if st.button("✅ ÁP DỤNG THAY ĐỔI"):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                for person in f_staff:
                    idx = st.session_state.db.index[st.session_state.db['Họ và Tên'] == person][0]
                    for i in range((f_date[1] - f_date[0]).days + 1):
                        d = f_date[0] + timedelta(days=i)
                        if d.month == curr_month:
                            day_prefix = f"{d.day:02d}/"
                            target_col = [c for c in DATE_COLS if c.startswith(day_prefix)]
                            if target_col:
                                st.session_state.db.at[idx, target_col[0]] = "" if f_status == "Xóa trắng" else f_val
                    if f_co != "Không đổi": st.session_state.db.at[idx, 'Công ty'] = f_co
                    if f_ti != "Không đổi": st.session_state.db.at[idx, 'Chức danh'] = f_ti
                st.session_state.db = recalculate_ca(st.session_state.db)
                st.rerun()

    # --- ĐẢM BẢO THỨ TỰ CỘT ---
    basic_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail', 'CA Tháng Trước', 'Quỹ CA Tổng']
    for col in basic_cols:
        if col not in st.session_state.db.columns:
            st.session_state.db[col] = 0.0 if "CA" in col else ""
    
    ordered_cols = basic_cols + DATE_COLS
    display_df = st.session_state.db[ordered_cols].fillna("").replace(["nan", "NaN"], "")
    
    ed_df = st.data_editor(display_df, use_container_width=True, height=600, hide_index=True,
                           column_config={
                               "STT": st.column_config.NumberColumn(disabled=True),
                               "Họ và Tên": st.column_config.TextColumn(disabled=True),
                               "CA Tháng Trước": st.column_config.NumberColumn("Tồn cũ", format="%.1f"),
                               "Quỹ CA Tổng": st.column_config.NumberColumn("Tổng ca", format="%.1f", disabled=True),
                           })
    if not ed_df.equals(display_df):
        st.session_state.db.update(ed_df)
        st.session_state.db = recalculate_ca(st.session_state.db)
        st.rerun()

with t2:
    st.subheader(f"📊 Phân tích hoạt động của nhân sự năm {curr_year}")
    sel_name = st.selectbox("🔍 Chọn nhân sự xem biểu đồ:", NAMES_66)
    
    recs = []
    with st.spinner("Đang tổng hợp dữ liệu 12 tháng..."):
        for m in range(1, 13):
            m_sheet = f"{m:02d}_{curr_year}"
            try:
                df_m = conn.read(worksheet=m_sheet, ttl=600)
                if df_m is not None and sel_name in df_m['Họ và Tên'].values:
                    row_p = df_m[df_m['Họ và Tên'] == sel_name].iloc[0]
                    m_label = date(curr_year, m, 1).strftime("%b")
                    for col in df_m.columns:
                        if "/" in col and m_label in col:
                            v = str(row_p[col]).strip().upper()
                            if v and v not in ["", "NAN", "NONE"]:
                                cat = "Đi Biển" if any(g.upper() in v for g in st.session_state.GIANS) else v
                                if cat in ["Đi Biển", "CA", "WS", "NP", "ỐM"]:
                                    recs.append({"Tháng": f"T{m}", "Loại": cat, "Ngày": 1})
            except: continue

    if recs:
        pdf = pd.DataFrame(recs)
        summary = pdf.groupby(['Tháng', 'Loại']).size().reset_index(name='Ngày')
        summary['MonthIdx'] = summary['Tháng'].str[1:].astype(int)
        summary = summary.sort_values('MonthIdx')

        fig = px.bar(summary, x="Tháng", y="Ngày", color="Loại", text="Ngày",
                     barmode="stack", color_discrete_map={"Đi Biển": "#00CC96", "CA": "#EF553B", "WS": "#FECB52", "NP": "#636EFA", "ỐM": "#AB63FA"},
                     category_orders={"Tháng": [f"T{i}" for i in range(1, 13)]})

        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", height=600)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nhân sự này chưa có dữ liệu hoạt động trong năm.")
