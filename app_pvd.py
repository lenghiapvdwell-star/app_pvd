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

# 2. KHỞI TẠO BỘ NHỚ & DANH SÁCH 64 NHÂN VIÊN
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

# 3. CSS CUSTOM: NỀN TỐI & HEADER CĂN GIỮA
st.markdown("""
    <style>
    /* Nền tối cho App */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    .header-block {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 10px 0px 30px 0px;
    }
    .main-title {
        font-size: 45px !important; /* Nhỏ lại xíu theo ý bạn */
        font-weight: 800 !important;
        color: #3b82f6; 
        margin-top: 15px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    /* Tùy chỉnh Tabs trên nền tối */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1f2937;
        border-radius: 5px 5px 0px 0px;
        color: white;
        padding: 10px 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. HEADER: LOGO NỐI TIẾP TIÊU ĐỀ (CĂN GIỮA)
st.markdown('<div class="header-block">', unsafe_allow_html=True)
try:
    st.image("logo_pvd.png", width=200) # Logo to vừa phải
except:
    st.write("### [ LOGO PVD ]")
st.markdown('<p class="main-title">HỆ THỐNG ĐIỀU PHỐI NHÂN SỰ PVD 2026</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 5. CÁC TABS CHỨC NĂNG
tabs = st.tabs(["🚀 Điều Động", "👤 Thêm Nhân Viên", "✍️ Chỉnh Sửa Tay", "🔍 Quét Số Dư", "🏗️ Quản Lý Giàn"])

with tabs[0]: # Điều động
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

with tabs[1]: # Thêm nhân viên
    with st.form("add_new"):
        n_name = st.text_input("Họ và Tên:")
        n_corp = st.text_input("Công ty:", value="PVD")
        n_pos = st.text_input("Chức danh:", value="Kỹ sư")
        if st.form_submit_button("Lưu nhân viên"):
            if n_name:
                new_stt = len(st.session_state.db) + 1
                new_row = {'STT': new_stt, 'Họ và Tên': n_name, 'Công ty': n_corp, 'Chức danh': n_pos, 'Nghỉ Ca Còn Lại': 0.0, 'Job Detail': ''}
                for d in range(1, 29): new_row[get_col_name(d)] = ""
                st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_row])], ignore_index=True)
                st.rerun()

with tabs[3]: # Quét số dư
    if st.button("🚀 QUÉT TOÀN BỘ & CHỐT THÁNG"):
        tet_2026 = [17, 18, 19, 20, 21]
        df_tmp = st.session_state.db.copy()
        for index, row in df_tmp.iterrows():
            balance = 0.0
            for d in range(1, 29):
                col = get_col_name(d)
                if col in df_tmp.columns:
                    val = row[col]
                    d_obj = date(2026, 2, d)
                    if val in st.session_state.list_gian:
                        if d in tet_2026: balance += 2.0
                        elif d_obj.weekday() >= 5: balance += 1.0
                        else: balance += 0.5
                    elif val == "CA": balance -= 1.0
            df_tmp.at[index, 'Nghỉ Ca Còn Lại'] = float(balance)
        st.session_state.db = df_tmp
        st.balloons()
        st.rerun()

# 6. HIỂN THỊ BẢNG DỮ LIỆU SẮC NÉT
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

# 7. XUẤT EXCEL
output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    st.session_state.db.to_excel(writer, index=False)
st.download_button("📥 XUẤT FILE BÁO CÁO", data=output.getvalue(), file_name="PVD_Report_2026.xlsx")
