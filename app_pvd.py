import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import time

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; font-size: 35px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 2px 2px 4px #000 !important;
    }
    .stButton>button {border-radius: 5px; height: 3em;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER & LOGO ---
c_logo, _ = st.columns([1, 4])
with c_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=160)
    else:
        st.markdown("<h2 style='color:red;'>🔴 PVD WELL</h2>", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. DỮ LIỆU CỐ ĐỊNH ---
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong"]
HOLIDAYS_2026 = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,2,21), date(2026,4,25), date(2026,4,30), date(2026,5,1), date(2026,9,2)]

# --- 4. KẾT NỐI ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_gians():
    try:
        df_config = conn.read(worksheet="CONFIG", ttl=600)
        return df_config.iloc[:, 0].dropna().astype(str).tolist()
    except:
        return ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

if "gians_list" not in st.session_state:
    st.session_state.gians_list = load_gians()

# --- 5. CHỌN THÁNG ---
_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
month_abbr = working_date.strftime("%b")

# --- 6. HÀM XỬ LÝ AUTOFILL & TÍNH CA TOÀN DIỆN ---
def apply_pvd_full_logic(df):
    num_days = calendar.monthrange(curr_year, curr_month)[1]
    # Tạo danh sách tiêu đề cột ngày
    date_cols = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days+1)]
    
    df_new = df.copy()
    
    for idx, row in df_new.iterrows():
        # 1. Logic Lan truyền dữ liệu (Autofill Real-time)
        last_val = ""
        for col in date_cols:
            if col not in df_new.columns: df_new[col] = ""
            current_val = str(df_new.at[idx, col]).strip()
            
            if current_val == "" or current_val.upper() in ["NAN", "NONE"]:
                df_new.at[idx, col] = last_val # Lấy lại giá trị ngày trước đó
            else:
                last_val = current_val # Cập nhật giá trị mốc mới để lan truyền tiếp
        
        # 2. Logic Tính toán Quỹ CA
        acc_month = 0.0
        for col in date_cols:
            v = str(df_new.at[idx, col]).strip().upper()
            if not v or v in ["WS", "NP", "ỐM"]: continue
            
            try:
                day_int = int(col[:2])
                dt = date(curr_year, curr_month, day_int)
                is_weekend = dt.weekday() >= 5
                is_holiday = dt in HOLIDAYS_2026
                is_offshore = any(g.upper() in v for g in st.session_state.gians_list)
                
                if is_offshore:
                    if is_holiday: acc_month += 2.0
                    elif is_weekend: acc_month += 1.0
                    else: acc_month += 0.5
                elif v == "CA":
                    if not is_weekend and not is_holiday:
                        acc_month -= 1.0 # Chỉ trừ ngày thường
            except: continue
        
        # 3. Cộng dồn với tháng trước
        old_val = pd.to_numeric(df_new.at[idx, 'CA Tháng Trước'], errors='coerce') or 0.0
        df_new.at[idx, 'Quỹ CA Tổng'] = old_val + acc_month
        
    return df_new

# --- 7. TẢI DỮ LIỆU ---
if 'db' not in st.session_state or st.session_state.get('active_sheet') != sheet_name:
    try:
        st.session_state.db = conn.read(worksheet=sheet_name, ttl=0)
    except:
        st.session_state.db = pd.DataFrame({
            'STT': range(1, 66),
            'Họ và Tên': NAMES_64[:65],
            'Công ty': 'PVDWS',
            'Chức danh': 'Casing crew',
            'CA Tháng Trước': 0.0,
            'Quỹ CA Tổng': 0.0
        })
    st.session_state.active_sheet = sheet_name

# --- 8. TABS CÔNG CỤ (THÊM/XÓA GIÀN) ---
with st.expander("🛠️ CÔNG CỤ CẬP NHẬT NHANH & QUẢN LÝ GIÀN"):
    c_rig, c_del = st.columns(2)
    with c_rig:
        new_rig = st.text_input("Tên giàn mới:")
        if st.button("➕ Thêm Giàn"):
            if new_rig:
                st.session_state.gians_list.append(new_rig.upper())
                conn.update(worksheet="CONFIG", data=pd.DataFrame({"Giàn": st.session_state.gians_list}))
                st.rerun()
    with c_del:
        rig_to_del = st.selectbox("Xóa giàn:", ["-- Chọn --"] + st.session_state.gians_list)
        if st.button("🗑️ Xóa") and rig_to_del != "-- Chọn --":
            st.session_state.gians_list.remove(rig_to_del)
            conn.update(worksheet="CONFIG", data=pd.DataFrame({"Giàn": st.session_state.gians_list}))
            st.rerun()

# --- 9. GIAO DIỆN CHÍNH ---
c1, c2 = st.columns([1, 6])
if c1.button("💾 LƯU CLOUD", type="primary"):
    final_to_save = apply_pvd_full_logic(st.session_state.db)
    conn.update(worksheet=sheet_name, data=final_to_save)
    st.success("Đã lưu thành công!")
    time.sleep(1)
    st.rerun()

# --- 10. BẢNG NHẬP LIỆU ---
st.info("💡 **Gợi ý:** Nhập trạng thái vào 1 ngày (VD: PVD 8), các ngày sau sẽ tự động nhảy theo. Nhấn Enter để máy tính toán lại Quỹ CA.")

# Luôn xử lý logic Autofill trước khi hiển thị để bảng luôn mới nhất
display_df = apply_pvd_full_logic(st.session_state.db)

# Đảm bảo cột tính toán nằm ở vị trí dễ nhìn (đưa Quỹ CA Tổng ra sau CA Tháng Trước hoặc cuối cùng)
cols = list(display_df.columns)
if 'Quỹ CA Tổng' in cols:
    cols.append(cols.pop(cols.index('Quỹ CA Tổng')))
display_df = display_df[cols]

edited_df = st.data_editor(
    display_df,
    use_container_width=True,
    height=600,
    hide_index=True,
    key=f"editor_{sheet_name}"
)

# Nếu có thay đổi, cập nhật session_state và reload để trigger Autofill
if not edited_df.equals(display_df):
    st.session_state.db = edited_df
    st.rerun()
