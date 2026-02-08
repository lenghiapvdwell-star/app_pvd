import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import time
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

# CSS tối ưu hóa giao diện
st.markdown("""
    <style>
    .block-container {padding-top: 0.5rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; font-size: 45px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 3px 3px 6px #000 !important;
        font-family: 'Arial Black', sans-serif !important;
    }
    [data-testid="stMetricValue"] { font-size: 28px !important; font-weight: bold !important; }
    /* Giúp bảng editor không bị mất focus khi sửa */
    iframe { height: auto; }
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
    """Lưu dữ liệu ngầm lên Google Sheets"""
    df_clean = df.fillna("").replace(["nan", "NaN", "None"], "")
    try:
        conn.update(worksheet=worksheet_name, data=df_clean)
        st.cache_data.clear()
        return True
    except Exception:
        return False

# --- 4. DATA LOGIC & SIDEBAR ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

with st.sidebar:
    st.header("⚙️ QUẢN LÝ GIÀN")
    new_gian = st.text_input("Tên giàn mới:")
    if st.button("➕ Thêm Giàn", use_container_width=True):
        if new_gian and new_gian.strip().upper() not in st.session_state.GIANS:
            st.session_state.GIANS.append(new_gian.strip().upper())
            st.rerun()
    st.divider()
    del_gian = st.selectbox("Xóa giàn:", ["-- Chọn --"] + st.session_state.GIANS)
    if del_gian != "-- Chọn --" and st.button(f"🗑️ Xóa {del_gian}", use_container_width=True):
        st.session_state.GIANS.remove(del_gian)
        st.rerun()

COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]

_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    # Key giúp giữ ngày khi reload
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today(), key="main_date_input")

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b")

# --- 5. HÀM TỰ ĐỘNG ENGINE ---
def auto_engine(df):
    hols = [date(2026,1,1), date(2026,4,30), date(2026,5,1), date(2026,9,2),
            date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19)]
    now = datetime.now()
    today = now.date()
    num_days = calendar.monthrange(curr_year, curr_month)[1]
    date_cols = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
    
    df_calc = df.copy()
    data_changed = False
    
    for idx, row in df_calc.iterrows():
        accrued = 0.0
        last_val = ""
        for col in date_cols:
            d_num = int(col[:2])
            target_date = date(curr_year, curr_month, d_num)
            val = str(row.get(col, "")).strip()
            
            # AUTOFILL REAL-TIME (Lấy ngày trước điền cho ngày hiện tại)
            if not val and (target_date < today or (target_date == today and now.hour >= 7)):
                if last_val and any(g.upper() in last_val.upper() for g in st.session_state.GIANS):
                    val = last_val
                    df_calc.at[idx, col] = val
                    data_changed = True
            
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

# --- 6. LOAD & AUTO SYNC ---
if 'active_sheet' not in st.session_state or st.session_state.active_sheet != sheet_name:
    st.session_state.active_sheet = sheet_name
    if 'db' in st.session_state: del st.session_state.db

if 'db' not in st.session_state:
    prev_sheet = (working_date.replace(day=1) - timedelta(days=1)).strftime("%m_%Y")
    try:
        df_p = conn.read(worksheet=prev_sheet, ttl=0)
        b_map = dict(zip(df_p['Họ và Tên'], df_p['Quỹ CA Tổng']))
    except: b_map = {}

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
    
    df_auto, has_changes = auto_engine(df_l)
    if has_changes:
        save_to_cloud_silent(sheet_name, df_auto)
        st.toast("⚡ Robot: Đã tự động cập nhật dữ liệu ngày mới!", icon="🤖")
    st.session_state.db = df_auto

# --- 7. TABS ---
num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]

# Sử dụng session_state để giữ tab hiện tại khi reload
if "current_tab" not in st.session_state: st.session_state.current_tab = 0

t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ"])

with t1:
    bc1, bc2, bc3 = st.columns([1, 1, 1])
    with bc1:
        if st.button("📤 LƯU CLOUD", type="primary", use_container_width=True):
            df_final, _ = auto_engine(st.session_state.db)
            if save_to_cloud_silent(sheet_name, df_final):
                st.success("Đã lưu!"); time.sleep(0.5); st.rerun()
    with bc2:
        if st.button("🔄 LÀM MỚI (TẢI LẠI)", use_container_width=True):
            st.cache_data.clear(); del st.session_state.db; st.rerun()
    with bc3:
        buf = io.BytesIO()
        st.session_state.db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf.getvalue(), f"PVD_{sheet_name}.xlsx", use_container_width=True)

    with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH"):
        c1, c2 = st.columns([2, 1])
        f_staff = c1.multiselect("Nhân sự:", NAMES_66)
        f_date = c2.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, num_days)))
        r2_1, r2_2, r2_3, r2_4 = st.columns(4)
        f_status = r2_1.selectbox("Trạng thái:", ["Xóa trắng", "Đi Biển", "CA", "WS", "NP", "Ốm"])
        f_val = r2_2.selectbox("Giàn:", st.session_state.GIANS) if f_status == "Đi Biển" else f_status
        f_co = r2_3.selectbox("Cty:", ["Không đổi"] + COMPANIES); f_ti = r2_4.selectbox("Chức danh:", ["Không đổi"] + TITLES)
        if st.button("✅ ÁP DỤNG"):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                for person in f_staff:
                    idx_list = st.session_state.db.index[st.session_state.db['Họ và Tên'] == person].tolist()
                    if idx_list:
                        idx = idx_list[0]
                        for i in range((f_date[1] - f_date[0]).days + 1):
                            d = f_date[0] + timedelta(days=i)
                            if d.month == curr_month:
                                col_search = f"{d.day:02d}/"
                                col_n = [c for c in DATE_COLS if c.startswith(col_search)]
                                if col_n:
                                    st.session_state.db.at[idx, col_n[0]] = "" if f_status == "Xóa trắng" else f_val
                df_recalc, _ = auto_engine(st.session_state.db)
                st.session_state.db = df_recalc
                save_to_cloud_silent(sheet_name, df_recalc)
                st.rerun()

    # BẢNG DỮ LIỆU - NÂNG CẤP CHỐNG NHẢY TRANG
    ordered_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail', 'CA Tháng Trước', 'Quỹ CA Tổng'] + DATE_COLS
    
    # Sử dụng key động dựa trên sheet_name để reset bảng khi đổi tháng, nhưng giữ nguyên khi sửa dữ liệu
    ed_df = st.data_editor(
        st.session_state.db[ordered_cols].fillna(""), 
        use_container_width=True, 
        height=600, 
        hide_index=True,
        key=f"editor_{sheet_name}",
        column_config={
            "CA Tháng Trước": st.column_config.NumberColumn("Tồn cũ", format="%.1f"),
            "Quỹ CA Tổng": st.column_config.NumberColumn("Tổng ca", format="%.1f", disabled=True)
        }
    )
    
    # Logic kiểm tra thay đổi: Chỉ rerun khi người dùng ĐÃ nhập xong và nhấn ra ngoài
    if not ed_df.equals(st.session_state.db[ordered_cols].fillna("")):
        st.session_state.db.update(ed_df)
        df_recalc, _ = auto_engine(st.session_state.db)
        st.session_state.db = df_recalc
        # Lưu ngầm (không thông báo success gây reload mạnh)
        save_to_cloud_silent(sheet_name, df_recalc)
        st.toast("Đã tự động lưu thay đổi...", icon="☁️")
        # Không dùng st.rerun() ở đây để tránh bảng bị nhảy về đầu trang khi đang sửa dở

with t2:
    st.subheader(f"📊 Phân tích nhân sự năm {curr_year}")
    sel_name = st.selectbox("🔍 Chọn nhân sự xem biểu đồ:", NAMES_66)
    recs = []
    # Quét dữ liệu 12 tháng
    for m in range(1, 13):
        m_sheet = f"{m:02d}_{curr_year}"
        try:
            df_m = conn.read(worksheet=m_sheet, ttl=0)
            if not df_m.empty and sel_name in df_m['Họ và Tên'].values:
                row_p = df_m[df_m['Họ và Tên'] == sel_name].iloc[0]
                m_label = date(curr_year, m, 1).strftime("%b")
                for col in df_m.columns:
                    if "/" in col and m_label in col:
                        v = str(row_p[col]).strip().upper()
                        if v and v not in ["", "NAN", "NONE"]:
                            if any(g.upper() in v for g in st.session_state.GIANS): cat = "Đi Biển"
                            elif v == "CA": cat = "CA"
                            elif v == "WS": cat = "WS"
                            elif v == "NP": cat = "NP"
                            elif v == "ỐM": cat = "ỐM"
                            else: continue
                            recs.append({"Tháng": f"T{m}", "Loại": cat, "Ngày": 1})
        except: continue
        
    if recs:
        pdf = pd.DataFrame(recs)
        summary = pdf.groupby(['Tháng', 'Loại']).size().reset_index(name='Ngày')
        fig = px.bar(summary, x="Tháng", y="Ngày", color="Loại", text="Ngày", barmode="stack",
                     category_orders={"Tháng": [f"T{i}" for i in range(1, 13)]},
                     color_discrete_map={"Đi Biển":"#00f2ff","CA":"#ff4b4b","WS":"#ffd700","NP":"#00ff00","ỐM":"#ff00ff"},
                     template="plotly_dark")
        fig.update_traces(textposition='inside', textfont_size=14)
        fig.update_layout(xaxis_title="Tháng", yaxis_title="Tổng số ngày", height=500)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")
        st.markdown("### 📋 Tổng kết số ngày hoạt động trong năm")
        total_sum = pdf.groupby('Loại')['Ngày'].sum().to_dict()
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("🚢 Đi Biển", f"{total_sum.get('Đi Biển', 0)} day")
        m2.metric("🏠 Nghỉ CA", f"{total_sum.get('CA', 0)} day")
        m3.metric("🛠️ Làm WS", f"{total_sum.get('WS', 0)} day")
        m4.metric("🏖️ Nghỉ NP", f"{total_sum.get('NP', 0)} day")
        m5.metric("🏥 Nghỉ ỐM", f"{total_sum.get('ỐM', 0)} day")
    else:
        st.info(f"Không có dữ liệu cho nhân sự {sel_name} trong năm {curr_year}.")
