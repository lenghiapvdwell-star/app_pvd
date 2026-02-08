import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import time
import plotly.express as px

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; font-size: 45px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 3px 3px 6px #000 !important;
        font-family: 'Arial Black', sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER ---
c_logo, _ = st.columns([1, 4])
with c_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=180)
    else:
        st.markdown("<h2 style='color:#ff4b4b;'>🔴 PVD WELL</h2>", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. KẾT NỐI & CACHING ---
conn = st.connection("gsheets", type=GSheetsConnection)

def clean_dataframe(df):
    if df is None or df.empty: return pd.DataFrame()
    df = df.astype(object)
    df = df.fillna("")
    return df.replace(["nan", "NaN", "None", "nat", "None", "<na>"], "")

@st.cache_data(ttl=600) 
def load_sheet_data(s_name):
    try:
        time.sleep(0.1)
        df = conn.read(worksheet=s_name, ttl=0)
        return clean_dataframe(df)
    except:
        return pd.DataFrame()

def save_to_cloud_smart(worksheet_name, df):
    cols_fixed = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail', 'CA Tháng Trước', 'Quỹ CA Tổng']
    cols_days = [c for c in df.columns if "/" in c and "(" in c]
    cols_days.sort()
    final_order = [c for c in cols_fixed if c in df.columns] + [c for c in cols_days if c in df.columns]
    
    df_clean = clean_dataframe(df[final_order])
    try:
        conn.update(worksheet=worksheet_name, data=df_clean)
        st.cache_data.clear() 
        return True
    except Exception as e:
        st.error(f"Lỗi Cloud: {e}")
        return False

# --- 4. SIDEBAR QUẢN LÝ GIÀN ---
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

# --- 5. LOGIC CHỌN THÁNG & CHUYỂN DỒN TỒN ---
COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]

_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today(), key="main_date_picker")

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b")

prev_month_date = (working_date.replace(day=1) - timedelta(days=1))
prev_sheet = prev_month_date.strftime("%m_%Y")

if 'active_sheet' not in st.session_state or st.session_state.active_sheet != sheet_name:
    st.session_state.active_sheet = sheet_name
    df_curr = load_sheet_data(sheet_name)
    df_prev = load_sheet_data(prev_sheet)
    balance_map = dict(zip(df_prev['Họ và Tên'], df_prev['Quỹ CA Tổng'])) if not df_prev.empty else {}

    if not df_curr.empty:
        df_curr['CA Tháng Trước'] = df_curr['Họ và Tên'].map(balance_map).fillna(0.0).apply(pd.to_numeric, errors='coerce').fillna(0.0)
        st.session_state.db = df_curr
    else:
        st.session_state.db = pd.DataFrame({
            'STT': range(1, len(NAMES_66) + 1),
            'Họ và Tên': NAMES_66,
            'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Job Detail': '',
            'CA Tháng Trước': [float(balance_map.get(n, 0.0)) for n in NAMES_66],
            'Quỹ CA Tổng': [float(balance_map.get(n, 0.0)) for n in NAMES_66]
        })

num_days = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
for col in DATE_COLS:
    if col not in st.session_state.db.columns: st.session_state.db[col] = ""

# --- 6. HÀM TÍNH TOÁN (GIỮ NGUYÊN) ---
def recalculate_ca(df):
    hols = {date(2026,1,1), date(2026,4,30), date(2026,5,1), date(2026,9,2),
            date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19)}
    df_calc = df.copy()
    df_calc['CA Tháng Trước'] = pd.to_numeric(df_calc['CA Tháng Trước'], errors='coerce').fillna(0.0)
    gians_upper = [g.upper() for g in st.session_state.GIANS]
    
    def calc_row(row):
        accrued = 0.0
        for col in DATE_COLS:
            val = str(row.get(col, "")).strip().upper()
            if not val or val in ["WS", "NP", "ỐM"]: continue
            try:
                dt = date(curr_year, curr_month, int(col[:2]))
                is_we, is_ho = dt.weekday() >= 5, dt in hols
                if any(g in val for g in gians_upper): accrued += 2.0 if is_ho else (1.0 if is_we else 0.5)
                elif val == "CA":
                    if not is_we and not is_ho: accrued -= 1.0
            except: pass
        return row['CA Tháng Trước'] + accrued
    df_calc['Quỹ CA Tổng'] = df_calc.apply(calc_row, axis=1)
    return df_calc

# --- 7. GIAO DIỆN CHÍNH ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ"])

