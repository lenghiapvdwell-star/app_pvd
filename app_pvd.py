import streamlit as st
import pandas as pd
from datetime import datetime, date
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

# --- 2. QUY ƯỚC DỮ LIỆU ---
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]
DATE_COLS = [f"{d:02d}/02" for d in range(1, 29)]
HOLIDAYS = [15, 16, 17, 18, 19] # Tết 2026

# --- 3. KHỞI TẠO KẾT NỐI ---
conn = st.connection("gsheets", type=GSheetsConnection)

if 'db' not in st.session_state:
    try:
        df_load = conn.read(worksheet="Sheet1")
        if df_load is None or df_load.empty: raise Exception
        st.session_state.db = df_load
    except:
        df_init = pd.DataFrame({'STT': range(1, 65), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư'})
        for c in DATE_COLS: df_init[c] = ""
        st.session_state.db = df_init

if 'gians' not in st.session_state:
    st.session_state.gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

if 'v_key' not in st.session_state:
    st.session_state.v_key = 0

# --- 4. HÀM TÍNH TOÁN QUỸ CA (QUY ƯỚC GỐC) ---
def apply_pvd_logic(df):
    gians = st.session_state.gians
    def calc_row(row):
        total = 0.0
        for col in DATE_COLS:
            if col in row.index:
                val = str(row[col]).strip()
                if not val or val.lower() in ["nan", "none", ""]: continue
                
                day_num = int(col.split('/')[0])
                dt = date(2026, 2, day_num)
                is_weekend = dt.weekday() >= 5
                is_holiday = day_num in HOLIDAYS
                
                # CỘNG NGÀY ĐI BIỂN
                if val in gians:
                    if is_holiday: total += 2.0
                    elif is_weekend: total += 1.0
                    else: total += 0.5
                # TRỪ NGÀY NGHỈ CA
                elif val.upper() == "CA":
                    if not is_weekend and not is_holiday:
                        total -= 1.0
        return total
    
    df['Nghỉ Ca Còn Lại'] = df.apply(calc_row, axis=1)
    return df

# Luôn cập nhật số liệu trước khi render
st.session_state.db = apply_pvd_logic(st.session_state.db)

# --- 5. GIAO DIỆN (LOGO GÓC TRÁI) ---
col_l, col_r = st.columns([1, 5])
with col_l:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=120)
    else:
        st.markdown("### PVD")
with col_r:
    st.markdown('<h1 style="color: #00f2ff; margin-top: 10px;">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 6. NHẬP LIỆU NHANH ---
with st.expander("➕ NHẬP DỮ LIỆU ĐIỀU ĐỘNG", expanded=True):
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    f_staff = c1.multiselect("Nhân viên:", st.session_state.db['Họ và Tên'].tolist())
    f_status = c2.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP", "Ốm"])
    f_gian = c3.selectbox("Chọn Giàn:", st.session_state.gians) if f_status == "Đi Biển" else f_status
    f_date = c4.date_input("Thời gian:", value=(date(2026, 2, 1), date(2026, 2, 2)))
    
    if st.button("✅ CẬP NHẬT VÀO BẢNG", use_container_width=True):
        if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
            for d in range(f_date[0].day, f_date[1].day + 1):
                col_name = f"{d:02d}/02"
                if col_name in st.session_state.db.columns:
                    st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), col_name] = f_gian
            st.session_state.v_key += 1 # Reset bảng
            st.rerun()

# --- 7. THAO TÁC FILE ---
b1, b2, _ = st.columns([1, 1, 2])
with b1:
    if st.button("💾 LƯU GOOGLE SHEETS", use_container_width=True):
        conn.update(worksheet="Sheet1", data=st.session_state.db)
        st.success("Đã lưu thành công!")
with b2:
    buffer = io.BytesIO()
    st.session_state.db.to_excel(buffer, index=False)
    st.download_button("📥 TẢI FILE EXCEL", data=buffer.getvalue(), file_name="PVD_Export.xlsx", use_container_width=True)

# --- 8. BẢNG DỮ LIỆU CHÍNH ---
# Chuyển cột Quỹ CA lên đầu để dễ nhìn
cols_order = ['STT', 'Họ và Tên', 'Nghỉ Ca Còn Lại'] + [c for c in st.session_state.db.columns if c not in ['STT', 'Họ và Tên', 'Nghỉ Ca Còn Lại']]
st.session_state.db = st.session_state.db[cols_order]

edited_df = st.data_editor(
    st.session_state.db,
    column_config={
        "Nghỉ Ca Còn Lại": st.column_config.NumberColumn("Quỹ CA", format="%.1f", disabled=True),
        "STT": st.column_config.NumberColumn(width="small"),
        "Họ và Tên": st.column_config.TextColumn(width="medium", pinned=True)
    },
    use_container_width=True,
    height=600,
    key=f"pvd_editor_{st.session_state.v_key}"
)

if not edited_df.equals(st.session_state.db):
    st.session_state.db = edited_df
    st.rerun()

# Script cuộn ngang
components.html("""
<script>
    setTimeout(() => {
        const el = window.parent.document.querySelector('div[data-testid="stDataEditor"] [role="grid"]');
        if (el) {
            let isDown = false; let startX, scrollLeft;
            el.addEventListener('mousedown', (e) => { isDown = true; startX = e.pageX - el.offsetLeft; scrollLeft = el.scrollLeft; });
            el.addEventListener('mouseleave', () => { isDown = false; });
            el.addEventListener('mouseup', () => { isDown = false; });
            el.addEventListener('mousemove', (e) => { if(!isDown) return; e.preventDefault(); const x = e.pageX - el.offsetLeft; el.scrollLeft = scrollLeft - (x - startX) * 2; });
        }
    }, 1000);
</script>
""", height=0)
