import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="PVD Well Services 2026", layout="wide")

# Hàm lấy tên cột: Ngày/Tháng \n Thứ
def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/02\n{days_vn[d.weekday()]}"

DATE_COLS = [get_col_name(d) for d in range(1, 29)]

# 2. KẾT NỐI GOOGLE SHEETS
# Lưu ý: Bạn cần cấu hình URL trong file .streamlit/secrets.toml hoặc mục Secrets trên Streamlit Cloud
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data_from_gs():
    try:
        # Đọc dữ liệu từ Google Sheets
        return conn.read(ttl=0) # ttl=0 để luôn lấy dữ liệu mới nhất
    except:
        return None

def save_data_to_gs(df):
    # Cập nhật dữ liệu ngược lại Google Sheets
    conn.update(data=df)
    st.success("Dữ liệu đã được lưu vĩnh viễn trên Google Sheets!")

# 3. KHỞI TẠO DỮ LIỆU BAN ĐẦU (Chỉ chạy 1 lần duy nhất)
if 'db' not in st.session_state:
    existing_data = load_data_from_gs()
    if existing_data is not None and not existing_data.empty:
        st.session_state.db = existing_data
    else:
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
        df_init = pd.DataFrame(init_data)
        st.session_state.db = df_init
        # Lưu lần đầu lên Sheets
        save_data_to_gs(df_init)

if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

# 4. CSS (GIỮ NGUYÊN BỐ CỤC SẠCH)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .main-title-container {
        text-align: center; padding-bottom: 15px; border-bottom: 4px solid #00f2ff;
        box-shadow: 0px 8px 20px -10px #00f2ff; margin-bottom: 30px;
    }
    .main-title-text { font-size: 38px !important; font-weight: 900; color: #00f2ff; margin: 0; }
    div[data-testid="stDataEditor"] th {
        height: 80px !important; white-space: pre !important; text-align: center !important;
        vertical-align: middle !important; color: #00f2ff !important; pointer-events: none;
    }
    div[data-testid="stDataEditor"] span:contains("None") { color: transparent !important; }
    </style>
    """, unsafe_allow_html=True)

# 5. HEADER
st.markdown('<div class="main-title-container">', unsafe_allow_html=True)
st.markdown('<p class="main-title-text">PVD WELL SERVICES MANAGEMENT 2026 (CLOUD SYNC)</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 6. TABS
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "📝 JOB DETAIL", "👤 NHÂN VIÊN", "🏗️ GIÀN KHOAN"])

with tabs[0]: # ĐIỀU ĐỘNG
    c1, c2, c3 = st.columns([2, 1, 1.5])
    sel_staff = c1.multiselect("CHỌN NHÂN VIÊN:", st.session_state.db['Họ và Tên'].tolist())
    status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "Nghỉ Ca (CA)", "Làm Xưởng (WS)", "Nghỉ Phép (NP)"])
    val_to_fill = c2.selectbox("CHỌN GIÀN:", st.session_state.list_gian) if status == "Đi Biển" else ({"Nghỉ Ca (CA)": "CA", "Làm Xưởng (WS)": "WS", "Nghỉ Phép (NP)": "NP"}.get(status))
    dates = c3.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))
    if st.button("XÁC NHẬN & LƯU LÊN CLOUD", use_container_width=True):
        if isinstance(dates, tuple) and len(dates) == 2:
            for d in range(dates[0].day, dates[1].day + 1):
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), get_col_name(d)] = val_to_fill
            save_data_to_gs(st.session_state.db)
            st.rerun()

# 7. QUÉT SỐ DƯ (LOGIC CHUẨN)
st.markdown("---")
if st.button("🚀 QUÉT & ĐỒNG BỘ SỐ DƯ (CLOUD)", type="primary", use_container_width=True):
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
    save_data_to_gs(df_tmp)
    st.rerun()

# 8. BẢNG TỔNG HỢP
st.write("### 📊 BẢNG TỔNG HỢP NHÂN SỰ")
display_order = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Nghỉ Ca Còn Lại', 'Job Detail'] + DATE_COLS
all_options = st.session_state.list_gian + ["CA", "WS", "NP"]

col_cfg = {
    "STT": st.column_config.NumberColumn(width="small"),
    "Nghỉ Ca Còn Lại": st.column_config.NumberColumn(format="%.1f", width="small"),
}
for c in DATE_COLS:
    col_cfg[c] = st.column_config.SelectboxColumn(width="small", options=all_options)

edited_df = st.data_editor(
    st.session_state.db[display_order], 
    use_container_width=True, height=600, 
    column_config=col_cfg,
    disabled=['STT', 'Nghỉ Ca Còn Lại']
)

# Nút lưu thủ công nếu sửa trực tiếp trên bảng
if st.button("LƯU THAY ĐỔI TRÊN BẢNG"):
    st.session_state.db = edited_df
    save_data_to_gs(edited_df)

# 9. XUẤT EXCEL & KÉO CHUỘT (GIỮ NGUYÊN)
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
                const x = e.pageX - el.offsetLeft;
                const walk = (x - startX) * 2;
                el.scrollLeft = scrollLeft - walk;
            });
            clearInterval(interval);
        }
    }, 1000);
</script>
""", height=0)
