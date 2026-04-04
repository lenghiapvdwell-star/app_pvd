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

# --- 3. DANH SÁCH MẶC ĐỊNH ---
DEFAULT_NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]
DEFAULT_RIGS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

# --- 4. KẾT NỐI ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data_safe(wks_name):
    try:
        return conn.read(worksheet=wks_name, ttl=0)
    except:
        return pd.DataFrame()

def load_config():
    df_conf = get_data_safe("config")
    rigs = [str(g).strip().upper() for g in df_conf["GIANS"].dropna().tolist()] if not df_conf.empty and "GIANS" in df_conf.columns else DEFAULT_RIGS
    
    # Ưu tiên lấy từ nhansu 999s nếu có
    df_ns = get_data_safe("nhansu 999s")
    if not df_ns.empty and "Họ và Tên" in df_ns.columns:
        names = [str(n).strip() for n in df_ns["Họ và Tên"].dropna().tolist() if str(n).strip()]
    elif not df_conf.empty and "NAMES" in df_conf.columns:
        names = [str(n).strip() for n in df_conf["NAMES"].dropna().tolist() if str(n).strip()]
    else:
        names = DEFAULT_NAMES
    return rigs, names

def save_config(rig_list, name_list):
    try:
        df_save = pd.DataFrame({"GIANS": pd.Series(rig_list), "NAMES": pd.Series(name_list)})
        conn.update(worksheet="config", data=df_save)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Lỗi lưu cấu hình: {e}")

if "GIANS" not in st.session_state or "NAMES" not in st.session_state:
    st.session_state.GIANS, st.session_state.NAMES = load_config()

# --- 5. ENGINE TÍNH TOÁN ---
def apply_logic(df, curr_m, curr_y, rigs):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    df_calc = df.copy()
    rigs_up = [r.upper() for r in rigs]
    date_cols = [c for c in df_calc.columns if "/" in str(c) and "(" in str(c)]

    for idx, row in df_calc.iterrows():
        if "Họ và Tên" not in row or not str(row.get('Họ và Tên', '')).strip(): continue
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

# --- 6. KHỞI TẠO DỮ LIỆU ---
_, mc, _ = st.columns([3, 2, 3])
with mc: wd = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_name = wd.strftime("%m_%Y")
curr_m, curr_y = wd.month, wd.year
days_in_m = calendar.monthrange(curr_y, curr_m)[1]
theoretical_date_cols = [f"{d:02d}/{wd.strftime('%b')} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_y,curr_m,d).weekday()]})" for d in range(1, days_in_m+1)]

df_raw = get_data_safe(sheet_name)

