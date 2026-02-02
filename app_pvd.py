import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="PVD Personnel Management 2026", layout="wide")

# Hàm tạo tên cột ngày tháng
def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/Feb {days_vn[d.weekday()]}"

# 2. KHỞI TẠO BỘ NHỚ (Session State)
if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

if 'db' not in st.session_state:
    NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung"] # Danh sách mẫu ban đầu
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
    html, body, [class*="css"], .stMarkdown, p, li { font-size: 20px !important; }
    label { font-size: 24px !important; font-weight: bold !important; color: #3b82f6 !important; }
    .stButton>button { font-size: 24px !important; font-weight: bold; height: 3.5em; border-radius: 10px; }
    .main-title-text {
        font-size: 55px !important; font-weight: 900 !important; color: #3b82f6; 
        text-transform: uppercase; text-align: center; line-height: 1.1; margin: 0;
    }
    .stTabs [data-baseweb="tab"] { font-size: 26px !important; height: 70px !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. HEADER
header_col1, header_col2, header_col3 = st.columns([2, 6, 2])
with header_col1:
    try: st.image("logo_pvd.png", width=220)
    except: st.write("⚠️ Logo")
with header_col2:
    st.markdown('<p class="main-title-text">HỆ THỐNG ĐIỀU PHỐI<br>NHÂN SỰ PVD 2026</p>', unsafe_allow_html=True)

# 5. CÁC TABS CHỨC NĂNG
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "📝 JOB DETAIL", "👤 NHÂN VIÊN", "✍️ SỬA TAY", "🔍 QUÉT SỐ DƯ", "🏗️ GIÀN KHOAN"])

# --- TAB 0: ĐIỀU ĐỘNG --- (Giữ nguyên logic cũ)
with tabs[0]:
    c1, c2, c3 = st.columns([2, 1, 1.5])
    sel_staff = c1.multiselect("CHỌN NHÂN VIÊN:", st.session_state.db['Họ và Tên'].tolist())
    status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "Nghỉ Ca (CA)", "Làm Xưởng (WS)", "Nghỉ Phép (NP)"])
    val_to_fill = c2.selectbox("CHỌN GIÀN:", st.session_state.list_gian) if status == "Đi Biển" else ({"Nghỉ Ca (CA)": "CA", "Làm Xưởng (WS)": "WS", "Nghỉ Phép (NP)": "NP"}.get(status))
    dates = c3.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))
    if st.button("XÁC NHẬN CẬP NHẬT"):
        if isinstance(dates, tuple) and len(dates) == 2:
            for d in range(dates[0].day, dates[1].day + 1):
                col = get_col_name(d)
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col] = val_to_fill
            st.rerun()

# --- TAB 2: QUẢN LÝ NHÂN VIÊN (Thêm mới) ---
with tabs[2]:
    st.subheader("👤 Thêm Nhân Viên Mới")
    with st.form("add_staff_form"):
        new_name = st.text_input("Họ và Tên nhân viên:")
        new_comp = st.text_input("Công ty:", value="PVD")
        new_pos = st.text_input("Chức danh:", value="Kỹ sư")
        if st.form_submit_button("LƯU NHÂN VIÊN"):
            if new_name:
                new_row = {
                    'STT': len(st.session_state.db) + 1,
                    'Họ và Tên': new_name,
                    'Công ty': new_comp,
                    'Chức danh': new_pos,
                    'Nghỉ Ca Còn Lại': 0.0,
                    'Job Detail': ''
                }
                for d in range(1, 29): new_row[get_col_name(d)] = ""
                st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"Đã thêm {new_name}")
                st.rerun()

# --- TAB 3: SỬA TRỰC TIẾP (Sửa tay bằng Data Editor) ---
with tabs[3]:
    st.subheader("✍️ Chỉnh sửa trực tiếp trên bảng")
    st.info("Bạn có thể nhấn đúp vào ô bất kỳ để sửa nội dung, sau đó nhấn 'LƯU THAY ĐỔI'")
    edited_db = st.data_editor(st.session_state.db, use_container_width=True, height=600, num_rows="dynamic")
    if st.button("LƯU THAY ĐỔI VÀO HỆ THỐNG"):
        st.session_state.db = edited_db
        st.success("Đã chốt thay đổi!")
        st.rerun()

# --- TAB 5: QUẢN LÝ GIÀN KHOAN ---
with tabs[5]:
    st.subheader("🏗️ Quản lý danh sách Giàn khoan")
    c1, c2 = st.columns(2)
    with c1:
        new_rig = st.text_input("Nhập tên giàn mới:")
        if st.button("THÊM GIÀN"):
            if new_rig and new_rig not in st.session_state.list_gian:
                st.session_state.list_gian.append(new_rig)
                st.rerun()
    with c2:
        rig_to_del = st.selectbox("Chọn giàn muốn xóa:", st.session_state.list_gian)
        if st.button("XÓA GIÀN"):
            st.session_state.list_gian.remove(rig_to_del)
            st.rerun()
    st.write("Danh sách hiện tại:", st.session_state.list_gian)

# 6. HIỂN THỊ BẢNG TỔNG HỢP (Ở trang chủ)
st.markdown("---")
date_cols = [c for c in st.session_state.db.columns if "/Feb" in c]
display_order = ['STT', 'Họ và Tên', 'Nghỉ Ca Còn Lại', 'Job Detail'] + date_cols

# Áp dụng format số dư gọn
def format_bal(v): return str(int(v)) if v == int(v) else str(v)
df_display = st.session_state.db[display_order].copy()
df_display['Nghỉ Ca Còn Lại'] = df_display['Nghỉ Ca Còn Lại'].apply(format_bal)

st.dataframe(df_display, use_container_width=True, height=600)

# 7. XUẤT EXCEL
output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    st.session_state.db.to_excel(writer, index=False)
st.download_button("📥 XUẤT FILE BÁO CÁO EXCEL", data=output.getvalue(), file_name="PVD_Report_2026.xlsx")
