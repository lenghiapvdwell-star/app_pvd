import streamlit as st
import pandas as pd
from datetime import datetime, date
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import io
import os

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

# --- 2. QUY ƯỚC & DỮ LIỆU ---
NAMES_64 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung"]
DATE_COLS = [f"{d:02d}/02" for d in range(1, 29)]
HOLIDAYS = [15, 16, 17, 18, 19]

# --- 3. HÀM TÍNH TOÁN (Logic chuẩn 2026) ---
def calculate_pvd_logic(df, gians):
    def calc_row(row):
        total = 0.0
        for col in DATE_COLS:
            if col in row.index:
                val = str(row[col]).strip() if pd.notna(row[col]) else ""
                if not val or val.lower() in ["nan", "none", ""]: continue
                
                day_num = int(col.split('/')[0])
                dt = date(2026, 2, day_num)
                is_weekend = dt.weekday() >= 5 # 5: Thứ 7, 6: CN
                is_holiday = day_num in HOLIDAYS
                
                if val in gians:
                    if is_holiday: total += 2.0
                    elif is_weekend: total += 1.0
                    else: total += 0.5
                elif val.upper() == "CA":
                    if not is_weekend and not is_holiday:
                        total -= 1.0
        return total
    
    df['Nghỉ Ca Còn Lại'] = df.apply(calc_row, axis=1)
    return df

# --- 4. KHỞI TẠO DỮ LIỆU ---
conn = st.connection("gsheets", type=GSheetsConnection)

if 'db' not in st.session_state:
    try:
        df_load = conn.read(worksheet="Sheet1")
        if df_load is None or df_load.empty: raise Exception
        st.session_state.db = df_load
    except:
        df_init = pd.DataFrame({'STT': range(1, 65), 'Họ và Tên': NAMES_64, 'Công ty': 'PVDWS', 'Chức danh': 'Kỹ sư', 'Job Detail': ''})
        for c in DATE_COLS: df_init[c] = ""
        st.session_state.db = df_init

if 'gians' not in st.session_state:
    st.session_state.gians = ["PVD I", "PVD II", "PVD III", "PVD VI", "PVD 11"]

if 'v_key' not in st.session_state:
    st.session_state.v_key = 0 # Dùng để ép bảng cập nhật

# --- 5. GIAO DIỆN ---
st.markdown('<h1 style="color: #00f2ff; text-align: center;">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# Luôn tính toán lại quỹ CA trước khi hiển thị
st.session_state.db = calculate_pvd_logic(st.session_state.db, st.session_state.gians)

c_input, c_action = st.columns([3, 1])

with c_input:
    with st.expander("➕ NHẬP DỮ LIỆU NHANH", expanded=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        f_staff = col1.multiselect("Nhân viên:", st.session_state.db['Họ và Tên'].tolist())
        f_status = col2.selectbox("Trạng thái:", ["Đi Biển", "CA", "WS", "NP"])
        f_gian = col3.selectbox("Chọn Giàn:", st.session_state.gians) if f_status == "Đi Biển" else f_status
        f_date = st.date_input("Khoảng thời gian:", value=(date(2026, 2, 1), date(2026, 2, 2)))
        
        if st.button("✅ XÁC NHẬN VÀO BẢNG", use_container_width=True):
            if f_staff and isinstance(f_date, tuple) and len(f_date) == 2:
                for d in range(f_date[0].day, f_date[1].day + 1):
                    col_name = f"{d:02d}/02"
                    if col_name in st.session_state.db.columns:
                        st.session_state.db.loc[st.session_state.db['Họ và Tên'].isin(f_staff), col_name] = f_gian
                # Quan trọng: Tăng v_key để ép bảng data_editor reset dữ liệu mới
                st.session_state.v_key += 1 
                st.rerun()

with c_action:
    st.write("###")
    if st.button("💾 LƯU CLOUD", use_container_width=True):
        conn.update(worksheet="Sheet1", data=st.session_state.db)
        st.success("Đã lưu!")
    
    buffer = io.BytesIO()
    st.session_state.db.to_excel(buffer, index=False)
    st.download_button("📥 TẢI EXCEL", data=buffer.getvalue(), file_name="PVD_Export.xlsx", use_container_width=True)

# HIỂN THỊ BẢNG DỮ LIỆU
# Cột Nghỉ Ca Còn Lại được tính toán tự động và không cho sửa tay
edited_df = st.data_editor(
    st.session_state.db,
    column_config={
        "Nghỉ Ca Còn Lại": st.column_config.NumberColumn("Quỹ CA", disabled=True, format="%.1f"),
        "STT": st.column_config.NumberColumn(width="small"),
        "Họ và Tên": st.column_config.TextColumn(width="medium")
    },
    use_container_width=True, 
    height=600,
    key=f"editor_v{st.session_state.v_key}" 
)

# Cập nhật state nếu người dùng sửa trực tiếp trên ô
if not edited_df.equals(st.session_state.db):
    st.session_state.db = edited_df
    st.rerun()

# Hỗ trợ cuộn ngang bằng chuột
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
