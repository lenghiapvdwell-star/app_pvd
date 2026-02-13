import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import time
import plotly.express as px

# --- 1. CẤU HÌNH ---
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

# --- 3. KẾT NỐI ---
conn = st.connection("gsheets", type=GSheetsConnection)

def save_to_cloud_silent(worksheet_name, df):
    # Dọn dẹp dữ liệu trước khi lưu
    df_clean = df.fillna("").replace(["nan", "NaN", "None", "nan"], "")
    try:
        conn.update(worksheet=worksheet_name, data=df_clean)
        st.cache_data.clear() # Xóa cache để lần sau load sẽ lấy dữ liệu mới nhất
        return True
    except Exception as e:
        st.error(f"Lỗi lưu Cloud: {e}")
        return False

# --- 4. DANH MỤC CỐ ĐỊNH ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]

with st.sidebar:
    st.header("⚙️ QUẢN LÝ GIÀN")
    new_gian = st.text_input("Tên giàn mới:")
    if st.button("➕ Thêm Giàn", use_container_width=True):
        if new_gian and new_gian.strip().upper() not in st.session_state.GIANS:
            st.session_state.GIANS.append(new_gian.strip().upper())
            st.rerun()

_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b")
num_days_curr = calendar.monthrange(curr_year, curr_month)[1]
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days_curr+1)]

# --- 5. ENGINE TỰ ĐỘNG (LUẬT CA) ---
def auto_engine(df):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    now = datetime.now()
    today = now.date()
    df_calc = df.copy()
    data_changed = False
    
    for idx, row in df_calc.iterrows():
        accrued = 0.0
        current_last_val = ""
        for col in DATE_COLS:
            if col not in df_calc.columns: continue
            d_num = int(col[:2])
            target_date = date(curr_year, curr_month, d_num)
            val = str(row.get(col, "")).strip()
            
            # Auto-fill Logic chuẩn
            if (not val or val == "" or val.lower() == "nan") and (target_date < today or (target_date == today and now.hour >= 6)):
                if current_last_val != "":
                    lv_up = current_last_val.upper()
                    if any(g.upper() in lv_up for g in st.session_state.GIANS) or lv_up in ["CA", "WS"]:
                        val = current_last_val
                        df_calc.at[idx, col] = val
                        data_changed = True
            
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
        
        ton_cu = float(row.get('CA Tháng Trước', 0)) if row.get('CA Tháng Trước') else 0.0
        df_calc.at[idx, 'Quỹ CA Tổng'] = round(ton_cu + accrued, 1)
        
    return df_calc, data_changed

# --- 6. LOAD DỮ LIỆU ---
if 'active_sheet' not in st.session_state or st.session_state.active_sheet != sheet_name:
    st.session_state.active_sheet = sheet_name
    if 'db' in st.session_state: del st.session_state.db

