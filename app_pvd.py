import streamlit as st
import pandas as pd
from datetime import datetime, date
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import os

# 1. CẤU HÌNH TRANG & LOGO
st.set_page_config(page_title="PVD Well Services 2026", layout="wide")

# Hiển thị Logo và Tiêu đề
col_logo, col_title = st.columns([1, 5])
with col_logo:
    # Thử nạp logo từ Github
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=150)
    else:
        st.write("📌 [Logo PVD]")
with col_title:
    st.markdown("""
        <div style="text-align: center;">
            <h1 style="color: #00f2ff; margin-bottom: 0;">PVD WELL SERVICES MANAGEMENT 2026</h1>
            <p style="color: #ffffff; font-weight: bold; font-size: 18px;">Hệ thống điều động và quản lý nghỉ ca</p>
        </div>
    """, unsafe_allow_html=True)

# 2. KẾT NỐI & HÀM BỔ TRỢ
conn = st.connection("gsheets", type=GSheetsConnection)

def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/02\n{days_vn[d.weekday()]}"

DATE_COLS = [get_col_name(d) for d in range(1, 29)]
# Cập nhật danh sách ngày lễ theo quy ước (Ví dụ Tết 2026)
NGAY_LE_TET = [15, 16, 17, 18, 19, 20, 21] 

# DANH SÁCH 64 NHÂN VIÊN GỐC
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

# 3. TẢI DỮ LIỆU TỪ 3 TAB
def load_all_data():
    try:
        db = conn.read(worksheet="Sheet1", ttl=0)
    except: db = pd.DataFrame()

    try:
        gians_df = conn.read(worksheet="Gians", ttl=0)
        gians = gians_df['TenGian'].dropna().tolist()
    except: gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

    try:
        staffs = conn.read(worksheet="Staffs", ttl=0)
    except: staffs = pd.DataFrame()
        
    return db, gians, staffs

# Khởi tạo dữ liệu ban đầu nếu trống
db_raw, gians_raw, staffs_raw = load_all_data()

if 'db' not in st.session_state:
    if staffs_raw.empty:
        # Nếu chưa có nhân viên, tạo mới 64 người
        st.session_state.staffs = pd.DataFrame({
            "STT": range(1, len(NAMES_64) + 1),
            "Họ và Tên": NAMES_64,
            "Công ty": ["PVD"] * len(NAMES_64),
            "Chức danh": ["Kỹ sư"] * len(NAMES_64)
        })
    else:
        st.session_state.staffs = staffs_raw

    if db_raw.empty:
        # Tạo bảng điều động dựa trên danh sách nhân viên
        init_db = st.session_state.staffs.copy()
        init_db["Nghỉ Ca Còn Lại"] = 0.0
        init_db["Job Detail"] = ""
        for col in DATE_COLS:
            init_db[col] = ""
        st.session_state.db = init_db
    else:
        st.session_state.db = db_raw
        
    st.session_state.gians = gians_raw

def save_all():
    conn.update(worksheet="Sheet1", data=st.session_state.db)
    conn.update(worksheet="Gians", data=pd.DataFrame({"TenGian": st.session_state.gians}))
    conn.update(worksheet="Staffs", data=st.session_state.staffs)
    st.toast("✅ Đã đồng bộ dữ liệu lên Cloud!", icon="☁️")

# 4. CSS TÔ MÀU & GIAO DIỆN
def get_rig_style():
    # Palette màu sắc cho các giàn
    colors = ["#FF4B4B", "#45FF45", "#4545FF", "#FFFF45", "#FF45FF", "#45FFFF", "#FFA500", "#00FF7F", "#FFD700"]
    style = "<style>"
    for i, gian in enumerate(st.session_state.gians):
        color = colors[i % len(colors)]
        style += f'div[data-testid="stDataEditor"] span:contains("{gian}") {{ background-color: {color} !important; color: black !important; padding: 2px 5px; border-radius: 4px; font-weight: bold; }}'
    
    # CSS cho tiêu đề bảng (Ngày/Thứ)
    style += """
        div[data-testid="stDataEditor"] th { height: 85px !important; white-space: pre !important; text-align: center !important; vertical-align: middle !important; color: #00f2ff !important; font-size: 14px !important; }
        div[data-testid="stDataEditor"] th div { justify-content: center !important; }
        .stTabs [data-baseweb="tab-list"] { gap: 20px; }
        .stTabs [data-baseweb="tab"] { font-weight: bold; font-size: 16px; }
    </style>"""
    return style

st.markdown(get_rig_style(), unsafe_allow_html=True)

# 5. GIAO DIỆN TABS
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 TỔNG HỢP", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "📝 JOB DETAIL"])

# TAB ĐIỀU ĐỘNG
with tabs[0]:
    c1, c2, c3 = st.columns([2, 1, 1.5])
    sel_staff = c1.multiselect("CHỌN NHÂN VIÊN:", st.session_state.db['Họ và Tên'].tolist())
    status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "CA", "WS", "NP"])
    val_to_fill = c2.selectbox("CHỌN GIÀN:", st.session_state.gians) if status == "Đi Biển" else status
    dates = c3.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))
    
    if st.button("XÁC NHẬN ĐIỀU ĐỘNG", use_container_width=True, type="primary"):
        if isinstance(dates, tuple) and len(dates) == 2:
            for d in range(dates[0].day, dates[1].day + 1):
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), get_col_name(d)] = val_to_fill
            save_all()
            st.rerun()

