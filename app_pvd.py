import streamlit as st
import pandas as pd
from io import BytesIO
import random
from datetime import datetime, date
from streamlit_gsheets import GSheetsConnection

# 1. Cấu hình trang
st.set_page_config(page_title="PVD Management 2026", layout="wide", initial_sidebar_state="collapsed")

# 2. Kết nối Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def get_col_name(day):
    d = datetime(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    month_en = d.strftime('%b')
    return f"{day:02d}/{month_en}\n{days_vn[d.weekday()]}"

NAMES = ["Bùi Anh Phương", "Lê Thái Việt", "Lê Tùng Phong", "Nguyễn Tiến Dũng", "Nguyễn Văn Quang", "Phạm Hồng Minh", "Nguyễn Gia Khánh", "Nguyễn Hữu Lộc", "Nguyễn Tấn Đạt", "Chu Văn Trường", "Hồ Sỹ Đức", "Hoàng Thái Sơn", "Phạm Thái Bảo", "Cao Trung Nam", "Lê Trọng Nghĩa", "Nguyễn Văn Mạnh", "Nguyễn Văn Sơn", "Dương Mạnh Quyết", "Trần Quốc Huy", "Rusliy Saifuddin", "Đào Tiến Thành", "Đoàn Minh Quân", "Rawing Empanit", "Bùi Sỹ Xuân", "Cao Văn Thắng", "Cao Xuân Vinh", "Đàm Quang Trung", "Đào Văn Tám", "Đinh Duy Long", "Đinh Ngọc Hiếu", "Đỗ Đức Ngọc", "Đỗ Văn Tường", "Đồng Văn Trung", "Hà Viết Hùng", "Hồ Trọng Đông", "Hoàng Tùng", "Lê Hoài Nam", "Lê Hoài Phước", "Lê Minh Hoàng", "Lê Quang Minh", "Lê Quốc Duy", "Mai Nhân Dương", "Ngô Quỳnh Hải", "Ngô Xuân Điền", "Nguyễn Hoàng Quy", "Nguyễn Hữu Toàn", "Nguyễn Mạnh Cường", "Nguyễn Quốc Huy", "Nguyễn Tuấn Anh", "Nguyễn Tuấn Minh", "Nguyễn Văn Bảo Ngọc", "Nguyễn Văn Duẩn", "Nguyễn Văn Hưng", "Nguyễn Văn Võ", "Phan Tây Bắc", "Trần Văn Hoàn", "Trần Văn Hùng", "Trần Xuân Nhật", "Võ Hồng Thịnh", "Vũ Tuấn Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Trần Tuấn Dũng"]

# 3. KHỞI TẠO BỘ NHỚ
if 'list_gian' not in st.session_state:
    st.session_state.list_gian = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

if 'rig_colors' not in st.session_state:
    st.session_state.rig_colors = {"PVD I": "#00D4FF", "PVD II": "#39FF14", "PVD III": "#FFD700", "PVD VI": "#FF8C00", "PVD 11": "#FFFFFF"}

if 'db' not in st.session_state:
    try:
        # Ưu tiên tải dữ liệu từ Google Sheets nếu có
        df_cloud = conn.read(worksheet="PVD_Data", ttl=0)
        if not df_cloud.empty:
            st.session_state.db = df_cloud
    except:
        # Nếu lỗi kết nối, tạo dữ liệu mới
        df = pd.DataFrame({'Họ và Tên': NAMES, 'Chức danh': 'Kỹ sư', 'Công ty': 'PVD'})
        for d in range(1, 29):
            df[get_col_name(d)] = "" 
        st.session_state.db = df

# 4. CSS (Nền Xanh Blue + Logo 2.5x)
st.markdown(
    """
    <style>
    .stApp { background-color: #0A192F !important; color: #E6F1FF !important; }
    .pvd-logo-fixed { position: fixed; top: 25px; left: 20px; z-index: 10000; width: 225px; }
    .main .block-container { padding-left: 290px; padding-right: 30px; }
    .main-header { color: #64FFDA; font-size: 32px; font-weight: 800; border-bottom: 2px solid #64FFDA; padding-bottom: 10px; }
    thead tr th { background-color: #112240 !important; color: #CCD6F6 !important; white-space: pre-wrap !important; }
    </style>
    """, unsafe_allow_html=True
)

st.image("logo_pvd.png", width=225)
st.markdown("<div class='pvd-logo-fixed'></div>", unsafe_allow_html=True)
st.markdown("<div class='main-header'>PV DRILLING PERSONNEL MANAGEMENT 2026</div>", unsafe_allow_html=True)

# 5. GIỮ NGUYÊN CÁC TAB CŨ
tab_rig, tab_info, tab_manage, tab_cloud = st.tabs(["🚀 CHẤM CÔNG", "📝 HỒ SƠ", "🏗️ GIÀN", "🌐 LƯU CLOUD"])

with tab_rig:
    c1, c2, c3 = st.columns([2, 1.5, 1.5])
    with c1: sel_staff = st.multiselect("Nhân viên:", NAMES)
    with c2:
        status_opt = st.selectbox("Trạng thái:", ["Đi Biển", "Nghỉ CA (CA)", "Làm Việc (WS)", "Nghỉ Phép (P)", "Nghỉ Ốm (S)"])
        final_val = st.selectbox("Giàn:", st.session_state.list_gian) if status_opt == "Đi Biển" else ( "CA" if status_opt == "Nghỉ CA (CA)" else {"Làm Việc (WS)": "WS", "Nghỉ Phép (P)": "P", "Nghỉ Ốm (S)": "S"}[status_opt])
    with c3: sel_dates = st.date_input("Chọn ngày:", value=(date(2026, 2, 1), date(2026, 2, 7)), min_value=date(2026, 2, 1), max_value=date(2026, 2, 28))
    if st.button("🔥 CẬP NHẬT DỮ LIỆU", type="primary", use_container_width=True):
        if isinstance(sel_dates, tuple) and len(sel_dates) == 2:
            start_d, end_d = sel_dates[0].day, sel_dates[1].day
            for d in range(start_d, end_d + 1):
                col_name = get_col_name(d)
                st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), col_name] = final_val
            st.rerun()

