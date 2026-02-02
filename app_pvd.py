import streamlit as st
import pandas as pd
from datetime import datetime, date
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import io
import os

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="PVD Well Services 2026", layout="wide")

# Hiển thị Logo và Tiêu đề
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=120)
with col_title:
    st.markdown('<h1 style="color: #00f2ff; text-align: center; margin-bottom: 0;">PVD WELL SERVICES MANAGEMENT 2026</h1>', unsafe_allow_html=True)

# 2. KHỞI TẠO KẾT NỐI
conn = st.connection("gsheets", type=GSheetsConnection)

def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/02\n{days_vn[d.weekday()]}"

DATE_COLS = [get_col_name(d) for d in range(1, 29)]
NGAY_LE_TET = [15, 16, 17, 18, 19, 20, 21]

# 3. HÀM KIỂM TRA VÀ TẠO CẤU TRÚC DỮ LIỆU (Sửa lỗi KeyError)
def validate_df(df, type="main"):
    if type == "main":
        required = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Nghỉ Ca Còn Lại', 'Job Detail']
        for col in required:
            if col not in df.columns: df[col] = ""
        for col in DATE_COLS:
            if col not in df.columns: df[col] = ""
        return df
    return df

@st.cache_data(ttl=0)
def load_data_initial():
    try:
        db = conn.read(worksheet="Sheet1")
        db = validate_df(db, "main")
    except: db = pd.DataFrame(columns=['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Nghỉ Ca Còn Lại', 'Job Detail'] + DATE_COLS)
    
    try:
        gians = conn.read(worksheet="Gians")['TenGian'].dropna().tolist()
    except: gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]
    
    try:
        staffs = conn.read(worksheet="Staffs")
    except: staffs = pd.DataFrame(columns=['STT', 'Họ và Tên', 'Công ty', 'Chức danh'])
    
    return db, gians, staffs

if 'db' not in st.session_state:
    db_r, gians_r, staffs_r = load_data_initial()
    st.session_state.db = db_r
    st.session_state.gians = gians_r
    st.session_state.staffs = staffs_r

def trigger_save():
    try:
        conn.update(worksheet="Sheet1", data=st.session_state.db)
        conn.update(worksheet="Gians", data=pd.DataFrame({"TenGian": st.session_state.gians}))
        conn.update(worksheet="Staffs", data=st.session_state.staffs)
        st.success("✅ ĐÃ ĐỒNG BỘ DỮ LIỆU LÊN CLOUD!")
    except Exception as e:
        st.error(f"❌ LỖI LƯU: {e}")

# 4. NÚT LƯU CHÍNH (Nằm ngoài các tab)
st.divider()
c_save1, c_save2 = st.columns([4, 1])
with c_save2:
    if st.button("💾 LƯU DỮ LIỆU CLOUD", use_container_width=True, type="primary"):
        trigger_save()

# 5. CSS TÔ MÀU
colors = ["#FF4B4B", "#45FF45", "#4B8BFF", "#FFFF45", "#FF45FF", "#45FFFF", "#FFA500", "#00FF7F"]
style = "<style>"
for i, gian in enumerate(st.session_state.gians):
    c = colors[i % len(colors)]
    style += f'div[data-testid="stDataEditor"] span:contains("{gian}") {{ background-color: {c} !important; color: black !important; font-weight: bold; border-radius: 4px; padding: 2px 4px; }}'
style += "div[data-testid='stDataEditor'] th { height: 75px !important; white-space: pre !important; }</style>"
st.markdown(style, unsafe_allow_html=True)

# 6. GIAO DIỆN TABS
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 TỔNG HỢP", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "📝 JOB DETAIL", "📥 XUẤT FILE"])

with tabs[0]: # ĐIỀU ĐỘNG
    c1, c2, c3 = st.columns([2, 1, 1.5])
    staff_list = st.session_state.db['Họ và Tên'].dropna().tolist()
    sel_staff = c1.multiselect("CHỌN NHÂN VIÊN:", staff_list)
    status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "CA", "WS", "NP"])
    val = c2.selectbox("GIÀN:", st.session_state.gians) if status == "Đi Biển" else status
    dates = c3.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))
    if st.button("ÁP DỤNG ĐIỀU ĐỘNG"):
        if isinstance(dates, tuple) and len(dates) == 2:
            for d in range(dates[0].day, dates[1].day + 1):
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), get_col_name(d)] = val
            st.toast("Đã áp dụng tạm thời!")