# TAB TỔNG HỢP & TÍNH TOÁN
with tabs[1]:
    if st.button("🚀 TÍNH TOÁN NGHỈ CA (QUY ƯỚC PVD)", use_container_width=True):
        for idx, row in st.session_state.db.iterrows():
            current_bal = 0.0
            for d in range(1, 29):
                col = get_col_name(d)
                val = row[col]
                d_obj = date(2026, 2, d)
                thu = d_obj.weekday()
                
                # TÍNH CỘNG (ĐI BIỂN)
                if val in st.session_state.gians:
                    if d in NGAY_LE_TET: current_bal += 2.0
                    elif thu >= 5: current_bal += 1.0
                    else: current_bal += 0.5
                
                # TÍNH TRỪ (NGHỈ CA)
                elif val == "CA":
                    if thu < 5 and d not in NGAY_LE_TET:
                        current_bal -= 1.0
            
            # Giữ nguyên số dư cũ và cộng dồn tháng mới
            st.session_state.db.at[idx, 'Nghỉ Ca Còn Lại'] = round(current_bal, 1)
        save_all()
        st.rerun()

    display_order = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Nghỉ Ca Còn Lại', 'Job Detail'] + DATE_COLS
    col_cfg = {
        "Nghỉ Ca Còn Lại": st.column_config.NumberColumn(format="%.1f", width="small"),
        "Job Detail": st.column_config.TextColumn(width="medium")
    }
    for c in DATE_COLS:
        col_cfg[c] = st.column_config.SelectboxColumn(options=st.session_state.gians + ["CA", "WS", "NP", ""], width="small")

    edited_df = st.data_editor(st.session_state.db[display_order], use_container_width=True, height=600, column_config=col_cfg)
    
    if st.button("LƯU SỬA TAY TRÊN BẢNG"):
        st.session_state.db.update(edited_df)
        save_all()
        st.rerun()

# TAB GIÀN KHOAN
with tabs[2]:
    st.subheader("⚙️ Quản lý danh sách Giàn khoan")
    c1, c2 = st.columns(2)
    with c1:
        new_rig = st.text_input("Tên giàn mới (VD: PVD VII):")
        if st.button("Thêm Giàn"):
            if new_rig and new_rig not in st.session_state.gians:
                st.session_state.gians.append(new_rig)
                save_all()
                st.rerun()
    with c2:
        sel_rig_del = st.selectbox("Chọn giàn muốn xóa:", st.session_state.gians)
        if st.button("Xóa Giàn"):
            st.session_state.gians.remove(sel_rig_del)
            save_all()
            st.rerun()

# TAB NHÂN VIÊN
with tabs[3]:
    st.subheader("👥 Quản lý danh sách Nhân viên")
    with st.form("add_staff"):
        c1, c2, c3 = st.columns(3)
        n_name = c1.text_input("Họ và Tên:")
        n_com = c2.text_input("Công ty:", value="PVD")
        n_pos = c3.text_input("Chức danh:", value="Kỹ sư")
        if st.form_submit_button("Thêm nhân viên mới"):
            if n_name:
                new_row_staff = {"STT": len(st.session_state.staffs)+1, "Họ và Tên": n_name, "Công ty": n_com, "Chức danh": n_pos}
                st.session_state.staffs = pd.concat([st.session_state.staffs, pd.DataFrame([new_row_staff])], ignore_index=True)
                
                main_new_row = {**new_row_staff, "Nghỉ Ca Còn Lại": 0.0, "Job Detail": ""}
                for c in DATE_COLS: main_new_row[c] = ""
                st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([main_new_row])], ignore_index=True)
                save_all()
                st.rerun()
    
    st.divider()
    del_name = st.selectbox("Chọn nhân viên muốn xóa khỏi hệ thống:", st.session_state.db['Họ và Tên'].tolist())
    if st.button("Xóa Nhân Viên"):
        st.session_state.db = st.session_state.db[st.session_state.db['Họ và Tên'] != del_name]
        st.session_state.staffs = st.session_state.staffs[st.session_state.staffs['Họ và Tên'] != del_name]
        save_all()
        st.rerun()

# TAB JOB DETAIL
with tabs[4]:
    st.subheader("📝 Cập nhật Job Detail")
    sel_name_job = st.selectbox("Chọn nhân viên cập nhật Job:", st.session_state.db['Họ và Tên'].tolist(), key="job_sel")
    job_text = st.text_area("Nội dung công việc chi tiết:", height=150)
    if st.button("Lưu Job Detail"):
        st.session_state.db.loc[st.session_state.db['Họ và Tên'] == sel_name_job, 'Job Detail'] = job_text
        save_all()
        st.success(f"Đã cập nhật công việc cho {sel_name_job}")

# JS SCROLL CHO BẢNG
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
                const x = e.pageX - el.offsetLeft;
                const walk = (x - startX) * 2;
                el.scrollLeft = scrollLeft - walk;
            });
            clearInterval(interval);
        }
    }, 1000);
</script>
""", height=0)
