import streamlit as st
import pandas as pd
from io import BytesIO
import random
from datetime import datetime, date

# 1. Cấu hình trang
st.set_page_config(page_title="PV Drilling Management 2026", layout="wide", initial_sidebar_state="collapsed")

# 2. KHỞI TẠO BỘ NHỚ
if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

if 'rig_colors' not in st.session_state:
    st.session_state.rig_colors = {
        "PVD I": "#00558F", "PVD II": "#1E8449", "PVD III": "#8E44AD", "PVD VI": "#D35400", "PVD 11": "#2E4053"
    }

# Hàm định dạng tiêu đề cột: Ngày/Tháng \n Thứ
def get_col_name(day):
    # Giả định chạy cho năm 2026
    d = datetime(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    month_en = d.strftime('%b') # Lấy tên tháng viết tắt (Feb, Mar...)
    return f"{day:02d}/{month_en}\n{days_vn[d.weekday()]}"

NAMES = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Duc Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manu Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

if 'db' not in st.session_state:
    df = pd.DataFrame({'Họ và Tên': NAMES})
    df['Chức danh'] = 'Kỹ sư'
    df['Công ty'] = 'PVD'
    # Khởi tạo dữ liệu cho tháng 2 (28 ngày)
    for d in range(1, 29):
        df[get_col_name(d)] = "CA"
    st.session_state.db = df

# 3. CSS LOGO TỪ FILE UPLOAD VÀ GIAO DIỆN
# Lưu ý: file logo_pvd.png phải nằm cùng thư mục với file app này
st.markdown(
    """
    <style>
    [data-testid="collapsedControl"] { display: none; }
    
    .pvd-logo {
        position: fixed;
        top: 15px;
        left: 15px;
        z-index: 10000;
        width: 90px;
        background: white;
        padding: 5px;
        border-radius: 5px;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
    }
    
    .main .block-container {
        padding-left: 130px;
        padding-right: 20px;
    }
    
    .main-header {
        color: #00558F;
        font-size: 26px;
        font-weight: bold;
        border-bottom: 2px solid #00558F;
        margin-bottom: 20px;
    }

    /* Định dạng cột ngày tháng xuống dòng */
    thead tr th {
        white-space: pre-wrap !important;
        text-align: center !important;
        font-size: 12px !important;
        background-color: #F0F2F6 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Hiển thị Logo từ file nội bộ
try:
    st.image("logo_pvd.png", width=90, output_format="PNG")
    # Sử dụng CSS để biến hình ảnh này thành vị trí cố định (hack nhẹ cho Streamlit)
    st.markdown('<div class="pvd-logo"></div>', unsafe_allow_html=True)
except:
    st.sidebar.error("Không tìm thấy file logo_pvd.png")

st.markdown("<div class='main-header'>HỆ THỐNG ĐIỀU PHỐI NHÂN SỰ PVD 2026</div>", unsafe_allow_html=True)

# 4. TABS CHỨC NĂNG
tab_rig, tab_info, tab_manage = st.tabs(["🚀 Chấm công & Đi biển", "📝 Hồ sơ Nhân viên", "🏗️ Quản lý Giàn"])

with tab_rig:
    c1, c2, c3 = st.columns([2, 1.5, 1.5])
    with c1:
        sel_staff = st.multiselect("1. Chọn nhân viên:", NAMES)
    with c2:
        status_opt = st.selectbox("2. Chọn trạng thái:", ["Đi Biển", "Nghỉ CA (CA)", "Làm Việc (WS)", "Nghỉ Phép (P)", "Nghỉ Ốm (S)"])
        if status_opt == "Đi Biển":
            final_val = st.selectbox("Chọn Giàn cụ thể:", st.session_state.list_gian)
        else:
            mapping = {"Nghỉ CA (CA)": "CA", "Làm Việc (WS)": "WS", "Nghỉ Phép (P)": "P", "Nghỉ Ốm (S)": "S"}
            final_val = mapping[status_opt]
    with c3:
        # LỊCH Ô VUÔNG ĐỂ TÍCH NGÀY ĐI - NGÀY VỀ
        sel_dates = st.date_input("3. Chọn khoảng ngày trên lịch:", 
                                  value=(date(2026, 2, 1), date(2026, 2, 7)),
                                  min_value=date(2026, 2, 1), 
                                  max_value=date(2026, 2, 28))

    if st.button("XÁC NHẬN CẬP NHẬT KHOẢNG NGÀY", type="primary"):
        if isinstance(sel_dates, tuple) and len(sel_dates) == 2:
            start_d, end_d = sel_dates[0].day, sel_dates[1].day
            for d in range(start_d, end_d + 1):
                col_name = get_col_name(d)
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col_name] = final_val
            st.success(f"Đã điền {final_val} từ ngày {start_d} đến {end_d}")
            st.rerun()

with tab_info:
    c_staff, c_role, c_corp = st.columns([2, 1, 1])
    with c_staff: info_staff = st.multiselect("Chọn nhân viên:", NAMES, key="info")
    with c_role: new_role = st.text_input("Chức danh mới:")
    with c_corp: new_corp = st.text_input("Công ty mới:")
    if st.button("Lưu hồ sơ"):
        if new_role: st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(info_staff), 'Chức danh'] = new_role
        if new_corp: st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(info_staff), 'Công ty'] = new_corp
        st.success("Đã cập nhật hồ sơ!")

with tab_manage:
    ca, cb = st.columns(2)
    with ca:
        new_rig = st.text_input("Thêm Giàn mới:")
        if st.button("Thêm"):
            if new_rig and new_rig not in st.session_state.list_gian:
                st.session_state.list_gian.append(new_rig)
                st.session_state.rig_colors[new_rig] = "#%06x" % random.randint(0, 0xFFFFFF)
                st.rerun()
    with cb:
        rig_del = st.selectbox("Xóa Giàn viết sai:", st.session_state.list_gian)
        if st.button("Xóa ngay"):
            st.session_state.list_gian.remove(rig_del)
            st.rerun()

# 5. HIỂN THỊ BẢNG
st.subheader("📅 Bảng chi tiết Tháng 02/2026")

def style_cells(val):
    if val in st.session_state.list_gian:
        color = st.session_state.rig_colors.get(val, "#00558F")
        return f'color: {color}; font-weight: bold; background-color: #F0F8FF;'
    styles = {
        "P": 'background-color: #FADBD8; color: #7B241C; font-weight: bold;',
        "S": 'background-color: #E8DAEF; color: #512E5F; font-weight: bold;',
        "WS": 'background-color: #FCF3CF; color: #7D6608; font-weight: bold;'
    }
    return styles.get(val, 'color: #BDC3C7;')

# Hiển thị bảng dữ liệu
cols = list(st.session_state.db.columns)
df_display = st.session_state.db[[cols[0], 'Chức danh', 'Công ty'] + cols[3:]]

st.dataframe(
    df_display.style.applymap(style_cells, subset=df_display.columns[3:]),
    use_container_width=True, 
    height=600
)

# 6. XUẤT EXCEL
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.download_button("📥 XUẤT FILE EXCEL BÁO CÁO", data=to_excel(st.session_state.db), file_name="PVD_2026.xlsx")