with tabs[1]: # TỔNG HỢP
    if st.button("🚀 TÍNH TOÁN NGHỈ CA"):
        for idx, row in st.session_state.db.iterrows():
            bal = 0.0
            for d in range(1, 29):
                col = get_col_name(d); v = row[col]; d_obj = date(2026, 2, d); thu = d_obj.weekday()
                if v in st.session_state.gians:
                    if d in NGAY_LE_TET: bal += 2.0
                    elif thu >= 5: bal += 1.0
                    else: bal += 0.5
                elif v == "CA" and thu < 5 and d not in NGAY_LE_TET: bal -= 1.0
            st.session_state.db.at[idx, 'Nghỉ Ca Còn Lại'] = round(bal, 1)
        st.toast("Đã tính xong!")
    
    disp_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Nghỉ Ca Còn Lại', 'Job Detail'] + DATE_COLS
    st.session_state.db = st.data_editor(st.session_state.db[disp_cols], use_container_width=True, height=550)

with tabs[2]: # GIÀN KHOAN
    st.subheader("Quản lý Giàn khoan")
    new_rig = st.text_input("Thêm giàn mới:")
    if st.button("Thêm"):
        if new_rig: st.session_state.gians.append(new_rig); st.rerun()
    del_rig = st.selectbox("Xóa giàn:", st.session_state.gians)
    if st.button("Xóa"):
        st.session_state.gians.remove(del_rig); st.rerun()

with tabs[3]: # NHÂN VIÊN
    st.subheader("Quản lý danh sách Nhân viên")
    st.session_state.staffs = st.data_editor(st.session_state.staffs, use_container_width=True, num_rows="dynamic")
    if st.button("CẬP NHẬT NHÂN VIÊN VÀO BẢNG CHÍNH"):
        current_names = st.session_state.db['Họ và Tên'].tolist()
        for _, s_row in st.session_state.staffs.iterrows():
            if s_row['Họ và Tên'] not in current_names:
                new_entry = {col: "" for col in st.session_state.db.columns}
                new_entry.update(s_row.to_dict())
                new_entry['Nghỉ Ca Còn Lại'] = 0.0
                st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_entry])], ignore_index=True)
        st.success("Đã đồng bộ nhân viên!")

with tabs[4]: # JOB DETAIL
    st.subheader("Chỉnh sửa Chi tiết")
    sel_name = st.selectbox("Nhân viên:", st.session_state.db['Họ và Tên'].dropna().tolist())
    idx = st.session_state.db[st.session_state.db['Họ và Tên'] == sel_name].index[0]
    c1, c2 = st.columns(2)
    st.session_state.db.at[idx, 'Công ty'] = c1.text_input("Công ty:", value=st.session_state.db.at[idx, 'Công ty'])
    st.session_state.db.at[idx, 'Chức danh'] = c2.text_input("Chức danh:", value=st.session_state.db.at[idx, 'Chức danh'])
    st.session_state.db.at[idx, 'Job Detail'] = st.text_area("Job Detail:", value=st.session_state.db.at[idx, 'Job Detail'])
    st.info("Sửa xong hãy ra ngoài nhấn LƯU DỮ LIỆU CLOUD")

with tabs[5]: # XUẤT FILE
    st.subheader("📥 Tải về báo cáo Excel")
    # Tạo file Excel trong bộ nhớ
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        st.session_state.db.to_excel(writer, index=False, sheet_name='Management')
    excel_data = output.getvalue()
    
    st.download_button(
        label="📥 TẢI FILE EXCEL (.xlsx)",
        data=excel_data,
        file_name=f"PVD_Management_{date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

# JS SCROLL
components.html("""
<script>
    const interval = setInterval(() => {
        const el = window.parent.document.querySelector('div[data-testid="stDataEditor"] [role="grid"]');
        if (el) {
            let isDown = false; let startX, scrollLeft;
            el.addEventListener('mousedown', (e) => { isDown = true; startX = e.pageX - el.offsetLeft; scrollLeft = el.scrollLeft; });
            el.addEventListener('mouseleave', () => { isDown = false; });
            el.addEventListener('mouseup', () => { isDown = false; });
            el.addEventListener('mousemove', (e) => {
                if(!isDown) return;
                const x = e.pageX - el.offsetLeft;
                el.scrollLeft = scrollLeft - (x - startX) * 2;
            });
            clearInterval(interval);
        }
    }, 1000);
</script>
""", height=0)
