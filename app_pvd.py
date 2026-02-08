import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import time

# --- 1. CẤU HÌNH & STYLE ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; font-size: 38px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 2px 2px 4px #000 !important;
    }
    /* Làm nổi bật cột Quỹ CA Tổng */
    [data-testid="stTable"] td:nth-child(7) {
        background-color: #004c4c !important; color: #00f2ff !important; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER & LOGO ---
c_logo, _ = st.columns([1, 4])
with c_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=180)
    else:
        st.markdown("<h2 style='color:red; border:2px solid red; padding:5px;'>PVD WELL</h2>", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. DANH MỤC DỮ LIỆU ---
NAMES_65 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong"]
COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
HOLIDAYS_2026 = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,2,21), date(2026,4,25), date(2026,4,30), date(2026,5,1), date(2026,9,2)]

# --- 4. KẾT NỐI & LOAD GIÀN ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_gians():
    try:
        df_config = conn.read(worksheet="CONFIG", ttl=1)
        return df_config.iloc[:, 0].dropna().astype(str).tolist()
    except:
        return ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

if "gians_list" not in st.session_state:
    st.session_state.gians_list = load_gians()

# --- 5. CHỌN THÁNG ---
_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b")

# --- 6. HÀM LOGIC XỬ LÝ DỮ LIỆU (AUTOFILL & CALCULATE) ---
def process_pvd_data(df):
    num_days = calendar.monthrange(curr_year, curr_month)[1]
    date_cols = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
    
    df_new = df.copy()
    
    for idx, row in df_new.iterrows():
        # A. Autofill: Lan truyền thông tin
        current_fill_value = ""
        for col in date_cols:
            if col not in df_new.columns: df_new[col] = ""
            val = str(df_new.at[idx, col]).strip()
            if val == "" or val.upper() in ["NAN", "NONE"]:
                df_new.at[idx, col] = current_fill_value
            else:
                current_fill_value = val

        # B. Tính toán Quỹ CA
        accrued_this_month = 0.0
        for col in date_cols:
            status = str(df_new.at[idx, col]).strip().upper()
            if not status or status in ["WS", "NP", "ỐM"]: continue
            try:
                dt = date(curr_year, curr_month, int(col[:2]))
                is_off = any(g.upper() in status for g in st.session_state.gians_list)
                if is_off:
                    if dt in HOLIDAYS_2026: accrued_this_month += 2.0
                    elif dt.weekday() >= 5: accrued_this_month += 1.0
                    else: accrued_this_month += 0.5
                elif status == "CA":
                    if dt.weekday() < 5 and dt not in HOLIDAYS_2026: accrued_this_month -= 1.0
            except: continue
            
        ca_truoc = pd.to_numeric(df_new.at[idx, 'CA Tháng Trước'], errors='coerce') or 0.0
        df_new.at[idx, 'Quỹ CA Tổng'] = ca_truoc + accrued_this_month
        
    return df_new

# --- 7. KHỞI TẠO / TẢI DATABASE ---
if 'db' not in st.session_state or st.session_state.get('active_sheet') != sheet_name:
    try:
        st.session_state.db = conn.read(worksheet=sheet_name, ttl=0)
    except:
        st.session_state.db = pd.DataFrame({
            'STT': range(1, 66),
            'Họ và Tên': NAMES_65,
            'Công ty': 'PVDWS',
            'Chức danh': 'Casing crew',
            'Job Detail': '',
            'CA Tháng Trước': 0.0,
            'Quỹ CA Tổng': 0.0
        })
    st.session_state.active_sheet = sheet_name

# --- 8. CÔNG CỤ (TABS) ---
with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH & QUẢN LÝ GIÀN"):
    t_quick, t_rigs = st.tabs(["⚡ Đổ dữ liệu hàng loạt", "⚓ Danh sách giàn khoan"])
    
    with t_quick:
        c1, c2, c3 = st.columns(3)
        sel_staff = c1.multiselect("Chọn nhân sự:", st.session_state.db['Họ và Tên'].tolist())
        sel_range = c2.date_input("Khoảng thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, 5)))
        sel_status = c3.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm"])
        sel_val = c3.selectbox("Chọn giàn:", st.session_state.gians_list) if sel_status == "Đi Biển" else sel_status
        if st.button("🚀 ÁP DỤNG NGAY"):
            if sel_staff and len(sel_range) == 2:
                for p in sel_staff:
                    idx = st.session_state.db.index[st.session_state.db['Họ và Tên'] == p][0]
                    for i in range((sel_range[1] - sel_range[0]).days + 1):
                        curr_d = sel_range[0] + timedelta(days=i)
                        col_target = [c for c in st.session_state.db.columns if c.startswith(f"{curr_d.day:02d}/")]
                        if col_target: st.session_state.db.at[idx, col_target[0]] = sel_val
                st.rerun()

    with t_rigs:
        ra, rb = st.columns([3, 1])
        new_r = ra.text_input("Tên giàn mới:")
        if rb.button("➕ Thêm") and new_r:
            st.session_state.gians_list.append(new_r.upper())
            conn.update(worksheet="CONFIG", data=pd.DataFrame({"Giàn": st.session_state.gians_list}))
            st.rerun()

# --- 9. NÚT ĐIỀU KHIỂN ---
action1, action2, _ = st.columns([2, 2, 5])
if action1.button("💾 LƯU & ĐỒNG BỘ CLOUD", type="primary", use_container_width=True):
    with st.spinner("Đang xử lý dữ liệu..."):
        final_processed = process_pvd_data(st.session_state.db)
        conn.update(worksheet=sheet_name, data=final_processed)
        st.session_state.db = final_processed
        st.success("Dữ liệu đã an toàn trên Cloud!")
        st.rerun()

buf = io.BytesIO()
st.session_state.db.to_excel(buf, index=False)
action2.download_button("📥 XUẤT EXCEL", buf, f"PVD_Report_{sheet_name}.xlsx", use_container_width=True)

# --- 10. BẢNG DỮ LIỆU CHÍNH ---
st.markdown("---")
# Chạy xử lý logic để hiển thị
display_df = process_pvd_data(st.session_state.db)

# SẮP XẾP THỨ TỰ CỘT THEO YÊU CẦU
cols = list(display_df.columns)
date_cols_list = [c for c in cols if '/' in c]
# STT -> Tên -> Công ty -> Chức danh -> Job Detail -> CA Trước -> TỔNG QUỸ CA -> Các ngày
reordered_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail', 'CA Tháng Trước', 'Quỹ CA Tổng'] + date_cols_list
display_df = display_df[reordered_cols]

# Hiển thị trình chỉnh sửa với cấu hình Dropdown cho Công ty và Chức danh
edited_df = st.data_editor(
    display_df,
    use_container_width=True,
    height=650,
    hide_index=True,
    key=f"pvd_editor_v8_{sheet_name}",
    column_config={
        "Công ty": st.column_config.SelectboxColumn(options=COMPANIES),
        "Chức danh": st.column_config.SelectboxColumn(options=TITLES),
        "Quỹ CA Tổng": st.column_config.NumberColumn(format="%.1f"),
        "CA Tháng Trước": st.column_config.NumberColumn(format="%.1f")
    }
)

if not edited_df.equals(display_df):
    st.session_state.db = edited_df
    st.rerun()
