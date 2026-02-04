import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH & GIAO DIỆN ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    /* Tiêu đề căn giữa, to, rõ */
    .main-title {
        color: #00f2ff;
        font-size: 36px;
        font-weight: bold;
        text-align: center;
        margin: 0;
        text-shadow: 2px 2px 4px #000;
        line-height: 1.5;
    }
    /* Nút bấm to, dễ nhấn */
    .stButton>button {border-radius: 5px; height: 3em; font-weight: bold;}
    div[data-testid="stDateInput"] {float: right;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER: LOGO - TIÊU ĐỀ - CHỌN THÁNG ---
c1, c2, c3 = st.columns([1.5, 4, 1.5])

with c1:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=180)
    else:
        st.write("### PVD LOGO")

with c2:
    st.markdown('<p class="main-title">PVD WELL SERVICES MANAGEMENT</p>', unsafe_allow_html=True)

with c3:
    st.write("##") 
    working_date = st.date_input("📅 THÁNG LÀM VIỆC:", value=date.today())

st.write("---")

# --- 3. NÚT CHỨC NĂNG (ĐƯA RA NGOÀI) ---
btn_col1, btn_col2, _ = st.columns([1.5, 1.5, 4])

# --- 4. XỬ LÝ DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)
curr_month = working_date.month
curr_year = working_date.year
month_abbr = working_date.strftime("%b") 
sheet_name = working_date.strftime("%m_%Y") 

# Danh sách nhân sự đầy đủ 64 người
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

if 'gians' not in st.session_state:
    st.session_state.gians = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9" , "THOR", "SDE" , "GUNNLOD"]

def get_prev_ca():
    prev_date = date(curr_year, curr_month, 1) - timedelta(days=1)
    prev_sheet = prev_date.strftime("%m_%Y")
    try:
        df_prev = conn.read(worksheet=prev_sheet, ttl=0)
        # Đảm bảo dữ liệu đọc về là số
        return df_prev.set_index('Họ và Tên')['Quỹ CA Tổng'].apply(pd.to_numeric, errors='coerce').fillna(0.0).to_dict()
    except: return {}

# Logic Load dữ liệu (Đã thêm xử lý chống lỗi type)
if 'active_sheet' not in st.session_state or st.session_state.active_sheet != sheet_name:
    st.session_state.active_sheet = sheet_name
    prev_ca_data = get_prev_ca()
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        if df_load is not None and not df_load.empty:
            st.session_state.db = df_load
            # Cập nhật tồn cũ
            st.session_state.db['CA Tháng Trước'] = st.session_state.db['Họ và Tên'].map(prev_ca_data).fillna(0.0)
        else: raise Exception
    except:
        df_init = pd.DataFrame({'STT': range(1, 65), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': ''})
        df_init['CA Tháng Trước'] = df_init['Họ và Tên'].map(prev_ca_data).fillna(0.0)
        st.session_state.db = df_init

# Tạo cột ngày
num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
for c in DATE_COLS: 
    if c not in st.session_state.db.columns: st.session_state.db[c] = ""

# --- 5. TÍNH TOÁN (CORE) ---
def update_logic(df):
    holidays = [date(curr_year, 1, 1), date(curr_year, 4, 30), date(curr_year, 5, 1), date(curr_year, 9, 2)]
    def calc_row(row):
        total = 0.0
        for col in DATE_COLS:
            val = str(row.get(col, "")).strip()
            if not val or val.lower() in ["nan", "none", ""]: continue
            try:
                d_int = int(col.split('/')[0])
                dt = date(curr_year, curr_month, d_int)
                if val in st.session_state.gians:
                    if dt in holidays: total += 2.0
                    elif dt.weekday() >= 5: total += 1.0
                    else: total += 0.5
                elif val.upper() == "CA" and dt.weekday() < 5 and dt not in holidays: total -= 1.0
            except: continue
        return total

    df['Phát sinh trong tháng'] = df.apply(calc_row, axis=1)
    
    # --- BƯỚC QUAN TRỌNG NHẤT: ÉP KIỂU SỐ ---
    # Chuyển đổi toàn bộ cột số về float, lỗi biến thành 0.0
    df['CA Tháng Trước'] = pd.to_numeric(df['CA Tháng Trước'], errors='coerce').fillna(0.0)
    df['Quỹ CA Tổng'] = df['CA Tháng Trước'] + df['Phát sinh trong tháng']
    
    return df

st.session_state.db = update_logic(st.session_state.db)

# Sắp xếp cột
cols_order = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail', 'Quỹ CA Tổng', 'CA Tháng Trước'] + DATE_COLS
st.session_state.db = st.session_state.db.reindex(columns=[c for c in cols_order if c in st.session_state.db.columns])

# --- 6. GẮN NÚT BẤM VÀO HÀNH ĐỘNG ---
with btn_col1:
    if st.button("📤 UPLOAD CLOUD", use_container_width=True, type="primary"):
        # Chuyển đổi dữ liệu trước khi lưu để đảm bảo sạch
        conn.update(worksheet=sheet_name, data=st.session_state.db)
        st.success(f"Đã lưu dữ liệu tháng {working_date.strftime('%m/%Y')} thành công!")

with btn_col2:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        st.session_state.db.to_excel(writer, index=False, sheet_name=sheet_name)
    st.download_button("📥 XUẤT EXCEL", buffer, file_name=f"PVD_{sheet_name}.xlsx", use_container_width=True)

# --- 7. HIỂN THỊ BẢNG (FIX LỖI STREAMLIT API) ---
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

    # Cấu hình hiển thị bảng
    config = {
        "STT": st.column_config.NumberColumn("STT", width=40, disabled=True, pinned=True),
        "Họ và Tên": st.column_config.TextColumn("Họ và Tên", width=180, pinned=True),
        "Công ty": st.column_config.TextColumn("Công ty", width=80),
        "Chức danh": st.column_config.TextColumn("Chức danh", width=100),
        "Job Detail": st.column_config.TextColumn("Job Detail", width=120),
        # Đã xử lý ép kiểu float ở trên, giờ hiển thị an toàn
        "Quỹ CA Tổng": st.column_config.NumberColumn("T ca", width=70, format="%.1f", disabled=True, pinned=True),
        "CA Tháng Trước": st.column_config.NumberColumn("Tồn cũ", width=70, format="%.1f", pinned=True),
    }
    for col in DATE_COLS: config[col] = st.column_config.TextColumn(col, width=65)

    # Hiển thị bảng an toàn
    st.data_editor(
        st.session_state.db, 
        column_config=config, 
        use_container_width=True, 
        height=600, 
        hide_index=True, 
        key=f"ed_{sheet_name}"
    )

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
