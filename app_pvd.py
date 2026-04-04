import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import time
import plotly.express as px

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="PVD MANAGEMENT SYSTEM", layout="wide")

st.markdown("""
    <style>
    .main-title {
        color: #007BFF; font-size: 35px; font-weight: bold; text-align: center;
        margin-bottom: 20px; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    .stButton>button {width: 100%; border-radius: 5px;}
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 2. DANH SÁCH 66 NHÂN SỰ CỨNG (DỰ PHÒNG) ---
NAMES_FIXED = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]

# --- 3. KẾT NỐI & LOAD DATA ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(wks, ttl=0):
    try:
        df = conn.read(worksheet=wks, ttl=ttl)
        return df if (df is not None and not df.empty) else pd.DataFrame()
    except: return pd.DataFrame()

def load_all_settings():
    # Lấy Giàn từ config
    df_c = get_data("config")
    rigs = [str(g).strip().upper() for g in df_c["GIANS"].dropna().tolist()] if not df_c.empty and "GIANS" in df_c.columns else ["PVD 8", "HK 11", "SDP", "PVD 11"]
    
    # Lấy Nhân sự (Ưu tiên nhansu hoặc 999s)
    names = []
    for s in ["nhansu", "999s"]:
        df_n = get_data(s)
        if not df_n.empty:
            col = "Họ và Tên" if "Họ và Tên" in df_n.columns else df_n.columns[1]
            names = [str(n).strip() for n in df_n[col].dropna().tolist() if str(n).strip()]
            if names: break
    
    if not names: names = NAMES_FIXED
    return rigs, names

if "GIANS" not in st.session_state:
    st.session_state.GIANS, st.session_state.NAMES = load_all_settings()

# --- 4. ENGINE TÍNH TOÁN (LOGIC CA) ---
def apply_pvd_logic(df, mm, yy, rigs):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    df_res = df.copy()
    date_cols = [c for c in df_res.columns if "/" in str(c)]
    
    for idx, row in df_res.iterrows():
        if not str(row.get('Họ và Tên', '')).strip(): continue
        acc = 0.0
        for col in date_cols:
            val = str(row.get(col, "")).strip().upper()
            if not val or val == "NAN": continue
            try:
                d_idx = int(col[:2])
                dt = date(yy, mm, d_idx)
                is_we = dt.weekday() >= 5
                is_ho = dt in hols
                if any(r.upper() in val for r in rigs):
                    if is_ho: acc += 2.0
                    elif is_we: acc += 1.0
                    else: acc += 0.5
                elif val == "CA":
                    if not is_we and not is_ho: acc -= 1.0
            except: continue
        t_cu = pd.to_numeric(row.get('Tồn cũ', 0), errors='coerce')
        df_res.at[idx, 'Tổng CA'] = round(float(t_cu if not pd.isna(t_cu) else 0.0) + acc, 1)
    return df_res

# --- 5. QUẢN LÝ THỜI GIAN & SHEET ---
_, mc, _ = st.columns([3, 2, 3])
with mc: wd = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_now = wd.strftime("%m_%Y")
mm, yy = wd.month, wd.year
days = calendar.monthrange(yy, mm)[1]
DATE_HEADERS = [f"{d:02d}/{wd.strftime('%b')} ({['T2','T3','T4','T5','T6','T7','CN'][date(yy,mm,d).weekday()]})" for d in range(1, days+1)]

df_main = get_data(sheet_now)

if df_main.empty:
    df_main = pd.DataFrame({'STT': range(1, len(st.session_state.NAMES)+1), 'Họ và Tên': st.session_state.NAMES, 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Tồn cũ': 0.0, 'Tổng CA': 0.0})
    for c in DATE_HEADERS: df_main[c] = ""
    # Lấy tồn cũ tháng trước
    prev_s = (wd.replace(day=1) - timedelta(days=1)).strftime("%m_%Y")
    df_p = get_data(prev_s)
    if not df_p.empty:
        df_main['Tồn cũ'] = df_main['Họ và Tên'].map(df_p.set_index('Họ và Tên')['Tổng CA']).fillna(0.0)

# --- 6. AUTO-FILL (CUỐI THÁNG TRƯỚC -> NGÀY 01 THÁNG SAU) ---
now = datetime.now()
if sheet_now == now.strftime("%m_%Y") and now.hour >= 6:
    updated = False
    if now.day == 1:
        col01 = [c for c in df_main.columns if c.startswith("01/")]
        if col01 and not any(str(x).strip() for x in df_main[col01[0]]):
            prev_s = (wd.replace(day=1) - timedelta(days=1)).strftime("%m_%Y")
            df_p = get_data(prev_s)
            if not df_p.empty:
                last_c = [c for c in df_p.columns if "/" in str(c)][-1]
                df_main[col01[0]] = df_main['Họ và Tên'].map(df_p.set_index('Họ và Tên')[last_c]).fillna("")
                updated = True
    elif now.day > 1:
        p_str, c_str = f"{(now.day-1):02d}/", f"{now.day:02d}/"
        cp = [c for c in df_main.columns if c.startswith(p_str)]
        cc = [c for c in df_main.columns if c.startswith(c_str)]
        if cp and cc and not any(str(x).strip() for x in df_main[cc[0]]):
            df_main[cc[0]] = df_main[cp[0]]
            updated = True
    if updated:
        df_main = apply_pvd_logic(df_main, mm, yy, st.session_state.GIANS)
        conn.update(worksheet=sheet_now, data=df_main)

current_df = apply_pvd_logic(df_main, mm, yy, st.session_state.GIANS)

# --- 7. GIAO DIỆN CHÍNH ---
tab1, tab2 = st.tabs(["🚀 ĐIỀU ĐỘNG CHI TIẾT", "📊 THỐNG KÊ"])

with tab1:
    # --- CÔNG CỤ NHẬP NHANH (ĐÃ KHÔI PHỤC) ---
    with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH (Quick Fill)"):
        c_n, c_d = st.columns([1, 1])
        sel_names = c_n.multiselect("Chọn nhân viên:", st.session_state.NAMES)
        date_range = c_d.date_input("Khoảng ngày áp dụng:", value=(date(yy, mm, 1), date(yy, mm, 1)))
        
        r1, r2, r3 = st.columns(3)
        mode = r1.selectbox("Loại hình:", ["Đi Biển", "Nghỉ CA", "Làm Xưởng (WS)", "Nghỉ phép/Ốm", "Xóa dữ liệu"])
        target_val = ""
        if mode == "Đi Biển": target_val = r2.selectbox("Chọn Giàn:", st.session_state.GIANS)
        elif mode == "Nghỉ CA": target_val = "CA"
        elif mode == "Làm Xưởng (WS)": target_val = "WS"
        elif mode == "Nghỉ phép/Ốm": target_val = "NP"
        
        if st.button("⚡ THỰC THI CẬP NHẬT"):
            if sel_names and len(date_range) == 2:
                s_d, e_d = date_range
                curr_ptr = s_d
                while curr_ptr <= e_d:
                    if curr_ptr.month == mm:
                        col_match = [c for c in current_df.columns if c.startswith(f"{curr_ptr.day:02d}/")]
                        if col_match:
                            for name in sel_names:
                                row_idx = current_df.index[current_df['Họ và Tên'] == name].tolist()
                                if row_idx: current_df.at[row_idx[0], col_match[0]] = target_val
                    curr_ptr += timedelta(days=1)
                st.success("Đã cập nhật tạm thời, nhấn 'LƯU' để hoàn tất!")

    # Nút chức năng
    btn1, btn2, btn3 = st.columns([2, 2, 4])
    if btn1.button("📤 LƯU LÊN GOOGLE SHEET", type="primary"):
        conn.update(worksheet=sheet_now, data=current_df)
        st.success("Dữ liệu đã được đồng bộ!")
        st.rerun()
    with btn3:
        out = io.BytesIO(); current_df.to_excel(out, index=False)
        st.download_button("📥 TẢI FILE EXCEL", out.getvalue(), f"PVD_{sheet_now}.xlsx")

    # Bảng chỉnh sửa chính
    cols_show = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Tồn cũ', 'Tổng CA'] + DATE_HEADERS
    edited_df = st.data_editor(current_df[cols_show], use_container_width=True, height=600, hide_index=True)
    
    if not edited_df.equals(current_df[cols_show]):
        for c in cols_show: current_df[c] = edited_df[c]
        current_df = apply_pvd_logic(current_df, mm, yy, st.session_state.GIANS)
        conn.update(worksheet=sheet_now, data=current_df)
        st.rerun()

with tab2:
    st.info("Tính năng thống kê đang hiển thị dữ liệu tháng hiện tại.")
    px_df = current_df[current_df['Họ và Tên'].isin(st.session_state.NAMES)]
    st.plotly_chart(px.bar(px_df, x='Họ và Tên', y='Tổng CA', title="Biểu đồ Tồn CA hiện tại"), use_container_width=True)

# --- 8. SIDEBAR QUẢN LÝ ---
with st.sidebar:
    st.header("⚙️ HỆ THỐNG")
    
    with st.expander("👤 NHÂN SỰ"):
        n_new = st.text_input("Thêm nhân sự:")
        if st.button("Thêm") and n_new:
            st.session_state.NAMES.append(n_new)
            df_ns = pd.DataFrame({"STT": range(1, len(st.session_state.NAMES)+1), "Họ và Tên": st.session_state.NAMES})
            conn.update(worksheet="nhansu", data=df_ns) # Cập nhật vào sheet nhansu
            st.rerun()
        
        n_del = st.selectbox("Xóa nhân sự:", st.session_state.NAMES)
        if st.button("Xóa"):
            st.session_state.NAMES.remove(n_del)
            df_ns = pd.DataFrame({"STT": range(1, len(st.session_state.NAMES)+1), "Họ và Tên": st.session_state.NAMES})
            conn.update(worksheet="nhansu", data=df_ns)
            st.rerun()

    with st.expander("🏗️ TÊN GIÀN"):
        g_new = st.text_input("Thêm Giàn:").upper()
        if st.button("Thêm Giàn") and g_new:
            st.session_state.GIANS.append(g_new)
            conn.update(worksheet="config", data=pd.DataFrame({"GIANS": st.session_state.GIANS}))
            st.rerun()
            
    if st.button("🔄 REFRESH DATA"):
        st.cache_data.clear()
        st.rerun()
