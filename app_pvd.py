import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import time

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 0.5rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; font-size: 40px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 2px 2px 4px #000 !important;
    }
    .stButton>button {transition: all 0.3s; border-radius: 5px;}
    .stButton>button:hover {transform: scale(1.02); background-color: #00f2ff; color: black;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. KẾT NỐI ---
conn = st.connection("gsheets", type=GSheetsConnection)

def save_to_cloud(worksheet_name, df):
    df_to_save = df[df['Họ và Tên'].str.strip() != ""].copy()
    for col in ['Tồn cũ', 'Tổng CA']:
        if col in df_to_save.columns:
            df_to_save[col] = pd.to_numeric(df_to_save[col], errors='coerce').fillna(0.0)
    df_clean = df_to_save.fillna("").replace(["nan", "NaN", "None"], "")
    try:
        conn.update(worksheet=worksheet_name, data=df_clean)
        st.cache_data.clear() 
        return True
    except:
        return False

# --- 3. ENGINE (Chỉ chạy khi được gọi) ---
def run_auto_engine(df, curr_month, curr_year, DATE_COLS):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    now = datetime.now()
    today = now.date()
    df_calc = df.copy()

    for idx, row in df_calc.iterrows():
        if not str(row.get('Họ và Tên', '')).strip(): continue
        accrued = 0.0
        current_last_val = ""
        
        for col in DATE_COLS:
            if col not in df_calc.columns: continue
            d_num = int(col[:2])
            target_date = date(curr_year, curr_month, d_num)
            val = str(row.get(col, "")).strip()
            
            # Autofill theo giờ hẹn (Trước 6h sáng hoặc ngày quá khứ)
            if (not val or val == "" or val.lower() == "nan") and (target_date < today or (target_date == today and now.hour >= 6)):
                if current_last_val != "":
                    lv_up = current_last_val.upper()
                    if any(g.upper() in lv_up for g in st.session_state.GIANS) or lv_up in ["CA", "WS", "NP", "ỐM"]:
                        val = current_last_val
                        df_calc.at[idx, col] = val
            
            if val and val != "" and val.lower() != "nan":
                current_last_val = val
            
            v_up = val.upper()
            if v_up:
                is_we = target_date.weekday() >= 5
                is_ho = target_date in hols
                if any(g.upper() in v_up for g in st.session_state.GIANS):
                    if is_ho: accrued += 2.0
                    elif is_we: accrued += 1.0
                    else: accrued += 0.5
                elif v_up == "CA":
                    if not is_we and not is_ho: accrued -= 1.0
        
        ton_cu = pd.to_numeric(row.get('Tồn cũ', 0), errors='coerce')
        df_calc.at[idx, 'Tổng CA'] = round(float(ton_cu if not pd.isna(ton_cu) else 0) + accrued, 1)
    return df_calc

# --- 4. KHỞI TẠO SESSION ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]

# --- 5. LỌC THÁNG & LOAD DỮ LIỆU ---
st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)
_, mid_c, _ = st.columns([3, 2, 3])
with mid_c:
    working_date = st.date_input("📅 THÁNG LÀM VIỆC:", value=date.today())

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b")
num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]

