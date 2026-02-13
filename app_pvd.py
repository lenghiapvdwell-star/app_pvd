import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import time

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 0.5rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; font-size: 45px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 3px 3px 6px #000 !important;
        font-family: 'Arial Black', sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KẾT NỐI ---
conn = st.connection("gsheets", type=GSheetsConnection)

def save_to_cloud_silent(worksheet_name, df):
    # Ép toàn bộ về chuỗi sạch trước khi đẩy lên cloud
    df_save = df.copy()
    for col in df_save.columns:
        df_save[col] = df_save[col].astype(str).replace(["nan", "NaN", "None", "<NA>", "None"], "")
    try:
        conn.update(worksheet=worksheet_name, data=df_save)
        st.cache_data.clear() 
        return True
    except Exception as e:
        if "429" in str(e):
            st.error("⚠️ Hệ thống đang quá tải yêu cầu. Vui lòng đợi 30 giây rồi thử lại.")
        else:
            st.error(f"Lỗi lưu Cloud: {e}")
        return False

# --- 3. DANH MỤC ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]

# --- 4. ENGINE TỰ ĐỘNG (GIỮ NGUYÊN LOGIC REAL-TIME & QUY TẮC) ---
def auto_engine(df, curr_year, curr_month, DATE_COLS):
    hols = [date(2026,1,1), date(2026,2,16), date(2026,2,17), date(2026,2,18), date(2026,2,19), date(2026,2,20), date(2026,4,26), date(2026,4,30), date(2026,5,1), date(2026,9,2)]
    now = datetime.now()
    today = now.date()
    df_calc = df.copy()
    data_changed = False
    
    for idx, row in df_calc.iterrows():
        accrued = 0.0
        current_last_val = ""
        for col in DATE_COLS:
            if col not in df_calc.columns: continue
            d_num = int(col[:2])
            target_date = date(curr_year, curr_month, d_num)
            val = str(row.get(col, "")).strip()
            
            # --- AUTOFILL REALTIME (KHÔNG THAY ĐỔI) ---
            if (not val or val == "" or val.lower() == "nan") and (target_date < today or (target_date == today and now.hour >= 6)):
                if current_last_val != "":
                    lv_up = current_last_val.upper()
                    # Điền tiếp nếu là đi biển, CA hoặc làm xưởng
                    if any(g.upper() in lv_up for g in st.session_state.GIANS) or lv_up in ["CA", "WS"]:
                        val = current_last_val
                        df_calc.at[idx, col] = val
                        data_changed = True
            
            if val and val != "" and val.lower() != "nan":
                current_last_val = val
            
            # --- LUẬT TÍNH CA (GIỮ NGUYÊN) ---
            v_up = val.upper()
            if v_up and v_up != "NAN":
                is_we = target_date.weekday() >= 5 
                is_ho = target_date in hols 
                
                # Đi biển: Cộng quỹ
                if any(g.upper() in v_up for g in st.session_state.GIANS):
                    if is_ho: accrued += 2.0
                    elif is_we: accrued += 1.0
                    else: accrued += 0.5
                # Nghỉ CA: Chỉ trừ vào ngày thường, không trừ WS/NP/Ốm
                elif v_up == "CA":
                    if not is_we and not is_ho:
                        accrued -= 1.0
        
        ton_cu = float(row.get('CA Tháng Trước', 0)) if row.get('CA Tháng Trước') else 0.0
        df_calc.at[idx, 'Quỹ CA Tổng'] = round(ton_cu + accrued, 1)
        
    return df_calc, data_changed

# --- 5. XỬ LÝ DỮ LIỆU ---
st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

working_date = st.date_input("📅 CHỌN THÁNG LÀM VIỆC:", value=date.today())
sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
num_days_curr = calendar.monthrange(curr_year, curr_month)[1]
month_abbr = working_date.strftime("%b")
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days_curr+1)]

if 'db' not in st.session_state or st.session_state.get('active_sheet') != sheet_name:
    try:
        df_l = conn.read(worksheet=sheet_name, ttl=0).fillna("")
        if df_l.empty: raise ValueError
    except:
        init_data = {'STT': range(1, len(NAMES_66)+1), 'Họ và Tên': NAMES_66, 'CA Tháng Trước': 0.0, 'Quỹ CA Tổng': 0.0}
        for c in DATE_COLS: init_data[c] = ""
        df_l = pd.DataFrame(init_data)
    
    df_ready, changed = auto_engine(df_l, curr_year, curr_month, DATE_COLS)
    if changed:
        save_to_cloud_silent(sheet_name, df_ready)
    
    st.session_state.db = df_ready
    st.session_state.active_sheet = sheet_name

# --- 6. GIAO DIỆN BẢNG (NÂNG CẤP) ---
st.subheader("📝 BẢNG ĐIỀU ĐỘNG CHI TIẾT")

# Thiết lập bôi màu tự động để dễ quan sát
def highlight_cells(val):
    v = str(val).upper()
    if any(g.upper() in v for g in st.session_state.GIANS): return 'background-color: #004d00; color: white' # Đi biển xanh đậm
    if v == "CA": return 'background-color: #4d0000; color: white' # CA đỏ đậm
    if v == "WS": return 'background-color: #4d4d00; color: white' # WS vàng đậm
    if v in ["NP", "ỐM"]: return 'background-color: #262626; color: #a6a6a6' # Nghỉ xám
    return ''

ed_df = st.data_editor(
    st.session_state.db, 
    use_container_width=True, 
    height=600, 
    hide_index=True,
    column_config={
        "Quỹ CA Tổng": st.column_config.NumberColumn("Số dư Quỹ", format="%.1f", disabled=True),
        "CA Tháng Trước": st.column_config.NumberColumn("Tồn cũ", format="%.1f"),
        "STT": st.column_config.Column(width="small", disabled=True)
    }
)

# NÚT LƯU TỔNG HỢP
c1, c2, c3 = st.columns([1,2,1])
with c2:
    if st.button("📤 XÁC NHẬN SỬA ĐỔI & LƯU CLOUD", type="primary", use_container_width=True):
        with st.spinner("🔄 Đang tính toán lại và đồng bộ Google Sheets..."):
            # Cập nhật thay đổi từ bảng editor vào session_state
            st.session_state.db.update(ed_df)
            # Chạy lại engine để đảm bảo CA được tính đúng sau khi sửa tay
            final_df, _ = auto_engine(st.session_state.db, curr_year, curr_month, DATE_COLS)
            if save_to_cloud_silent(sheet_name, final_df):
                st.session_state.db = final_df
                st.toast("✅ Đã lưu thành công!", icon="🚀")
                time.sleep(1)
                st.rerun()

# Xuất Excel nhanh
st.divider()
buf = io.BytesIO()
st.session_state.db.to_excel(buf, index=False)
st.download_button("📥 TẢI FILE EXCEL THÁNG NÀY", buf.getvalue(), f"PVD_Management_{sheet_name}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
