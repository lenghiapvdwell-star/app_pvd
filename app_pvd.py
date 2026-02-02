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

# 3. CSS CUSTOM: ÉP HEADER RA GIỮA TUYỆT ĐỐI
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    
    /* Container bao quanh logo và chữ */
    .full-header-container {
        display: flex;
        flex-direction: row;
        align-items: center;
        justify-content: center; /* Căn giữa theo chiều ngang */
        width: 100%;
        gap: 30px;
        padding: 20px 0px 50px 0px;
    }
    
    .main-title-text {
        font-size: 55px !important;
        font-weight: 850 !important;
        color: #3b82f6; 
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 2px;
        line-height: 1.1;
        text-align: left; /* Chữ canh lề trái so với logo nhưng cả cụm vẫn ở giữa */
    }

    /* Giữ Tabs lề trái */
    .stTabs [data-baseweb="tab-list"] {
        justify-content: flex-start !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. HEADER CĂN GIỮA (Dùng Columns để bổ trợ việc căn chỉnh)
# Tạo 3 cột, cột giữa chứa cả Logo và Tiêu đề
empty_l, center_col, empty_r = st.columns([1, 8, 1])

with center_col:
    # Dùng HTML để bọc cả Image và Text vào một dòng duy nhất và căn giữa
    header_html = f"""
    <div class="full-header-container">
        <img src="https://www.pvdrilling.com.vn/images/logo.png" width="220">
        <p class="main-title-text">HỆ THỐNG ĐIỀU PHỐI<br>NHÂN SỰ PVD 2026</p>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)
    # Lưu ý: Nếu file logo_pvd.png của bạn đã upload, hãy thay link online bằng file nội bộ nếu cần.

# 5. CÁC TABS CHỨC NĂNG
tabs = st.tabs(["🚀 Điều Động", "📝 Nhập Job Detail", "👤 Thêm Nhân Viên", "✍️ Sửa Tổng Hợp", "🔍 Quét Số Dư", "🏗️ Giàn Khoan"])

# --- Các phần logic bên dưới giữ nguyên ---
with tabs[0]:
    c1, c2, c3 = st.columns([2, 1, 1.5])
    sel_staff = c1.multiselect("Chọn nhân viên:", st.session_state.db['Họ và Tên'].tolist())
    status = c2.selectbox("Trạng thái:", ["Đi Biển", "Nghỉ Ca (CA)", "Làm Xưởng (WS)", "Nghỉ Phép (NP)"])
    val_to_fill = ""
    if status == "Đi Biển":
        val_to_fill = c2.selectbox("Chọn Giàn:", st.session_state.list_gian)
    else:
        mapping = {"Nghỉ Ca (CA)": "CA", "Làm Xưởng (WS)": "WS", "Nghỉ Phép (NP)": "NP"}
        val_to_fill = mapping.get(status, status)
    dates = c3.date_input("Khoảng ngày:", value=(date(2026, 2, 1), date(2026, 2, 2)))
    if st.button("XÁC NHẬN CẬP NHẬT", type="primary"):
        if isinstance(dates, tuple) and len(dates) == 2:
            for d in range(dates[0].day, dates[1].day + 1):
                col = get_col_name(d)
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col] = val_to_fill
            st.rerun()

with tabs[1]:
    st.subheader("📝 Cập nhật nội dung công việc")
    with st.form("job_form"):
        sel_job_staff = st.multiselect("Chọn nhân viên thực hiện job:", st.session_state.db['Họ và Tên'].tolist())
        job_text = st.text_area("Nội dung Job Detail:", placeholder="Gõ ghi chú công việc tại đây...")
        if st.form_submit_button("LƯU JOB DETAIL"):
            if sel_job_staff:
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_job_staff), 'Job Detail'] = job_text
                st.success("Đã cập nhật Job Detail thành công!")
                st.rerun()

# (Các tab khác giữ nguyên logic của bạn...)
# ...

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

st.dataframe(
    st.session_state.db[display_order].style.applymap(style_cells, subset=date_cols),
    use_container_width=True, height=600
)

output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    st.session_state.db.to_excel(writer, index=False)
st.download_button("📥 XUẤT FILE BÁO CÁO", data=output.getvalue(), file_name="PVD_Report_2026.xlsx")
