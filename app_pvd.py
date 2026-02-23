import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import time
import plotly.express as px
import os

# --- 1. CẤU HÌNH & STYLE ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 1rem;}
    .main-title {
        color: #007BFF !important; 
        font-size: 39px !important; 
        font-weight: bold !important;
        text-align: center !important; 
        margin-bottom: 10px !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    .logo-container { display: flex; justify-content: center; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HIỂN THỊ LOGO TRUNG TÂM ---
def display_main_logo():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        logo_path = os.path.join(current_dir, f"logo_pvd{ext}")
        if os.path.exists(logo_path):
            col1, col2, col3 = st.columns([4, 2, 4])
            with col2: st.image(logo_path, use_container_width=True)
            return True
    return False

display_main_logo()
st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. DANH MỤC CỐ ĐỊNH ---
COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]
DEFAULT_RIGS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

# --- 4. KẾT NỐI & HÀM HỖ TRỢ ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data_safe(wks_name, ttl=0):
    try:
        df = conn.read(worksheet=wks_name, ttl=ttl)
        return df if not df.empty else pd.DataFrame()
    except: return pd.DataFrame()

def load_config_rigs():
    df = get_data_safe("config", ttl=300)
    if not df.empty and "GIANS" in df.columns:
        return [str(g).strip().upper() for g in df["GIANS"].dropna().tolist() if str(g).strip()]
    return DEFAULT_RIGS

def save_config_rigs(rig_list):
    try:
        df_save = pd.DataFrame({"GIANS": rig_list})
        conn.update(worksheet="config", data=df_save)
        st.cache_data.clear()
        return True
    except: return False

# --- 5. ENGINE TÍNH TOÁN ---
def apply_logic(df, curr_m, curr_y, rigs):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    df_calc = df.copy()
    rigs_up = [r.upper() for r in rigs]
    date_cols = [c for c in df_calc.columns if "/" in c and "(" in c]

    for idx, row in df_calc.iterrows():
        if not str(row.get('Họ và Tên', '')).strip(): continue
        accrued = 0.0
        for col in date_cols:
            try:
                val = str(row.get(col, "")).strip().upper()
                if not val or val == "NAN": continue
                d_num = int(col[:2])
                target_date = date(curr_y, curr_m, d_num)
                is_we = target_date.weekday() >= 5
                is_ho = target_date in hols
                if any(g in val for g in rigs_up):
                    if is_ho: accrued += 2.0
                    elif is_we: accrued += 1.0
                    else: accrued += 0.5
                elif val == "CA":
                    if not is_we and not is_ho: accrued -= 1.0
            except: continue
        ton_cu = pd.to_numeric(row.get('Tồn cũ', 0), errors='coerce')
        df_calc.at[idx, 'Tổng CA'] = round(float(ton_cu if not pd.isna(ton_cu) else 0.0) + accrued, 1)
    return df_calc

# --- 6. KHỞI TẠO & CHỌN THÁNG ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = load_config_rigs()
if "store" not in st.session_state:
    st.session_state.store = {}

_, mc, _ = st.columns([3, 2, 3])
with mc:
    wd = st.date_input("📅 CHỌN THÁNG:", value=date.today())

sheet_name = wd.strftime("%m_%Y")
curr_m, curr_y = wd.month, wd.year
days_in_m = calendar.monthrange(curr_y, curr_m)[1]
DATE_COLS = [f"{d:02d}/{wd.strftime('%b')} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_y,curr_m,d).weekday()]})" for d in range(1, days_in_m+1)]

# --- 7. LOGIC AUTO-FILL & AUTO-SAVE (MỖI 6H SÁNG) ---
def perform_auto_maintenance(df, s_name, rigs):
    now = datetime.now()
    # Chỉ chạy cho tháng hiện tại
    if s_name == now.strftime("%m_%Y") and now.hour >= 6:
        today_num = now.day
        if today_num > 1:
            prev_col_prefix = f"{(today_num - 1):02d}/"
            curr_col_prefix = f"{today_num:02d}/"
            
            col_prev = [c for c in DATE_COLS if c.startswith(prev_col_prefix)]
            col_curr = [c for c in DATE_COLS if c.startswith(curr_col_prefix)]
            
            if col_prev and col_curr:
                c_p, c_c = col_prev[0], col_curr[0]
                # Nếu hôm nay chưa có dữ liệu nhưng hôm qua có
                mask = (df[c_c].isna() | (df[c_c] == "")) & (df[c_p].notna() & (df[c_p] != ""))
                if mask.any():
                    df.loc[mask, c_c] = df.loc[mask, c_p]
                    # Tính lại CA và TỰ ĐỘNG ĐẨY LÊN GOOGLE SHEETS
                    df = apply_logic(df, now.month, now.year, rigs)
                    conn.update(worksheet=s_name, data=df)
                    st.toast(f"✅ Hệ thống đã tự động nối dữ liệu từ ngày {today_num-1} sang {today_num}", icon="⚡")
                    return df
    return df

# Tải dữ liệu ban đầu
if sheet_name not in st.session_state.store:
    df_raw = get_data_safe(sheet_name, ttl=0)
    if df_raw.empty:
        df_raw = pd.DataFrame({'STT': range(1, len(NAMES_66)+1), 'Họ và Tên': NAMES_66, 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Tồn cũ': 0.0, 'Tổng CA': 0.0})
        for c in DATE_COLS: df_raw[c] = ""
        prev_date = wd.replace(day=1) - timedelta(days=1)
        prev_df = get_data_safe(prev_date.strftime("%m_%Y"), ttl=0)
        if not prev_df.empty:
            balances = prev_df.set_index('Họ và Tên')['Tổng CA'].to_dict()
            for idx, row in df_raw.iterrows():
                if row['Họ và Tên'] in balances: df_raw.at[idx, 'Tồn cũ'] = balances[row['Họ và Tên']]
    
    # Chạy bảo trì tự động ngay khi tải sheet
    df_raw = perform_auto_maintenance(df_raw, sheet_name, st.session_state.GIANS)
    st.session_state.store[sheet_name] = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)

# --- 8. GIAO DIỆN CHÍNH ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ TỔNG HỢP"])

with t1:
    db = st.session_state.store[sheet_name]
    c1, c2, c3 = st.columns([2, 2, 4])
    
    if c1.button("📤 CHỐT & ĐẨY SỐ DƯ (CẢ NĂM)", type="primary", use_container_width=True):
        try:
            with st.spinner("Đang đồng bộ dây chuyền..."):
                conn.update(worksheet=sheet_name, data=db)
                # Hàm này đẩy tồn cũ sang các tháng tương lai
                def push_balances_to_future(start_date, start_df, rigs):
                    current_df = start_df.copy()
                    current_date = start_date
                    for i in range(1, 12):
                        days_in_m = calendar.monthrange(current_date.year, current_date.month)[1]
                        next_date = current_date.replace(day=1) + timedelta(days=days_in_m)
                        next_sheet = next_date.strftime("%m_%Y")
                        try:
                            time.sleep(1) 
                            next_df = get_data_safe(next_sheet, ttl=0)
                            if next_df.empty: break 
                            balances = current_df.set_index('Họ và Tên')['Tổng CA'].to_dict()
                            for idx, row in next_df.iterrows():
                                name = row['Họ và Tên']
                                if name in balances: next_df.at[idx, 'Tồn cũ'] = balances[name]
                            next_df = apply_logic(next_df, next_date.month, next_date.year, rigs)
                            conn.update(worksheet=next_sheet, data=next_df)
                            current_df = next_df
                            current_date = next_date
                        except: break
                push_balances_to_future(wd, db, st.session_state.GIANS)
            st.cache_data.clear()
            st.success("Hoàn tất quy trình đồng bộ!")
            st.rerun()
        except Exception as e: st.error(f"Lỗi: {e}")

    with c3:
        buf = io.BytesIO()
        db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf.getvalue(), f"PVD_{sheet_name}.xlsx", use_container_width=True)

    # Bảng chỉnh sửa chính
    all_col = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Tồn cũ', 'Tổng CA'] + DATE_COLS
    ed_db = st.data_editor(db[all_col], use_container_width=True, height=550, hide_index=True)
    
    if not ed_db.equals(db[all_col]):
        st.session_state.store[sheet_name].update(ed_db)
        # Sửa xong tự tính lại
        st.session_state.store[sheet_name] = apply_logic(st.session_state.store[sheet_name], curr_m, curr_y, st.session_state.GIANS)
        st.rerun()

with t2:
    st.subheader(f"📊 Thống kê nhân sự năm {curr_y}")
    sel_name = st.selectbox("🔍 Chọn nhân sự:", NAMES_66)
    if sel_name:
        yearly_data = []
        rigs_up = [r.upper() for r in st.session_state.GIANS]
        for m in range(1, 13):
            try:
                m_df = get_data_safe(f"{m:02d}_{curr_y}", ttl=600) 
                if not m_df.empty and sel_name in m_df['Họ và Tên'].values:
                    p_row = m_df[m_df['Họ và Tên'] == sel_name].iloc[0]
                    counts = {"Đi Biển": 0, "Nghỉ CA": 0, "Làm xưởng": 0, "Nghỉ/Ốm": 0}
                    for c in m_df.columns:
                        if "/" in c and "(" in c:
                            val = str(p_row[c]).strip().upper()
                            if any(g in val for g in rigs_up) and val != "": counts["Đi Biển"] += 1
                            elif val == "CA": counts["Nghỉ CA"] += 1
                            elif val == "WS": counts["Làm xưởng"] += 1
                            elif val in ["NP", "ỐM"]: counts["Nghỉ/Ốm"] += 1
                    for k, v in counts.items():
                        if v > 0: yearly_data.append({"Tháng": f"Tháng {m}", "Loại": k, "Số ngày": v})
            except: continue
        if yearly_data:
            df_chart = pd.DataFrame(yearly_data)
            fig = px.bar(df_chart, x="Tháng", y="Số ngày", color="Loại", barmode="stack", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

# --- 9. SIDEBAR QUẢN LÝ ---
with st.sidebar:
    st.header("⚙️ QUẢN LÝ GIÀN")
    ng = st.text_input("➕ Thêm giàn mới:").upper().strip()
    if st.button("Thêm ngay"):
        if ng and ng not in st.session_state.GIANS:
            st.session_state.GIANS.append(ng)
            if save_config_rigs(st.session_state.GIANS): st.rerun()
    st.markdown("---")
    dg = st.selectbox("❌ Xóa giàn:", st.session_state.GIANS)
    if st.button("Xóa ngay"):
        if len(st.session_state.GIANS) > 1:
            st.session_state.GIANS.remove(dg) 
            if save_config_rigs(st.session_state.GIANS): st.rerun()
