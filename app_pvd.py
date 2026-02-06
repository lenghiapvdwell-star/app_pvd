# --- Tìm đến phần nút chức năng (khoảng dòng 145) và thay thế bằng đoạn này ---

bc1, bc2, _ = st.columns([1.5, 1.5, 5])

with bc1:
    if st.button("📤 LƯU CLOUD", use_container_width=True, type="primary"):
        try:
            with st.spinner(f"正在 {sheet_name}... Đang kết nối an toàn với Cloud..."):
                # 1. Kiểm tra dữ liệu trước khi lưu
                if st.session_state.db is None or st.session_state.db.empty:
                    st.error("Dữ liệu trống, không thể lưu!")
                else:
                    # 2. Thực hiện cập nhật lên Google Sheets
                    conn.update(worksheet=sheet_name, data=st.session_state.db)
                    
                    # 3. Thông báo thành công
                    st.success(f"✅ Đã lưu thành công dữ liệu tháng {sheet_name}")
                    st.toast(f"Đã cập nhật Cloud lúc {datetime.now().strftime('%H:%M:%S')}")
                    st.balloons() # Hiệu ứng cho phấn khởi
                    
        except Exception as e:
            # Phân loại lỗi để thông báo cho bạn chính xác nhất
            error_msg = str(e)
            st.error("❌ LỖI KẾT NỐI CLOUD!")
            
            if "APIError" in error_msg:
                st.warning("⚠️ Google Sheets API đang quá tải (Rate Limit). Bạn hãy đợi khoảng 30 giây rồi nhấn Lưu lại nhé.")
            elif "WorksheetNotFound" in error_msg or "not found" in error_msg.lower():
                st.warning(f"⚠️ Không tìm thấy Sheet tên '{sheet_name}'. Bạn hãy kiểm tra lại file Google Sheets đã tạo sheet này chưa.")
            else:
                st.info(f"Chi tiết lỗi: {error_msg}")
                st.write("Lời khuyên: Kiểm tra lại kết nối internet hoặc quyền truy cập của file secrets.toml")

with bc2:
    try:
        buffer = io.BytesIO()
        st.session_state.db.to_excel(buffer, index=False)
        st.download_button(
            label="📥 XUẤT EXCEL",
            data=buffer,
            file_name=f"PVD_{sheet_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Lỗi xuất file: {e}")
