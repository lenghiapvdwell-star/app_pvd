import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 0.5rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; 
        font-size: 80px !important; 
        font-weight: bold !important;
        text-align: center !important; 
        width: 100% !important;
        display: block !important;
        margin-top: 10px !important;
        margin-bottom: 10px !important;
        text-shadow: 4px 4px 8px #000 !important;
        font-family: 'Arial Black', sans-serif !important;
        line-height: 1.1 !important;
    }
    .stButton>button {border-radius: 5px; height: 3em; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. HIỂN THỊ HEADER ---
c_logo, _ = st.columns([1, 4])
with c_logo:
    if os.path.exists("logo_pvd.png"): st.image("logo_pvd.png", width=220)
    else: st.markdown("### 🔴 PVD")

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

st.write("---")

# --- 3. DỮ LIỆU & KẾT NỐI ---
conn = st.connection("gsheets", type=GSheetsConnection)
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b") 
sheet_name = working_date.strftime("%m_%Y") 

# Khởi tạo danh sách mặc định
if 'gians' not in st.session_state:
    st.session_state.gians = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9" , "THOR", "SDE" , "GUNNLOD"]

if 'companies' not in st.session_state:
    st.session_state.companies = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]

if 'titles' not in st.session_state:
    st.session_state.titles = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]

NAMES_64 = [
    "Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", 
    "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", 
    "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", 
    "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", 
    "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", 
    "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", 
    "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", 
    "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", 
    "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", 
    "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", 
    "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong"
]

def get_prev_ca():
    prev_date = date(curr_year, curr_month, 1) - timedelta(days=1)
    prev_sheet = prev_date.strftime("%m_%Y")
    try:
        df_prev = conn.read(worksheet=prev_sheet, ttl=0)
        series = df_prev.set_index('Họ và Tên')['Quỹ CA Tổng']
        return pd.to_numeric(series, errors='coerce').fillna(0.0).to_dict()
    except: return {}

