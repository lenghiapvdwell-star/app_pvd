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
    # Thêm key để theo dõi sự thay đổi tháng
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today(), key="main_date_input")

st.write("---")

# --- 3. DỮ LIỆU & KẾT NỐI ---
conn = st.connection("gsheets", type=GSheetsConnection)
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b") 
sheet_name = working_date.strftime("%m_%Y") 

# --- CHIẾN THUẬT FIX LỖI: RESET SESSION KHI ĐỔI THÁNG ---
if "current_active_month" not in st.session_state:
    st.session_state.current_active_month = sheet_name

if st.session_state.current_active_month != sheet_name:
    # Nếu phát hiện đổi tháng, xóa sạch các state liên quan đến editor cũ
    keys_to_delete = [k for k in st.session_state.keys() if k.startswith("ed_")]
    for k in keys_to_delete:
        del st.session_state[k]
    st.session_state.current_active_month = sheet_name
    # Buộc app phải load lại từ đầu với tháng mới
    st.rerun()

# Khởi tạo danh mục mặc định
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

# Quản lý việc tải dữ liệu vào session_state
if 'db' not in st.session_state or st.session_state.get('loaded_sheet') != sheet_name:
    prev_ca_data = get_prev_ca()
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        if df_load is not None and not df_load.empty:
            st.session_state.db = df_load
        else: raise Exception
    except:
        df_init = pd.DataFrame({'STT': range(1, 66), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Job Detail': '', 'CA Tháng Trước': 0.0})
        st.session_state.db = df_init
    
    st.session_state.db['CA Tháng Trước'] = st.session_state.db['Họ và Tên'].map(prev_ca_data).fillna(0.0)
    st.session_state.loaded_sheet = sheet_name

# Tính toán các cột ngày
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
            try:
                d_idx = int(col[:2])
                dt = date(curr_year, curr_month, d_idx)
                if val in st.session_state.gians:
                    if dt in holidays: total_delta += 2.0
                    elif dt.weekday() >= 5: total_delta += 1.0
                    else: total_delta += 0.5
                elif val.upper() == "CA":
                    if dt not in holidays and dt.weekday() < 5: total_delta -= 1.0
            except: continue
        return total_delta

    df['CA Tháng Trước'] = pd.to_numeric(df['CA Tháng Trước'], errors='coerce').fillna(0.0)
    df['Phát sinh trong tháng'] = df.apply(calc_row, axis=1)
    df['Quỹ CA Tổng'] = df['CA Tháng Trước'] + df['Phát sinh trong tháng']
    return df

st.session_state.db = apply_calculation(st.session_state.db)

# Sắp xếp lại cột để loại bỏ cột thừa của tháng cũ
main_cols = ['STT', 'Họ và Tên', 'Quỹ CA Tổng', 'CA Tháng Trước', 'Công ty', 'Chức danh', 'Job Detail']
st.session_state.db = st.session_state.db.reindex(columns=main_cols + DATE_COLS)

# --- 4. NÚT CHỨC NĂNG ---
bc1, bc2, _ = st.columns([1.5, 1.5, 5])
with bc1:
    if st.button("📤 LƯU CLOUD", use_container_width=True, type="primary"):
        conn.update(worksheet=sheet_name, data=st.session_state.db)
        st.success(f"Đã lưu bảng {sheet_name}")
with bc2:
    buffer = io.BytesIO()
    st.session_state.db.to_excel(buffer, index=False)
    st.download_button("📥 XUẤT EXCEL", buffer, file_name=f"PVD_{sheet_name}.xlsx", use_container_width=True)

# --- 5. TABS ---
t1, t2, t3 = st.tabs(["🚀 ĐIỀU ĐỘNG", "🏗️ DANH MỤC", "📊 THỐNG KÊ"])

with t1:
    # --- CÔNG CỤ CẬP NHẬT NHANH ---
    with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH"):
        r1_c1, r1_c2 = st.columns([2, 1.2])
        f_staff = r1_c1.multiselect("Nhân sự:", st.session_state.db['Họ và Tên'].tolist())
        # Giới hạn ngày chọn trong tháng hiện tại để tránh lỗi
        f_date = r1_c2.date_input("Khoảng ngày:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, num_days)))
        
        r2_c1, r2_c2, r2_c3, r2_c4 = st.columns([1, 1, 1, 1])
        f_status = r2_c1.selectbox("Trạng thái:", ["Không đổi", "Đi Biển", "CA", "NP", "Ốm", "WS"])
        f_val = r2_c2.selectbox("Chọn Giàn:", st.session_state.gians) if f_status == "Đi Biển" else f_status
        f_co = r2_c3.selectbox("Công ty:", ["Không đổi"] + st.session_state.companies)
        f_ti = r2_c4.selectbox("Chức danh:", ["Không đổi"] + st.session_state.titles)
        
        if st.button("✅ XÁC NHẬN"):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                s_d, e_d = f_date
                if f_co != "Không đổi":
                    st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), 'Công ty'] = f_co
                if f_ti != "Không đổi":
                    st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), 'Chức danh'] = f_ti
                if f_status != "Không đổi":
                    for i in range((e_d - s_d).days + 1):
                        day = s_d + timedelta(days=i)
                        if day.month == curr_month:
                            col = f"{day.day:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][day.weekday()]})"
                            if col in st.session_state.db.columns:
                                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), col] = f_val
                st.rerun()

    # --- CHUẨN BỊ DỮ LIỆU HIỂN THỊ ---
    df_editor = st.session_state.db.copy()
    # Chống lỗi kiểu dữ liệu cho Selectbox
    df_editor['Công ty'] = df_editor['Công ty'].fillna("PVDWS").astype(str)
    df_editor['Chức danh'] = df_editor['Chức danh'].fillna("Casing crew").astype(str)
    
    s_cos = sorted(list(set(st.session_state.companies + df_editor['Công ty'].unique().tolist())))
    s_tis = sorted(list(set(st.session_state.titles + df_editor['Chức danh'].unique().tolist())))

    config = {
        "STT": st.column_config.NumberColumn("STT", width=40, disabled=True, pinned=True),
        "Họ và Tên": st.column_config.TextColumn("Họ và Tên", width=180, pinned=True),
        "Quỹ CA Tổng": st.column_config.NumberColumn("Tồn Cuối", width=85, format="%.1f", disabled=True, pinned=True),
        "CA Tháng Trước": st.column_config.NumberColumn("Tồn Đầu", width=80, format="%.1f", pinned=True),
        "Công ty": st.column_config.SelectboxColumn("Công ty", width=120, options=s_cos, pinned=True),
        "Chức danh": st.column_config.SelectboxColumn("Chức danh", width=120, options=s_tis, pinned=True),
    }
    for col in DATE_COLS: config[col] = st.column_config.TextColumn(col, width=75)

    # Dùng key động ed_ + sheet_name để Streamlit không dùng lại cache tháng cũ
    edited_df = st.data_editor(
        df_editor,
        column_config=config,
        use_container_width=True,
        height=600,
        hide_index=True,
        key=f"ed_{sheet_name}" 
    )
    
    if not edited_df.equals(df_editor):
        st.session_state.db = edited_df
        st.rerun()

