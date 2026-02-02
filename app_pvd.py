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

# 2. KHỞI TẠO DANH SÁCH 64 NHÂN VIÊN
NAMES = [
    "Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang",
    "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong",
    "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia",
    "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin",
    "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang",
    "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu",
    "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong",
    "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh",
    "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy",
    "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh",
    "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung",
    "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat",
    "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"
]

if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

if 'db' not in st.session_state:
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

# 3. CSS TỔNG THỂ (CHỮ TO 1.5X & LOGO TRÁI)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    html, body, [class*="css"] { font-size: 20px !important; }
    label { font-size: 24px !important; font-weight: bold !important; color: #3b82f6 !important; }
    .stButton>button { font-size: 22px !important; font-weight: bold; border-radius: 10px; height: 3em; }
    .main-title-text {
        font-size: 50px !important; font-weight: 900 !important; color: #3b82f6; 
        text-transform: uppercase; text-align: center; line-height: 1.1; margin: 0;
    }
    .stTabs [data-baseweb="tab"] { font-size: 24px !important; height: 60px !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. HEADER
h_col1, h_col2, h_col3 = st.columns([2, 6, 2])
with h_col1:
    try: st.image("logo_pvd.png", width=200)
    except: st.write("### PVD LOGO")
with h_col2:
    st.markdown('<p class="main-title-text">HỆ THỐNG ĐIỀU PHỐI<br>NHÂN SỰ PVD 2026</p>', unsafe_allow_html=True)

# 5. CÁC TABS CHỨC NĂNG
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "📝 JOB DETAIL", "👤 NHÂN VIÊN", "✍️ SỬA TAY", "🏗️ GIÀN KHOAN"])

# --- TAB ĐIỀU ĐỘNG ---
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

# --- TAB JOB DETAIL ---
with tabs[1]:
    st.subheader("📝 Cập nhật nội dung công việc")
    with st.form("job_form"):
        sel_job_staff = st.multiselect("Chọn nhân viên:", st.session_state.db['Họ và Tên'].tolist())
        job_text = st.text_area("Nội dung công việc:")
        if st.form_submit_button("LƯU JOB"):
            if sel_job_staff:
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_job_staff), 'Job Detail'] = job_text
                st.success("Đã lưu thành công!")
                st.rerun()

# --- TAB NHÂN VIÊN ---
with tabs[2]:
    with st.form("add_staff"):
        n_name = st.text_input("Họ và Tên mới:")
        n_cty = st.text_input("Tên Công ty:", value="PVD")
        n_pos = st.text_input("Chức danh:", value="Kỹ sư")
        if st.form_submit_button("LƯU NHÂN VIÊN"):
            new_row = {
                'STT': len(st.session_state.db) + 1, 
                'Họ và Tên': n_name, 
                'Công ty': n_cty, 
                'Chức danh': n_pos, 
                'Nghỉ Ca Còn Lại': 0.0,
                'Job Detail': ''
            }
            for d in range(1, 29): new_row[get_col_name(d)] = ""
            st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_row])], ignore_index=True)
            st.rerun()

# --- TAB SỬA TAY (Tích hợp thêm chức năng sửa nhanh) ---
with tabs[3]:
    st.info("💡 Bạn có thể sửa trực tiếp mọi thông tin ở bảng bên dưới và nhấn CHỐT DỮ LIỆU.")
    edited_df = st.data_editor(st.session_state.db, use_container_width=True, height=600)
    if st.button("CHỐT DỮ LIỆU ĐÃ SỬA"):
        st.session_state.db = edited_df
        st.rerun()

# --- TAB GIÀN KHOAN ---
with tabs[4]:
    g1, g2 = st.columns(2)
    with g1:
        new_g = st.text_input("Tên giàn mới")
        if st.button("THÊM GIÀN"): st.session_state.list_gian.append(new_g); st.rerun()
    with g2:
        del_g = st.selectbox("Xóa giàn", st.session_state.list_gian)
        if st.button("XÓA GIÀN"): st.session_state.list_gian.remove(del_g); st.rerun()

# 6. KHU VỰC QUÉT SỐ DƯ (GÓC TRÁI)
st.markdown("---")
col_scan, col_save = st.columns([1.5, 3])
with col_scan:
    if st.button("🚀 QUÉT & CẬP NHẬT SỐ DƯ", type="primary", use_container_width=True):
        ngay_le_tet = [17, 18, 19, 20, 21] 
        df_tmp = st.session_state.db.copy()
        for index, row in df_tmp.iterrows():
            balance = 0.0
            for d in range(1, 29):
                col = get_col_name(d)
                val = row[col]
                d_obj = date(2026, 2, d)
                is_weekend = d_obj.weekday() >= 5
                is_holiday = d in ngay_le_tet
                
                if val in st.session_state.list_gian:
                    if is_holiday: balance += 2.0
                    elif is_weekend: balance += 1.0
                    else: balance += 0.5
                elif val == "CA":
                    if not is_weekend and not is_holiday:
                        balance -= 1.0
            df_tmp.at[index, 'Nghỉ Ca Còn Lại'] = round(balance, 1)
        st.session_state.db = df_tmp
        st.success("Đã cập nhật số dư thành công!")
        st.rerun()

# 7. HIỂN THỊ BẢNG TỔNG HỢP (CHỈNH SỬA TRỰC TIẾP)
# Đưa Công ty và Chức danh ra bảng hiển thị
date_cols = [c for c in st.session_state.db.columns if "/Feb" in c]
display_order = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Nghỉ Ca Còn Lại', 'Job Detail'] + date_cols

# Sử dụng data_editor để bạn có thể sửa tay ngay tại bảng chính
st.subheader("📊 BẢNG TỔNG HỢP NHÂN SỰ")
st.session_state.db = st.data_editor(
    st.session_state.db[display_order], 
    use_container_width=True, 
    height=800,
    disabled=['STT', 'Nghỉ Ca Còn Lại'] # Không cho sửa STT và Số dư vì hệ thống tự tính
)

# 8. XUẤT EXCEL
output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    st.session_state.db.to_excel(writer, index=False)
st.download_button("📥 XUẤT BÁO CÁO EXCEL", data=output.getvalue(), file_name="PVD_Report_2026.xlsx")
