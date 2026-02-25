# --- BẢNG DỮ LIỆU (ĐÃ SỬA LỖI KEYERROR) ---
    col_config = {
        "STT": st.column_config.NumberColumn("STT", width="min", pinned=True, format="%d"),
        "Họ và Tên": st.column_config.TextColumn("Họ và Tên", width="medium", pinned=True),
        "Công ty": st.column_config.SelectboxColumn("Công ty", options=COMPANIES, width="normal"),
        "Chức danh": st.column_config.SelectboxColumn("Chức danh", options=TITLES, width="normal"),
        "Tồn cũ": st.column_config.NumberColumn("Tồn cũ", format="%.1f", width="normal"),
        "Tổng CA": st.column_config.NumberColumn("Tổng CA", format="%.1f", width="normal"),
    }
    
    status_options = st.session_state.GIANS + ["CA", "WS", "Lễ", "NP", "Ốm", ""]
    for c in DATE_COLS:
        col_config[c] = st.column_config.SelectboxColumn(c, options=status_options, width="normal")

    # Kiểm tra những cột nào thực sự có trong dataframe db
    actual_cols = [c for c in ['STT', 'Họ và Tên', 'Công ty', 'Chức danh', 'Tồn cũ', 'Tổng CA'] + DATE_COLS if c in db.columns]
    
    # Lọc data theo các cột thực tế đang có
    display_df = db[actual_cols]

    # Áp dụng Style tô màu đỏ cho ngày lễ
    styled_db = display_df.style.apply(highlight_holidays, axis=0)

    # Hiển thị Editor
    ed_db = st.data_editor(
        styled_db, 
        use_container_width=True, 
        height=600, 
        hide_index=True, 
        column_config=col_config, 
        key=f"editor_{sheet_name}"
    )
    
    # So sánh và cập nhật dữ liệu
    if not ed_db.equals(display_df):
        st.session_state.store[sheet_name].update(ed_db)
        # Tính toán lại logic sau khi sửa đổi
        st.session_state.store[sheet_name] = apply_logic(st.session_state.store[sheet_name], curr_m, curr_y, st.session_state.GIANS)
        st.rerun()
