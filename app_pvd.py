import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import time
import plotly.express as px

# --- CẤU HÌNH ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

# --- DANH MỤC CỐ ĐỊNH (Giữ nguyên của bạn) ---
COMPANIES = ["PVDWS", "OWS", "National", "Baker Hughes", "Schlumberger", "Halliburton"]
TITLES = ["Casing crew", "CRTI LD", "CRTI SP", "SOLID", "MUDCL", "UNDERRM", "PPLS", "HAMER"]
NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]
DEFAULT_RIGS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

conn = st.connection("gsheets", type=GSheetsConnection)

# --- HÀM HỖ TRỢ DỮ LIỆU ---
def get_data_safe(wks_name):
    try:
        df = conn.read(worksheet=wks_name, ttl=0)
        return df if not df.empty else pd.DataFrame()
    except:
        return pd.DataFrame()

def apply_logic(df, curr_m, curr_y, rigs):
    """Tính toán Tổng CA dựa trên Tồn cũ và dữ liệu trong tháng"""
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    df_calc = df.copy()
    rigs_up = [r.upper() for r in rigs]
    
    # Xác định các cột ngày
    date_cols = [c for c in df_calc.columns if "/" in c and "(" in c]
    
    for idx, row in df_calc.iterrows():
        accrued = 0.0
        for col in date_cols:
            val = str(row.get(col, "")).strip().upper()
            if not val or val == "NAN": continue
            
            try:
                d_num = int(col[:2])
                target_date = date(curr_y, curr_m, d_num)
                is_we = target_date.weekday() >= 5
                is_ho = target_date in hols
                
                if any(g in val for g in rigs_up):
                    if is_ho: accrued += 2.0
                    elif is_we: accrued += 1.0
                    else: accrued += 0.5
                elif val == "CA":
                    if not is_we and not is_ho: accrued -= 1.0
            except: continue
            
        ton_cu = pd.to_numeric(row.get('Tồn cũ', 0), errors='coerce')
        df_calc.at[idx, 'Tổng CA'] = round(float(ton_cu if not pd.isna(ton_cu) else 0.0) + accrued, 1)
    return df_calc

# --- HÀM CẬP NHẬT DÂY CHUYỀN ---
def update_chain_reaction(start_date, start_df, rigs):
    """Khi lưu Tháng N, tự động cập nhật Tồn cũ cho Tháng N+1, N+2... trên Cloud"""
    current_df = start_df.copy()
    current_date = start_date
    
    # 1. Lưu tháng hiện tại
    sheet_name = current_date.strftime("%m_%Y")
    conn.update(worksheet=sheet_name, data=current_df)
    
    # 2. Lan tỏa sang các tháng sau
    for _ in range(1, 12): # Kiểm tra tối đa 12 tháng kế tiếp
        # Chuyển sang tháng tiếp theo
        days_in_m = calendar.monthrange(current_date.year, current_date.month)[1]
        next_date = current_date.replace(day=1) + timedelta(days=days_in_m)
        next_sheet = next_date.strftime("%m_%Y")
        
        next_df = get_data_safe(next_sheet)
        if next_df.empty: break # Dừng nếu tháng sau chưa được tạo
        
        # Lấy Tổng CA tháng trước làm Tồn cũ tháng này
        balances = current_df.set_index('Họ và Tên')['Tổng CA'].to_dict()
        for idx, row in next_df.iterrows():
            name = row['Họ và Tên']
            if name in balances:
                next_df.at[idx, 'Tồn cũ'] = balances[name]
        
        # Tính toán lại Tổng CA cho tháng sau dựa trên Tồn cũ mới
        next_df = apply_logic(next_df, next_date.month, next_date.year, rigs)
        
        # Lưu tháng sau lên Cloud
        conn.update(worksheet=next_sheet, data=next_df)
        
        # Tiếp tục vòng lặp cho tháng kế tiếp
        current_df = next_df
        current_date = next_date

# --- MAIN APP ---
if "all_months_data" not in st.session_state:
    st.session_state.all_months_data = {} # Dùng dict để tránh trắng bảng khi chuyển tháng

st.title("PVD WELL SERVICES MANAGEMENT")

wd = st.date_input("📅 CHỌN THÁNG:", value=date.today())
sheet_name = wd.strftime("%m_%Y")

# Load dữ liệu vào session_state nếu chưa có
if sheet_name not in st.session_state.all_months_data:
    with st.spinner(f"Đang tải dữ liệu {sheet_name}..."):
        df_load = get_data_safe(sheet_name)
        if df_load.empty:
            # Khởi tạo mới nếu chưa có sheet
            days_in_m = calendar.monthrange(wd.year, wd.month)[1]
            cols = [f"{d:02d}/{wd.strftime('%b')} (..)" for d in range(1, days_in_m+1)]
            df_load = pd.DataFrame({'STT': range(1, len(NAMES_66)+1), 'Họ và Tên': NAMES_66, 'Công ty': 'PVDWS', 'Chức danh': 'Casing crew', 'Tồn cũ': 0.0, 'Tổng CA': 0.0})
            for c in cols: df_load[c] = ""
        
        # Luôn lấy số dư từ tháng trước khi load lần đầu
        prev_date = (wd.replace(day=1) - timedelta(days=1))
        df_prev = get_data_safe(prev_date.strftime("%m_%Y"))
        if not df_prev.empty:
            balances = df_prev.set_index('Họ và Tên')['Tổng CA'].to_dict()
            for idx, row in df_load.iterrows():
                if row['Họ và Tên'] in balances:
                    df_load.at[idx, 'Tồn cũ'] = balances[row['Họ và Tên']]
        
        st.session_state.all_months_data[sheet_name] = apply_logic(df_load, wd.month, wd.year, DEFAULT_RIGS)

# Lấy dữ liệu hiện hành từ dict
df_current = st.session_state.all_months_data[sheet_name]

# Giao diện chính
c1, c2 = st.columns([2, 6])
with c1:
    if st.button("📤 LƯU CLOUD & CẬP NHẬT DÂY CHUYỀN", type="primary"):
        with st.spinner("Đang đồng bộ hóa dữ liệu toàn hệ thống..."):
            # Tính toán lại tháng hiện tại
            df_to_save = apply_logic(df_current, wd.month, wd.year, DEFAULT_RIGS)
            # Chạy phản ứng dây chuyền
            update_chain_reaction(wd, df_to_save, DEFAULT_RIGS)
            st.success("Đã lưu và cập nhật tất cả các tháng liên quan!")
            time.sleep(1)
            st.rerun()

# Data Editor
date_cols = [c for c in df_current.columns if "/" in c]
show_cols = ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Tồn cũ', 'Tổng CA'] + date_cols
edited_df = st.data_editor(df_current[show_cols], use_container_width=True, height=600, hide_index=True)

# Cập nhật lại vào dict khi người dùng sửa trên màn hình
if not edited_df.equals(df_current[show_cols]):
    st.session_state.all_months_data[sheet_name].update(edited_df)
    # Tự động tính toán lại Tổng CA khi có thay đổi trên lưới
    st.session_state.all_months_data[sheet_name] = apply_logic(st.session_state.all_months_data[sheet_name], wd.month, wd.year, DEFAULT_RIGS)
