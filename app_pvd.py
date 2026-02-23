import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import time
import plotly.express as px
import os

# --- 1. CẤU HÌNH HỆ THỐNG ---
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

# --- 2. DANH MỤC CỐ ĐỊNH ---
COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]
DEFAULT_RIGS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

# --- 3. KẾT NỐI & HÀM LƯU TRỮ ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_config_rigs():
    try:
        df_config = conn.read(worksheet="config", ttl=0)
        if not df_config.empty and "GIANS" in df_config.columns:
            return [str(g).strip().upper() for g in df_config["GIANS"].dropna().tolist() if str(g).strip()]
    except: return DEFAULT_RIGS
    return DEFAULT_RIGS

def save_config_rigs(rig_list):
    try:
        # Xóa cache trước khi lưu để đảm bảo không bị xung đột dữ liệu cũ
        st.cache_data.clear() 
        df_save = pd.DataFrame({"GIANS": rig_list})
        conn.update(worksheet="config", data=df_save)
        # Thông báo cho người dùng biết hệ thống đang xử lý
        return True
    except Exception as e:
        st.error(f"Lỗi lưu giàn: {e}")
        return False

# --- 4. ENGINE TÍNH TOÁN (QUY TẮC CŨ) ---
def apply_logic(df, curr_m, curr_y, DATE_COLS, rigs):
    # Danh sách ngày lễ 2026
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    now = datetime.now()
    today = now.date()
    df_calc = df.copy()
    rigs_up = [r.upper() for r in rigs]

    for idx, row in df_calc.iterrows():
        if not str(row.get('Họ và Tên', '')).strip(): continue
        accrued = 0.0
        last_val = ""
        
        for col in DATE_COLS:
            d_num = int(col[:2])
            target_date = date(curr_y, curr_m, d_num)
            val = str(row.get(col, "")).strip()
            
            # Autofill tự động sau 6h sáng (Lấy giá trị cũ điền vào ô trống)
            if (not val or val == "" or val.lower() == "nan"):
                if target_date < today or (target_date == today and now.hour >= 6):
                    if last_val != "":
                        lv_up = last_val.upper()
                        if any(g in lv_up for g in rigs_up) or lv_up in ["CA", "WS", "NP", "ỐM"]:
                            val = last_val
                            df_calc.at[idx, col] = val
            
            if val and val.lower() != "nan": last_val = val
            
            # QUY TẮC TÍNH CA
            v_up = val.upper()
            if v_up:
                is_we = target_date.weekday() >= 5 # T7, CN
                is_ho = target_date in hols       # Lễ
                # 1. Đi biển
                if any(g in v_up for g in rigs_up):
                    if is_ho: accrued += 2.0
                    elif is_we: accrued += 1.0
                    else: accrued += 0.5
                # 2. Nghỉ CA (Trừ công)
                elif v_up == "CA":
                    if not is_we and not is_ho: accrued -= 1.0
        
        ton_cu = pd.to_numeric(row.get('Tồn cũ', 0), errors='coerce')
        df_calc.at[idx, 'Tổng CA'] = round(float(ton_cu if not pd.isna(ton_cu) else 0.0) + accrued, 1)
    return df_calc

# --- 5. KHỞI TẠO LOGO & DATA ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = load_config_rigs()

c_logo, _ = st.columns([1, 4])
with c_logo:
    if os.path.exists("logo_pvd.png"): st.image("logo_pvd.png", width=180)
    else: st.markdown("### 🔴 PVD WELL")

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# Chọn tháng
_, mc, _ = st.columns([3, 2, 3])
with mc:
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
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BÁO CÁO & BIỂU ĐỒ"])

