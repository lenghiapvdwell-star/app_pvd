import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date
import streamlit.components.v1 as components

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="PVD Management 2026", layout="wide")

def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/Feb {days_vn[d.weekday()]}"

# 2. KHỞI TẠO DỮ LIỆU
if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

if 'db' not in st.session_state:
    initial_names = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang"]
    df = pd.DataFrame({
        'STT': range(1, len(initial_names) + 1),
        'Họ và Tên': initial_names, 'Công ty': 'PVD', 'Chức danh': 'Kỹ sư',
        'Nghỉ Ca Còn Lại': 0.0, 'Job Detail': ''
    })
    for d in range(1, 29): df[get_col_name(d)] = ""
    st.session_state.db = df

# 3. CSS & JS (PHÔNG CHỮ TO 1.5x & KÉO CHUỘT)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    html, body, [class*="css"] { font-size: 22px !important; }
    .main-title-text { font-size: 40px !important; font-weight: 900; color: #3b82f6; text-align: center; margin: 0; }
    div[data-testid="stDataEditor"] div { font-size: 20px !important; }
    div[data-testid="stDataEditor"] > div:first-child { cursor: grab; }
    div[data-testid="stDataEditor"] > div:first-child:active { cursor: grabbing; }
    </style>
    """, unsafe_allow_html=True)

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
                const walk = (x - startX) * 1.5;
                el.scrollLeft = scrollLeft - walk;
            });
            clearInterval(interval);
        }
    }, 1000);
</script>
""", height=0)

# 4. HEADER
h1, h2 = st.columns([1.5, 8.5])
with h1: 
    try: st.image("logo_pvd.png", width=120)
    except: st.write("### PVD")
with h2: st.markdown('<p class="main-title-text">HỆ THỐNG ĐIỀU PHỐI NHÂN SỰ PVD 2026</p>', unsafe_allow_html=True)

# 5. TABS CHỨC NĂNG
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "📝 JOB DETAIL", "👤 NHÂN VIÊN", "🏗️ GIÀN KHOAN"])

# --- TAB ĐIỀU ĐỘNG ---
with tabs[0]:
    c1, c2, c3 = st.columns([2, 1, 1.5])
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

# --- TAB JOB DETAIL ---
with tabs[1]:
    st.write("### Cập nhật nội dung công việc")
    j1, j2 = st.columns([2, 3])
    sel_j_staff = j1.multiselect("Chọn nhân sự:", st.session_state.db['Họ và Tên'].tolist())
    j_content = j2.text_area("Nội dung Job Detail:")
    if st.button("LƯU NỘI DUNG JOB"):
        st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_j_staff), 'Job Detail'] = j_content
        st.success("Đã cập nhật Job Detail!")
        st.rerun()

# --- TAB NHÂN VIÊN ---
with tabs[2]:
    st.write("### Quản lý danh sách nhân sự")
    a1, a2, a3 = st.columns(3)
    new_name = a1.text_input("Tên nhân viên mới:")
    new_pos = a2.text_input("Chức danh:", value="Kỹ sư")
    if st.button("THÊM NHÂN VIÊN"):
        new_row = {'STT': len(st.session_state.db)+1, 'Họ và Tên': new_name, 'Công ty': 'PVD', 'Chức danh': new_pos, 'Nghỉ Ca Còn Lại': 0.0, 'Job Detail': ''}
        for d in range(1, 29): new_row[get_col_name(d)] = ""
        st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_row])], ignore_index=True)
        st.rerun()
    
    st.divider()
    del_staff = st.selectbox("Chọn nhân viên cần xóa:", st.session_state.db['Họ and Tên'].tolist())
    if st.button("XÓA NHÂN VIÊN", type="secondary"):
        st.session_state.db = st.session_state.db[st.session_state.db['Họ và Tên'] != del_staff]
        st.rerun()

# --- TAB GIÀN KHOAN ---
with tabs[3]:
    st.write("### Quản lý danh sách Giàn khoan")
    g1, g2 = st.columns(2)
    with g1:
        new_g = st.text_input("Tên giàn mới:")
        if st.button("THÊM GIÀN"):
            st.session_state.list_gian.append(new_g)
            st.rerun()
    with g2:
        del_g = st.selectbox("Chọn giàn cần xóa:", st.session_state.list_gian)
        if st.button("XÓA GIÀN"):
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
            is_off = d_obj.weekday() >= 5 or d in ngay_le_tet
            if val in st.session_state.list_gian:
                if d in ngay_le_tet: bal += 2.0
                elif d_obj.weekday() >= 5: bal += 1.0
                else: bal += 0.5
            elif val == "CA" and not is_off: bal -= 1.0
        df_tmp.at[idx, 'Nghỉ Ca Còn Lại'] = round(bal, 1)
    st.session_state.db = df_tmp
    st.rerun()

# 7. BẢNG TỔNG HỢP (MÀU SẮC GIÀN)
st.write("### 📊 BẢNG TỔNG HỢP NHÂN SỰ")
date_cols = [c for c in st.session_state.db.columns if "/Feb" in c]
display_order = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Nghỉ Ca Còn Lại', 'Job Detail'] + date_cols

# Cấu hình màu sắc tag cho từng giàn
options = st.session_state.list_gian + ["CA", "WS", "NP"]
col_cfg = {
    "Nghỉ Ca Còn Lại": st.column_config.NumberColumn(format="%.1f", width="small"),
    "Job Detail": st.column_config.TextColumn(width="large")
}
for c in date_cols:
    col_cfg[c] = st.column_config.SelectboxColumn(width="small", options=options)

st.session_state.db = st.data_editor(
    st.session_state.db[display_order], 
    use_container_width=True, height=500, 
    column_config=col_cfg,
    disabled=['STT', 'Nghỉ Ca Còn Lại']
)

# 8. XUẤT EXCEL
st.download_button("📥 XUẤT BÁO CÁO", data=BytesIO().getvalue(), file_name="PVD_Report.xlsx", use_container_width=True)
