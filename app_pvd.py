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
        font-size: 35px !important; 
        font-weight: bold !important;
        text-align: center !important; 
        margin-bottom: 20px !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO ---
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
st.markdown('<h1 class="main-title">QUẢN LÝ NHÂN SỰ PVD WELL SERVICES</h1>', unsafe_allow_html=True)

# --- 3. DANH MỤC CỐ ĐỊNH ---
COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]
DEFAULT_RIGS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]
HOLIDAYS_2026 = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]

# --- 4. KẾT NỐI DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def get_data_cached(wks_name):
    try:
        return conn.read(worksheet=wks_name, ttl=0)
    except: return pd.DataFrame()

# --- 5. LOGIC TÍNH TOÁN ---
def apply_logic(df, curr_m, curr_y, rigs):
    df_calc = df.copy()
    rigs_up = [r.upper() for r in rigs]
    date_cols = [c for c in df_calc.columns if "/" in str(c)]
    
    for idx, row in df_calc.iterrows():
        if not str(row.get('Họ và Tên', '')).strip(): continue
        accrued = 0.0
        for col in date_cols:
            try:
                val = str(row.get(col, "")).strip().upper()
                if val in ["", "NAN", "NONE"]: continue
                d_num = int(col[:2])
                target_date = date(curr_y, curr_m, d_num)
                is_we = target_date.weekday() >= 5
                is_ho = target_date in HOLIDAYS_2026
                
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

# --- 6. KHỞI TẠO VÀ AUTO-FILL THEO NGÀY/THÁNG ---
# --- 6. KHỞI TẠO VÀ AUTO-FILL NÂNG CAO (BẢN SỬA LỖI KEYERROR) ---
if "GIANS" not in st.session_state:
    df_conf = get_data_cached("config")
    st.session_state.GIANS = df_conf["GIANS"].dropna().tolist() if not df_conf.empty else DEFAULT_RIGS

col_d1, col_d2, col_d3 = st.columns([3, 2, 3])
with col_d2:
    wd = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_name = wd.strftime("%m_%Y")
curr_m, curr_y = wd.month, wd.year
days_in_m = calendar.monthrange(curr_y, curr_m)[1]
# Định dạng cột: "01/Apr (T2)"
DATE_COLS = [f"{d:02d}/{wd.strftime('%b')} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_y,curr_m,d).weekday()]})" for d in range(1, days_in_m+1)]

df_raw = get_data_cached(sheet_name)