with t1:
    # HÀNG NÚT CHỨC NĂNG
    c1, c2, c3 = st.columns([2, 2, 4])
    if c1.button("📤 LƯU CLOUD (ĐỒNG BỘ)", type="primary", use_container_width=True):
        st.session_state.db = apply_logic(st.session_state.db, curr_m, curr_y, DATE_COLS, st.session_state.GIANS)
        conn.update(worksheet=sheet_name, data=st.session_state.db)
        st.cache_data.clear(); st.success("Đã lưu!"); time.sleep(1); st.rerun()
    
    with c3:
        buf = io.BytesIO(); st.session_state.db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf.getvalue(), f"PVD_{sheet_name}.xlsx", use_container_width=True)

    # CÔNG CỤ NHẬP NHANH (KHÔI PHỤC)
    with st.expander("🛠️ CÔNG CỤ NHẬP NHANH (CHO NHIỀU NGƯỜI)"):
        sel_names = st.multiselect("1. Chọn nhân sự:", NAMES_66)
        d_range = st.date_input("2. Chọn khoảng thời gian:", value=(date(curr_y, curr_m, 1), date(curr_y, curr_m, days_in_m)))
        
        r1, r2, r3, r4 = st.columns(4)
        stt_q = r1.selectbox("3. Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm", "Xóa trắng"])
        rig_q = r2.selectbox("4. Tên Giàn (Nếu đi biển):", st.session_state.GIANS) if stt_q == "Đi Biển" else stt_q
        co_q = r3.selectbox("5. Cập nhật Công ty:", ["Giữ nguyên"] + COMPANIES)
        ti_q = r4.selectbox("6. Cập nhật Chức danh:", ["Giữ nguyên"] + TITLES)
        
        if st.button("✅ ÁP DỤNG CHO DANH SÁCH ĐÃ CHỌN", use_container_width=True):
            if sel_names and len(d_range) == 2:
                for name in sel_names:
                    idx = st.session_state.db.index[st.session_state.db['Họ và Tên'] == name].tolist()[0]
                    if co_q != "Giữ nguyên": st.session_state.db.at[idx, 'Công ty'] = co_q
                    if ti_q != "Giữ nguyên": st.session_state.db.at[idx, 'Chức danh'] = ti_q
                    
                    start_d, end_d = d_range
                    curr_d = start_d
                    while curr_d <= end_d:
                        if curr_d.month == curr_m:
                            c_col = [c for c in DATE_COLS if c.startswith(f"{curr_d.day:02d}/")][0]
                            st.session_state.db.at[idx, c_col] = "" if stt_q == "Xóa trắng" else rig_q
                        curr_d += timedelta(days=1)
                st.session_state.db = apply_logic(st.session_state.db, curr_m, curr_y, DATE_COLS, st.session_state.GIANS)
                st.rerun()

    # BẢNG DỮ LIỆU
    all_v = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Tồn cũ', 'Tổng CA'] + DATE_COLS
    edited = st.data_editor(
        st.session_state.db[all_v],
        use_container_width=True, height=600, hide_index=True, key="pvd_editor_final",
        column_config={
            "Công ty": st.column_config.SelectboxColumn(options=COMPANIES),
            "Chức danh": st.column_config.SelectboxColumn(options=TITLES),
            "Tổng CA": st.column_config.NumberColumn(disabled=True, format="%.1f"),
        }
    )
    st.session_state.db.update(edited)

with t2:
    st.subheader(f"📊 Thống kê công năm {curr_y}")
    sel_user = st.selectbox("🔍 Chọn nhân sự xem báo cáo:", NAMES_66)
    if sel_user:
        history = []
        for m in range(1, 13):
            try:
                m_df = conn.read(worksheet=f"{m:02d}_{curr_y}", ttl=0).fillna("")
                row = m_df[m_df['Họ và Tên'] == sel_user].iloc[0]
                for c in m_df.columns:
                    if "/" in c:
                        v = str(row[c]).strip().upper()
                        if any(g in v for g in st.session_state.GIANS): history.append({"Tháng": f"T{m}", "Loại": "Đi Biển"})
                        elif v == "CA": history.append({"Tháng": f"T{m}", "Loại": "Nghỉ CA"})
                        elif v == "WS": history.append({"Tháng": f"T{m}", "Loại": "Xưởng"})
                        elif v in ["NP", "ỐM"]: history.append({"Tháng": f"T{m}", "Loại": "Nghỉ/Ốm"})
            except: continue
        
        if history:
            df_h = pd.DataFrame(history)
            df_sum = df_h.groupby(['Tháng', 'Loại']).size().reset_index(name='Ngày')
            st.plotly_chart(px.bar(df_sum, x="Tháng", y="Ngày", color="Loại", barmode="stack", template="plotly_dark"), use_container_width=True)
            st.table(df_sum.pivot(index='Loại', columns='Tháng', values='Ngày').fillna(0).astype(int))

with st.sidebar:
    st.header("⚙️ QUẢN LÝ GIÀN")
    st.info("Dữ liệu sẽ được đồng bộ trực tiếp lên tab 'config'")
    
    # Khu vực thêm giàn
    new_g = st.text_input("Nhập tên giàn mới:", key="input_new_rig").upper().strip()
    if st.button("➕ XÁC NHẬN THÊM", use_container_width=True, type="primary"):
        if new_g:
            if new_g not in st.session_state.GIANS:
                # Tạo danh sách mới và lưu ngay
                updated_rigs = st.session_state.GIANS + [new_g]
                if save_config_rigs(updated_rigs):
                    st.session_state.GIANS = updated_rigs
                    st.success(f"✅ Đã thêm giàn {new_g}")
                    time.sleep(0.5) # Chờ một chút để Google Sheet kịp nhận lệnh
                    st.rerun()
            else:
                st.warning("Giàn này đã tồn tại!")
        else:
            st.error("Vui lòng nhập tên giàn")

    st.markdown("---")
    
    # Khu vực xóa giàn
    if st.session_state.GIANS:
        del_g = st.selectbox("Chọn giàn cần xóa:", st.session_state.GIANS)
        if st.button("❌ XÁC NHẬN XÓA", use_container_width=True):
            updated_rigs = [r for r in st.session_state.GIANS if r != del_g]
            if save_config_rigs(updated_rigs):
                st.session_state.GIANS = updated_rigs
                st.warning(f"🗑️ Đã xóa giàn {del_g}")
                time.sleep(0.5)
                st.rerun()
    
    st.markdown("---")
    if st.button("🔄 LÀM MỚI DANH SÁCH", use_container_width=True):
        st.cache_data.clear()
        st.session_state.GIANS = load_config_rigs()
        st.rerun()