# Nếu tháng mới hoàn toàn chưa có sheet
if df_raw.empty:
    df_raw = pd.DataFrame({'STT': range(1, len(st.session_state.NAMES)+1), 'Họ và Tên': st.session_state.NAMES, 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Tồn cũ': 0.0, 'Tổng CA': 0.0})
    for c in theoretical_date_cols: df_raw[c] = ""
    
    # Lấy tồn cũ từ tháng trước
    prev_date = wd.replace(day=1) - timedelta(days=1)
    df_prev = get_data_safe(prev_date.strftime("%m_%Y"))
    if not df_prev.empty:
        bal_map = df_prev.set_index('Họ và Tên')['Tổng CA'].to_dict()
        df_raw['Tồn cũ'] = df_raw['Họ và Tên'].map(bal_map).fillna(0.0)
    
    # Tạo sheet mới trên Google Sheets ngay lập tức để tránh lỗi API sau này
    try:
        conn.update(worksheet=sheet_name, data=df_raw)
        st.toast(f"Đã khởi tạo bảng cho tháng {sheet_name}")
    except: pass

# --- AUTO-FILL HÀNG NGÀY ---
now = datetime.now()
if sheet_name == now.strftime("%m_%Y") and now.hour >= 6:
    changed = False
    # Ngày 01 lấy từ tháng trước
    if now.day == 1:
        c01 = [c for c in df_raw.columns if str(c).startswith("01/")]
        if c01 and (df_raw[c01[0]].isna() | (df_raw[c01[0]] == "")).all():
            prev_date = wd.replace(day=1) - timedelta(days=1)
            df_prev = get_data_safe(prev_date.strftime("%m_%Y"))
            if not df_prev.empty:
                last_cols = [c for c in df_prev.columns if "/" in str(c)]
                if last_cols:
                    st_map = df_prev.set_index('Họ và Tên')[last_cols[-1]].to_dict()
                    df_raw[c01[0]] = df_raw['Họ và Tên'].map(st_map).fillna("")
                    changed = True
    # Các ngày khác lấy từ hôm qua
    elif now.day > 1:
        p_day, c_day = f"{(now.day-1):02d}/", f"{now.day:02d}/"
        cp = [c for c in df_raw.columns if str(c).startswith(p_day)]
        cc = [c for c in df_raw.columns if str(c).startswith(c_day)]
        if cp and cc:
            mask = (df_raw[cc[0]].isna() | (df_raw[cc[0]] == "")) & (df_raw[cp[0]].notna() & (df_raw[cp[0]] != ""))
            if mask.any():
                df_raw.loc[mask, cc[0]] = df_raw.loc[mask, cp[0]]
                changed = True
    
    if changed:
        df_raw = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)
        try: conn.update(worksheet=sheet_name, data=df_raw)
        except: pass

current_db = apply_logic(df_raw, curr_m, curr_y, st.session_state.GIANS)

# --- 7. GIAO DIỆN ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG CHI TIẾT", "📊 BÁO CÁO NĂM"])

with t1:
    c1, c2, c3 = st.columns([2, 2, 4])
    if c1.button("📤 LƯU DỮ LIỆU", type="primary", use_container_width=True):
        try:
            conn.update(worksheet=sheet_name, data=current_db)
            st.success("Đã lưu thành công!")
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi API Google Sheets: {e}. Vui lòng thử lại sau 1 phút.")

    with c3:
        buf = io.BytesIO(); current_db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf.getvalue(), f"PVDWS_{sheet_name}.xlsx", use_container_width=True)

    with st.expander("🛠️ CÔNG CỤ NHẬP NHANH"):
        names_sel = st.multiselect("Nhân viên:", st.session_state.NAMES)
        dr = st.date_input("Khoảng ngày:", value=(date(curr_y, curr_m, 1), date(curr_y, curr_m, 1)))
        r1, r2, r3, r4 = st.columns(4)
        stt = r1.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm", "Xóa"])
        rig = r2.selectbox("Giàn:", st.session_state.GIANS) if stt == "Đi Biển" else stt
        if st.button("✅ ÁP DỤNG"):
            if names_sel and len(dr) == 2:
                sd, ed = dr
                while sd <= ed:
                    if sd.month == curr_m:
                        match = [c for c in current_db.columns if str(c).startswith(f"{sd.day:02d}/")]
                        if match:
                            for n in names_sel:
                                idx = current_db.index[current_db['Họ và Tên'] == n].tolist()
                                if idx: current_db.at[idx[0], match[0]] = "" if stt == "Xóa" else rig
                    sd += timedelta(days=1)
                st.rerun()

    # Chỉ hiển thị những cột thực sự tồn tại
    base_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Tồn cũ', 'Tổng CA']
    existing_base = [c for c in base_cols if c in current_db.columns]
    date_cols = [c for c in current_db.columns if "/" in str(c)]
    all_display = existing_base + date_cols
    
    ed_db = st.data_editor(current_db[all_display], use_container_width=True, height=550, hide_index=True)
    
    if not ed_db.equals(current_db[all_display]):
        for col in all_display: current_db[col] = ed_db[col]
        current_db = apply_logic(current_db, curr_m, curr_y, st.session_state.GIANS)
        try: conn.update(worksheet=sheet_name, data=current_db)
        except: pass
        st.rerun()

with t2:
    st.subheader(f"📊 Thống kê nhân sự năm {curr_y}")
    person = st.selectbox("🔍 Tìm tên:", st.session_state.NAMES)
    if person:
        y_data = []
        for m in range(1, 13):
            m_df = get_data_safe(f"{m:02d}_{curr_y}")
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
                for k, v in c.items():
                    if v > 0: y_data.append({"Tháng": f"T{m}", "Loại": k, "Số ngày": v})
        if y_data:
            st.plotly_chart(px.bar(pd.DataFrame(y_data), x="Tháng", y="Số ngày", color="Loại", barmode="stack", template="plotly_dark"), use_container_width=True)

with st.sidebar:
    st.header("⚙️ CÀI ĐẶT")
    with st.expander("👤 QUẢN LÝ NHÂN VIÊN"):
        new_n = st.text_input("Thêm tên mới:")
        if st.button("➕ Thêm") and new_n:
            st.session_state.NAMES.append(new_n); save_config(st.session_state.GIANS, st.session_state.NAMES); st.rerun()
        del_n = st.selectbox("Xóa tên:", st.session_state.NAMES)
        if st.button("❌ Xóa"):
            st.session_state.NAMES.remove(del_n); save_config(st.session_state.GIANS, st.session_state.NAMES); st.rerun()
    
    with st.expander("🏗️ QUẢN LÝ GIÀN"):
        new_g = st.text_input("Thêm giàn:").upper()
        if st.button("➕ Thêm Giàn") and new_g:
            st.session_state.GIANS.append(new_g); save_config(st.session_state.GIANS, st.session_state.NAMES); st.rerun()
        del_g = st.selectbox("Xóa giàn:", st.session_state.GIANS)
        if st.button("❌ Xóa Giàn"):
            st.session_state.GIANS.remove(del_g); save_config(st.session_state.GIANS, st.session_state.NAMES); st.rerun()
