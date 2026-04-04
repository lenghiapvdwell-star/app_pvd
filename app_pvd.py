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
        font-size: 39px !important; 
        font-weight: bold !important;
        text-align: center !important; 
        margin-bottom: 20px !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
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
st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. DANH MỤC CỐ ĐỊNH (GIỮ NGUYÊN 66 NHÂN SỰ) ---
COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]
DEFAULT_RIGS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

# --- 4. KẾT NỐI ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data_safe(wks_name, ttl=0):
    try:
        df = conn.read(worksheet=wks_name, ttl=ttl)
        return df if (df is not None and not df.empty) else pd.DataFrame()
    except: return pd.DataFrame()

def load_config_rigs():
    df = get_data_safe("config", ttl=300)
    if not df.empty and "GIANS" in df.columns:
        return [str(g).strip().upper() for g in df["GIANS"].dropna().tolist() if str(g).strip()]
    return DEFAULT_RIGS

# --- 5. ENGINE TÍNH TOÁN ---
def apply_logic(df, curr_m, curr_y, rigs):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    df_calc = df.copy()
    rigs_up = [r.upper() for r in rigs]
    date_cols = [c for c in df_calc.columns if "/" in str(c)]

    for idx, row in df_calc.iterrows():
        if not str(row.get('Họ và Tên', '')).strip(): continue
        accrued = 0.0
        for col in date_cols:
            try:
                val = str(row.get(col, "")).strip().upper()
                if not val or val == "NAN": continue
                d_num = int(str(col)[:2])
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

# --- 6. KHỞI TẠO DỮ LIỆU THÁNG ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = load_config_rigs()

_, mc, _ = st.columns([3, 2, 3])
with mc: wd = st.date_input("📅 CHỌN THÁNG:", value=date.today())

sheet_name = wd.strftime("%m_%Y")
curr_m, curr_y = wd.month, wd.year
days_in_m = calendar.monthrange(curr_y, curr_m)[1]
DATE_COLS = [f"{d:02d}/{wd.strftime('%b')} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_y,curr_m,d).weekday()]})" for d in range(1, days_in_m+1)]

df_raw = get_data_safe(sheet_name, ttl=0)

if df_raw.empty:
    df_raw = pd.DataFrame({'STT': range(1, len(NAMES_66)+1), 'Họ và Tên': NAMES_66, 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Tồn cũ': 0.0, 'Tổng CA': 0.0})
    for c in DATE_COLS: df_raw[c] = ""
    # Lấy tồn từ tháng trước
    prev_date = wd.replace(day=1) - timedelta(days=1)
    prev_df = get_data_safe(prev_date.strftime("%m_%Y"))
    if not prev_df.empty:
        balances = prev_df.set_index('Họ và Tên')['Tổng CA'].to_dict()
        df_raw['Tồn cũ'] = df_raw['Họ và Tên'].map(balances).fillna(0.0)

# --- 7. NÂNG CẤP AUTO-FILL (XUYÊN THÁNG) ---
now = datetime.now()
# Chỉ chạy nếu đang xem tháng hiện tại và sau 6h sáng
if sheet_name == now.strftime("%m_%Y") and now.hour >= 6:
    changed = False
    # Trường hợp: Ngày đầu tháng (01) -> Lấy dữ liệu từ ngày cuối cùng của tháng trước
    if now.day == 1:
        col_01 = [c for c in DATE_COLS if c.startswith("01/")]
        if col_01 and (df_raw[col_01[0]].isna() | (df_raw[col_01[0]] == "")).all():
            prev_date = wd.replace(day=1) - timedelta(days=1)
            prev_df = get_data_safe(prev_date.strftime("%m_%Y"))
            if not prev_df.empty:
                last_day_cols = [c for c in prev_df.columns if "/" in str(c)]
                if last_day_cols:
                    # Lấy trạng thái ngày cuối cùng tháng trước map sang ngày 01 tháng này
                    status_map = prev_df.set_index('Họ và Tên')[last_day_cols[-1]].to_dict()
                    df_raw[col_01[0]] = df_raw['Họ và Tên'].map(status_map).fillna("")
                    changed = True

    # Trường hợp: Các ngày khác trong tháng -> Lấy từ ngày hôm trước (Logic cũ của anh)
    elif now.day > 1:
        p_day, c_day = f"{(now.day-1):02d}/", f"{now.day:02d}/"
        col_p = [c for c in DATE_COLS if c.startswith(p_day)]
        col_c = [c for c in DATE_COLS if c.startswith(c_day)]
        if col_p and col_c:
            cp, cc = col_p[0], col_c[0]
            mask = (df_raw[cc].isna() | (df_raw[cc] == "")) & (df_raw[cp].notna() & (df_raw[cp] != ""))
            if mask.any():
                df_raw.loc[mask, cc] = df_raw.loc[mask, cp]
                changed = True

    if changed:
        df_raw = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)
        conn.update(worksheet=sheet_name, data=df_raw)
        st.toast("⚡ Tự động cập nhật dữ liệu ngày mới!", icon="✅")

current_db = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)

