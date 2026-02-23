import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import time
import plotly.express as px
import os

# --- 1. CẤU HÌNH & STYLE (GIỮ NGUYÊN) ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 1rem;}
    .main-title {
        color: #007BFF !important; 
        font-size: 35px !important; 
        font-weight: bold !important;
        text-align: center !important; 
        margin-bottom: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DANH MỤC CỐ ĐỊNH (GIỮ NGUYÊN) ---
COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]
DEFAULT_RIGS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. HÀM HỖ TRỢ (NÂNG CẤP ĐỂ XỬ LÝ DÂY CHUYỀN) ---
def get_data_safe(wks_name, ttl=60):
    try:
        df = conn.read(worksheet=wks_name, ttl=ttl)
        return df if not df.empty else pd.DataFrame()
    except:
        return pd.DataFrame()
# --- BỔ SUNG CÁC HÀM CÒN THIẾU ---

def load_config_rigs():
    """Lấy danh sách giàn từ sheet 'config'"""
    try:
        df = get_data_safe("config", ttl=300)
        if not df.empty and "GIANS" in df.columns:
            return [str(g).strip().upper() for g in df["GIANS"].dropna().tolist() if str(g).strip()]
    except:
        pass
    return DEFAULT_RIGS # Trả về danh sách mặc định nếu lỗi

def save_config_rigs(rig_list):
    """Lưu danh sách giàn vào sheet 'config'"""
    try:
        df_save = pd.DataFrame({"GIANS": rig_list})
        conn.update(worksheet="config", data=df_save)
        st.cache_data.clear()
        return True
    except:
        return False
        
def apply_logic_core(df, m, y, rigs):
    """Hàm lõi tính toán logic công, dùng chung cho cả app và chain reaction"""
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    df_calc = df.copy()
    rigs_up = [r.upper() for r in rigs]
    date_cols = [c for c in df_calc.columns if "/" in c]

    for idx, row in df_calc.iterrows():
        if not str(row.get('Họ và Tên', '')).strip(): continue
        accrued = 0.0
        for col in date_cols:
            try:
                val = str(row.get(col, "")).strip().upper()
                if not val or val == "NAN": continue
                d_num = int(col[:2])
                target_date = date(y, m, d_num)
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

def update_chain_reaction(start_date, current_df, rigs):
    """NÂNG CẤP QUAN TRỌNG: Tự động đẩy số dư sang các tháng sau trên Google Sheets"""
    # 1. Lưu tháng hiện tại
    sheet_now = start_date.strftime("%m_%Y")
    conn.update(worksheet=sheet_now, data=current_df)
    
    # 2. Đẩy dữ liệu dây chuyền sang các tháng sau
    temp_df = current_df.copy()
    temp_date = start_date
    
    for _ in range(1, 12): # Chạy tối đa đến hết năm
        # Tính tháng tiếp theo
        days_in_m = calendar.monthrange(temp_date.year, temp_date.month)[1]
        temp_date = temp_date.replace(day=1) + timedelta(days=days_in_m)
        next_sheet = temp_date.strftime("%m_%Y")
        
        # Kiểm tra xem tháng sau có tồn tại trên Cloud không
        next_df = get_data_safe(next_sheet, ttl=0)
        if next_df.empty: break # Nếu chưa tạo tháng sau thì dừng chain
        
        # Lấy 'Tổng CA' tháng trước làm 'Tồn cũ' tháng này
        balances = temp_df.set_index('Họ và Tên')['Tổng CA'].to_dict()
        for idx, row in next_df.iterrows():
            name = row['Họ và Tên']
            if name in balances:
                next_df.at[idx, 'Tồn cũ'] = balances[name]
        
        # Tính lại logic cho tháng sau với Tồn cũ mới
        next_df = apply_logic_core(next_df, temp_date.month, temp_date.year, rigs)
        
        # Cập nhật lên Cloud
        conn.update(worksheet=next_sheet, data=next_df)
        
        # Gán để lặp tiếp cho tháng sau nữa
        temp_df = next_df
    
    st.cache_data.clear()

# --- 4. KHỞI TẠO (CHỐNG TRẮNG BẢNG) ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = load_config_rigs()

# Dùng dictionary để lưu dữ liệu các tháng đã load, chuyển tháng không bị mất dữ liệu tạm
if "data_store" not in st.session_state:
    st.session_state.data_store = {}

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

_, mc, _ = st.columns([3, 2, 3])
with mc:
    wd = st.date_input("📅 CHỌN THÁNG:", value=date.today())

sheet_name = wd.strftime("%m_%Y")
curr_m, curr_y = wd.month, wd.year
days_in_m = calendar.monthrange(curr_y, curr_m)[1]
DATE_COLS = [f"{d:02d}/{wd.strftime('%b')} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_y,curr_m,d).weekday()]})" for d in range(1, days_in_m+1)]

