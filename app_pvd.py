import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection
import io
import os
import time
import plotly.express as px

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="PVD MANAGEMENT", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 0.5rem; padding-bottom: 0rem;}
    .main-title {
        color: #00f2ff !important; font-size: 45px !important; font-weight: bold !important;
        text-align: center !important; text-shadow: 3px 3px 6px #000 !important;
        font-family: 'Arial Black', sans-serif !important;
    }
    .signature-section {
        margin-top: 50px; text-align: center; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO VÀ TIÊU ĐỀ ---
c_logo, _ = st.columns([1, 4])
with c_logo:
    if os.path.exists("logo_pvd.png"):
        st.image("logo_pvd.png", width=180)
    else:
        st.markdown("<h2 style='color:red;'>🔴 PVD WELL</h2>", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">PVD WELL SERVICES MANAGEMENT</h1>', unsafe_allow_html=True)

# --- 3. KẾT NỐI VÀ HÀM LƯU ---
conn = st.connection("gsheets", type=GSheetsConnection)

def save_to_cloud_silent(worksheet_name, df):
    df_save = df.copy()
    for col in df_save.columns:
        df_save[col] = df_save[col].astype(str).replace(["nan", "NaN", "None", "<NA>"], "")
    try:
        conn.update(worksheet=worksheet_name, data=df_save)
        st.cache_data.clear() 
        return True
    except Exception as e:
        st.error(f"Lỗi lưu Cloud: {e}")
        return False

# --- 4. DANH MỤC VÀ QUẢN LÝ GIÀN (SIDEBAR) ---
if "GIANS" not in st.session_state:
    st.session_state.GIANS = ["PVD 8", "HK 11", "HK 14", "SDP", "PVD 9", "THOR", "SDE", "GUNNLOD"]

with st.sidebar:
    st.header("⚙️ QUẢN LÝ HỆ THỐNG")
    new_gian = st.text_input("Thêm tên giàn mới:")
    if st.button("➕ Thêm Giàn", use_container_width=True):
        if new_gian and new_gian.strip().upper() not in st.session_state.GIANS:
            st.session_state.GIANS.append(new_gian.strip().upper())
            st.rerun()
    st.divider()
    st.subheader("Trạng thái nhân sự:")
    st.info("WS: Làm xưởng\nNP: Nghỉ phép\nCA: Nghỉ bù\nĐi biển: Tên giàn")

NAMES_66 = ["Bui Anh Phuong", "Le Thai Viet", "Le Tung Phong", "Nguyen Tien Dung", "Nguyen Van Quang", "Pham Hong Minh", "Nguyen Gia Khanh", "Nguyen Huu Loc", "Nguyen Tan Dat", "Chu Van Truong", "Ho Sy Duc", "Hoang Thai Son", "Pham Thai Bao", "Cao Trung Nam", "Le Trong Nghia", "Nguyen Van Manh", "Nguyen Van Son", "Duong Manh Quyet", "Tran Quoc Huy", "Rusliy Saifuddin", "Dao Tien Thanh", "Doan Minh Quan", "Rawing Empanit", "Bui Sy Xuan", "Cao Van Thang", "Cao Xuan Vinh", "Dam Quang Trung", "Dao Van Tam", "Dinh Duy Long", "Dinh Ngoc Hieu", "Do Đức Ngoc", "Do Van Tuong", "Dong Van Trung", "Ha Viet Hung", "Ho Trong Dong", "Hoang Tung", "Le Hoai Nam", "Le Hoai Phuoc", "Le Minh Hoang", "Le Quang Minh", "Le Quoc Duy", "Mai Nhan Duong", "Ngo Quynh Hai", "Ngo Xuan Dien", "Nguyen Hoang Quy", "Nguyen Huu Toan", "Nguyen Manh Cuong", "Nguyen Quoc Huy", "Nguyen Tuan Anh", "Nguyen Tuan Minh", "Nguyen Van Bao Ngoc", "Nguyen Van Duan", "Nguyen Van Hung", "Nguyen Van Vo", "Phan Tay Bac", "Tran Van Hoan", "Tran Van Hung", "Tran Xuan Nhat", "Vo Hong Thinh", "Vu Tuan Anh", "Arent Fabian Imbar", "Hendra", "Timothy", "Tran Tuan Dung", "Nguyen Van Cuong", "Nguyen Huu Phuc"]

# --- 5. CHỌN THỜI GIAN ---
_, c_mid_date, _ = st.columns([3.5, 2, 3.5])
with c_mid_date:
    working_date = st.date_input("📅 THÁNG LÀM VIỆC:", value=date.today())

sheet_name = working_date.strftime("%m_%Y")
curr_month, curr_year = working_date.month, working_date.year
num_days_curr = calendar.monthrange(curr_year, curr_month)[1]
month_abbr = working_date.strftime("%b")
DATE_COLS = [f"{d:02d}/{month_abbr} ({['T2','T3','T4','T5','T6','T7','CN'][date(curr_year,curr_month,d).weekday()]})" for d in range(1, num_days_curr+1)]

# --- 6. ENGINE AUTO-FILL REAL TIMES (KHÔNG ĐỔI) ---
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
            
            # AUTO-FILL: Nếu trống và đã qua 6h sáng ngày hôm đó
            if (not val or val == "" or val.lower() == "nan") and (target_date < today or (target_date == today and now.hour >= 6)):
                if current_last_val != "":
                    lv_up = current_last_val.upper()
                    if any(g.upper() in lv_up for g in st.session_state.GIANS) or lv_up in ["CA", "WS"]:
                        val = current_last_val
                        df_calc.at[idx, col] = val
                        data_changed = True
            
            if val and val != "" and val.lower() != "nan":
                current_last_val = val
            
            # TÍNH TOÁN QUỸ CA
            v_up = val.upper()
            if v_up and v_up != "NAN":
                is_we = target_date.weekday() >= 5 
                is_ho = target_date in hols 
                if any(g.upper() in v_up for g in st.session_state.GIANS):
                    if is_ho: accrued += 2.0
                    elif is_we: accrued += 1.0
                    else: accrued += 0.5
                elif v_up == "CA":
                    if not is_we and not is_ho:
                        accrued -= 1.0
        
        ton_cu = float(row.get('CA Tháng Trước', 0)) if row.get('CA Tháng Trước') else 0.0
        df_calc.at[idx, 'Quỹ CA Tổng'] = round(ton_cu + accrued, 1)
        
    return df_calc, data_changed

# --- 7. LOAD DỮ LIỆU ---
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

# --- 8. TABS GIAO DIỆN ---
t1, t2 = st.tabs(["🚀 ĐIỀU ĐỘNG & BÁO CÁO", "📊 BIỂU ĐỒ PHÂN TÍCH"])

with t1:
    st.subheader("📝 BẢNG CHI TIẾT ĐIỀU ĐỘNG NHÂN SỰ")
    
    # BẢNG DỮ LIỆU (Sửa trực tiếp)
    ed_df = st.data_editor(
        st.session_state.db, 
        use_container_width=True, 
        height=550, 
        hide_index=True,
        column_config={
            "Quỹ CA Tổng": st.column_config.NumberColumn("Số dư Quỹ", disabled=True),
            "STT": st.column_config.Column(width="small", disabled=True)
        }
    )

    # NÚT XÁC NHẬN LƯU
    if st.button("📤 CẬP NHẬT VÀ LƯU LÊN GOOGLE SHEETS", type="primary", use_container_width=True):
        with st.spinner("Đang lưu dữ liệu lên Cloud..."):
            st.session_state.db.update(ed_df)
            final_df, _ = auto_engine(st.session_state.db, curr_year, curr_month, DATE_COLS)
            if save_to_cloud_silent(sheet_name, final_df):
                st.session_state.db = final_df
                st.toast("✅ Đã đồng bộ thành công!")
                time.sleep(1)
                st.rerun()

    st.divider()

    # --- PHẦN XUẤT EXCEL (GIỐNG BẢN TRƯỚC) ---
    st.subheader("📥 XUẤT BÁO CÁO EXCEL")
    c_ex1, c_ex2 = st.columns([1, 1])
    with c_ex1:
        # Xuất CSV (Nhẹ, nhanh)
        csv_data = st.session_state.db.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📂 Xuất file CSV", data=csv_data, file_name=f"PVD_Report_{sheet_name}.csv", mime='text/csv', use_container_width=True)
    with c_ex2:
        # Xuất XLSX (Đẹp, đầy đủ)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            st.session_state.db.to_excel(writer, index=False, sheet_name='Personnel')
        st.download_button("📂 Xuất file EXCEL (XLSX)", data=output.getvalue(), file_name=f"PVD_Report_{sheet_name}.xlsx", mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)

    # --- PHẦN XÁC NHẬN (KÝ TÊN) ---
    st.markdown("""
        <div class="signature-section">
            <table style="width:100%; border:none;">
                <tr>
                    <td style="width:33%;">NGƯỜI LẬP BIỂU</td>
                    <td style="width:33%;">QUẢN LÝ TRỰC TIẾP</td>
                    <td style="width:33%;">BAN GIÁM ĐỐC XÁC NHẬN</td>
                </tr>
                <tr style="height:100px;">
                    <td></td><td></td><td></td>
                </tr>
                <tr>
                    <td>(Ký và ghi rõ họ tên)</td>
                    <td>(Ký và ghi rõ họ tên)</td>
                    <td>(Ký và ghi rõ họ tên)</td>
                </tr>
            </table>
        </div>
    """, unsafe_allow_html=True)

with t2:
    st.subheader(f"📊 Phân tích nhân sự {sheet_name}")
    # Biểu đồ tròn cho ngày hôm nay
    day_now = datetime.now().day
    col_name = [c for c in DATE_COLS if c.startswith(f"{day_now:02d}/")]
    if col_name:
        data_today = st.session_state.db[col_name[0]].value_counts()
        fig = px.pie(values=data_today.values, names=data_today.index, title=f"Tình hình nhân sự ngày {col_name[0]}")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Dữ liệu biểu đồ sẽ cập nhật khi có thông tin ngày hiện tại.")
