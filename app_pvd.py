import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import time
import plotly.express as px

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 0.5rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; font-size: 45px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 3px 3px 6px #000 !important;
        font-family: 'Arial Black', sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER & LOGO ---
c_logo, _ = st.columns([1, 4])
with c_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=180)
    else:
        st.markdown("### 🔴 PVD WELL")

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. KẾT NỐI & HÀM LƯU ---
conn = st.connection("gsheets", type=GSheetsConnection)

def save_to_cloud(worksheet_name, df):
    if df.empty:
        st.error("Lỗi: Dữ liệu trống!")
        return False
    df_clean = df.fillna("").replace(["nan", "NaN", "None"], "")
    try:
        conn.update(worksheet=worksheet_name, data=df_clean)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Lỗi kết nối khi lưu: {e}")
        return False

# --- 4. DANH MỤC CỐ ĐỊNH ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

with st.sidebar:
    st.header("⚙️ QUẢN LÝ GIÀN KHOAN")
    new_g = st.text_input("Tên giàn mới:").strip().upper()
    if st.button("➕ THÊM GIÀN", use_container_width=True):
        if new_g and new_g not in st.session_state.GIANS:
            st.session_state.GIANS.append(new_g)
            st.rerun()
    st.divider()
    if st.session_state.GIANS:
        del_g = st.selectbox("Chọn giàn xóa:", st.session_state.GIANS)
        if st.button("❌ XÓA GIÀN", use_container_width=True):
            st.session_state.GIANS.remove(del_g)
            st.rerun()

COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]

# --- 5. ENGINE TÍNH TOÁN ---
def auto_engine(df, curr_month, curr_year, DATE_COLS):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    now = datetime.now()
    today = now.date()
    df_calc = df.copy()
    
    for idx, row in df_calc.iterrows():
        accrued = 0.0
        current_last_val = ""
        for col in DATE_COLS:
            if col not in df_calc.columns: continue
            d_num = int(col[:2])
            target_date = date(curr_year, curr_month, d_num)
            val = str(row.get(col, "")).strip()
            
            if (not val or val == "" or val.lower() == "nan") and (target_date < today or (target_date == today and now.hour >= 6)):
                if current_last_val != "":
                    lv_up = current_last_val.upper()
                    if any(g.upper() in lv_up for g in st.session_state.GIANS) or lv_up in ["CA", "WS"]:
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
        
        ton_cu = pd.to_numeric(row.get('Tồn cũ', 0), errors='coerce') or 0.0
        df_calc.at[idx, 'Tổng CA'] = round(ton_cu + accrued, 1)
    return df_calc

# --- 6. CHỌN THÁNG ---
_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today(), key="main_date_picker")

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b")
num_days_curr = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days_curr+1)]

# --- 7. TẢI DỮ LIỆU & QUẢN LÝ STATE ---
if 'active_sheet' not in st.session_state or st.session_state.active_sheet != sheet_name:
    st.session_state.active_sheet = sheet_name
    if 'db' in st.session_state: del st.session_state.db

if 'db' not in st.session_state:
    with st.spinner(f"🚀 Đang tải dữ liệu {sheet_name}..."):
        try:
            df_load = conn.read(worksheet=sheet_name, ttl="10s").fillna("")
            # Chuẩn hóa tên cột nếu từ Cloud về là tên cũ
            df_load = df_load.rename(columns={'CA Tháng Trước': 'Tồn cũ', 'Quỹ CA Tổng': 'Tổng CA'})
            if df_load.empty or len(df_load) < 5: raise ValueError
        except:
            # TỰ ĐỘNG LẤY TỒN CŨ TỪ THÁNG TRƯỚC NẾU LÀ THÁNG MỚI CHƯA CÓ DỮ LIỆU
            prev_month_date = working_date.replace(day=1) - timedelta(days=1)
            prev_sheet = prev_month_date.strftime("%m_%Y")
            ton_cu_dict = {}
            try:
                df_prev = conn.read(worksheet=prev_sheet, ttl="10s").fillna("")
                # Lấy cột Tổng CA (hoặc Quỹ CA Tổng) của tháng trước làm Tồn cũ tháng này
                col_name = 'Tổng CA' if 'Tổng CA' in df_prev.columns else 'Quỹ CA Tổng'
                ton_cu_dict = dict(zip(df_prev['Họ và Tên'], df_prev[col_name]))
            except: pass

            init_data = {'STT': range(1, len(NAMES_66) + 1), 'Họ và Tên': NAMES_66, 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Job Detail': '', 
                         'Tồn cũ': [ton_cu_dict.get(name, 0.0) for name in NAMES_66], 'Tổng CA': 0.0}
            for c in DATE_COLS: init_data[c] = ""
            df_load = pd.DataFrame(init_data)
        
        st.session_state.db = auto_engine(df_load, curr_month, curr_year, DATE_COLS)

# --- 8. TABS ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ"])

