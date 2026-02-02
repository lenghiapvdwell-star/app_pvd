import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date, timedelta

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="PVD Personnel Management 2026", layout="wide")

# Hàm tạo tên cột ngày tháng
def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/Feb {days_vn[d.weekday()]}"

# 2. KHỞI TẠO BỘ NHỚ
if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

if 'db' not in st.session_state:
    NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang"]
    df = pd.DataFrame({
        'STT': range(1, len(NAMES) + 1),
        'Họ và Tên': NAMES,
        'Công ty': 'PVD',
        'Chức danh': 'Kỹ sư',
        'Nghỉ Ca Còn Lại': 0.0,
        'Job Detail': ''
    })
    for d in range(1, 29):
        df[get_col_name(d)] = ""
    st.session_state.db = df

# 3. CSS TỔNG THỂ (Chữ to 1.5x)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    html, body, [class*="css"] { font-size: 20px !important; }
    label { font-size: 24px !important; font-weight: bold !important; color: #3b82f6 !important; }
    .stButton>button { font-size: 22px !important; font-weight: bold; border-radius: 10px; }
    .main-title-text {
        font-size: 50px !important; font-weight: 900 !important; color: #3b82f6; 
        text-transform: uppercase; text-align: center; line-height: 1.1; margin: 0;
    }
    .stTabs [data-baseweb="tab"] { font-size: 24px !important; height: 60px !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. HEADER
header_col1, header_col2, header_col3 = st.columns([2, 6, 2])
with header_col1:
    try: st.image("logo_pvd.png", width=200)
    except: st.write("### PVD")
with header_col2:
    st.markdown('<p class="main-title-text">HỆ THỐNG ĐIỀU PHỐI<br>NHÂN SỰ PVD 2026</p>', unsafe_allow_html=True)

# 5. CÁC TABS CHỨC NĂNG (Bỏ Tab Quét số dư)
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "📝 JOB DETAIL", "👤 NHÂN VIÊN", "✍️ SỬA TAY", "🏗️ GIÀN KHOAN"])

# --- TAB: ĐIỀU ĐỘNG ---
with tabs[0]:
    c1, c2, c3 = st.columns([2, 1, 1.5])
    sel_staff = c1.multiselect("CHỌN NHÂN VIÊN:", st.session_state.db['Họ và Tên'].tolist())
    status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "Nghỉ Ca (CA)", "Làm Xưởng (WS)", "Nghỉ Phép (NP)"])
    val_to_fill = c2.selectbox("CHỌN GIÀN:", st.session_state.list_gian) if status == "Đi Biển" else ({"Nghỉ Ca (CA)": "CA", "Làm Xưởng (WS)": "WS", "Nghỉ Phép (NP)": "NP"}.get(status))
    dates = c3.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))
    if st.button("XÁC NHẬN ĐIỀU ĐỘNG"):
        if isinstance(dates, tuple) and len(dates) == 2:
            for d in range(dates[0].day, dates[1].day + 1):
                col = get_col_name(d)
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col] = val_to_fill
            st.rerun()

# --- CÁC TAB NHÂN VIÊN, GIÀN KHOAN VÀ SỬA TAY (Giữ nguyên như bản trước) ---
with tabs[2]: # Nhân viên
    with st.form("add_staff"):
        n1 = st.text_input("Họ Tên:"); n2 = st.text_input("Công ty", "PVD")
        if st.form_submit_button("LƯU"):
            new_row = {'STT': len(st.session_state.db)+1, 'Họ và Tên': n1, 'Công ty': n2, 'Nghỉ Ca Còn Lại': 0.0}
            for d in range(1, 29): new_row[get_col_name(d)] = ""
            st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_row])], ignore_index=True)
            st.rerun()

with tabs[3]: # Sửa tay
    st.session_state.db = st.data_editor(st.session_state.db, use_container_width=True, height=500)
    if st.button("CHỐT DỮ LIỆU SỬA TAY"): st.rerun()

with tabs[4]: # Giàn khoan
    g1, g2 = st.columns(2)
    with g1: 
        new_g = st.text_input("Tên giàn mới")
        if st.button("THÊM"): st.session_state.list_gian.append(new_g); st.rerun()
    with g2:
        del_g = st.selectbox("Xóa giàn", st.session_state.list_gian)
        if st.button("XÓA"): st.session_state.list_gian.remove(del_g); st.rerun()

# 6. KHU VỰC ĐIỀU KHIỂN CHÍNH (QUÉT SỐ DƯ GÓC TRÁI)
st.markdown("---")
col_scan, col_empty = st.columns([1, 3])

with col_scan:
    if st.button("🚀 QUÉT & CẬP NHẬT SỐ DƯ", type="primary", use_container_width=True):
        # Ngày Lễ Tết 2026 (Ví dụ: 17/02 đến 21/02)
        ngay_le_tet = [17, 18, 19, 20, 21]
        
        df_tmp = st.session_state.db.copy()
        for index, row in df_tmp.iterrows():
            balance = 0.0
            for d in range(1, 29):
                col = get_col_name(d)
                val = row[col]
                d_obj = date(2026, 2, d)
                is_weekend = d_obj.weekday() >= 5 # Thứ 7 (5), CN (6)
                is_holiday = d in ngay_le_tet
                
                # 1. Nếu ĐI BIỂN (Nằm trong danh sách giàn)
                if val in st.session_state.list_gian:
                    if is_holiday: balance += 2.0  # Lễ tính gấp đôi
                    elif is_weekend: balance += 1.0 # Cuối tuần tính 1
                    else: balance += 0.5            # Ngày thường tính 0.5
                
                # 2. Nếu NGHỈ CA (CA)
                elif val == "CA":
                    # CHỈ TRỪ nếu KHÔNG PHẢI thứ 7, CN và KHÔNG PHẢI ngày lễ
                    if not is_weekend and not is_holiday:
                        balance -= 1.0
                
                # 3. Nếu NGHỈ PHÉP (NP) -> KHÔNG TRỪ vào số dư nghỉ ca
                elif val == "NP":
                    pass # Giữ nguyên số dư
            
            df_tmp.at[index, 'Nghỉ Ca Còn Lại'] = round(balance, 1)
        
        st.session_state.db = df_tmp
        st.success("Đã cập nhật số dư mới nhất!")
        st.rerun()

# 7. HIỂN THỊ BẢNG TỔNG HỢP
date_cols = [c for c in st.session_state.db.columns if "/Feb" in c]
display_order = ['STT', 'Họ và Tên', 'Nghỉ Ca Còn Lại', 'Job Detail'] + date_cols

def format_bal(v): return str(int(v)) if v == int(v) else str(v)
df_display = st.session_state.db[display_order].copy()
df_display['Nghỉ Ca Còn Lại'] = df_display['Nghỉ Ca Còn Lại'].apply(format_bal)

st.dataframe(df_display, use_container_width=True, height=650)

# Xuất file
output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    st.session_state.db.to_excel(writer, index=False)
st.download_button("📥 XUẤT BÁO CÁO", data=output.getvalue(), file_name="PVD_2026.xlsx")
