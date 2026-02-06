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

# --- 3. CHỌN THÁNG & QUẢN LÝ TRẠNG THÁI ---
_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today(), key="main_date_picker")

sheet_name = working_date.strftime("%m_%Y")

# Hard Reset khi đổi tháng
if "current_sheet" not in st.session_state:
    st.session_state.current_sheet = sheet_name

if st.session_state.current_sheet != sheet_name:
    for key in list(st.session_state.keys()):
        if key.startswith("editor_") or key == "db":
            del st.session_state[key]
    st.session_state.current_sheet = sheet_name
    st.rerun()

st.write("---")

# --- 4. KẾT NỐI & TẢI DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b") 

# --- HÀM LẤY TỒN CUỐI THÁNG TRƯỚC LÀM TỒN ĐẦU THÁNG NÀY ---
def get_transfer_data():
    # Tìm ngày cuối cùng của tháng trước
    first_day_curr = date(curr_year, curr_month, 1)
    last_day_prev = first_day_curr - timedelta(days=1)
    prev_sheet_name = last_day_prev.strftime("%m_%Y")
    
    try:
        # Đọc dữ liệu tháng trước từ Cloud
        df_prev = conn.read(worksheet=prev_sheet_name, ttl=0)
        if df_prev is not None and not df_prev.empty:
            # Lấy cột Họ và Tên và Quỹ CA Tổng (Tồn cuối tháng trước)
            transfer_df = df_prev[['Họ và Tên', 'Quỹ CA Tổng']].copy()
            transfer_df.rename(columns={'Quỹ CA Tổng': 'CA Tháng Trước'}, inplace=True)
            return transfer_df
    except:
        return None

if 'db' not in st.session_state:
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
    
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0)
        if df_load is not None and not df_load.empty:
            st.session_state.db = df_load
        else: raise Exception
    except:
        # Nếu chưa có tháng này, tạo mới và lấy tồn từ tháng trước
        st.session_state.db = pd.DataFrame({'STT': range(1, 66), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Job Detail': '', 'CA Tháng Trước': 0.0})
        
        prev_data = get_transfer_data()
        if prev_data is not None:
            # Gộp dữ liệu tồn từ tháng trước vào tháng mới theo tên
            st.session_state.db = st.session_state.db.drop(columns=['CA Tháng Trước'])
            st.session_state.db = pd.merge(st.session_state.db, prev_data, on='Họ và Tên', how='left')
            st.session_state.db['CA Tháng Trước'] = st.session_state.db['CA Tháng Trước'].fillna(0.0)

    st.session_state.db = st.session_state.db.fillna("")

# Danh mục
if 'gians' not in st.session_state: st.session_state.gians = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]
if 'companies' not in st.session_state: st.session_state.companies = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
if 'titles' not in st.session_state: st.session_state.titles = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]

# --- 5. CHUẨN HÓA CỘT NGÀY ---
num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]

main_cols = ['STT', 'Họ và Tên', 'Quỹ CA Tổng', 'CA Tháng Trước', 'Công ty', 'Chức danh', 'Job Detail']
st.session_state.db = st.session_state.db.reindex(columns=main_cols + DATE_COLS, fill_value="")

# --- 6. NÚT CHỨC NĂNG ---
bc1, bc2, _ = st.columns([1.5, 1.5, 5])
with bc1:
    if st.button("📤 LƯU CLOUD", use_container_width=True, type="primary"):
        try:
            conn.update(worksheet=sheet_name, data=st.session_state.db)
            st.success("Đã lưu thành công lên Cloud!")
        except Exception as e: st.error(f"Lỗi: {e}")

with bc2:
    buffer = io.BytesIO()
    st.session_state.db.to_excel(buffer, index=False)
    st.download_button("📥 XUẤT EXCEL", buffer, file_name=f"PVD_{sheet_name}.xlsx", use_container_width=True)

# --- 7. TABS ---
t1, t2, t3 = st.tabs(["🚀 ĐIỀU ĐỘNG", "🏗️ DANH MỤC", "📊 THỐNG KÊ"])

