import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import time
import plotly.express as px

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; font-size: 35px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 2px 2px 4px #000 !important;
        font-family: 'Arial', sans-serif;
    }
    .stAlert {margin-top: 1rem;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. KẾT NỐI & HÀM LƯU TRỮ TỐI ƯU ---
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_save(worksheet_name, df):
    """Lưu dữ liệu với cơ chế chống nghẽn mạng"""
    with st.status(f" đang đồng bộ dữ liệu lên Cloud...", expanded=False) as status:
        try:
            df_to_save = df[df['Họ và Tên'].str.strip() != ""].copy()
            # Ép kiểu số để tránh lỗi định dạng Sheets
            for col in ['Tồn cũ', 'Tổng CA']:
                if col in df_to_save.columns:
                    df_to_save[col] = pd.to_numeric(df_to_save[col], errors='coerce').fillna(0.0)
            
            df_clean = df_to_save.fillna("").replace(["nan", "NaN", "None"], "")
            
            # Gửi dữ liệu
            conn.update(worksheet=worksheet_name, data=df_clean)
            st.cache_data.clear() # Làm mới bộ nhớ đệm sau khi lưu
            status.update(label="✅ Đã lưu thành công lên Google Sheets!", state="complete")
            return True
        except Exception as e:
            status.update(label=f"❌ Lỗi: {e}. Đang thử lại...", state="error")
            time.sleep(2)
            return False

# --- 3. ENGINE TÍNH TOÁN & AUTOFILL TỰ ĐỘNG ---
def apply_logic(df, curr_m, curr_y, DATE_COLS):
    """Tính toán CA và Autofill tự động hoàn toàn"""
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    now = datetime.now()
    today = now.date()
    df_calc = df.copy()

    for idx, row in df_calc.iterrows():
        if not str(row.get('Họ và Tên', '')).strip(): continue
        accrued = 0.0
        last_val = ""
        
        for col in DATE_COLS:
            d_num = int(col[:2])
            target_date = date(curr_y, curr_m, d_num)
            val = str(row.get(col, "")).strip()
            
            # --- AUTOFILL TỰ ĐỘNG (Sau 6h sáng hoặc ngày cũ) ---
            if (not val or val == "" or val.lower() == "nan"):
                if target_date < today or (target_date == today and now.hour >= 6):
                    if last_val != "":
                        lv_up = last_val.upper()
                        # Chỉ fill nếu ngày trước đó đang làm việc hoặc nghỉ chế độ
                        if any(g.upper() in lv_up for g in st.session_state.GIANS) or lv_up in ["CA", "WS", "NP", "ỐM"]:
                            val = last_val
                            df_calc.at[idx, col] = val
            
            if val and val.lower() != "nan": last_val = val
            
            # --- TÍNH TOÁN QUỸ CA ---
            v_up = val.upper()
            if v_up:
                is_we = target_date.weekday() >= 5
                is_ho = target_date in hols
                if any(g.upper() in v_up for g in st.session_state.GIANS): # Đi biển
                    if is_ho: accrued += 2.0
                    elif is_we: accrued += 1.0
                    else: accrued += 0.5
                elif v_up == "CA": # Nghỉ CA
                    if not is_we and not is_ho: accrued -= 1.0
        
        ton_cu = pd.to_numeric(row.get('Tồn cũ', 0), errors='coerce')
        df_calc.at[idx, 'Tổng CA'] = round(float(ton_cu if not pd.isna(ton_cu) else 0.0) + accrued, 1)
    
    return df_calc

# --- 4. KHỞI TẠO DỮ LIỆU ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# Sidebar quản lý giàn
with st.sidebar:
    st.header("⚙️ QUẢN LÝ DANH MỤC")
    new_g = st.text_input("Tên giàn mới:").upper().strip()
    if st.button("➕ THÊM GIÀN"):
        if new_g and new_g not in st.session_state.GIANS:
            st.session_state.GIANS.append(new_g); st.rerun()
    
    del_g = st.selectbox("Xóa giàn:", st.session_state.GIANS)
    if st.button("❌ XÓA GIÀN"):
        st.session_state.GIANS.remove(del_g); st.rerun()

# Chọn ngày tháng làm việc
_, mc, _ = st.columns([3, 2, 3])
with mc:
    wd = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_name = wd.strftime("%m_%Y")
curr_m, curr_y = wd.month, wd.year
days_in_m = calendar.monthrange(curr_y, curr_m)[1]
month_name = wd.strftime('%b')
DATE_COLS = [f"{d:02d}/{month_name} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_y,curr_m,d).weekday()]})" for d in range(1, days_in_m+1)]

# Tải dữ liệu và áp dụng Autofill ngay lập tức
if 'db' not in st.session_state or st.session_state.get('active_sheet') != sheet_name:
    try:
        df_raw = conn.read(worksheet=sheet_name, ttl=0).fillna("")
        if 'Quỹ CA Tổng' in df_raw.columns: df_raw = df_raw.rename(columns={'Quỹ CA Tổng': 'Tổng CA'})
        if 'CA Tháng Trước' in df_raw.columns: df_raw = df_raw.rename(columns={'CA Tháng Trước': 'Tồn cũ'})
    except:
        df_raw = pd.DataFrame({'STT': range(1,67), 'Họ và Tên': [f"Nhân viên {i}" for i in range(1,67)], 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Tồn cũ': 0.0, 'Tổng CA': 0.0})
        for c in DATE_COLS: df_raw[c] = ""
    
    # Tự động chạy logic Autofill & Tính toán khi vừa mở bảng
    st.session_state.db = apply_logic(df_raw, curr_m, curr_y, DATE_COLS)
    st.session_state.active_sheet = sheet_name

# --- 5. GIAO DIỆN TABS ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG & NHẬP LIỆU", "📊 BIỂU ĐỒ THỐNG KÊ"])

with t1:
    c1, c2, c3 = st.columns([2, 2, 4])
    if c1.button("📤 LƯU CLOUD (ĐỒNG BỘ)", type="primary", use_container_width=True):
        # Tính toán lại lần cuối trước khi lưu
        st.session_state.db = apply_logic(st.session_state.db, curr_m, curr_y, DATE_COLS)
        if safe_save(sheet_name, st.session_state.db):
            st.rerun()
            
    with c3:
        # Xuất Excel
        buf = io.BytesIO()
        st.session_state.db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf.getvalue(), f"PVD_Report_{sheet_name}.xlsx", use_container_width=True)

    # Công cụ nhập nhanh
    with st.expander("🛠️ CÔNG CỤ NHẬP NHANH (Chọn nhiều người cùng lúc)"):
        names = [n for n in st.session_state.db['Họ và Tên'].tolist() if n.strip()]
        sel_names = st.multiselect("Nhân sự:", names)
        d_range = st.date_input("Thời gian:", value=(date(curr_y, curr_m, 1), date(curr_y, curr_m, days_in_m)))
        r1, r2 = st.columns(2)
        stt_quick = r1.selectbox("Trạng thái:", ["Xóa trắng", "Đi Biển", "CA", "WS", "NP", "Ốm"])
        rig_quick = r2.selectbox("Chọn Giàn:", st.session_state.GIANS) if stt_quick == "Đi Biển" else stt_quick
        
        if st.button("✅ ÁP DỤNG NHANH"):
            if sel_names and len(d_range) == 2:
                for name in sel_names:
                    idx = st.session_state.db.index[st.session_state.db['Họ và Tên'] == name].tolist()[0]
                    curr_d = d_range[0]
                    while curr_d <= d_range[1]:
                        if curr_d.month == curr_m:
                            c_name = [c for c in DATE_COLS if c.startswith(f"{curr_d.day:02d}/")][0]
                            st.session_state.db.at[idx, c_name] = "" if stt_quick == "Xóa trắng" else rig_quick
                        curr_d += timedelta(days=1)
                # Sau khi áp dụng, tự động tính toán lại
                st.session_state.db = apply_logic(st.session_state.db, curr_m, curr_y, DATE_COLS)
                st.rerun()

    # Bảng dữ liệu chính
    st.info("💡 Hệ thống tự động điền (Autofill) sau 6h sáng mỗi ngày. Bạn có thể sửa trực tiếp trên bảng.")
    all_view_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Tồn cũ', 'Tổng CA'] + DATE_COLS
    edited_df = st.data_editor(
        st.session_state.db[all_view_cols],
        use_container_width=True,
        height=600,
        hide_index=True,
        key="main_data_editor",
        column_config={
            "Tổng CA": st.column_config.NumberColumn(disabled=True, format="%.1f"),
            "Tồn cũ": st.column_config.NumberColumn(format="%.1f"),
            "STT": st.column_config.Column(width="small", disabled=True)
        }
    )
    # Lưu thay đổi vào session (Không gọi rerun ở đây để tránh giật bảng)
    st.session_state.db.update(edited_df)

with t2:
    st.subheader(f"📊 Phân tích nhân sự - Năm {curr_y}")
    chart_names = [n for n in st.session_state.db['Họ và Tên'].tolist() if n.strip()]
    sel_chart_name = st.selectbox("🔍 Chọn nhân sự xem biểu đồ:", chart_names)
    
    if sel_chart_name:
        yearly_data = []
        # Quét dữ liệu 12 tháng (Dựa trên cache hoặc Sheets)
        for m in range(1, 13):
            m_sheet = f"{m:02d}_{curr_y}"
            try:
                # Dùng cache_data để việc quét 12 tháng cực nhanh
                m_df = conn.read(worksheet=m_sheet, ttl=300).fillna("")
                p_df = m_df[m_df['Họ và Tên'] == sel_chart_name]
                if not p_df.empty:
                    row = p_df.iloc[0]
                    for col in m_df.columns:
                        if "/" in col:
                            v = str(row[col]).strip().upper()
                            if v:
                                cat = None
                                if any(g.upper() in v for g in st.session_state.GIANS): cat = "Đi Biển"
                                elif v == "CA": cat = "Nghỉ CA"
                                elif v == "WS": cat = "Làm xưởng (WS)"
                                elif v in ["NP", "ỐM"]: cat = "Nghỉ phép/Ốm"
                                if cat: yearly_data.append({"Tháng": f"Tháng {m}", "Loại": cat, "Số Ngày": 1})
            except: continue
        
        if yearly_data:
            df_chart = pd.DataFrame(yearly_data)
            summary = df_chart.groupby(['Tháng', 'Loại']).sum().reset_index()
            
            # Biểu đồ cột chồng
            fig = px.bar(summary, x="Tháng", y="Số Ngày", color="Loại", 
                         text="Số Ngày", barmode="stack", template="plotly_dark",
                         color_discrete_map={"Đi Biển": "#00f2ff", "Nghỉ CA": "#ffaa00", "Làm xưởng (WS)": "#a6a6a6", "Nghỉ phép/Ốm": "#00ff00"})
            st.plotly_chart(fig, use_container_width=True)
            
            # Bảng thống kê chi tiết dưới biểu đồ
            st.markdown("### 📋 Bảng thống kê chi tiết")
            stat_table = summary.pivot(index='Loại', columns='Tháng', values='Số Ngày').fillna(0).astype(int)
            stat_table['TỔNG CỘNG'] = stat_table.sum(axis=1)
            st.table(stat_table)
        else:
            st.warning(f"Chưa có dữ liệu lưu trên Cloud cho {sel_chart_name} trong năm {curr_y}")
