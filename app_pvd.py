import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date
import streamlit.components.v1 as components

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="PVD Personnel Management 2026", layout="wide")

def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/Feb {days_vn[d.weekday()]}"

# 2. KHỞI TẠO DỮ LIỆU
if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

if 'db' not in st.session_state:
    df = pd.DataFrame({
        'STT': range(1, len(NAMES) + 1),
        'Họ và Tên': NAMES, 'Công ty': 'PVD', 'Chức danh': 'Kỹ sư',
        'Nghỉ Ca Còn Lại': 0.0, 'Job Detail': ''
    })
    for d in range(1, 29): df[get_col_name(d)] = ""
    st.session_state.db = df

# 3. CSS & JAVASCRIPT ĐỂ KÉO CHUỘT (DRAG TO SCROLL)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    html, body, [class*="css"] { font-size: 18px !important; }
    .main-title-text { font-size: 45px !important; font-weight: 900 !important; color: #3b82f6; text-transform: uppercase; text-align: center; }
    
    /* Làm cho bảng có thể cuộn mượt hơn */
    div[data-testid="stDataEditor"] > div { cursor: grab; }
    div[data-testid="stDataEditor"] > div:active { cursor: grabbing; }
    </style>
    """, unsafe_allow_html=True)

# Script hỗ trợ kéo chuột trái để cuộn ngang
components.html("""
<script>
    const interval = setInterval(() => {
        const el = window.parent.document.querySelector('div[data-testid="stDataEditor"] div[data-testid="stTableBodyContainer"]');
        if (el) {
            let isDown = False; let startX; let scrollLeft;
            el.addEventListener('mousedown', (e) => { isDown = True; startX = e.pageX - el.offsetLeft; scrollLeft = el.scrollLeft; });
            el.addEventListener('mouseleave', () => { isDown = False; });
            el.addEventListener('mouseup', () => { isDown = False; });
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

# 4. HEADER
h_col1, h_col2, h_col3 = st.columns([2, 6, 2])
with h_col1:
    try: st.image("logo_pvd.png", width=180)
    except: st.write("### PVD")
with h_col2: st.markdown('<p class="main-title-text">HỆ THỐNG ĐIỀU PHỐI<br>NHÂN SỰ PVD 2026</p>', unsafe_allow_html=True)

# 5. TABS (Giữ nguyên cấu trúc)
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "📝 JOB DETAIL", "👤 NHÂN VIÊN", "🏗️ GIÀN KHOAN"])

# (Phần xử lý Tab Điều Động, Nhân Viên, Giàn Khoan giữ nguyên logic của bạn...)
# ... [Code logic cũ] ...

# 6. NÚT QUÉT SỐ DƯ
st.markdown("---")
if st.button("🚀 QUÉT & CẬP NHẬT SỐ DƯ", type="primary"):
    ngay_le_tet = [17, 18, 19, 20, 21]
    df_tmp = st.session_state.db.copy()
    for index, row in df_tmp.iterrows():
        bal = 0.0
        for d in range(1, 29):
            col = get_col_name(d); val = row[col]; d_obj = date(2026, 2, d)
            is_off = d_obj.weekday() >= 5 or d in ngay_le_tet
            if val in st.session_state.list_gian:
                if d in ngay_le_tet: bal += 2.0
                elif d_obj.weekday() >= 5: bal += 1.0
                else: bal += 0.5
            elif val == "CA" and not is_off: bal -= 1.0
        df_tmp.at[index, 'Nghỉ Ca Còn Lại'] = round(bal, 1)
    st.session_state.db = df_tmp
    st.rerun()

# 7. BẢNG TỔNG HỢP NHÂN SỰ VỚI MÀU SẮC GIÀN KHOAN
st.subheader("BẢNG TỔNG HỢP NHÂN SỰ")

date_cols = [c for c in st.session_state.db.columns if "/Feb" in c]
display_order = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Nghỉ Ca Còn Lại', 'Job Detail'] + date_cols

# Định nghĩa màu sắc cho từng giàn
# Mỗi giàn sẽ có một màu tag riêng biệt trong bảng
rig_options = [
    {"label": "PVD I", "color": "blue"},
    {"label": "PVD II", "color": "green"},
    {"label": "PVD III", "color": "orange"},
    {"label": "PVD VI", "color": "red"},
    {"label": "PVD 11", "color": "purple"},
    {"label": "CA", "color": "gray"},
    {"label": "WS", "color": "yellow"},
    {"label": "NP", "color": "lightgreen"}
]

# Cấu hình các cột ngày tháng hiện màu sắc
col_cfg = {
    "Nghỉ Ca Còn Lại": st.column_config.NumberColumn(format="%.1f"),
    "Job Detail": st.column_config.TextColumn(width="large")
}
for c in date_cols:
    col_cfg[c] = st.column_config.SelectboxColumn(
        width="medium",
        options=[r["label"] for r in rig_options]
    )

edited_db = st.data_editor(
    st.session_state.db[display_order], 
    use_container_width=True, 
    height=750,
    column_config=col_cfg,
    disabled=['STT', 'Nghỉ Ca Còn Lại']
)

st.session_state.db.update(edited_db)

# 8. XUẤT EXCEL
output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    st.session_state.db.to_excel(writer, index=False)
st.download_button("📥 XUẤT BÁO CÁO", data=output.getvalue(), file_name="PVD_Report.xlsx")
