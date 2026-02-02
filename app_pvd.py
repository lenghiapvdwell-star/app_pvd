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

# 2. KHỞI TẠO BỘ NHỚ
if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

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

# 3. CSS CUSTOM: LOGO TRÁI - TIÊU ĐỀ GIỮA - NỀN TỐI
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    
    .header-container {
        display: flex;
        align-items: center;
        justify-content: flex-start; /* Logo nằm góc trái */
        padding: 10px 0px 30px 0px;
        border-bottom: 1px solid #3b82f6;
        margin-bottom: 20px;
    }
    
    .title-wrapper {
        flex-grow: 1;
        text-align: center; /* Tiêu đề vẫn nằm giữa trang */
        margin-right: 220px; /* Bù trừ khoảng cách để tiêu đề cân giữa so với toàn trang */
    }

    .main-title-text {
        font-size: 45px !important;
        font-weight: 850 !important;
        color: #3b82f6; 
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 1px;
        line-height: 1.2;
    }

    .stTabs [data-baseweb="tab-list"] { justify-content: flex-start !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. HEADER: LOGO TRÁI & TIÊU ĐỀ GIỮA
col_logo, col_title = st.columns([1, 4])
with col_logo:
    try:
        # Sử dụng logo nội bộ, nếu lỗi sẽ hiện text
        st.image("logo_pvd.png", width=220)
    except:
        st.write("### PETROVIETNAM")

with col_title:
    st.markdown('<p class="main-title-text" style="text-align: center;">HỆ THỐNG ĐIỀU PHỐI<br>NHÂN SỰ PVD 2026</p>', unsafe_allow_html=True)

# 5. CÁC TABS CHỨC NĂNG
tabs = st.tabs(["🚀 Điều Động", "📝 Nhập Job Detail", "👤 Thêm Nhân Viên", "✍️ Sửa Tổng Hợp", "🔍 Quét Số Dư", "🏗️ Giàn Khoan"])

# --- Tab 2: Nhập Job Detail (Đã sửa lỗi Họ và Tên) ---
with tabs[1]:
    st.subheader("📝 Cập nhật Job Detail")
    with st.form("job_form"):
        sel_job_staff = st.multiselect("Chọn nhân viên:", st.session_state.db['Họ và Tên'].tolist())
        job_text = st.text_area("Nội dung công việc:")
        if st.form_submit_button("LƯU JOB DETAIL"):
            if sel_job_staff:
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_job_staff), 'Job Detail'] = job_text
                st.success("Đã cập nhật!")
                st.rerun()

# --- Tab 5: Quét số dư (Làm tròn số) ---
with tabs[4]:
    if st.button("🚀 QUÉT & CHỐT THÁNG"):
        tet_2026 = [17, 18, 19, 20, 21]
        df_tmp = st.session_state.db.copy()
        for index, row in df_tmp.iterrows():
            balance = 0.0
            for d in range(1, 29):
                col = get_col_name(d)
                if col in df_tmp.columns:
                    val = row[col]
                    d_obj = date(2026, 2, d)
                    if val in st.session_state.list_gian:
                        if d in tet_2026: balance += 2.0
                        elif d_obj.weekday() >= 5: balance += 1.0
                        else: balance += 0.5
                    elif val == "CA": balance -= 1.0
            # Làm tròn về 1 chữ số thập phân
            df_tmp.at[index, 'Nghỉ Ca Còn Lại'] = round(float(balance), 1)
        st.session_state.db = df_tmp
        st.balloons()
        st.rerun()

# 6. HIỂN THỊ BẢNG TỔNG HỢP
st.markdown("---")
date_cols = [c for c in st.session_state.db.columns if "/Feb" in c]
display_order = ['STT', 'Họ và Tên', 'Công ty', 'Nghỉ Ca Còn Lại', 'Job Detail'] + date_cols

def style_cells(val):
    if not val or val == "": return ""
    if val in st.session_state.list_gian: return 'background-color: #00558F; color: white; font-weight: bold;'
    if val == "CA": return 'background-color: #E74C3C; color: white; font-weight: bold;'
    if val == "WS": return 'background-color: #F1C40F; color: black;'
    if val == "NP": return 'background-color: #9B59B6; color: white;'
    return ''

# Định dạng hiển thị cột Nghỉ Ca Còn Lại cho đẹp
st.dataframe(
    st.session_state.db[display_order].style.applymap(style_cells, subset=date_cols)
    .format({"Nghỉ Ca Còn Lại": "{:.1f}"}), # Ép hiển thị 0.5 hoặc 1.0 thay vì 0.5000
    use_container_width=True, height=600
)

# 7. XUẤT EXCEL
output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    st.session_state.db.to_excel(writer, index=False)
st.download_button("📥 XUẤT FILE BÁO CÁO", data=output.getvalue(), file_name="PVD_Report_2026.xlsx")