# 1. Nếu tháng hoàn toàn mới hoặc lỗi không đọc được -> Khởi tạo
if df_raw.empty:
    df_raw = pd.DataFrame({'STT': range(1, len(NAMES_66)+1), 'Họ và Tên': NAMES_66, 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Tồn cũ': 0.0, 'Tổng CA': 0.0})
    for c in DATE_COLS: df_raw[c] = ""
    
    prev_m_date = wd.replace(day=1) - timedelta(days=1)
    df_prev = get_data_cached(prev_m_date.strftime("%m_%Y"))
    if not df_prev.empty:
        bal_map = df_prev.set_index('Họ và Tên')['Tổng CA'].to_dict()
        df_raw['Tồn cũ'] = df_raw['Họ và Tên'].map(bal_map).fillna(0.0)
    
    df_raw = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)
    conn.update(worksheet=sheet_name, data=df_raw)

# 2. AUTO-FILL THÔNG MINH (CHẶY SAU 6H SÁNG)
now = datetime.now()
# Chỉ tự động fill nếu đang xem đúng tháng hiện tại
if sheet_name == now.strftime("%m_%Y") and now.hour >= 6:
    changed = False
    
    # TRƯỜNG HỢP A: Ngày đầu tháng (Ngày 01)
    if now.day == 1:
        col_01 = DATE_COLS[0]
        # Kiểm tra cột 01 có tồn tại trong df_raw không để tránh KeyError
        if col_01 in df_raw.columns:
            if (df_raw[col_01].isna() | (df_raw[col_01] == "")).all():
                prev_m_date = wd.replace(day=1) - timedelta(days=1)
                df_prev = get_data_cached(prev_m_date.strftime("%m_%Y"))
                if not df_prev.empty:
                    # Lấy cột ngày cuối cùng của tháng trước
                    prev_date_cols = [c for c in df_prev.columns if "/" in str(c)]
                    if prev_date_cols:
                        last_day_col = prev_date_cols[-1]
                        status_map = df_prev.set_index('Họ và Tên')[last_day_col].to_dict()
                        df_raw[col_01] = df_raw['Họ và Tên'].map(status_map).fillna("")
                        changed = True

    # TRƯỜNG HỢP B: Các ngày khác trong tháng
    else:
        today_prefix = f"{now.day:02d}/"
        yesterday_prefix = f"{(now.day-1):02d}/"
        
        col_today = [c for c in df_raw.columns if str(c).startswith(today_prefix)]
        col_yesterday = [c for c in df_raw.columns if str(c).startswith(yesterday_prefix)]
        
        # Chỉ xử lý nếu tìm thấy cả cột hôm nay và hôm qua trong dữ liệu thực tế
        if col_today and col_yesterday:
            c_t = col_today[0]
            c_y = col_yesterday[0]
            mask = (df_raw[c_t].isna() | (df_raw[c_t] == "")) & \
                   (df_raw[c_y].notna() & (df_raw[c_y] != ""))
            if mask.any():
                df_raw.loc[mask, c_t] = df_raw.loc[mask, c_y]
                changed = True
    
    if changed:
        df_raw = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)
        conn.update(worksheet=sheet_name, data=df_raw)

current_df = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)

# --- 7. TABS GIAO DIỆN ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG CHI TIẾT", "📊 BÁO CÁO TỔNG HỢP"])

with t1:
    c1, c2, c3 = st.columns([2, 2, 4])
    if c1.button("📤 LƯU DỮ LIỆU", type="primary", use_container_width=True):
        conn.update(worksheet=sheet_name, data=current_df)
        st.cache_data.clear()
        st.success("Đã lưu thành công!")
        st.rerun()
    
    with c2:
        output = io.BytesIO()
        current_df.to_excel(output, index=False)
        st.download_button("📥 XUẤT EXCEL", output.getvalue(), f"PVD_{sheet_name}.xlsx", use_container_width=True)

    # Công cụ nhập nhanh
    with st.expander("🛠️ CÔNG CỤ NHẬP NHANH (CHO NHIỀU NGƯỜI)"):
        sel_names = st.multiselect("Chọn nhân viên:", NAMES_66)
        date_rng = st.date_input("Chọn khoảng ngày:", value=(date(curr_y, curr_m, 1), date(curr_y, curr_m, 1)))
        r1, r2, r3, r4 = st.columns(4)
        stt = r1.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm", "Xóa"])
        rig = r2.selectbox("Tên Giàn:", st.session_state.GIANS) if stt == "Đi Biển" else stt
        co_input = r3.selectbox("Công ty:", ["Giữ nguyên"] + COMPANIES)
        ti_input = r4.selectbox("Chức danh:", ["Giữ nguyên"] + TITLES)
        
        if st.button("✅ ÁP DỤNG NHANH", use_container_width=True):
            if sel_names and len(date_rng) == 2:
                for n in sel_names:
                    idx = current_df.index[current_df['Họ và Tên'] == n].tolist()
                    if idx:
                        i = idx[0]
                        if co_input != "Giữ nguyên": current_df.at[i, 'Công ty'] = co_input
                        if ti_input != "Giữ nguyên": current_df.at[i, 'Chức danh'] = ti_input
                        sd, ed = date_rng
                        while sd <= ed:
                            if sd.month == curr_m:
                                target = [c for c in DATE_COLS if c.startswith(f"{sd.day:02d}/")]
                                if target: current_df.at[i, target[0]] = "" if stt == "Xóa" else str(rig)
                            sd += timedelta(days=1)
                current_df = apply_logic(current_df, curr_m, curr_y, st.session_state.GIANS)
                conn.update(worksheet=sheet_name, data=current_df)
                st.rerun()

    # Cấu hình hiển thị bảng
    fixed_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Tồn cũ', 'Tổng CA']
    all_display_cols = fixed_cols + DATE_COLS
    
    col_config = {
        "STT": st.column_config.NumberColumn("STT", width="small", pinned=True),
        "Họ và Tên": st.column_config.TextColumn("Họ và Tên", width="medium", pinned=True),
        "Tồn cũ": st.column_config.NumberColumn("Tồn cũ", format="%.1f", pinned=True),
        "Tổng CA": st.column_config.NumberColumn("Tổng CA", format="%.1f", pinned=True),
        "Công ty": st.column_config.TextColumn("Công ty", width="small"),
        "Chức danh": st.column_config.TextColumn("Chức danh", width="small")
    }
    
    status_opts = st.session_state.GIANS + ["CA", "WS", "NP", "ỐM", ""]
    for c in DATE_COLS:
        col_config[c] = st.column_config.SelectboxColumn(c, options=status_opts, width="small")

    ed_df = st.data_editor(current_df[all_display_cols], use_container_width=True, height=550, hide_index=True, column_config=col_config)
    
    if not ed_df.equals(current_df[all_display_cols]):
        for col in all_display_cols: current_df[col] = ed_df[col]
        current_df = apply_logic(current_df, curr_m, curr_y, st.session_state.GIANS)
        conn.update(worksheet=sheet_name, data=current_df)
        st.rerun()

