import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="PVD Personnel Management 2026", layout="wide")

def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/Feb {days_vn[d.weekday()]}"

# 2. KHỞI TẠO DỮ LIỆU
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
        'Họ và Tên': NAMES,
        'Công ty': 'PVD',
        'Chức danh': 'Kỹ sư',
        'Nghỉ Ca Còn Lại': 0.0,
        'Job Detail': ''
    })
    for d in range(1, 29):
        df[get_col_name(d)] = ""
    st.session_state.db = df

# 3. CSS (CHỮ TO & GIAO DIỆN)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    html, body, [class*="css"] { font-size: 18px !important; }
    .main-title-text {
        font-size: 45px !important; font-weight: 900 !important; color: #3b82f6; 
        text-transform: uppercase; text-align: center; margin: 0;
    }
    /* Tối ưu hóa vùng cuộn cho Data Editor */
    div[data-testid="stDataEditor"] > div {
        overflow-x: auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. HEADER
h_col1, h_col2, h_col3 = st.columns([2, 6, 2])
with h_col1:
    try: st.image("logo_pvd.png", width=180)
    except: st.write("### PVD")
with h_col2:
    st.markdown('<p class="main-title-text">HỆ THỐNG ĐIỀU PHỐI<br>NHÂN SỰ PVD 2026</p>', unsafe_allow_html=True)

# 5. TABS
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "📝 JOB DETAIL", "👤 NHÂN VIÊN", "🏗️ GIÀN KHOAN"])

with tabs[0]: # Điều động
    c1, c2, c3 = st.columns([2, 1, 1.5])
    sel_staff = c1.multiselect("CHỌN NHÂN VIÊN:", st.session_state.db['Họ và Tên'].tolist())
    status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "Nghỉ Ca (CA)", "Làm Xưởng (WS)", "Nghỉ Phép (NP)"])
    val_to_fill = c2.selectbox("CHỌN GIÀN:", st.session_state.list_gian) if status == "Đi Biển" else ({"Nghỉ Ca (CA)": "CA", "Làm Xưởng (WS)": "WS", "Nghỉ Phép (NP)": "NP"}.get(status))
    dates = c3.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))
    if st.button("XÁC NHẬN"):
        if isinstance(dates, tuple) and len(dates) == 2:
            for d in range(dates[0].day, dates[1].day + 1):
                col = get_col_name(d)
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col] = val_to_fill
            st.rerun()

# 6. NÚT QUÉT SỐ DƯ (GÓC TRÁI)
st.markdown("---")
col_scan, _ = st.columns([1.5, 3])
with col_scan:
    if st.button("🚀 QUÉT & CẬP NHẬT SỐ DƯ", type="primary", use_container_width=True):
        ngay_le_tet = [17, 18, 19, 20, 21] # Lễ Tết tháng 2/2026
        df_tmp = st.session_state.db.copy()
        for index, row in df_tmp.iterrows():
            balance = 0.0
            for d in range(1, 29):
                col = get_col_name(d)
                val = row[col]
                d_obj = date(2026, 2, d)
                is_weekend = d_obj.weekday() >= 5 # T7, CN
                is_holiday = d in ngay_le_tet
                
                # CỘNG: Khi đi biển
                if val in st.session_state.list_gian:
                    if is_holiday: balance += 2.0
                    elif is_weekend: balance += 1.0
                    else: balance += 0.5
                
                # TRỪ: Chỉ khi là CA và KHÔNG PHẢI ngày nghỉ/lễ
                elif val == "CA":
                    if not is_weekend and not is_holiday:
                        balance -= 1.0
                
                # KHÔNG ĐỔI: Nếu là WS hoặc NP hoặc để trống
                else:
                    pass
                    
            df_tmp.at[index, 'Nghỉ Ca Còn Lại'] = round(balance, 1)
        st.session_state.db = df_tmp
        st.success("Đã tính toán xong số dư ca!")
        st.rerun()

# 7. BẢNG TỔNG HỢP (Kéo ngang/dọc & Sửa trực tiếp)
st.subheader("📊 BẢNG TỔNG HỢP NHÂN SỰ (Cho phép sửa tay & kéo cuộn)")
date_cols = [c for c in st.session_state.db.columns if "/Feb" in c]
display_order = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Nghỉ Ca Còn Lại', 'Job Detail'] + date_cols

# Lưu lại thay đổi từ bảng editor
edited_db = st.data_editor(
    st.session_state.db[display_order], 
    use_container_width=True, 
    height=600,
    disabled=['STT', 'Nghỉ Ca Còn Lại'] # Hệ thống tự quản lý 2 cột này
)

# Cập nhật ngược lại vào session_state khi người dùng sửa tay
if not edited_db.equals(st.session_state.db[display_order]):
    st.session_state.db.update(edited_df)

# 8. XUẤT EXCEL
output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    st.session_state.db.to_excel(writer, index=False)
st.download_button("📥 XUẤT BÁO CÁO", data=output.getvalue(), file_name="PVD_Report.xlsx")
