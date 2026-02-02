import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date
import streamlit.components.v1 as components

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="PVD Management", layout="wide")

def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/Feb {days_vn[d.weekday()]}"

# 2. KHỞI TẠO DỮ LIỆU
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
        'Họ và Tên': NAMES, 'Công ty': 'PVD', 'Chức danh': 'Kỹ sư',
        'Nghỉ Ca Còn Lại': 0.0, 'Job Detail': ''
    })
    for d in range(1, 29): df[get_col_name(d)] = ""
    st.session_state.db = df

# 3. CSS TINH GỌN & MÀU SẮC (Chữ nhỏ 14px)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    html, body, [class*="css"] { font-size: 14px !important; }
    .main-title-text { font-size: 30px !important; font-weight: 800; color: #3b82f6; text-align: center; margin: 0; }
    
    /* Hiệu ứng cầm tay để kéo bảng */
    div[data-testid="stDataEditor"] > div:first-child { cursor: grab; }
    div[data-testid="stDataEditor"] > div:first-child:active { cursor: grabbing; }
    
    /* Thu nhỏ khoảng cách giữa các thành phần */
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    </style>
    """, unsafe_allow_html=True)

# JS hỗ trợ kéo chuột trái để cuộn ngang bảng
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

# 4. HEADER (Dùng logo_pvd.png)
h1, h2 = st.columns([1, 4])
with h1: 
    try: st.image("logo_pvd.png", width=120)
    except: st.write("### PVD")
with h2: st.markdown('<p class="main-title-text">HỆ THỐNG NHÂN SỰ PVD 2026</p>', unsafe_allow_html=True)

# 5. TABS
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "📝 JOB", "👤 NHÂN VIÊN", "🏗️ GIÀN"])

with tabs[0]:
    c1, c2, c3 = st.columns([2, 1, 1.5])
    sel_staff = c1.multiselect("Nhân viên:", st.session_state.db['Họ và Tên'].tolist())
    status = c2.selectbox("Trạng thái:", ["Đi Biển", "Nghỉ Ca (CA)", "Làm Xưởng (WS)", "Nghỉ Phép (NP)"])
    val_to_fill = c2.selectbox("Giàn:", st.session_state.list_gian) if status == "Đi Biển" else ({"Nghỉ Ca (CA)": "CA", "Làm Xưởng (WS)": "WS", "Nghỉ Phép (NP)": "NP"}.get(status))
    dates = c3.date_input("Ngày:", value=(date(2026, 2, 1), date(2026, 2, 2)))
    if st.button("CẬP NHẬT DỮ LIỆU"):
        if isinstance(dates, tuple) and len(dates) == 2:
            for d in range(dates[0].day, dates[1].day + 1):
                col = get_col_name(d)
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col] = val_to_fill
            st.rerun()

# 6. QUÉT SỐ DƯ (GÓC TRÁI)
st.markdown("---")
if st.button("🚀 QUÉT SỐ DƯ", type="primary"):
    ngay_le_tet = [17, 18, 19, 20, 21]
    df_tmp = st.session_state.db.copy()
    for idx, row in df_tmp.iterrows():
        bal = 0.0
        for d in range(1, 29):
            col = get_col_name(d); val = row[col]; d_obj = date(2026, 2, d)
            is_off = d_obj.weekday() >= 5 or d in ngay_le_tet
            if val in st.session_state.list_gian:
                if d in ngay_le_tet: bal += 2.0
                elif d_obj.weekday() >= 5: bal += 1.0
                else: bal += 0.5
            elif val == "CA" and not is_off: bal -= 1.0
        df_tmp.at[idx, 'Nghỉ Ca Còn Lại'] = round(bal, 1)
    st.session_state.db = df_tmp
    st.rerun()

# 7. BẢNG TỔNG HỢP (PHÂN MÀU GIÀN KHOAN)
date_cols = [c for c in st.session_state.db.columns if "/Feb" in c]
display_order = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Nghỉ Ca Còn Lại', 'Job Detail'] + date_cols

# Cấu hình danh sách chọn kèm màu sắc
options = st.session_state.list_gian + ["CA", "WS", "NP"]

col_cfg = {
    "STT": st.column_config.NumberColumn(width="small"),
    "Nghỉ Ca Còn Lại": st.column_config.NumberColumn(format="%.1f", width="small"),
    "Job Detail": st.column_config.TextColumn(width="medium")
}

# Tự động gán SelectboxColumn cho tất cả các cột ngày tháng
for c in date_cols:
    col_cfg[c] = st.column_config.SelectboxColumn(
        width="small",
        options=options
    )

st.write("**📊 BẢNG TỔNG HỢP NHÂN SỰ**")
st.session_state.db = st.data_editor(
    st.session_state.db[display_order], 
    use_container_width=True, 
    height=600,
    column_config=col_cfg,
    disabled=['STT', 'Nghỉ Ca Còn Lại']
)

# 8. XUẤT FILE
st.download_button("📥 XUẤT EXCEL", data=BytesIO().getvalue(), file_name="PVD_Management_2026.xlsx")