# LOAD DỮ LIỆU
if sheet_name not in st.session_state.data_store:
    with st.spinner(f"Đang tải {sheet_name}..."):
        df_raw = get_data_safe(sheet_name, ttl=0)
        if df_raw.empty:
            df_raw = pd.DataFrame({'STT': range(1, len(NAMES_66)+1), 'Họ và Tên': NAMES_66, 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Tồn cũ': 0.0, 'Tổng CA': 0.0})
            for c in DATE_COLS: df_raw[c] = ""
        
        # Tự động lấy số dư từ tháng trước nếu là lần đầu load sheet này
        first_day = wd.replace(day=1)
        prev_date = first_day - timedelta(days=1)
        prev_df = get_data_safe(prev_date.strftime("%m_%Y"), ttl=0)
        if not prev_df.empty:
            balances = prev_df.set_index('Họ và Tên')['Tổng CA'].to_dict()
            for idx, row in df_raw.iterrows():
                if row['Họ và Tên'] in balances:
                    df_raw.at[idx, 'Tồn cũ'] = balances[row['Họ và Tên']]
        
        st.session_state.data_store[sheet_name] = apply_logic_core(df_raw, curr_m, curr_y, st.session_state.GIANS)

# --- 5. GIAO DIỆN TABS ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ TỔNG HỢP"])

with t1:
    db = st.session_state.data_store[sheet_name]
    
    c1, c2, c3 = st.columns([2, 2, 4])
    if c1.button("📤 LƯU & CẬP NHẬT CẢ NĂM", type="primary", use_container_width=True):
        with st.spinner("Đang cập nhật dây chuyền dữ liệu toàn hệ thống..."):
            # Tính toán lại lần cuối trước khi đẩy
            db = apply_logic_core(db, curr_m, curr_y, st.session_state.GIANS)
            update_chain_reaction(wd, db, st.session_state.GIANS)
            st.success("Đã đồng bộ hóa dữ liệu thành công!")
            time.sleep(1)
            st.rerun()

    with st.expander("🛠️ CÔNG CỤ NHẬP NHANH"):
        names = st.multiselect("Chọn nhân sự:", NAMES_66)
        dr = st.date_input("Khoảng ngày:", value=(date(curr_y, curr_m, 1), date(curr_y, curr_m, 5)))
        r1, r2 = st.columns(2)
        stt = r1.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm", "Xóa"])
        rig = r2.selectbox("Tên Giàn:", st.session_state.GIANS) if stt == "Đi Biển" else stt
        
        if st.button("✅ ÁP DỤNG", use_container_width=True):
            if names and len(dr) == 2:
                for n in names:
                    if n in db['Họ và Tên'].values:
                        idx = db.index[db['Họ và Tên'] == n].tolist()[0]
                        sd, ed = dr
                        while sd <= ed:
                            if sd.month == curr_m:
                                col_d = [c for c in DATE_COLS if c.startswith(f"{sd.day:02d}/")][0]
                                db.at[idx, col_d] = "" if stt == "Xóa" else rig
                            sd += timedelta(days=1)
                st.session_state.data_store[sheet_name] = apply_logic_core(db, curr_m, curr_y, st.session_state.GIANS)
                st.rerun()

    # HIỂN THỊ BẢNG (CHỐNG TRẮNG BẢNG BẰNG CÁCH UPDATE TRỰC TIẾP)
    all_col = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Tồn cũ', 'Tổng CA'] + DATE_COLS
    edited_df = st.data_editor(db[all_col], use_container_width=True, height=550, hide_index=True)
    
    # Nếu có thay đổi trên bảng, cập nhật lại logic ngay lập tức
    if not edited_df.equals(db[all_col]):
        st.session_state.data_store[sheet_name].update(edited_df)
        st.session_state.data_store[sheet_name] = apply_logic_core(st.session_state.data_store[sheet_name], curr_m, curr_y, st.session_state.GIANS)
        st.rerun()

with t2:
    st.subheader(f"📊 Thống kê nhân sự năm {curr_y}")
    sel_name = st.selectbox("🔍 Chọn nhân sự:", NAMES_66)
    if sel_name:
        yearly_data = []
        for m in range(1, 13):
            try:
                m_df = get_data_safe(f"{m:02d}_{curr_y}", ttl=300)
                if not m_df.empty and sel_name in m_df['Họ và Tên'].values:
                    p_row = m_df[m_df['Họ và Tên'] == sel_name].iloc[0]
                    for c in m_df.columns:
                        if "/" in c:
                            val = str(p_row[c]).strip().upper()
                            if any(g in val for g in [r.upper() for r in st.session_state.GIANS]) and val != "":
                                yearly_data.append({"Tháng": f"T{m}", "Loại": "Đi Biển", "Ngày": 1})
                            elif val == "CA": yearly_data.append({"Tháng": f"T{m}", "Loại": "Nghỉ CA", "Ngày": 1})
            except: continue
        if yearly_data:
            df_chart = pd.DataFrame(yearly_data)
            pv = df_chart.pivot_table(index='Loại', columns='Tháng', values='Ngày', aggfunc='sum').fillna(0).astype(int)
            pv.index.name = None
            pv.columns.name = None
            st.table(pv)

with st.sidebar:
    st.header("⚙️ QUẢN LÝ GIÀN")
    ng = st.text_input("Thêm giàn:").upper().strip()
    if st.button("➕ Thêm"):
        if ng and ng not in st.session_state.GIANS:
            st.session_state.GIANS.append(ng)
            save_config_rigs(st.session_state.GIANS)
            st.rerun()
