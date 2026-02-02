import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date
import streamlit.components.v1 as components

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="PVD Well Services 2026", layout="wide")

# Hàm lấy tên cột: Ngày/Tháng \n Thứ (Căn giữa)
def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/02\n{days_vn[d.weekday()]}"

DATE_COLS = [get_col_name(d) for d in range(1, 29)]

# RESET DỮ LIỆU NẾU CẤU TRÚC CỘT THAY ĐỔI
if 'db' in st.session_state:
    if get_col_name(1) not in st.session_state.db.columns:
        del st.session_state.db

if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

if 'db' not in st.session_state:
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
    init_data = {'STT': range(1, len(NAMES) + 1), 'Họ và Tên': NAMES, 'Công ty': 'PVD', 'Chức danh': 'Kỹ sư', 'Nghỉ Ca Còn Lại': 0.0, 'Job Detail': ""}
    for col in DATE_COLS: init_data[col] = ""
    st.session_state.db = pd.DataFrame(init_data)

# 3. CSS "BÀN TAY SẮT" - VÔ HIỆU HÓA ICON TRÊN TIÊU ĐỀ
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    
    .main-title-container {
        text-align: center; padding-bottom: 15px; border-bottom: 4px solid #00f2ff;
        box-shadow: 0px 8px 20px -10px #00f2ff; margin-bottom: 30px;
    }
    .main-title-text { font-size: 38px !important; font-weight: 900; color: #00f2ff; margin: 0; }
    
    /* ÉP TIÊU ĐỀ BẢNG: Căn giữa, xuống dòng và KHÔNG CHO CHUỘT TƯƠNG TÁC */
    div[data-testid="stDataEditor"] th {
        height: 80px !important;
        white-space: pre !important;
        text-align: center !important;
        vertical-align: middle !important;
        color: #00f2ff !important;
        pointer-events: none; /* Khóa chuột: Không hiện icon, không cho sắp xếp */
    }
    
    /* Đảm bảo chữ nằm chính giữa */
    div[data-testid="stDataEditor"] th div {
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        width: 100%;
    }

    /* Ẩn chữ None */
    div[data-testid="stDataEditor"] span:contains("None") { color: transparent !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. HEADER
st.markdown('<div class="main-title-container">', unsafe_allow_html=True)
h1, h2 = st.columns([2, 8])
with h1: 
    try: st.image("logo_pvd.png", width=200)
    except: st.write("### PVD")
with h2: st.markdown('<p class="main-title-text">PVD WELL SERVICES MANAGEMENT 2026</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 5. TABS (GIỮ NGUYÊN LOGIC CŨ)
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "📝 JOB DETAIL", "👤 NHÂN VIÊN", "🏗️ GIÀN KHOAN"])

with tabs[0]: # ĐIỀU ĐỘNG
    c1, c2, c3 = st.columns([2, 1, 1.5])
    sel_staff = c1.multiselect("CHỌN NHÂN VIÊN:", st.session_state.db['Họ và Tên'].tolist())
    status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "Nghỉ Ca (CA)", "Làm Xưởng (WS)", "Nghỉ Phép (NP)"])
    val_to_fill = c2.selectbox("CHỌN GIÀN:", st.session_state.list_gian) if status == "Đi Biển" else ({"Nghỉ Ca (CA)": "CA", "Làm Xưởng (WS)": "WS", "Nghỉ Phép (NP)": "NP"}.get(status))
    dates = c3.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))
    if st.button("XÁC NHẬN CẬP NHẬT", use_container_width=True):
        if isinstance(dates, tuple) and len(dates) == 2:
            for d in range(dates[0].day, dates[1].day + 1):
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), get_col_name(d)] = val_to_fill
            st.rerun()

# 6. QUÉT SỐ DƯ
st.markdown("---")
if st.button("🚀 QUÉT & CẬP NHẬT SỐ DƯ", type="primary", use_container_width=True):
    ngay_le_tet = [17, 18, 19, 20, 21]
    df_tmp = st.session_state.db.copy()
    for idx, row in df_tmp.iterrows():
        bal = 0.0
        for d in range(1, 29):
            col = get_col_name(d); val = row[col]; d_obj = date(2026, 2, d)
            is_off_day = d_obj.weekday() >= 5 or d in ngay_le_tet
            if val in st.session_state.list_gian:
                if d in ngay_le_tet: bal += 2.0
                elif d_obj.weekday() >= 5: bal += 1.0
                else: bal += 0.5
            elif val == "CA" and not is_off_day:
                bal -= 1.0
        df_tmp.at[idx, 'Nghỉ Ca Còn Lại'] = round(bal, 1)
    st.session_state.db = df_tmp
    st.rerun()

# 7. BẢNG TỔNG HỢP
st.write("### 📊 BẢNG TỔNG HỢP NHÂN SỰ")

display_order = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Nghỉ Ca Còn Lại', 'Job Detail'] + DATE_COLS
all_options = st.session_state.list_gian + ["CA", "WS", "NP"]

col_cfg = {
    "STT": st.column_config.NumberColumn(width="small"),
    "Nghỉ Ca Còn Lại": st.column_config.NumberColumn(format="%.1f", width="small"),
}
for c in DATE_COLS:
    col_cfg[c] = st.column_config.SelectboxColumn(width="small", options=all_options)

st.session_state.db = st.data_editor(
    st.session_state.db[display_order], 
    use_container_width=True, height=600, 
    column_config=col_cfg,
    disabled=['STT', 'Nghỉ Ca Còn Lại']
)

# 8. XUẤT EXCEL & KÉO CHUỘT
st.download_button("📥 XUẤT EXCEL", data=BytesIO().getvalue(), file_name="PVD_WS_2026.xlsx", use_container_width=True)

components.html("""
<script>
    const interval = setInterval(() => {
        const el = window.parent.document.querySelector('div[data-testid="stDataEditor"] [role="grid"]');
        if (el) {
            let isDown = false; let startX; let scrollLeft;
            el.addEventListener('mousedown', (e) => { isDown = true; startX = e.pageX - el.offsetLeft; scrollLeft = el.scrollLeft; });
            el.addEventListener('mouseleave', () => { isDown = false; });
            el.addEventListener('mouseup', () => { isDown = false; });
            el.addEventListener('mousemove', (e) => {
                if(!isDown) return;
                e.preventDefault();
                const x = e.pageX - el.offsetLeft;
                const walk = (x - startX) * 2;
                el.scrollLeft = scrollLeft - walk;
            });
            clearInterval(interval);
        }
    }, 1000);
</script>
""", height=0)
