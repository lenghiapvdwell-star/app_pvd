import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date
import streamlit.components.v1 as components

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="PVD Well Services 2026", layout="wide")

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
        'Họ và Tên': NAMES, 'Công ty': 'PVD', 'Chức danh': 'Kỹ sư',
        'Nghỉ Ca Còn Lại': 0.0, 'Job Detail': ""
    })
    for d in range(1, 29): df[get_col_name(d)] = None
    st.session_state.db = df

# 3. CSS GIAO DIỆN & XỬ LÝ NONE
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    html, body, [class*="css"] { font-size: 22px !important; }
    
    /* Đường gạch xanh Pro dưới Header */
    .main-title-container {
        text-align: center;
        padding-bottom: 15px;
        border-bottom: 4px solid #00f2ff;
        box-shadow: 0px 8px 20px -10px #00f2ff;
        margin-bottom: 30px;
    }
    .main-title-text { 
        font-size: 42px !important; font-weight: 900; color: #00f2ff; 
        margin: 0; text-transform: uppercase; letter-spacing: 1px;
    }
    
    /* Xử lý xóa chữ None trên bảng hiển thị */
    div[data-testid="stDataEditor"] span:empty::before { content: ""; }
    
    /* Font chữ bảng */
    div[data-testid="stDataEditor"] div { font-size: 19px !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. HEADER
st.markdown('<div class="main-title-container">', unsafe_allow_html=True)
h1, h2 = st.columns([2, 8])
with h1: 
    try: st.image("logo_pvd.png", width=220)
    except: st.write("### PVD WELL SERVICES")
with h2: st.markdown('<p class="main-title-text">PVD WELL SERVICES MANAGEMENT 2026</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 5. TABS CHỨC NĂNG
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "📝 JOB DETAIL", "👤 NHÂN VIÊN", "🏗️ GIÀN KHOAN"])

with tabs[0]: # TAB ĐIỀU ĐỘNG
    c1, c2, c3 = st.columns([2, 1, 1.5])
    # SỬA LỖI TYPO: 'Họ và Tên'
    sel_staff = c1.multiselect("CHỌN NHÂN VIÊN:", st.session_state.db['Họ và Tên'].tolist())
    status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "Nghỉ Ca (CA)", "Làm Xưởng (WS)", "Nghỉ Phép (NP)"])
    val_to_fill = c2.selectbox("CHỌN GIÀN:", st.session_state.list_gian) if status == "Đi Biển" else ({"Nghỉ Ca (CA)": "CA", "Làm Xưởng (WS)": "WS", "Nghỉ Phép (NP)": "NP"}.get(status))
    dates = c3.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))
    if st.button("XÁC NHẬN CẬP NHẬT", use_container_width=True):
        if isinstance(dates, tuple) and len(dates) == 2:
            for d in range(dates[0].day, dates[1].day + 1):
                col = get_col_name(d)
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col] = val_to_fill
            st.rerun()

with tabs[1]: # TAB JOB DETAIL
    st.write("### Cập nhật chi tiết công việc")
    j1, j2 = st.columns([2, 3])
    # SỬA LỖI TYPO TẠI ĐÂY:
    sel_j_staff = j1.multiselect("Chọn nhân viên thực hiện job:", st.session_state.db['Họ và Tên'].tolist())
    j_content = j2.text_area("Nội dung Job Detail:")
    if st.button("LƯU NỘI DUNG"):
        st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_j_staff), 'Job Detail'] = j_content
        st.rerun()

with tabs[2]: # TAB NHÂN VIÊN
    a1, a2 = st.columns(2)
    with a1:
        n_nv = st.text_input("Tên nhân viên mới:")
        p_nv = st.text_input("Chức danh:", value="Kỹ sư")
        if st.button("THÊM NHÂN VIÊN"):
            new_row = {'STT': len(st.session_state.db)+1, 'Họ và Tên': n_nv, 'Công ty': 'PVD', 'Chức danh': p_nv, 'Nghỉ Ca Còn Lại': 0.0, 'Job Detail': ""}
            for d in range(1, 29): new_row[get_col_name(d)] = None
            st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_row])], ignore_index=True)
            st.rerun()
    with a2:
        d_nv = st.selectbox("Xóa nhân viên:", st.session_state.db['Họ và Tên'].tolist())
        if st.button("XÁC NHẬN XÓA"):
            st.session_state.db = st.session_state.db[st.session_state.db['Họ và Tên'] != d_nv]
            st.rerun()

with tabs[3]: # TAB GIÀN KHOAN
    g1, g2 = st.columns(2)
    with g1:
        new_g = st.text_input("Tên giàn khoan mới:")
        if st.button("LƯU TÊN GIÀN"):
            st.session_state.list_gian.append(new_g)
            st.rerun()
    with g2:
        del_g = st.selectbox("Xóa giàn khoan:", st.session_state.list_gian)
        if st.button("XÁC NHẬN XÓA GIÀN"):
            st.session_state.list_gian.remove(del_g)
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
            if pd.isna(val) or val == "": continue
            is_off = d_obj.weekday() >= 5 or d in ngay_le_tet
            if val in st.session_state.list_gian:
                if d in ngay_le_tet: bal += 2.0
                elif d_obj.weekday() >= 5: bal += 1.0
                else: bal += 0.5
            elif val == "CA" and not is_off: bal -= 1.0
        df_tmp.at[idx, 'Nghỉ Ca Còn Lại'] = round(bal, 1)
    st.session_state.db = df_tmp
    st.rerun()

# 7. BẢNG TỔNG HỢP (XÓA NONE & HIỆN MÀU TAGS)
st.write("### 📊 BẢNG TỔNG HỢP NHÂN SỰ")

# Làm sạch None trước khi đưa vào editor để tránh chữ None hiện lên
df_final = st.session_state.db.copy()
date_cols = [c for c in df_final.columns if "/Feb" in c]
display_order = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Nghỉ Ca Còn Lại', 'Job Detail'] + date_cols

# Cấu hình Tags màu sắc
options = st.session_state.list_gian + ["CA", "WS", "NP"]
col_cfg = {
    "STT": st.column_config.NumberColumn(width="small"),
    "Nghỉ Ca Còn Lại": st.column_config.NumberColumn(format="%.1f", width="small"),
    "Job Detail": st.column_config.TextColumn(width="small"),
}
for c in date_cols:
    col_cfg[c] = st.column_config.SelectboxColumn(width="small", options=options, required=False)

# Chèn CSS ẩn chữ None trực tiếp vào dataframe hiển thị
st.session_state.db = st.data_editor(
    df_final[display_order], 
    use_container_width=True, height=600, 
    column_config=col_cfg,
    disabled=['STT', 'Nghỉ Ca Còn Lại']
)

# 8. XUẤT EXCEL
st.download_button("📥 XUẤT EXCEL", data=BytesIO().getvalue(), file_name="PVD_WS_Report.xlsx", use_container_width=True)

# 9. JS KÉO CHUỘT
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