with t1:
    @st.fragment
    def render_data_section():
        bc1, bc2, bc3 = st.columns([1, 1, 1])
        with bc1:
            if st.button("📤 LƯU CLOUD", type="primary", use_container_width=True):
                st.session_state.db = recalculate_ca(st.session_state.db)
                if save_to_cloud_smart(sheet_name, st.session_state.db):
                    st.toast("Đã lưu thành công!", icon="✅")
        with bc2:
            if st.button("🔄 LÀM MỚI", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
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
                        idx = st.session_state.db.index[st.session_state.db['Họ và Tên'] == person][0]
                        for i in range((f_date[1] - f_date[0]).days + 1):
                            d = f_date[0] + timedelta(days=i)
                            if d.month == curr_month:
                                col_n = [c for c in DATE_COLS if c.startswith(f"{d.day:02d}/")][0]
                                st.session_state.db.at[idx, col_n] = "" if f_status == "Xóa trắng" else f_val
                    st.session_state.db = recalculate_ca(st.session_state.db)
                    st.rerun()

        cols_info = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail', 'CA Tháng Trước', 'Quỹ CA Tổng']
        cols_final = cols_info + [c for c in DATE_COLS if c in st.session_state.db.columns]
        
        display_df = st.session_state.db[cols_final].fillna("")
        ed_df = st.data_editor(
            display_df, 
            use_container_width=True, 
            height=600, 
            hide_index=True,
            column_config={
                "CA Tháng Trước": st.column_config.NumberColumn("🏠 Tồn cũ", format="%.1f"),
                "Quỹ CA Tổng": st.column_config.NumberColumn("📊 Tổng ca", format="%.1f", disabled=True),
            }
        )
        if not ed_df.equals(display_df):
            st.session_state.db.update(ed_df)
            st.session_state.db = recalculate_ca(st.session_state.db)
            st.rerun()
            
    render_data_section()

with t2:
    st.subheader(f"📊 Phân tích nhân sự {curr_year}")
    sel_name = st.selectbox("🔍 Chọn nhân sự:", NAMES_66)
    recs = []
    
    with st.spinner("Đang truy xuất dữ liệu..."):
        for m in range(1, 13):
            df_m = load_sheet_data(f"{m:02d}_{curr_year}")
            if not df_m.empty and sel_name in df_m['Họ và Tên'].values:
                row_p = df_m[df_m['Họ và Tên'] == sel_name].iloc[0]
                # Lấy tên viết tắt của tháng (ví dụ Jan, Feb...)
                m_label = date(curr_year, m, 1).strftime("%b")
                for col in df_m.columns:
                    # Kiểm tra cột có chứa ngày/tháng không (ví dụ "01/Jan")
                    if "/" in col and m_label in col:
                        v = str(row_p.get(col, "")).strip().upper()
                        if v and v not in ["", "NAN", "NONE"]:
                            # Phân loại trạng thái
                            if any(g.upper() in v for g in st.session_state.GIANS):
                                cat = "ĐI BIỂN"
                            elif v == "CA": cat = "NGHỈ CA"
                            elif v == "WS": cat = "LÀM WS"
                            elif v == "NP": cat = "NGHỈ PHÉP"
                            elif v == "ỐM": cat = "NGHỈ ỐM"
                            else: continue
                            
                            recs.append({"Tháng": f"T{m}", "Loại": cat, "Ngày": 1})
    
    if recs:
        pdf = pd.DataFrame(recs)
        # Nhóm dữ liệu để vẽ biểu đồ
        summary = pdf.groupby(['Tháng', 'Loại']).size().reset_index(name='Số ngày')
        
        # Sắp xếp thứ tự tháng
        month_order = [f"T{i}" for i in range(1, 13)]
        
        # Vẽ biểu đồ với Plotly
        fig = px.bar(
            summary, 
            x="Tháng", 
            y="Số ngày", 
            color="Loại", 
            text="Số ngày", # Hiển thị số ngày trên đồ thị màu đó
            barmode="stack",
            category_orders={"Tháng": month_order},
            color_discrete_map={
                "ĐI BIỂN": "#00f2ff", # Xanh Neon
                "NGHỈ CA": "#ff4b4b", # Đỏ
                "LÀM WS": "#ffd700",  # Vàng
                "NGHỈ PHÉP": "#00ff00", # Xanh lá
                "NGHỈ ỐM": "#ff00ff"   # Tím
            }
        )
        
        # Tinh chỉnh hiển thị số trên cột
        fig.update_traces(textposition='inside', textfont_size=14)
        fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide', xaxis_title="Tháng trong năm", yaxis_title="Tổng số ngày")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # BẢNG TỔNG HỢP SỐ LIỆU DƯỚI ĐỒ THỊ
        st.markdown("#### 📑 Bảng tổng hợp chi tiết theo loại hình:")
        
        # Tạo bảng ngang để dễ nhìn
        total_summary = pdf.groupby('Loại')['Ngày'].sum().reset_index()
        total_summary.columns = ['Hạng mục', 'Tổng số ngày trong năm']
        
        # Hiển thị bảng đẹp hơn với style
        st.dataframe(total_summary, use_container_width=True, hide_index=True)
    else:
        st.info(f"Chưa có dữ liệu hoạt động của {sel_name} trong năm {curr_year}")