with t1:
    # Công cụ cập nhật nhanh (Giữ nguyên logic bạn đã hài lòng)
    with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH"):
        r1_c1, r1_c2 = st.columns([2, 1.2])
        f_staff = r1_c1.multiselect("Nhân sự:", st.session_state.db['Họ và Tên'].tolist())
        f_date = r1_c2.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, num_days)))
        
        r2_c1, r2_c2, r2_c3, r2_c4 = st.columns([1, 1, 1, 1])
        f_status = r2_c1.selectbox("Trạng thái:", ["Không đổi", "Đi Biển", "CA", "NP", "Ốm", "WS"])
        f_val = r2_c2.selectbox("Chọn Giàn:", st.session_state.gians) if f_status == "Đi Biển" else f_status
        f_co = r2_c3.selectbox("Công ty:", ["Không đổi"] + st.session_state.companies)
        f_ti = r2_c4.selectbox("Chức danh:", ["Không đổi"] + st.session_state.titles)
        
        if st.button("✅ ÁP DỤNG CẬP NHẬT"):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                start_d, end_d = f_date
                for person in f_staff:
                    idx = st.session_state.db.index[st.session_state.db['Họ và Tên'] == person].tolist()[0]
                    if f_co != "Không đổi": st.session_state.db.at[idx, 'Công ty'] = f_co
                    if f_ti != "Không đổi": st.session_state.db.at[idx, 'Chức danh'] = f_ti
                    if f_status != "Không đổi":
                        delta = (end_d - start_d).days + 1
                        for i in range(delta):
                            d = start_d + timedelta(days=i)
                            if d.month == curr_month and d.year == curr_year:
                                col_name = f"{d.day:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][d.weekday()]})"
                                if col_name in st.session_state.db.columns:
                                    st.session_state.db.at[idx, col_name] = f_val
                st.rerun()

    # --- HÀM TÍNH TOÁN LŨY KẾ ---
    def auto_calc(df):
        holidays = [date(curr_year, 1, 1), date(curr_year, 4, 30), date(curr_year, 5, 1), date(curr_year, 9, 2)]
        if curr_year == 2026: holidays += [date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19)]
        
        def row_logic(row):
            p_sinh = 0.0
            for col in DATE_COLS:
                val = str(row.get(col, "")).strip()
                if not val or val == "": continue
                try:
                    dt = date(curr_year, curr_month, int(col[:2]))
                    if val in st.session_state.gians:
                        # Đi biển lễ/tết: +2, Thứ 7/CN: +1, Ngày thường: +0.5
                        if dt in holidays: p_sinh += 2.0
                        elif dt.weekday() >= 5: p_sinh += 1.0
                        else: p_sinh += 0.5
                    elif val.upper() == "CA":
                        # Nghỉ CA vào ngày thường: trừ 1
                        if dt not in holidays and dt.weekday() < 5: p_sinh -= 1.0
                except: continue
            return p_sinh

        # Chuyển kiểu dữ liệu số
        df['CA Tháng Trước'] = pd.to_numeric(df['CA Tháng Trước'], errors='coerce').fillna(0.0)
        # Quỹ CA Tổng = Tồn đầu tháng (tức tồn cuối tháng trước) + phát sinh trong tháng này
        df['Quỹ CA Tổng'] = df['CA Tháng Trước'] + df.apply(row_logic, axis=1)
        return df

    st.session_state.db = auto_calc(st.session_state.db)

    # Hiển thị bảng Editor
    config = {
        "STT": st.column_config.NumberColumn("STT", width=40, disabled=True, pinned=True),
        "Họ và Tên": st.column_config.TextColumn("Họ và Tên", width=180, pinned=True),
        "Quỹ CA Tổng": st.column_config.NumberColumn("Tồn Cuối", width=85, format="%.1f", disabled=True, pinned=True, help="Tổng CA tích lũy tính đến cuối tháng này"),
        "CA Tháng Trước": st.column_config.NumberColumn("Tồn Đầu", width=80, format="%.1f", pinned=True, help="Dữ liệu Quỹ CA Tổng từ tháng trước chuyển sang"),
        "Công ty": st.column_config.SelectboxColumn("Công ty", width=120, options=st.session_state.companies, pinned=True),
        "Chức danh": st.column_config.SelectboxColumn("Chức danh", width=120, options=st.session_state.titles, pinned=True),
    }
    for col in DATE_COLS: config[col] = st.column_config.TextColumn(col, width=75)

    edited_df = st.data_editor(
        st.session_state.db,
        column_config=config,
        use_container_width=True,
        height=600,
        hide_index=True,
        key=f"editor_{sheet_name}"
    )
    
    if not edited_df.equals(st.session_state.db):
        st.session_state.db = edited_df
        st.rerun()

with t2:
    st.subheader("⚙️ QUẢN LÝ DANH MỤC")
    # Code danh mục giữ nguyên...

with t3:
    st.subheader("📊 THỐNG KÊ")
    # Code thống kê...