with t2:
    st.subheader(f"📊 Thống kê chi tiết năm {curr_y}")
    person = st.selectbox("🔍 Tìm kiếm nhân sự:", NAMES_66)
    if person:
        y_data = []
        for m in range(1, 13):
            m_df = get_data_cached(f"{m:02d}_{curr_y}")
            if not m_df.empty and person in m_df['Họ và Tên'].values:
                row = m_df[m_df['Họ và Tên'] == person].iloc[0]
                c = {"Đi Biển": 0, "Nghỉ CA": 0, "Tại Xưởng": 0, "Vắng/Ốm": 0}
                for col in m_df.columns:
                    if "/" in str(col):
                        v = str(row[col]).strip().upper()
                        if any(g in v for g in [r.upper() for r in st.session_state.GIANS]) and v != "": c["Đi Biển"] += 1
                        elif v == "CA": c["Nghỉ CA"] += 1
                        elif v == "WS": c["Tại Xưởng"] += 1
                        elif v in ["NP", "ỐM"]: c["Vắng/Ốm"] += 1
                for k, val in c.items():
                    if val > 0: y_data.append({"Tháng": f"T{m}", "Loại": k, "Ngày": val})
        
        if y_data:
            df_c = pd.DataFrame(y_data)
            fig = px.bar(df_c, x="Tháng", y="Ngày", color="Loại", barmode="stack", text="Ngày", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            st.table(df_c.pivot_table(index='Loại', columns='Tháng', values='Ngày', aggfunc='sum', fill_value=0))

with st.sidebar:
    st.header("⚙️ CÀI ĐẶT")
    new_rig = st.text_input("Thêm giàn:").upper().strip()
    if st.button("Thêm") and new_rig:
        st.session_state.GIANS.append(new_rig)
        conn.update(worksheet="config", data=pd.DataFrame({"GIANS": st.session_state.GIANS}))
        st.rerun()
    
    st.markdown("---")
    if st.button("🔄 LÀM MỚI HỆ THỐNG"):
        st.cache_data.clear()
        st.rerun()