with tab_info:
    c_s, c_r, c_c = st.columns([2, 1, 1])
    with c_s: i_staff = st.multiselect("Chọn nhân sự:", NAMES, key="info_k")
    with c_r: n_role = st.text_input("Chức danh:")
    with c_c: n_corp = st.text_input("Đơn vị:")
    if st.button("💾 LƯU HỒ SƠ"):
        if n_role: st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(i_staff), 'Chức danh'] = n_role
        if n_corp: st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(i_staff), 'Công ty'] = n_corp
        st.success("Hồ sơ đã được lưu tạm!")

with tab_manage:
    ca, cb = st.columns(2)
    with ca:
        new_rig = st.text_input("Thêm Giàn mới:")
        if st.button("THÊM"):
            st.session_state.list_gian.append(new_rig)
            st.session_state.rig_colors[new_rig] = "#%06x" % random.randint(0, 0xFFFFFF)
            st.rerun()
    with cb:
        rig_del = st.selectbox("Xóa Giàn:", st.session_state.list_gian)
        if st.button("XÓA"):
            st.session_state.list_gian.remove(rig_del)
            st.rerun()

with tab_cloud:
    st.info("Nhấn nút dưới đây để đồng bộ toàn bộ dữ liệu lên Google Sheets. Bạn của bạn chỉ cần Refresh trang là thấy.")
    if st.button("🌐 ĐỒNG BỘ LÊN GOOGLE SHEETS", use_container_width=True):
        try:
            conn.update(worksheet="PVD_Data", data=st.session_state.db)
            st.success("✅ Đã lưu lên Cloud thành công!")
        except Exception as e:
            st.error(f"Lỗi: Hãy chắc chắn bạn đã tạo tab 'PVD_Data' trong Google Sheet. {e}")

# 6. HIỂN THỊ BẢNG (Sửa lỗi map)
st.subheader("BẢNG TỔNG HỢP CHI TIẾT")

def style_cells(val):
    if val == "": return 'background-color: #0A192F;'
    if val in st.session_state.list_gian:
        color = st.session_state.rig_colors.get(val, "#64FFDA")
        return f'color: {color}; font-weight: bold; background-color: #112240; border: 0.5px solid #233554;'
    if val == "CA": return 'color: #FFFFFF; font-weight: bold; background-color: #1B2631;' 
    styles = {"P": 'background-color: #F44336; color: white; font-weight: bold;', "S": 'background-color: #9C27B0; color: white; font-weight: bold;', "WS": 'background-color: #FFEB3B; color: #0A192F; font-weight: bold;'}
    return styles.get(val, 'background-color: #0A192F;')

cols = list(st.session_state.db.columns)
df_display = st.session_state.db[[cols[0], 'Chức danh', 'Công ty'] + cols[3:]]
# Sửa lỗi: Thay applymap bằng map
st.dataframe(df_display.style.map(style_cells, subset=df_display.columns[3:]), use_container_width=True, height=650)

# 7. XUẤT EXCEL
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.download_button("📥 TẢI EXCEL", data=to_excel(st.session_state.db), file_name="PVD_2026.xlsx", use_container_width=True)