if 'db' not in st.session_state:
    with st.spinner(f"🚀 Đang tải dữ liệu {sheet_name}..."):
        try:
            df_l = conn.read(worksheet=sheet_name, ttl=0).fillna("")
            if df_l.empty or len(df_l) < 5: raise ValueError
        except:
            # Tạo mới nếu chưa có
            init_data = {'STT': range(1, len(NAMES_66) + 1), 'Họ và Tên': NAMES_66, 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Job Detail': '', 'CA Tháng Trước': 0.0, 'Quỹ CA Tổng': 0.0}
            for c in DATE_COLS: init_data[c] = ""
            df_l = pd.DataFrame(init_data)

        df_auto, has_updates = auto_engine(df_l)
        if has_updates: save_to_cloud_silent(sheet_name, df_auto)
        st.session_state.db = df_auto

# --- 7. TABS ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 BIỂU ĐỒ"])

with t1:
    # Thanh điều khiển
    bc1, bc2, bc3 = st.columns([1, 1, 1])
    with bc2:
        if st.button("🔄 LÀM MỚI (TẢI LẠI TỪ SHEETS)", use_container_width=True):
            st.cache_data.clear()
            if 'db' in st.session_state: del st.session_state.db
            st.rerun()
    with bc3:
        buf = io.BytesIO()
        st.session_state.db.to_excel(buf, index=False)
        st.download_button("📥 XUẤT EXCEL", buf.getvalue(), f"PVD_{sheet_name}.xlsx", use_container_width=True)

    # Bảng chỉnh sửa chính
    st.info("💡 Bạn có thể sửa trực tiếp vào các ô dưới đây, sau đó nhấn nút 'LƯU TẤT CẢ LÊN GOOGLE SHEETS'.")
    
    all_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Job Detail', 'CA Tháng Trước', 'Quỹ CA Tổng'] + DATE_COLS
    # Đảm bảo các cột hiển thị đúng
    display_df = st.session_state.db.reindex(columns=all_cols).fillna("")

    # Sử dụng key để quản lý trạng thái editor
    ed_df = st.data_editor(
        display_df, 
        use_container_width=True, 
        height=650, 
        hide_index=True,
        column_config={
            "Quỹ CA Tổng": st.column_config.NumberColumn("Số dư Quỹ", format="%.1f", disabled=True),
            "CA Tháng Trước": st.column_config.NumberColumn("Tồn cũ", format="%.1f"),
            "STT": st.column_config.Column(width="small", disabled=True)
        }
    )

    # Nút lưu duy nhất và quan trọng nhất
    if st.button("💾 LƯU TẤT CẢ LÊN GOOGLE SHEETS", type="primary", use_container_width=True):
        with st.spinner("Đang tính toán lại và đồng bộ..."):
            # Bước 1: Cập nhật dữ liệu từ Editor vào Session State
            st.session_state.db = ed_df
            # Bước 2: Chạy lại Engine để tính toán Quỹ CA dựa trên dữ liệu vừa sửa
            df_recalc, _ = auto_engine(st.session_state.db)
            # Bước 3: Lưu lên Google Sheets
            if save_to_cloud_silent(sheet_name, df_recalc):
                st.session_state.db = df_recalc
                st.toast("✅ Đã lưu thành công!", icon="🚀")
                time.sleep(1)
                st.rerun()

    # Phần xác nhận ký tên
    st.markdown("""
        <div style="margin-top: 50px; text-align: center; font-weight: bold;">
            <table style="width:100%; border:none; color: white;">
                <tr>
                    <td style="width:33%;">NGƯỜI LẬP BIỂU</td>
                    <td style="width:33%;">QUẢN LÝ TRỰC TIẾP</td>
                    <td style="width:33%;">BAN GIÁM ĐỐC</td>
                </tr>
                <tr style="height:80px;"><td></td><td></td><td></td></tr>
            </table>
        </div>
    """, unsafe_allow_html=True)

with t2:
    st.subheader(f"📊 Phân tích hoạt động cá nhân - Năm {curr_year}")
    sel_name = st.selectbox("🔍 Chọn nhân sự:", NAMES_66)
    
    # Hàm lấy dữ liệu cả năm
    results = []
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
                        if v and v not in ["", "NAN"]:
                            cat = None
                            if any(g.upper() in v for g in st.session_state.GIANS): cat = "Đi Biển"
                            elif v == "CA": cat = "CA"
                            elif v == "WS": cat = "WS"
                            elif v == "NP": cat = "NP"
                            if cat: results.append({"Tháng": f"T{m}", "Loại": cat, "Ngày": 1})
        except: continue
    
    if results:
        pdf = pd.DataFrame(results)
        summary = pdf.groupby(['Tháng', 'Loại']).size().reset_index(name='Ngày')
        fig = px.bar(summary, x="Tháng", y="Ngày", color="Loại", barmode="stack",
                     category_orders={"Tháng": [f"T{i}" for i in range(1, 13)]},
                     template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Chưa có dữ liệu cho nhân sự này.")
