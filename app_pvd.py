import streamlit as st
import pandas as pd
from datetime import datetime, date
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import io
import os

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="PVD Well Services 2026", layout="wide")

st.markdown("""
    <style>
        [data-testid="stStatusWidget"] {display: none;}
        .stButton button {width: 100%; border-radius: 5px; height: 3em; font-weight: bold;}
        .main { background-color: #0e1117; }
        h1 { text-shadow: 2px 2px #000000; }
    </style>
""", unsafe_allow_html=True)

# Hiển thị Logo và Tiêu đề
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=120)
with col_title:
    st.markdown('<h1 style="color: #00f2ff; text-align: center; margin-top: 10px;">PVD WELL SERVICES MANAGEMENT 2026</h1>', unsafe_allow_html=True)

# 2. KHỞI TẠO DANH SÁCH 64 NHÂN VIÊN GỐC
NAMES_64 = [
    "Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", 
    "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", 
    "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", 
    "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", 
    "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", 
    "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", 
    "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", 
    "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", 
    "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", 
    "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", 
    "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"
]

# 3. KẾT NỐI VÀ QUẢN LÝ DỮ LIỆU
conn = st.connection("gsheets", type=GSheetsConnection)

def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/02\n{days_vn[d.weekday()]}"

DATE_COLS = [get_col_name(d) for d in range(1, 29)]
NGAY_LE_TET = [15, 16, 17, 18, 19, 20, 21]

@st.cache_data(ttl=0)
def load_all_data():
    try:
        db = conn.read(worksheet="Sheet1")
    except:
        db = pd.DataFrame()
    
    try:
        gians = conn.read(worksheet="Gians")['TenGian'].dropna().tolist()
    except:
        gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]
        
    try:
        staffs = conn.read(worksheet="Staffs")
    except:
        staffs = pd.DataFrame()
        
    return db, gians, staffs

# KIỂM TRA VÀ KHỞI TẠO DỮ LIỆU (Đảm bảo có 64 nhân viên)
if 'db' not in st.session_state:
    db_raw, gians_raw, staffs_raw = load_all_data()
    
    # Nếu tab Staffs trống, nạp 64 người
    if staffs_raw.empty:
        st.session_state.staffs = pd.DataFrame({
            "STT": range(1, len(NAMES_64) + 1),
            "Họ và Tên": NAMES_64,
            "Công ty": ["PVD"] * len(NAMES_64),
            "Chức danh": ["Kỹ sư"] * len(NAMES_64)
        })
    else:
        st.session_state.staffs = staffs_raw

    # Nếu tab Sheet1 trống, tạo bảng điều động từ danh sách NV
    if db_raw.empty:
        init_db = st.session_state.staffs.copy()
        init_db["Nghỉ Ca Còn Lại"] = 0.0
        init_db["Job Detail"] = ""
        for c in DATE_COLS: init_db[c] = ""
        st.session_state.db = init_db
    else:
        st.session_state.db = db_raw
        
    st.session_state.gians = gians_raw

# 4. NÚT LƯU CLOUD TỔNG THỂ
st.divider()
col_save_text, col_save_btn = st.columns([4, 1])
with col_save_btn:
    if st.button("💾 LƯU CLOUD (SAVE ALL)", type="primary", use_container_width=True):
        with st.spinner("Đang đồng bộ dữ liệu..."):
            conn.update(worksheet="Sheet1", data=st.session_state.db)
            conn.update(worksheet="Gians", data=pd.DataFrame({"TenGian": st.session_state.gians}))
            conn.update(worksheet="Staffs", data=st.session_state.staffs)
            st.success("✅ Đã lưu thành công!")

# 5. GIAO DIỆN TABS
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 TỔNG HỢP", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "📝 CHI TIẾT", "📥 XUẤT FILE"])

with tabs[0]: # TAB ĐIỀU ĐỘNG
    with st.form("dieu_dong_form"):
        c1, c2, c3 = st.columns([2, 1, 1.5])
        sel_staff = c1.multiselect("CHỌN NHÂN VIÊN:", st.session_state.db['Họ và Tên'].tolist())
        status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "CA", "WS", "NP"])
        val = c2.selectbox("GIÀN:", st.session_state.gians) if status == "Đi Biển" else status
        dates = c3.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))
        if st.form_submit_button("ÁP DỤNG THAY ĐỔI"):
            if isinstance(dates, tuple) and len(dates) == 2:
                for d in range(dates[0].day, dates[1].day + 1):
                    st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), get_col_name(d)] = val
                st.toast("Đã ghi nhận thay đổi tạm thời!")

with tabs[1]: # TAB TỔNG HỢP (BẢNG CHÍNH)
    if st.button("🚀 TÍNH TOÁN NGHỈ CA TOÀN BỘ"):
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
        st.rerun()

    disp_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Nghỉ Ca Còn Lại', 'Job Detail'] + DATE_COLS
    st.session_state.db = st.data_editor(st.session_state.db[disp_cols], use_container_width=True, height=550)

with tabs[2]: # TAB GIÀN KHOAN
    st.session_state.gians = st.data_editor(pd.DataFrame({"TenGian": st.session_state.gians}), num_rows="dynamic")['TenGian'].dropna().tolist()

with tabs[3]: # TAB NHÂN VIÊN (Chỉnh tên, cty, chức danh)
    st.subheader("👥 Danh sách nhân viên (64 người +)")
    st.session_state.staffs = st.data_editor(st.session_state.staffs, use_container_width=True, num_rows="dynamic")
    if st.button("ĐỒNG BỘ THÔNG TIN SANG BẢNG CHÍNH"):
        # Cập nhật thông tin cơ bản sang bảng điều động
        for _, s in st.session_state.staffs.iterrows():
            if s['Họ và Tên'] in st.session_state.db['Họ và Tên'].values:
                idx = st.session_state.db[st.session_state.db['Họ và Tên'] == s['Họ và Tên']].index[0]
                st.session_state.db.at[idx, 'Công ty'] = s['Công ty']
                st.session_state.db.at[idx, 'Chức danh'] = s['Chức danh']
            else:
                # Nếu là nhân viên mới hoàn toàn
                new_row = {c: "" for c in st.session_state.db.columns}
                new_row.update(s.to_dict()); new_row['Nghỉ Ca Còn Lại'] = 0.0
                st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_row])], ignore_index=True)
        st.success("Đã đồng bộ thông tin!")

with tabs[4]: # TAB CHI TIẾT (Sửa Job Detail nhanh)
    sel_name = st.selectbox("Chọn nhân viên sửa Job Detail:", st.session_state.db['Họ và Tên'].tolist())
    idx_job = st.session_state.db[st.session_state.db['Họ và Tên'] == sel_name].index[0]
    new_job_val = st.text_area("Nội dung Job Detail:", value=st.session_state.db.at[idx_job, 'Job Detail'], height=200)
    if st.button("Cập nhật Job"):
        st.session_state.db.at[idx_job, 'Job Detail'] = new_job_val
        st.success("Đã cập nhật!")

with tabs[5]: # TAB XUẤT FILE
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        st.session_state.db.to_excel(writer, index=False, sheet_name='PVD_2026')
    st.download_button("📥 TẢI FILE EXCEL (.xlsx)", data=output.getvalue(), file_name=f"PVD_Management_2026.xlsx", use_container_width=True)

# 6. JS CUỘN NGANG
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