with t2:
    st.subheader("⚙️ QUẢN LÝ DANH MỤC")
    ca, cb, cc = st.columns(3)
    with ca:
        st.write("**🏗️ Giàn**")
        ng = st.text_input("Thêm giàn mới:", key="in_g")
        if st.button("➕ Thêm Giàn"):
            if ng and ng not in st.session_state.gians:
                st.session_state.gians.append(ng)
                st.rerun()
        st.dataframe(st.session_state.gians)
    with cb:
        st.write("**🏢 Công ty**")
        nc = st.text_input("Thêm công ty mới:", key="in_c")
        if st.button("➕ Thêm Công ty"):
            if nc and nc not in st.session_state.companies:
                st.session_state.companies.append(nc)
                st.rerun()
        st.dataframe(st.session_state.companies)
    with cc:
        st.write("**🎖️ Chức danh**")
        nt = st.text_input("Thêm chức danh mới:", key="in_t")
        if st.button("➕ Thêm Chức danh"):
            if nt and nt not in st.session_state.titles:
                st.session_state.titles.append(nt)
                st.rerun()
        st.dataframe(st.session_state.titles)

with t3:
    st.subheader("📊 THỐNG KÊ")
    st.write("Dữ liệu được cập nhật dựa trên bảng điều động tháng hiện tại.")