# --- 8. GIAO DIỆN CHÍNH (GIỮ NGUYÊN) ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ TỔNG HỢP"])

with t1:
    c1, c2, c3 = st.columns([2, 2, 4])
    if c1.button("📤 LƯU DỮ LIỆU", type="primary", use_container_width=True):
        conn.update(worksheet=sheet_name, data=current_db)
        st.success("Đã lưu lên Cloud!")
        st.rerun()

    with c3:
        buf = io.BytesIO(); current_db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf.getvalue(), f"PVD_{sheet_name}.xlsx", use_container_width=True)

    with st.expander("🛠️ CÔNG CỤ NHẬP NHANH"):
        names = st.multiselect("Chọn nhân sự:", NAMES_66)
        dr = st.date_input("Khoảng ngày:", value=(date(curr_y, curr_m, 1), date(curr_y, curr_m, 1)))
        r1, r2, r3, r4 = st.columns(4)
        stt = r1.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm", "Xóa"])
        rig = r2.selectbox("Tên Giàn:", st.session_state.GIANS) if stt == "Đi Biển" else stt
        if st.button("✅ ÁP DỤNG"):
            if names and len(dr) == 2:
                sd, ed = dr
                while sd <= ed:
                    if sd.month == curr_m:
                        match = [c for c in DATE_COLS if c.startswith(f"{sd.day:02d}/")]
                        if match:
                            for n in names:
                                idx = current_db.index[current_db['Họ và Tên'] == n].tolist()
                                if idx: current_db.at[idx[0], match[0]] = "" if stt == "Xóa" else rig
                    sd += timedelta(days=1)
                st.rerun()

    all_col = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Tồn cũ', 'Tổng CA'] + DATE_COLS
    st.data_editor(current_db[all_col], use_container_width=True, height=550, hide_index=True)

with t2:
    sel_name = st.selectbox("🔍 Chọn nhân sự xem báo cáo:", NAMES_66)
    if sel_name:
        y_data = []
        for m in range(1, 13):
            m_df = get_data_safe(f"{m:02d}_{curr_y}", ttl=600)
            if not m_df.empty and sel_name in m_df['Họ và Tên'].values:
                row = m_df[m_df['Họ và Tên'] == sel_name].iloc[0]
                c = {"Đi Biển": 0, "CA": 0, "Xưởng": 0, "Khác": 0}
                for col in m_df.columns:
                    if "/" in str(col):
                        v = str(row[col]).strip().upper()
                        if any(g in v for g in [r.upper() for r in st.session_state.GIANS]) and v != "": c["Đi Biển"] += 1
                        elif v == "CA": c["CA"] += 1
                        elif v == "WS": c["Xưởng"] += 1
                for k, v in c.items():
                    if v > 0: y_data.append({"Tháng": f"T{m}", "Loại": k, "Số ngày": v})
        if y_data:
            st.plotly_chart(px.bar(pd.DataFrame(y_data), x="Tháng", y="Số ngày", color="Loại", barmode="stack", template="plotly_dark"), use_container_width=True)
