import streamlit as st
import pandas as pd
from datetime import datetime, date
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="PVD Management 2026", layout="wide")

# CSS tối ưu: Ẩn mọi vòng xoay load gây ức chế
st.markdown("""
    <style>
        [data-testid="stStatusWidget"] {display: none !important;}
        .stButton button {width: 100%; border-radius: 8px; font-weight: bold; height: 3em; background-color: #0e1117; border: 1px solid #00f2ff; color: #00f2ff;}
        .stButton button:hover {background-color: #00f2ff; color: black;}
        div[data-testid="stForm"] {border: 1px solid #333; padding: 20px; border-radius: 10px;}
    </style>
""", unsafe_allow_html=True)

# Hiển thị Logo và Tiêu đề
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists("logo_pvd.png"): st.image("logo_pvd.png", width=120)
with col_title:
    st.markdown('<h1 style="color: #00f2ff; text-align: center;">PVD WELL SERVICES MANAGEMENT 2026</h1>', unsafe_allow_html=True)

# --- QUẢN LÝ DỮ LIỆU (SESSION STATE) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_col_name(day):
    d = date(2026, 2, day)
    days_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    return f"{day:02d}/02\n{days_vn[d.weekday()]}"

DATE_COLS = [get_col_name(d) for d in range(1, 29)]
NGAY_LE_TET = [15, 16, 17, 18, 19, 20, 21]
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]

@st.cache_data(ttl=600) # Chỉ tải lại từ Cloud mỗi 10 phút
def load_data_from_gsheets():
    try:
        db = conn.read(worksheet="Sheet1")
        gians = conn.read(worksheet="Gians")['TenGian'].dropna().tolist()
        staffs = conn.read(worksheet="Staffs")
        return db, gians, staffs
    except:
        return pd.DataFrame(), ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"], pd.DataFrame()

# KHỞI TẠO BỘ NHỚ TẠM (Chỉ chạy 1 lần khi mở App)
if 'db' not in st.session_state:
    db_r, gians_r, staffs_r = load_data_from_gsheets()
    
    # Thiết lập Staffs
    if staffs_r.empty:
        st.session_state.staffs = pd.DataFrame({"STT": range(1, 65), "Họ và Tên": NAMES_64, "Công ty": ["PVD"]*64, "Chức danh": ["Kỹ sư"]*64})
    else: st.session_state.staffs = staffs_r

    # Thiết lập Bảng chính (Sheet1)
    if db_r.empty:
        df = st.session_state.staffs.copy()
        df["Nghỉ Ca Còn Lại"] = 0.0
        df["Job Detail"] = ""
        for c in DATE_COLS: df[c] = ""
        st.session_state.db = df
    else: st.session_state.db = db_r
    
    st.session_state.gians = gians_r

# --- GIAO DIỆN CHÍNH ---
st.divider()
col_save_l, col_save_r = st.columns([4, 1])
with col_save_r:
    if st.button("💾 LƯU CLOUD (SAVE ALL)", type="primary"):
        with st.spinner("Đang đồng bộ..."):
            conn.update(worksheet="Sheet1", data=st.session_state.db)
            conn.update(worksheet="Gians", data=pd.DataFrame({"TenGian": st.session_state.gians}))
            conn.update(worksheet="Staffs", data=st.session_state.staffs)
            st.success("Đã lưu thành công!")

tabs = st.tabs(["🚀 ĐIỀU ĐỘNG", "📊 TỔNG HỢP", "🏗️ GIÀN KHOAN", "👤 NHÂN VIÊN", "📝 CHI TIẾT", "📥 XUẤT FILE"])

with tabs[0]: # ĐIỀU ĐỘNG
    with st.form("dieu_dong_form"):
        c1, c2, c3 = st.columns([2, 1, 1.5])
        sel_staff = c1.multiselect("NHÂN VIÊN:", st.session_state.db['Họ và Tên'].tolist())
        status = c2.selectbox("TRẠNG THÁI:", ["Đi Biển", "CA", "WS", "NP"])
        val = c2.selectbox("GIÀN:", st.session_state.gians) if status == "Đi Biển" else status
        dates = c3.date_input("KHOẢNG NGÀY:", value=(date(2026, 2, 1), date(2026, 2, 2)))
        if st.form_submit_button("XÁC NHẬN"):
            if isinstance(dates, tuple) and len(dates) == 2:
                for d in range(dates[0].day, dates[1].day + 1):
                    st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(sel_staff), get_col_name(d)] = val
                st.toast("Đã cập nhật bảng tạm!")

with tabs[1]: # TỔNG HỢP
    if st.button("🚀 TÍNH NGHỈ CA (RUN)"):
        for idx, row in st.session_state.db.iterrows():
            bal = 0.0
            for d in range(1, 29):
                col = get_col_name(d); v = row[col]; d_obj = date(2026, 2, d); thu = d_obj.weekday()
                if v in st.session_state.gians:
                    bal += (2.0 if d in NGAY_LE_TET else (1.0 if thu >= 5 else 0.5))
                elif v == "CA" and thu < 5 and d not in NGAY_LE_TET: bal -= 1.0
            st.session_state.db.at[idx, 'Nghỉ Ca Còn Lại'] = round(bal, 1)
        st.rerun()
    st.session_state.db = st.data_editor(st.session_state.db, use_container_width=True, height=500)

with tabs[2]: # GIÀN KHOAN - ĐÃ SỬA LỖI HIỂN THỊ
    st.subheader("🏗️ Quản lý danh sách Giàn khoan")
    # Sử dụng data_editor để thêm/xóa trực tiếp cho mượt
    gians_df = pd.DataFrame({"TenGian": st.session_state.gians})
    edited_gians = st.data_editor(gians_df, num_rows="dynamic", use_container_width=True)
    st.session_state.gians = edited_gians['TenGian'].dropna().tolist()
    st.info("💡 Bạn có thể nhập tên giàn mới vào dòng cuối cùng, hoặc chọn dòng rồi nhấn phím Delete để xóa.")

with tabs[3]: # NHÂN VIÊN
    st.subheader("👤 Thông tin Nhân viên (64 người)")
    st.session_state.staffs = st.data_editor(st.session_state.staffs, use_container_width=True, num_rows="dynamic")
    if st.button("ĐỒNG BỘ THÔNG TIN SANG BẢNG TỔNG HỢP"):
        # Cập nhật Công ty/Chức danh từ Staffs sang DB chính dựa trên Họ và Tên
        merged = st.session_state.db.drop(columns=['Công ty', 'Chức danh'], errors='ignore')
        st.session_state.db = pd.merge(merged, st.session_state.staffs[['Họ và Tên', 'Công ty', 'Chức danh']], on='Họ và Tên', how='left')
        st.success("Đã đồng bộ!")

with tabs[4]: # CHI TIẾT
    sel_n = st.selectbox("Chọn nhân viên sửa Job Detail:", st.session_state.db['Họ và Tên'].tolist())
    idx_n = st.session_state.db[st.session_state.db['Họ và Tên'] == sel_n].index[0]
    st.session_state.db.at[idx_n, 'Job Detail'] = st.text_area("Nội dung Job Detail:", value=st.session_state.db.at[idx_n, 'Job Detail'], height=250)

with tabs[5]: # XUẤT FILE
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        st.session_state.db.to_excel(writer, index=False, sheet_name='Management')
    st.download_button("📥 TẢI FILE EXCEL (.xlsx)", data=output.getvalue(), file_name=f"PVD_Report_2026.xlsx", use_container_width=True)

# JS Cuộn ngang (Chống lag khi cuộn bảng lớn)
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
