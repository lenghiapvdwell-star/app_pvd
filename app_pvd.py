import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import time

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 0.5rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; font-size: 40px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 2px 2px 4px #000 !important;
        margin-bottom: 15px;
    }
    .stButton>button {border-radius: 5px; height: 3em;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER & LOGO ---
c_logo, _ = st.columns([1, 4])
with c_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=180)
    else:
        st.markdown("<h2 style='color:red;'>🔴 PVD WELL</h2>", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. KẾT NỐI & DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_gians():
    try:
        df_config = conn.read(worksheet="CONFIG", ttl=1)
        return df_config.iloc[:, 0].dropna().astype(str).tolist()
    except:
        return ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

if "gians_list" not in st.session_state:
    st.session_state.gians_list = load_gians()

# --- 4. CHỌN THÁNG ---
_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b")

# --- 5. HÀM LOGIC QUAN TRỌNG (AUTOFILL & TÍNH CA) ---
def apply_pro_logic(df):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,2,21), date(2026,4,25), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    num_days = calendar.monthrange(curr_year, curr_month)[1]
    date_cols = [f"{d:02d}/{month_abbr}" for d in range(1, num_days+1)]
    
    df_new = df.copy()
    for idx, row in df_new.iterrows():
        if not str(row.get('Họ và Tên', '')).strip(): continue
        
        # A. Autofill: Lấy trạng thái ngày trước điền cho ngày sau nếu trống
        last_val = ""
        for col in date_cols:
            curr_val = str(df_new.at[idx, col]).strip()
            if curr_val == "" or curr_val.upper() in ["NAN", "NONE"]:
                df_new.at[idx, col] = last_val
            else:
                last_val = curr_val

        # B. Tính toán Quỹ CA dựa trên kết quả đã Autofill
        acc = 0.0
        for col in date_cols:
            v = str(df_new.at[idx, col]).strip().upper()
            if not v or v in ["WS", "NP", "ỐM"]: continue
            try:
                dt = date(curr_year, curr_month, int(col[:2]))
                is_offshore = any(g.upper() in v for g in st.session_state.gians_list)
                if is_offshore:
                    if dt in hols: acc += 2.0
                    elif dt.weekday() >= 5: acc += 1.0
                    else: acc += 0.5
                elif v == "CA":
                    if dt.weekday() < 5 and dt not in hols: acc -= -1.0 # Trừ 1 ngày CA
                    # Sửa lại logic chuẩn: Nghỉ CA ngày thường thì trừ 1
                    if dt.weekday() < 5 and dt not in hols: acc -= 1.0
            except: continue
        df_new.at[idx, 'Quỹ CA Tổng'] = acc
    return df_new

# --- 6. KHỞI TẠO SESSION STATE ---
if 'db' not in st.session_state or st.session_state.get('active_sheet') != sheet_name:
    try:
        st.session_state.db = conn.read(worksheet=sheet_name, ttl=0)
    except:
        st.session_state.db = pd.DataFrame({'STT': range(1, 61), 'Họ và Tên': [""]*60})
    st.session_state.active_sheet = sheet_name
    st.session_state.editor_key = str(time.time())

# --- 7. TABS CÔNG CỤ (GIỮ NGUYÊN) ---
with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH & QUẢN LÝ GIÀN KHOAN"):
    tab_bulk, tab_rig = st.tabs(["⚡ Đổ dữ liệu nhanh", "⚓ Quản lý danh sách giàn"])
    
    with tab_bulk:
        col_a, col_b, col_c = st.columns(3)
        f_staff = col_a.multiselect("Chọn nhân sự:", st.session_state.db['Họ và Tên'].dropna().unique().tolist())
        # Sửa lỗi chọn ngày để không bị crash
        try:
            f_date = col_b.date_input("Thời gian:", value=(date(curr_year, curr_month, 1), date(curr_year, curr_month, 2)))
        except:
            f_date = date(curr_year, curr_month, 1)

        f_status = col_c.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm"])
        f_val = col_c.selectbox("Chọn giàn:", st.session_state.gians_list) if f_status == "Đi Biển" else f_status
        
        if st.button("🚀 ÁP DỤNG LÊN BẢNG"):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                for name in f_staff:
                    idx = st.session_state.db.index[st.session_state.db['Họ và Tên'] == name][0]
                    for i in range((f_date[1] - f_date[0]).days + 1):
                        d = f_date[0] + timedelta(days=i)
                        col_n = f"{d.day:02d}/{month_abbr}"
                        if col_n in st.session_state.db.columns:
                            st.session_state.db.at[idx, col_n] = f_val
                st.session_state.editor_key = str(time.time()) # Làm mới bảng
                st.rerun()

    with tab_rig:
        ra, rb = st.columns([3, 1])
        new_rig_name = ra.text_input("Tên giàn mới:")
        if rb.button("➕ Thêm"):
            if new_rig_name:
                st.session_state.gians_list.append(new_rig_name.upper())
                conn.update(worksheet="CONFIG", data=pd.DataFrame({"Giàn": st.session_state.gians_list}))
                st.success(f"Đã thêm {new_rig_name}")
                st.rerun()
        
        st.markdown("---")
        # CHỨC NĂNG XÓA GIÀN
        col_del_1, col_del_2 = st.columns([3, 1])
        rig_to_del = col_del_1.selectbox("Chọn giàn cần xóa:", ["-- Chọn --"] + st.session_state.gians_list)
        if col_del_2.button("🗑️ Xóa Giàn"):
            if rig_to_del != "-- Chọn --":
                st.session_state.gians_list.remove(rig_to_del)
                conn.update(worksheet="CONFIG", data=pd.DataFrame({"Giàn": st.session_state.gians_list}))
                st.toast(f"Đã xóa giàn {rig_to_del}")
                time.sleep(1)
                st.rerun()

# --- 8. GIAO DIỆN ĐIỀU KHIỂN CHÍNH ---
c1, c2, c3 = st.columns([2.5, 2, 4])
if c1.button("💾 LƯU & ĐỒNG BỘ CLOUD", type="primary", use_container_width=True):
    with st.status("🔄 Đang xử lý Autofill & Lưu...", expanded=False):
        # Trước khi lưu, áp dụng logic autofill cuối cùng
        final_df = apply_pro_logic(st.session_state.db)
        conn.update(worksheet=sheet_name, data=final_df)
        st.session_state.db = final_df
        st.success("Đã đồng bộ thành công!")
        st.rerun()

buf = io.BytesIO()
st.session_state.db.to_excel(buf, index=False)
c2.download_button("📥 XUẤT EXCEL", buf, f"PVD_{sheet_name}.xlsx", use_container_width=True)

# --- 9. BẢNG NHẬP LIỆU REAL-TIME ---
st.markdown("---")
st.info("💡 **Gợi ý:** Nhập trạng thái cho 1 ngày, các ngày trống phía sau sẽ tự nhảy theo. Cột Quỹ CA tự tính.")

# Áp dụng logic hiển thị nhưng vẫn cho phép chỉnh sửa
display_df = apply_pro_logic(st.session_state.db)

edited_df = st.data_editor(
    display_df,
    use_container_width=True,
    height=600,
    hide_index=True,
    key=st.session_state.editor_key
)

# Cập nhật ngược lại session_state khi có thay đổi
if not edited_df.equals(display_df):
    st.session_state.db = edited_df
    # Không dùng rerun ở đây để tránh mất focus khi đang gõ
