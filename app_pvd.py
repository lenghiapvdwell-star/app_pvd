import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import time
import plotly.express as px

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
    [data-testid="stMetricValue"] { font-size: 28px !important; font-weight: bold !important; }
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

# --- 3. KẾT NỐI ---
conn = st.connection("gsheets", type=GSheetsConnection)

def save_to_cloud_silent(worksheet_name, df):
    """Hàm lưu ngầm không gây phiền nhiễu"""
    df_clean = df.fillna("").replace(["nan", "NaN", "None"], "")
    try:
        conn.update(worksheet=worksheet_name, data=df_clean)
        st.cache_data.clear()
        return True
    except:
        return False

# --- 4. DATA LOGIC ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]

_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b")

# --- 5. HÀM TỰ ĐỘNG XỬ LÝ DỮ LIỆU (AUTO-ENGINE) ---
def auto_engine(df, is_readonly=False):
    """Tính toán CA + Tự động điền ngày mới"""
    hols = [date(2026,1,1), date(2026,4,30), date(2026,5,1), date(2026,9,2),
            date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19)]
    
    now = datetime.now()
    today = now.date()
    num_days = calendar.monthrange(curr_year, curr_month)[1]
    date_cols = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
    
    df_calc = df.copy()
    data_changed = False # Cờ kiểm tra xem có autofill phát sinh không
    
    for idx, row in df_calc.iterrows():
        accrued = 0.0
        last_val = ""
        
        for col in date_cols:
            d_num = int(col[:2])
            target_date = date(curr_year, curr_month, d_num)
            val = str(row.get(col, "")).strip()
            
            # Logic Auto-Fill: Nếu trống và đã qua 7h sáng ngày đó (hoặc ngày quá khứ)
            if not val and (target_date < today or (target_date == today and now.hour >= 7)):
                if last_val and any(g.upper() in last_val.upper() for g in st.session_state.GIANS):
                    val = last_val
                    df_calc.at[idx, col] = val
                    data_changed = True # Đánh dấu có thay đổi tự động
            
            # Tính toán CA
            v_up = val.upper()
            if v_up and v_up not in ["NAN", "NONE", "WS", "NP", "ỐM"]:
                try:
                    is_we, is_ho = target_date.weekday() >= 5, target_date in hols
                    if any(g.upper() in v_up for g in st.session_state.GIANS):
                        accrued += 2.0 if is_ho else (1.0 if is_we else 0.5)
                    elif v_up == "CA":
                        if not is_we and not is_ho: accrued -= 1.0
                except: pass
            
            if val: last_val = val
            
        df_calc.at[idx, 'Quỹ CA Tổng'] = float(row.get('CA Tháng Trước', 0)) + accrued
        
    return df_calc, data_changed

# --- 6. TẢI VÀ TỰ ĐỒNG BỘ ---
if 'active_sheet' not in st.session_state or st.session_state.active_sheet != sheet_name:
    st.session_state.active_sheet = sheet_name
    if 'db' in st.session_state: del st.session_state.db

if 'db' not in st.session_state:
    # 1. Lấy tồn tháng trước
    prev_sheet = (working_date.replace(day=1) - timedelta(days=1)).strftime("%m_%Y")
    try:
        df_p = conn.read(worksheet=prev_sheet, ttl=0)
        b_map = dict(zip(df_p['Họ và Tên'], df_p['Quỹ CA Tổng']))
    except: b_map = {}

    # 2. Tải tháng hiện tại
    try:
        df_l = conn.read(worksheet=sheet_name, ttl=0).fillna("").replace(["nan", "NaN", "None"], "")
        if df_l.empty or len(df_l) < 5: raise ValueError
        for idx, r in df_l.iterrows():
            if r['Họ và Tên'] in b_map: df_l.at[idx, 'CA Tháng Trước'] = float(b_map[r['Họ và Tên']])
    except:
        df_l = pd.DataFrame({
            'STT': range(1, len(NAMES_66) + 1), 'Họ và Tên': NAMES_66,
            'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Job Detail': '',
            'CA Tháng Trước': [float(b_map.get(n, 0.0)) for n in NAMES_66], 'Quỹ CA Tổng': 0.0
        })

    # 3. CHẠY ENGINE TỰ ĐỘNG
    df_auto, has_changes = auto_engine(df_l)
    
    # 4. Nếu có ngày mới tự sinh ra, lưu thẳng lên Cloud luôn
    if has_changes:
        save_to_cloud_silent(sheet_name, df_auto)
        st.toast("⚡ Hệ thống tự động cập nhật ngày mới!", icon="🤖")
    
    st.session_state.db = df_auto

# --- 7. HIỂN THỊ ---
num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]

t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ"])

with t1:
    # Thanh công cụ
    c_btn1, c_btn2, c_btn3 = st.columns([1, 1, 1])
    with c_btn1:
        if st.button("📤 LƯU THỦ CÔNG", type="primary", use_container_width=True):
            df_final, _ = auto_engine(st.session_state.db)
            if save_to_cloud_silent(sheet_name, df_final):
                st.success("Đã lưu!"); time.sleep(0.5); st.rerun()
    with c_btn2:
        if st.button("🔄 LÀM MỚI", use_container_width=True):
            st.cache_data.clear(); del st.session_state.db; st.rerun()
    with c_btn3:
        buf = io.BytesIO()
        st.session_state.db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf.getvalue(), f"PVD_{sheet_name}.xlsx", use_container_width=True)

    # Bảng dữ liệu
    ordered_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail', 'CA Tháng Trước', 'Quỹ CA Tổng'] + DATE_COLS
    ed_df = st.data_editor(st.session_state.db[ordered_cols].fillna(""), use_container_width=True, height=600, hide_index=True,
                           column_config={"CA Tháng Trước": st.column_config.NumberColumn("Tồn cũ", format="%.1f"),
                                         "Quỹ CA Tổng": st.column_config.NumberColumn("Tổng ca", format="%.1f", disabled=True)})
    
    # Nếu người dùng sửa bằng tay, tính toán lại và lưu
    if not ed_df.equals(st.session_state.db[ordered_cols].fillna("")):
        st.session_state.db.update(ed_df)
        df_recalc, _ = auto_engine(st.session_state.db)
        st.session_state.db = df_recalc
        save_to_cloud_silent(sheet_name, df_recalc) # Lưu ngay khi sửa tay
        st.rerun()

with t2:
    # Giữ nguyên phần Biểu đồ của bạn...
    st.subheader(f"📊 Phân tích nhân sự năm {curr_year}")
    sel_name = st.selectbox("🔍 Chọn nhân sự:", NAMES_66)
    # (Phần code biểu đồ giữ nguyên như cũ)