if 'active_sheet' not in st.session_state or st.session_state.active_sheet != sheet_name:
    st.session_state.active_sheet = sheet_name
    prev_ca_data = get_prev_ca()
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        if df_load is not None and not df_load.empty:
            st.session_state.db = df_load
            st.session_state.db['CA Tháng Trước'] = st.session_state.db['Họ và Tên'].map(prev_ca_data).fillna(0.0)
        else: raise Exception
    except:
        df_init = pd.DataFrame({'STT': range(1, 66), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Job Detail': '', 'CA Tháng Trước': 0.0})
        df_init['CA Tháng Trước'] = df_init['Họ và Tên'].map(prev_ca_data).fillna(0.0)
        st.session_state.db = df_init

num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
for c in DATE_COLS:
    if c not in st.session_state.db.columns: st.session_state.db[c] = ""

def apply_calculation(df):
    holidays = [date(curr_year, 1, 1), date(curr_year, 4, 30), date(curr_year, 5, 1), date(curr_year, 9, 2)]
    if curr_year == 2026: holidays += [date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19)]
    
    def calc_row(row):
        total_delta = 0.0
        for col in DATE_COLS:
            val = str(row.get(col, "")).strip()
            if not val or val.lower() in ["nan", ""]: continue
            dt = date(curr_year, curr_month, int(col[:2]))
            if val in st.session_state.gians:
                if dt in holidays: total_delta += 2.0
                elif dt.weekday() >= 5: total_delta += 1.0
                else: total_delta += 0.5
            elif val.upper() == "CA":
                if dt not in holidays and dt.weekday() < 5: total_delta -= 1.0
        return total_delta

    df['CA Tháng Trước'] = pd.to_numeric(df['CA Tháng Trước'], errors='coerce').fillna(0.0).astype(float)
    df['Phát sinh trong tháng'] = df.apply(calc_row, axis=1).astype(float)
    df['Quỹ CA Tổng'] = df['CA Tháng Trước'] + df['Phát sinh trong tháng']
    return df

st.session_state.db = apply_calculation(st.session_state.db)
main_cols = ['STT', 'Họ và Tên', 'Quỹ CA Tổng', 'CA Tháng Trước', 'Công ty', 'Chức danh', 'Job Detail']
st.session_state.db = st.session_state.db.reindex(columns=main_cols + DATE_COLS)

# --- 4. NÚT CHỨC NĂNG ---
bc1, bc2, _ = st.columns([1.5, 1.5, 5])
with bc1:
    if st.button("📤 LƯU CLOUD", use_container_width=True, type="primary"):
        conn.update(worksheet=sheet_name, data=st.session_state.db)
        st.success("Đã đồng bộ dữ liệu lên Cloud!")
with bc2:
    buffer = io.BytesIO()
    st.session_state.db.to_excel(buffer, index=False)
    st.download_button("📥 XUẤT EXCEL", buffer, file_name=f"PVD_WS_{sheet_name}.xlsx", use_container_width=True)

# --- 5. TABS ---
t1, t2, t3 = st.tabs(["🚀 ĐIỀU ĐỘNG & NHÂN SỰ", "🏗️ QUẢN LÝ DANH MỤC", "📊 THỐNG KÊ"])

with t1:
    with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH (Trạng thái, Công ty, Chức danh)"):
        # Dòng 1: Chọn nhân sự và Thời gian
        r1_c1, r1_c2 = st.columns([2, 1.2])
        f_staff = r1_c1.multiselect("Chọn nhân sự cần cập nhật:", st.session_state.db['Họ và Tên'].tolist())
        f_date = r1_c2.date_input("Thời gian áp dụng:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, num_days)))
        
        # Dòng 2: Chọn Trạng thái, Công ty, Chức danh
        r2_c1, r2_c2, r2_c3, r2_c4 = st.columns([1, 1, 1, 1])
        f_status = r2_c1.selectbox("Trạng thái mới:", ["Không đổi", "Đi Biển", "CA", "NP", "Ốm", "WS"])
        f_val = r2_c2.selectbox("Chọn Giàn:", st.session_state.gians) if f_status == "Đi Biển" else f_status
        f_co = r2_c3.selectbox("Cập nhật Công ty:", ["Không đổi"] + st.session_state.companies)
        f_ti = r2_c4.selectbox("Cập nhật Chức danh:", ["Không đổi"] + st.session_state.titles)
        
        if st.button("✅ XÁC NHẬN CẬP NHẬT", use_container_width=True):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                s_d, e_d = f_date
                # Cập nhật Công ty & Chức danh (nếu có chọn)
                if f_co != "Không đổi":
                    st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), 'Công ty'] = f_co
                if f_ti != "Không đổi":
                    st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), 'Chức danh'] = f_ti
                
                # Cập nhật trạng thái theo ngày
                if f_status != "Không đổi":
                    for i in range((e_d - s_d).days + 1):
                        day = s_d + timedelta(days=i)
                        if day.month == curr_month:
                            col = f"{day.day:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][day.weekday()]})"
                            if col in st.session_state.db.columns:
                                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), col] = f_val
                st.rerun()

    # Bảng biên tập chính
    config = {
        "STT": st.column_config.NumberColumn("STT", width=40, disabled=True, pinned=True),
        "Họ và Tên": st.column_config.TextColumn("Họ và Tên", width=180, pinned=True),
        "Quỹ CA Tổng": st.column_config.NumberColumn("Tồn Cuối", width=85, format="%.1f", disabled=True, pinned=True),
        "CA Tháng Trước": st.column_config.NumberColumn("Tồn Đầu", width=80, format="%.1f", pinned=True),
        "Công ty": st.column_config.SelectboxColumn("Công ty", width=120, options=st.session_state.companies, pinned=True),
        "Chức danh": st.column_config.SelectboxColumn("Chức danh", width=120, options=st.session_state.titles, pinned=True),
    }
    for col in DATE_COLS: config[col] = st.column_config.TextColumn(col, width=75)

    edited_df = st.data_editor(st.session_state.db, column_config=config, use_container_width=True, height=600, hide_index=True, key=f"ed_{sheet_name}")
    if not edited_df.equals(st.session_state.db):
        st.session_state.db = edited_df
        st.rerun()

with t2:
    st.subheader("⚙️ QUẢN LÝ DANH MỤC HỆ THỐNG")
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        st.write("**🏗️ Giàn khoan**")
        new_g = st.text_input("Tên giàn mới:", key="add_g")
        if st.button("➕ Thêm Giàn"):
            if new_g and new_g not in st.session_state.gians:
                st.session_state.gians.append(new_g)
                st.rerun()
        st.dataframe(st.session_state.gians, use_container_width=True)

    with col_b:
        st.write("**🏢 Công ty**")
        new_c = st.text_input("Tên công ty mới:", key="add_c")
        if st.button("➕ Thêm Công ty"):
            if new_c and new_c not in st.session_state.companies:
                st.session_state.companies.append(new_c)
                st.rerun()
        st.dataframe(st.session_state.companies, use_container_width=True)

    with col_c:
        st.write("**🎖️ Chức danh**")
        new_t = st.text_input("Chức danh mới:", key="add_t")
        if st.button("➕ Thêm Chức danh"):
            if new_t and new_t not in st.session_state.titles:
                st.session_state.titles.append(new_t)
                st.rerun()
        st.dataframe(st.session_state.titles, use_container_width=True)

with t3:
    st.subheader("📊 THỐNG KÊ NHÂN SỰ")
    st.write("Dữ liệu đang được tổng hợp dựa trên bảng Điều động...")
    # Tương lai có thể thêm biểu đồ số người đi biển/nghỉ CA tại đây
