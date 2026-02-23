import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import time
import plotly.express as px
import os

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 0.5rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; font-size: 38px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 2px 2px 5px #000 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DANH MỤC ---
COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]
DEFAULT_RIGS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

# --- 3. KẾT NỐI ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_config_rigs():
    try:
        df_config = conn.read(worksheet="config", ttl=0)
        if not df_config.empty and "GIANS" in df_config.columns:
            return [str(g).strip().upper() for g in df_config["GIANS"].dropna().tolist() if str(g).strip()]
    except:
        return DEFAULT_RIGS
    return DEFAULT_RIGS

def save_config_rigs(rig_list):
    try:
        df_save = pd.DataFrame({"GIANS": rig_list})
        conn.update(worksheet="config", data=df_save)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"⚠️ Lỗi lưu config: {e}")
        return False

# --- 4. ENGINE TÍNH TOÁN & AUTOFILL ---
def apply_logic(df, curr_m, curr_y, DATE_COLS, rigs):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    now = datetime.now()
    today = now.date()
    df_calc = df.copy()
    rigs_upper = [r.upper() for r in rigs]

    for idx, row in df_calc.iterrows():
        if not str(row.get('Họ và Tên', '')).strip(): continue
        accrued = 0.0
        last_val = ""
        
        for col in DATE_COLS:
            d_num = int(col[:2])
            target_date = date(curr_y, curr_m, d_num)
            val = str(row.get(col, "")).strip()
            
            # Autofill tự động (Sau 6h sáng)
            if (not val or val == "" or val.lower() == "nan"):
                if target_date < today or (target_date == today and now.hour >= 6):
                    if last_val != "":
                        lv_up = last_val.upper()
                        if any(g in lv_up for g in rigs_upper) or lv_up in ["CA", "WS", "NP", "ỐM"]:
                            val = last_val
                            df_calc.at[idx, col] = val
            
            if val and val.lower() != "nan": last_val = val
            
            # Quy tắc tính CA
            v_up = val.upper()
            if v_up:
                is_we = target_date.weekday() >= 5
                is_ho = target_date in hols
                if any(g in v_up for g in rigs_upper):
                    if is_ho: accrued += 2.0
                    elif is_we: accrued += 1.0
                    else: accrued += 0.5
                elif v_up == "CA":
                    if not is_we and not is_ho: accrued -= 1.0
        
        ton_cu = pd.to_numeric(row.get('Tồn cũ', 0), errors='coerce')
        df_calc.at[idx, 'Tổng CA'] = round(float(ton_cu if not pd.isna(ton_cu) else 0.0) + accrued, 1)
    return df_calc

# --- 5. KHỞI TẠO ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = load_config_rigs()

c_logo, _ = st.columns([1, 4])
with c_logo:
    if os.path.exists("logo_pvd.png"): st.image("logo_pvd.png", width=180)
    else: st.markdown("### 🔴 PVD WELL")

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

wd = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())
sheet_name = wd.strftime("%m_%Y")
curr_m, curr_y = wd.month, wd.year
days_in_m = calendar.monthrange(curr_y, curr_m)[1]
DATE_COLS = [f"{d:02d}/{wd.strftime('%b')} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_y,curr_m,d).weekday()]})" for d in range(1, days_in_m+1)]

if 'db' not in st.session_state or st.session_state.get('active_sheet') != sheet_name:
    try:
        df_raw = conn.read(worksheet=sheet_name, ttl=0).fillna("")
    except:
        df_raw = pd.DataFrame({'STT': range(1, len(NAMES_66)+1), 'Họ và Tên': NAMES_66, 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Tồn cũ': 0.0, 'Tổng CA': 0.0})
        for c in DATE_COLS: df_raw[c] = ""
    st.session_state.db = apply_logic(df_raw, curr_m, curr_y, DATE_COLS, st.session_state.GIANS)
    st.session_state.active_sheet = sheet_name

# --- 6. GIAO DIỆN CHÍNH ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ & BÁO CÁO"])

with t1:
    c1, c2, c3 = st.columns([2, 2, 4])
    if c1.button("📤 LƯU CLOUD (ĐỒNG BỘ)", type="primary", use_container_width=True):
        st.session_state.db = apply_logic(st.session_state.db, curr_m, curr_y, DATE_COLS, st.session_state.GIANS)
        if conn.update(worksheet=sheet_name, data=st.session_state.db):
            st.cache_data.clear(); st.success("Đã lưu!"); time.sleep(1); st.rerun()

    all_v = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Tồn cũ', 'Tổng CA'] + DATE_COLS
    edited = st.data_editor(st.session_state.db[all_v], use_container_width=True, height=550, hide_index=True, key="pvd_v6")
    st.session_state.db.update(edited)

with t2:
    st.subheader(f"📊 Thống kê nhân sự năm {curr_y}")
    sel_name = st.selectbox("🔍 Chọn nhân sự để xem báo cáo:", NAMES_66)
    
    if sel_name:
        yearly_data = []
        rigs_up = [r.upper() for r in st.session_state.GIANS]
        
        for m in range(1, 13):
            try:
                m_sheet = f"{m:02d}_{curr_y}"
                m_df = conn.read(worksheet=m_sheet, ttl=0).fillna("")
                p_row = m_df[m_df['Họ và Tên'] == sel_name].iloc[0]
                
                counts = {"Đi Biển": 0, "Nghỉ CA": 0, "Làm xưởng": 0, "Nghỉ/Ốm": 0}
                for c in m_df.columns:
                    if "/" in c:
                        val = str(p_row[c]).strip().upper()
                        if any(g in val for g in rigs_up): counts["Đi Biển"] += 1
                        elif val == "CA": counts["Nghỉ CA"] += 1
                        elif val == "WS": counts["Làm xưởng"] += 1
                        elif val in ["NP", "ỐM"]: counts["Nghỉ/Ốm"] += 1
                
                for k, v in counts.items():
                    if v > 0: yearly_data.append({"Tháng": f"Tháng {m}", "Loại": k, "Số ngày": v})
            except: continue

        if yearly_data:
            df_chart = pd.DataFrame(yearly_data)
            fig = px.bar(df_chart, x="Tháng", y="Số ngày", color="Loại", barmode="stack", text="Số ngày", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("### 📋 Chi tiết số ngày công")
            pv = df_chart.pivot_table(index='Loại', columns='Tháng', values='Số ngày', aggfunc='sum').fillna(0).astype(int)
            pv['TỔNG NĂM'] = pv.sum(axis=1)
            st.table(pv)
        else:
            st.info(f"Hiện chưa có dữ liệu công của {sel_name} trên Cloud. Hãy nhập dữ liệu và nhấn 'Lưu Cloud' để hệ thống ghi nhận.")

with st.sidebar:
    st.header("⚙️ DANH MỤC GIÀN")
    new_g = st.text_input("Thêm giàn:").upper().strip()
    if st.button("➕ THÊM"):
        if new_g and new_g not in st.session_state.GIANS:
            st.session_state.GIANS.append(new_g); save_config_rigs(st.session_state.GIANS); st.rerun()
    
    del_g = st.selectbox("Xóa giàn:", st.session_state.GIANS)
    if st.button("❌ XÓA"):
        st.session_state.GIANS.remove(del_g); save_config_rigs(st.session_state.GIANS); st.rerun()
