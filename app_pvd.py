with t2:
    st.subheader("📊 Phân tích cường độ & Tổng hợp ngày biển")
    sel = st.selectbox("🔍 Chọn nhân sự:", NAMES_64)
    year_data = load_year_data(curr_year)
    
    recs = []
    if year_data:
        # Lấy dữ liệu từ T1 đến T12 để tính cộng dồn
        for m in range(1, 13):
            if m in year_data:
                df_m = year_data[m]
                if 'Họ và Tên' in df_m.columns and sel in df_m['Họ và Tên'].values:
                    row_p = df_m[df_m['Họ và Tên'] == sel].iloc[0]
                    m_label = date(curr_year, m, 1).strftime("%b")
                    
                    # Duyệt qua các cột ngày của tháng đó
                    for col in df_m.columns:
                        if "/" in col and m_label in col:
                            v = str(row_p[col]).strip().upper()
                            if v and v not in ["NAN", "NONE", ""]:
                                cat = "Đi Biển" if any(g.upper() in v for g in GIANS) else v
                                if cat in ["Đi Biển", "CA", "WS", "NP", "ỐM"]:
                                    recs.append({"Tháng": f"T{m}", "Loại": cat, "Ngày": 1})

    if recs:
        pdf = pd.DataFrame(recs)
        
        # 1. Tính toán tổng hợp để hiển thị con số
        summary = pdf.groupby(['Tháng', 'Loại']).sum().reset_index()
        
        # 2. Tính lũy kế ngày đi biển (Cumulative)
        sea_only = summary[summary['Loại'] == "Đi Biển"].copy()
        # Đảm bảo thứ tự tháng chuẩn T1 -> T12
        sea_only['MonthIdx'] = sea_only['Tháng'].str[1:].astype(int)
        sea_only = sea_only.sort_values('MonthIdx')
        sea_only['Lũy kế biển'] = sea_only['Ngày'].cumsum()

        # 3. Vẽ biểu đồ chính (Cột chồng có số liệu)
        fig = px.bar(summary, x="Tháng", y="Ngày", color="Loại", 
                     text="Ngày", # Hiển thị con số trên cột
                     barmode="stack",
                     color_discrete_map={
                         "Đi Biển": "#00CC96", "CA": "#EF553B", 
                         "WS": "#FECB52", "NP": "#636EFA", "ỐM": "#AB63FA"
                     },
                     category_orders={"Tháng": [f"T{i}" for i in range(1, 13)]})

        # 4. Thêm đường biểu diễn tổng cộng dồn ngày biển
        if not sea_only.empty:
            import plotly.graph_objects as go
            fig.add_trace(go.Scatter(
                x=sea_only["Tháng"], 
                y=sea_only["Lũy kế biển"],
                name="Tổng Biển Cộng Dồn",
                mode="lines+markers+text",
                text=sea_only["Lũy kế biển"],
                textposition="top center",
                line=dict(color="#00f2ff", width=3)
            ))

        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)', 
            font_color="white",
            height=600,
            xaxis_title="Tháng làm việc",
            yaxis_title="Số lượng ngày"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Hiển thị bảng tóm tắt nhanh bên dưới cho chuyên nghiệp
        st.markdown("### 📋 Bảng tổng hợp chi tiết")
        col_sum1, col_sum2 = st.columns(2)
        with col_sum1:
            total_sea = sea_only['Ngày'].sum() if not sea_only.empty else 0
            st.metric("Tổng ngày biển cả năm", f"{total_sea} ngày")
        with col_sum2:
            total_ca = summary[summary['Loại'] == "CA"]['Ngày'].sum()
            st.metric("Tổng ngày nghỉ CA", f"{total_ca} ngày")
            
    else:
        st.info("Chưa có dữ liệu lịch sử để hiển thị biểu đồ cho nhân sự này.")