if 'current_sheet' not in st.session_state or st.session_state.current_sheet != sheet_name:
    st.session_state.current_sheet = sheet_name
    try:
        df_load = conn.read(worksheet=sheet_name, ttl=0).fillna("")
        if 'Quỹ CA Tổng' in df_load.columns: df_load = df_load.rename(columns={'Quỹ CA Tổng': 'Tổng CA'})
        if 'CA Tháng Trước' in df_load.columns: df_load = df_load.rename(columns={'CA Tháng Trước': 'Tồn cũ'})
        if df_load.empty: raise ValueError
    except:
        df_load = pd.DataFrame({'STT': range(1, len(NAMES_66)+1), 'Họ và Tên': NAMES_66, 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Job Detail': '', 'Tồn cũ': 0.0, 'Tổng CA': 0.0})
        for c in DATE_COLS: df_load[c] = ""
    st.session_state.db = df_load

# --- 6. GIAO DIỆN CHÍNH ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ"])

with t1:
    # THANH CÔNG CỤ CỐ ĐỊNH (Không reload khi nhấn)
    c1, c2, c3 = st.columns([2, 2, 4])
    with c1:
        if st.button("🔄 TÍNH TOÁN & AUTOFILL", use_container_width=True, type="secondary"):
            st.session_state.db = run_auto_engine(st.session_state.db, curr_month, curr_year, DATE_COLS)
            st.rerun()
    with c2:
        if st.button("📤 LƯU LÊN CLOUD", use_container_width=True, type="primary"):
            st.session_state.db = run_auto_engine(st.session_state.db, curr_month, curr_year, DATE_COLS)
            if save_to_cloud(sheet_name, st.session_state.db):
                st.success("Đã lưu!")
                time.sleep(1)
                st.rerun()
    with c3:
        buf = io.BytesIO()
        st.session_state.db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf.getvalue(), f"PVD_{sheet_name}.xlsx", use_container_width=True)

    # CÔNG CỤ CẬP NHẬT NHANH (Bọc trong fragment để không load lại toàn trang)
    @st.fragment
    def quick_update():
        with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH (Chọn xong nhấn Áp dụng)"):
            c_n, c_d = st.columns([2, 1])
            f_staff = c_n.multiselect("Nhân sự:", st.session_state.db['Họ và Tên'].tolist())
            f_date = c_d.date_input("Đoạn thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, num_days)))
            r1, r2, r3, r4 = st.columns(4)
            f_status = r1.selectbox("Trạng thái:", ["Xóa trắng", "Đi Biển", "CA", "WS", "NP", "Ốm"])
            f_val = r2.selectbox("Giàn:", st.session_state.GIANS) if f_status == "Đi Biển" else f_status
            if st.button("✅ ÁP DỤNG THAY ĐỔI", use_container_width=True):
                if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                    for person in f_staff:
                        idx = st.session_state.db.index[st.session_state.db['Họ và Tên'] == person].tolist()
                        if idx:
                            i = idx[0]
                            curr_d = f_date[0]
                            while curr_d <= f_date[1]:
                                if curr_d.month == curr_month:
                                    col_t = [c for c in DATE_COLS if c.startswith(f"{curr_d.day:02d}/")]
                                    if col_t: st.session_state.db.at[i, col_t[0]] = "" if f_status == "Xóa trắng" else f_val
                                curr_d += timedelta(days=1)
                    st.success("Đã cập nhật tạm thời. Nhấn 'Tính toán' để xem kết quả.")

    quick_update()

    # BẢNG DỮ LIỆU (Khóa key để không tự động reload)
    all_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail', 'Tồn cũ', 'Tổng CA'] + DATE_COLS
    
    # Quan trọng: Không dùng st.rerun() bên trong data_editor để tránh lặp
    edited_df = st.data_editor(
        st.session_state.db[all_cols],
        use_container_width=True,
        height=650,
        hide_index=True,
        key="main_editor_stable",
        column_config={
            "Tổng CA": st.column_config.NumberColumn(disabled=True, format="%.1f"),
            "Tồn cũ": st.column_config.NumberColumn(format="%.1f")
        }
    )
    # Cập nhật session ngầm, không gọi rerun
    st.session_state.db.update(edited_df)

with t2:
    st.info("Biểu đồ sẽ hiển thị dựa trên dữ liệu đã lưu trên Cloud.")

with st.sidebar:
    st.header("⚙️ CÀI ĐẶT")
    new_g = st.text_input("Thêm giàn:").upper()
    if st.button("➕"):
        if new_g and new_g not in st.session_state.GIANS:
            st.session_state.GIANS.append(new_g)
            st.rerun()