with t1:
    bc1, bc2 = st.columns([1, 1])
    with bc1:
        if st.button("📤 LƯU TẤT CẢ LÊN CLOUD", type="primary", use_container_width=True):
            with st.spinner("⏳ Đang đồng bộ..."):
                final_df = auto_engine(st.session_state.db, curr_month, curr_year, DATE_COLS)
                if save_to_cloud(sheet_name, final_df):
                    st.session_state.db = final_df
                    st.success("Đã đồng bộ thành công!")
                    time.sleep(0.5)
                    st.rerun()
    with bc2:
        buf = io.BytesIO()
        st.session_state.db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf.getvalue(), f"PVD_{sheet_name}.xlsx", use_container_width=True)

    @st.fragment
    def data_section():
        st.markdown("#### 🛠️ Cập nhật & Bảng điều động")
        
        with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH"):
            c1, c2 = st.columns([2, 1])
            f_staff = c1.multiselect("Nhân sự:", NAMES_66, key="quick_staff")
            f_date = c2.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, num_days_curr)), key="quick_date")
            r2_1, r2_2, r2_3, r2_4 = st.columns(4)
            f_status = r2_1.selectbox("Trạng thái:", ["Xóa trắng", "Đi Biển", "CA", "WS", "NP", "Ốm"], key="quick_status")
            f_val = r2_2.selectbox("Giàn:", st.session_state.GIANS, key="quick_rig") if f_status == "Đi Biển" else f_status
            f_co = r2_3.selectbox("Công ty:", ["Không đổi"] + COMPANIES, key="quick_co")
            f_ti = r2_4.selectbox("Chức danh:", ["Không đổi"] + TITLES, key="quick_title")
            
            if st.button("✅ ÁP DỤNG", use_container_width=True, key="btn_apply"):
                if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                    for person in f_staff:
                        idx_list = st.session_state.db.index[st.session_state.db['Họ và Tên'] == person].tolist()
                        if idx_list:
                            i = idx_list[0]
                            if f_co != "Không đổi": st.session_state.db.at[i, 'Công ty'] = f_co
                            if f_ti != "Không đổi": st.session_state.db.at[i, 'Chức danh'] = f_ti
                            start_d, end_d = f_date
                            curr_d = start_d
                            while curr_d <= end_d:
                                if curr_d.month == curr_month:
                                    col_t = [c for c in DATE_COLS if c.startswith(f"{curr_d.day:02d}/")]
                                    if col_t: st.session_state.db.at[i, col_t[0]] = "" if f_status == "Xóa trắng" else f_val
                                curr_d += timedelta(days=1)
                    st.session_state.db = auto_engine(st.session_state.db, curr_month, curr_year, DATE_COLS)
                    st.rerun()

        st.divider()
        
        # Cấu hình các cột hiển thị
        all_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail', 'Tồn cũ', 'Tổng CA'] + DATE_COLS
        edited_df = st.data_editor(
            st.session_state.db[all_cols],
            use_container_width=True,
            height=650,
            hide_index=True,
            key="editor_fragment",
            column_config={
                "Tổng CA": st.column_config.NumberColumn("Tổng CA", format="%.1f", disabled=True),
                "Tồn cũ": st.column_config.NumberColumn("Tồn cũ", format="%.1f"),
                "STT": st.column_config.Column(width="small", disabled=True)
            }
        )
        
        if not edited_df.equals(st.session_state.db[all_cols]):
            st.session_state.db.update(edited_df)
            st.session_state.db = auto_engine(st.session_state.db, curr_month, curr_year, DATE_COLS)

    data_section()

with t2:
    st.subheader(f"📊 Phân tích hoạt động cá nhân - Năm {curr_year}")
    sel_name = st.selectbox("🔍 Chọn nhân sự để xem báo cáo:", NAMES_66, key="report_staff")
    
    if st.button("🔄 TẢI/CẬP NHẬT DỮ LIỆU BIỂU ĐỒ", use_container_width=True):
        results = []
        with st.spinner("Đang quét dữ liệu 12 tháng..."):
            for m in range(1, 13):
                m_s = f"{m:02d}_{curr_year}"
                try:
                    df_m = conn.read(worksheet=m_s, ttl="5m").fillna("")
                    df_p = df_m[df_m['Họ và Tên'] == sel_name]
                    if not df_p.empty:
                        row_p = df_p.iloc[0]
                        for col in df_m.columns:
                            if "/" in col:
                                v = str(row_p[col]).strip().upper()
                                if v and v not in ["", "NAN", "NONE"]:
                                    cat = None
                                    if any(g.upper() in v for g in st.session_state.GIANS): cat = "Đi Biển"
                                    elif v == "CA": cat = "Nghỉ CA"
                                    elif v == "WS": cat = "Làm xưởng (WS)"
                                    elif v == "NP": cat = "Nghỉ phép (NP)"
                                    elif v == "ỐM": cat = "Nghỉ ốm"
                                    if cat:
                                        results.append({"Tháng": f"Tháng {m}", "Loại": cat, "Ngày": 1})
                except: continue
        
        if results:
            pdf = pd.DataFrame(results)
            summary = pdf.groupby(['Tháng', 'Loại']).size().reset_index(name='Số Ngày')
            fig = px.bar(summary, x="Tháng", y="Số Ngày", color="Loại", text="Số Ngày", 
                         barmode="stack", category_orders={"Tháng": [f"Tháng {i}" for i in range(1, 13)]},
                         template="plotly_dark",
                         color_discrete_map={"Đi Biển": "#00f2ff", "Nghỉ CA": "#ffaa00", "Làm xưởng (WS)": "#a6a6a6", "Nghỉ phép (NP)": "#00ff00", "Nghỉ ốm": "#ff4b4b"})
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("### 📝 Bảng tổng hợp số ngày chi tiết")
            stat_table = summary.pivot(index='Loại', columns='Tháng', values='Số Ngày').fillna(0).astype(int)
            for i in range(1, 13):
                if f"Tháng {i}" not in stat_table.columns: stat_table[f"Tháng {i}"] = 0
            stat_table = stat_table[[f"Tháng {i}" for i in range(1, 13)]]
            stat_table['TỔNG CẢ NĂM'] = stat_table.sum(axis=1)
            st.table(stat_table)
        else:
            st.info(f"Chưa có dữ liệu lịch sử cho nhân sự {sel_name}")
