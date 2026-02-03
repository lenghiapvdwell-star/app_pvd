import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff;
        font-size: 35px;
        font-weight: bold;
        text-align: center;
        margin: 0;
        text-shadow: 2px 2px 4px #000;
    }
    .stButton>button {border-radius: 5px; height: 3em;}
    </style>
    """, unsafe_allow_html=True)

# --- HEADER NGANG HÀNG: LOGO - CHỮ - NGÀY ---
c1, c2, c3 = st.columns([1.2, 3.5, 1.3])

with c1:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=180)
    else:
        st.write("### PVD LOGO")

with c2:
    st.markdown('<p class="main-title">PVD WELL SERVICES MANAGEMENT</p>', unsafe_allow_html=True)

with c3:
    st.write("##") 
    working_date = st.date_input("📅 CHỌN THÁNG:", value=date.today())

st.write("---")

# --- 2. DỮ LIỆU NHÂN SỰ (ĐÃ FIX LỖI ĐỘ DÀI) ---
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong"]

# --- 3. THUẬT TOÁN & KẾT NỐI ---
conn = st.connection("gsheets", type=GSheetsConnection)
curr_month = working_date.month
curr_year = working_date.year
month_abbr = working_date.strftime("%b") 
sheet_name = working_date.strftime("%m_%Y") 

if 'gians' not in st.session_state:
    st.session_state.gians = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9" , "THOR", "SDE" , "GUNNLOD"]

def get_prev_ca(p_name):
    try:
        df_p = conn.read(worksheet=p_name, ttl=0)
        return df_p.set_index('Họ và Tên')['Quỹ CA Tổng'].to_dict() if 'Quỹ CA Tổng' in df_p.columns else {}
    except: return {}

if 'active_sheet' not in st.session_state or st.session_state.active_sheet != sheet_name:
    st.session_state.active_sheet = sheet_name
    prev_name = (date(curr_year, curr_month, 1) - timedelta(days=1)).strftime("%m_%Y")
    prev_ca_data = get_prev_ca(prev_name)
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        if df_load is not None and not df_load.empty:
            st.session_state.db = df_load
            st.session_state.db['CA Tháng Trước'] = st.session_state.db['Họ và Tên'].map(prev_ca_data).fillna(0.0)
        else: raise Exception
    except:
        df_init = pd.DataFrame({'STT': range(1, 65), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': ''})
        df_init['CA Tháng Trước'] = df_init['Họ và Tên'].map(prev_ca_data).fillna(0.0)
        st.session_state.db = df_init

num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
for c in DATE_COLS: 
    if c not in st.session_state.db.columns: st.session_state.db[c] = ""

def update_logic(df):
    holidays = [date(curr_year, 1, 1), date(curr_year, 4, 30), date(curr_year, 5, 1), date(curr_year, 9, 2)]
    def calc_row(row):
        total = 0.0
        for col in DATE_COLS:
            val = str(row.get(col, "")).strip()
            if not val or val.lower() in ["nan", "none", ""]: continue
            dt = date(curr_year, curr_month, int(col[:2]))
            if val in st.session_state.gians:
                if dt in holidays: total += 2.0
                elif dt.weekday() >= 5: total += 1.0
                else: total += 0.5
            elif val.upper() == "CA" and dt.weekday() < 5 and dt not in holidays: total -= 1.0
        return total
    df['Phát sinh trong tháng'] = df.apply(calc_row, axis=1)
    df['Quỹ CA Tổng'] = pd.to_numeric(df['CA Tháng Trước'], errors='coerce').fillna(0) + df['Phát sinh trong tháng']
    return df

st.session_state.db = update_logic(st.session_state.db)
cols_order = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail', 'Quỹ CA Tổng', 'CA Tháng Trước'] + DATE_COLS
st.session_state.db = st.session_state.db.reindex(columns=cols_order)

# --- 4. THAO TÁC NHANH ---
act_c1, act_c2, _ = st.columns([1.5, 1.5, 4])
with act_c1:
    if st.button("📤 UPLOAD CLOUD", use_container_width=True, type="primary"):
        conn.update(worksheet=sheet_name, data=st.session_state.db)
        st.success("Đã lưu!")
with act_c2:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        st.session_state.db.to_excel(writer, index=False, sheet_name=sheet_name)
    st.download_button("📥 XUẤT EXCEL", buffer, file_name=f"PVD_{sheet_name}.xlsx", use_container_width=True)

# --- 5. TABS ---
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN"])

with tabs[0]:
    with st.expander("🛠️ Công cụ cập nhật nhanh"):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1.2])
        f_staff = c1.multiselect("Nhân sự:", st.session_state.db['Họ và Tên'].tolist())
        f_status = c2.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm"])
        f_val = c3.selectbox("Giàn:", st.session_state.gians) if f_status == "Đi Biển" else f_status
        f_date = c4.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, num_days)))
        if st.button("✅ ÁP DỤNG", use_container_width=True):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                s_d, e_d = f_date
                for i in range((e_d - s_d).days + 1):
                    day = s_d + timedelta(days=i)
                    if day.month == curr_month:
                        col = f"{day.day:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][day.weekday()]})"
                        if col in st.session_state.db.columns:
                            st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), col] = f_val
                st.rerun()

    config = {
        "STT": st.column_config.NumberColumn("STT", width=40, disabled=True, pinned=True),
        "Họ và Tên": st.column_config.TextColumn("Họ và Tên", width=180, pinned=True),
        "Công ty": st.column_config.TextColumn("Công ty", width=80),
        "Chức danh": st.column_config.TextColumn("Chức danh", width=100),
        "Job Detail": st.column_config.TextColumn("Job Detail", width=120),
        "Quỹ CA Tổng": st.column_config.NumberColumn("T ca", width=70, format="%.1f", disabled=True, pinned=True),
        "CA Tháng Trước": st.column_config.NumberColumn("Tồn cũ", width=70, format="%.1f", pinned=True),
    }
    for col in DATE_COLS: config[col] = st.column_config.TextColumn(col, width=65)

    st.data_editor(st.session_state.db, column_config=config, use_container_width=True, height=600, hide_index=True, key=f"ed_{sheet_name}")

with tabs[1]:
    st.subheader("🏗️ Quản lý Giàn khoan")
    st.dataframe(pd.DataFrame({"Tên Giàn": st.session_state.gians}), use_container_width=True)
    new_g = st.text_input("Thêm giàn mới:")
    if st.button("➕ Thêm"):
        if new_g and new_g not in st.session_state.gians:
            st.session_state.gians.append(new_g)
            st.rerun()

with tabs[2]:
    st.subheader("👤 Danh sách nhân sự")
    st.dataframe(st.session_state.db[['STT', 'Họ và Tên', 'Công ty', 'Chức danh']], use_container_width=True, hide_index=True)
