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

# 2. KHỞI TẠO BỘ NHỚ
if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

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

# 3. CSS TỔNG THỂ: LOGO TRÁI TUYỆT ĐỐI & CHỮ SIÊU TO
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    
    /* Phóng to font chữ toàn hệ thống */
    html, body, [class*="css"], .stMarkdown, p, li { font-size: 20px !important; }
    label { font-size: 24px !important; font-weight: bold !important; color: #3b82f6 !important; }
    .stButton>button { font-size: 24px !important; font-weight: bold; height: 3.5em; border-radius: 10px; }
    
    /* Cấu trúc Header */
    .header-box {
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        padding: 30px 0;
        border-bottom: 3px solid #3b82f6;
        margin-bottom: 40px;
    }
    .logo-left {
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        background-color: white; /* Tạo nền trắng cho logo nổi bật trên nền tối */
        padding: 10px;
        border-radius: 8px;
    }
    .main-title-text {
        font-size: 60px !important;
        font-weight: 900 !important;
        color: #3b82f6; 
        text-transform: uppercase;
        text-align: center;
        line-height: 1.1;
        margin: 0;
        letter-spacing: 2px;
    }
    
    /* Phóng to Tabs */
    .stTabs [data-baseweb="tab"] { font-size: 26px !important; height: 70px !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. HIỂN THỊ HEADER VỚI LOGO TRỰC TIẾP
st.markdown(f"""
    <div class="header-box">
        <div class="logo-left">
            <img src="https://www.pvdrilling.com.vn/images/logo.png" width="220">
        </div>
        <p class="main-title-text">HỆ THỐNG ĐIỀU PHỐI<br>NHÂN SỰ PVD 2026</p>
    </div>
    """, unsafe_allow_html=True)

# 5. TABS CHỨC NĂNG (TO RÕ)
tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "📝 NHẬP JOB DETAIL", "👤 NHÂN VIÊN", "✍️ CHỈNH SỬA", "🔍 QUÉT SỐ DƯ", "🏗️ GIÀN KHOAN"])

with tabs[0]: # Điều động
    c1, c2, c3 = st.columns([2, 1, 1.5])
    sel_staff = c1.multiselect("CHỌN NHÂN VIÊN:", st.session_state.db['Họ và Tên'].tolist())
    status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "Nghỉ Ca (CA)", "Làm Xưởng (WS)", "Nghỉ Phép (NP)"])
    val_to_fill = ""
    if status == "Đi Biển":
        val_to_fill = c2.selectbox("CHỌN GIÀN KHOAN:", st.session_state.list_gian)
    else:
        mapping = {"Nghỉ Ca (CA)": "CA", "Làm Xưởng (WS)": "WS", "Nghỉ Phép (NP)": "NP"}
        val_to_fill = mapping.get(status, status)
    dates = c3.date_input("KHOẢNG NGÀY ĐIỀU ĐỘNG:", value=(date(2026, 2, 1), date(2026, 2, 2)))
    if st.button("XÁC NHẬN CẬP NHẬT DỮ LIỆU"):
        if isinstance(dates, tuple) and len(dates) == 2:
            for d in range(dates[0].day, dates[1].day + 1):
                col = get_col_name(d)
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col] = val_to_fill
            st.rerun()

with tabs[1]: # Job Detail
    st.subheader("📝 Nhập chi tiết nội dung công việc")
    with st.form("job_form"):
        sel_job_staff = st.multiselect("Chọn nhân viên thực hiện:", st.session_state.db['Họ và Tên'].tolist())
        job_text = st.text_area("Nội dung Job (to rõ):", height=200)
        if st.form_submit_button("LƯU CHI TIẾT CÔNG VIỆC"):
            if sel_job_staff:
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_job_staff), 'Job Detail'] = job_text
                st.success("Hệ thống đã lưu thành công!")
                st.rerun()

with tabs[4]: # Quét số dư
    if st.button("🚀 CHỐT SỐ DƯ THÁNG 02/2026"):
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
            df_tmp.at[index, 'Nghỉ Ca Còn Lại'] = round(float(balance), 1)
        st.session_state.db = df_tmp
        st.balloons()
        st.rerun()

# 6. HIỂN THỊ BẢNG (Font to + Format số đẹp)
st.markdown("---")
date_cols = [c for c in st.session_state.db.columns if "/Feb" in c]
display_order = ['STT', 'Họ và Tên', 'Nghỉ Ca Còn Lại', 'Job Detail'] + date_cols

def style_cells(val):
    if not val or val == "": return ""
    base = 'font-weight: bold; font-size: 18px; color: white;'
    if val in st.session_state.list_gian: return base + 'background-color: #00558F;'
    if val == "CA": return base + 'background-color: #E74C3C;'
    if val == "WS": return 'font-weight: bold; font-size: 18px; color: black; background-color: #F1C40F;'
    if val == "NP": return base + 'background-color: #9B59B6;'
    return ''

def format_bal(v):
    return str(int(v)) if v == int(v) else str(v)

df_view = st.session_state.db[display_order].copy()
df_view['Nghỉ Ca Còn Lại'] = df_view['Nghỉ Ca Còn Lại'].apply(format_bal)

st.dataframe(
    df_view.style.applymap(style_cells, subset=date_cols),
    use_container_width=True, height=800
)

# 7. XUẤT EXCEL
output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    st.session_state.db.to_excel(writer, index=False)
st.download_button("📥 XUẤT FILE BÁO CÁO EXCEL", data=output.getvalue(), file_name="PVD_Report_2026.xlsx")
