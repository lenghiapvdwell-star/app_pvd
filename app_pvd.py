import streamlit as st
import pandas as pd
from io import BytesIO
import random
from datetime import datetime, date

# 1. Cấu hình trang
st.set_page_config(page_title="PVD Personnel Management 2026", layout="wide", initial_sidebar_state="collapsed")

# 2. KHỞI TẠO BỘ NHỚ
if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

if 'rig_colors' not in st.session_state:
    st.session_state.rig_colors = {
        "PVD I": "#00558F", "PVD II": "#1E8449", "PVD III": "#8E44AD", "PVD VI": "#D35400", "PVD 11": "#2E4053"
    }

def get_col_name(day):
    d = datetime(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    month_en = d.strftime('%b')
    return f"{day:02d}/{month_en}\n{days_vn[d.weekday()]}"

NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngọc", "Đỗ Văn Tường", "Đồng Văn Trung", "Hà Viết Hùng", "Hồ Trọng Đông", "Hoàng Tùng", "Lê Hoài Nam", "Lê Hoài Phước", "Lê Minh Hoàng", "Lê Quang Minh", "Lê Quốc Duy", "Mai Nhân Dương", "Ngô Quỳnh Hải", "Ngô Xuân Điền", "Nguyễn Hoàng Quy", "Nguyễn Hữu Toàn", "Nguyễn Mạnh Cường", "Nguyễn Quốc Huy", "Nguyễn Tuấn Anh", "Nguyễn Tuấn Minh", "Nguyễn Văn Bảo Ngọc", "Nguyễn Văn Duẩn", "Nguyễn Văn Hưng", "Nguyễn Văn Võ", "Phan Tây Bắc", "Trần Văn Hoàn", "Trần Văn Hùng", "Trần Xuân Nhật", "Võ Hồng Thịnh", "Vũ Tuấn Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

if 'db' not in st.session_state:
    df = pd.DataFrame({'Họ và Tên': NAMES})
    df['Chức danh'] = 'Kỹ sư'
    df['Công ty'] = 'PVD'
    for d in range(1, 29):
        df[get_col_name(d)] = "CA"
    st.session_state.db = df

# 3. CSS: MÀU NỀN DỊU MẮT + LOGO TO
st.markdown(
    """
    <style>
    /* Màu nền dịu mắt (Soft Blue-Grey) */
    .stApp {
        background-color: #F0F2F5 !important;
    }
    
    [data-testid="collapsedControl"] { display: none; }
    
    /* Logo to 225px */
    .pvd-logo-fixed {
        position: fixed;
        top: 25px;
        left: 20px;
        z-index: 10000;
        width: 225px;
    }
    
    /* Đẩy nội dung sang phải */
    .main .block-container {
        padding-left: 280px; 
        padding-right: 30px;
        background-color: transparent;
    }
    
    /* Tiêu đề chính */
    .main-header {
        color: #004080;
        font-size: 28px;
        font-weight: bold;
        margin-bottom: 25px;
        padding-bottom: 10px;
        border-bottom: 2px solid #00558F;
    }

    /* Các Tab trắng nhẹ để tách biệt với nền */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #F0F2F5;
    }
    
    /* Container trắng cho phần nhập liệu */
    [data-testid="stVerticalBlock"] > div:has(div.stExpander) {
        background: white;
        padding: 15px;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Hiển thị Logo từ file nội bộ
try:
    st.image("logo_pvd.png", width=225)
    st.markdown('<div class="pvd-logo-fixed"></div>', unsafe_allow_html=True)
except:
    st.sidebar.warning("Hãy đảm bảo file logo_pvd.png đã được upload.")

st.markdown("<div class='main-header'>HỆ THỐNG ĐIỀU PHỐI NHÂN SỰ PV DRILLING 2026</div>", unsafe_allow_html=True)

# 4. TABS CHỨC NĂNG
tab_rig, tab_info, tab_manage = st.tabs(["🚀 Chấm công & Đi biển", "📝 Hồ sơ Nhân viên", "🏗️ Quản lý Giàn"])

with tab_rig:
    with st.container():
        c1, c2, c3 = st.columns([2, 1.5, 1.5])
        with c1:
            sel_staff = st.multiselect("1. Chọn nhân viên:", NAMES)
        with c2:
            status_opt = st.selectbox("2. Trạng thái:", ["Đi Biển", "Nghỉ CA (CA)", "Làm Việc (WS)", "Nghỉ Phép (P)", "Nghỉ Ốm (S)"])
            if status_opt == "Đi Biển":
                final_val = st.selectbox("Chọn Giàn cụ thể:", st.session_state.list_gian)
            else:
                final_val = {"Nghỉ CA (CA)": "CA", "Làm Việc (WS)": "WS", "Nghỉ Phép (P)": "P", "Nghỉ Ốm (S)": "S"}[status_opt]
        with c3:
            sel_dates = st.date_input("3. Chọn khoảng ngày:", 
                                      value=(date(2026, 2, 1), date(2026, 2, 7)),
                                      min_value=date(2026, 2, 1), 
                                      max_value=date(2026, 2, 28))

        if st.button("XÁC NHẬN CẬP NHẬT", type="primary"):
            if isinstance(sel_dates, tuple) and len(sel_dates) == 2:
                start_d, end_d = sel_dates[0].day, sel_dates[1].day
                for d in range(start_d, end_d + 1):
                    col_name = get_col_name(d)
                    st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col_name] = final_val
                st.success("Đã cập nhật dữ liệu!")
                st.rerun()

with tab_info:
    c_staff, c_role, c_corp = st.columns([2, 1, 1])
    with c_staff: info_staff = st.multiselect("Chọn nhân viên để sửa hồ sơ:", NAMES, key="info_staff")
    with c_role: new_role = st.text_input("Chức danh:")
    with c_corp: new_corp = st.text_input("Công ty:")
    if st.button("Lưu thay đổi"):
        if new_role: st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(info_staff), 'Chức danh'] = new_role
        if new_corp: st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(info_staff), 'Công ty'] = new_corp
        st.success("Hồ sơ đã lưu!")

with tab_manage:
    ca, cb = st.columns(2)
    with ca:
        new_rig = st.text_input("Thêm Giàn mới:")
        if st.button("Lưu Giàn"):
            st.session_state.list_gian.append(new_rig)
            st.session_state.rig_colors[new_rig] = "#%06x" % random.randint(0, 0xFFFFFF)
            st.rerun()
    with cb:
        rig_del = st.selectbox("Xóa Giàn:", st.session_state.list_gian)
        if st.button("Thực hiện Xóa"):
            st.session_state.list_gian.remove(rig_del)
            st.rerun()

# 5. HIỂN THỊ BẢNG
st.subheader("📅 Chi tiết bảng điều phối")

def style_cells(val):
    if val in st.session_state.list_gian:
        color = st.session_state.rig_colors.get(val, "#00558F")
        return f'color: {color}; font-weight: bold; background-color: #FFFFFF; border: 1px solid #E0E0E0;'
    styles = {
        "P": 'background-color: #FFEBEE; color: #C62828; font-weight: bold;',
        "S": 'background-color: #F3E5F5; color: #7B1FA2; font-weight: bold;',
        "WS": 'background-color: #FFF9C4; color: #F57F17; font-weight: bold;'
    }
    return styles.get(val, 'color: #B0BEC5; background-color: #FFFFFF;')

cols = list(st.session_state.db.columns)
df_display = st.session_state.db[[cols[0], 'Chức danh', 'Công ty'] + cols[3:]]

# Hiển thị bảng với style dịu mắt
st.dataframe(df_display.style.applymap(style_cells, subset=df_display.columns[3:]), use_container_width=True, height=600)

# 6. XUẤT EXCEL
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.download_button("📥 XUẤT FILE EXCEL", data=to_excel(st.session_state.db), file_name="PVD_2026_Report.xlsx")
