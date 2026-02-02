import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import base64
import json

# 1. Cấu hình trang
st.set_page_config(page_title="PVD Personnel 2026", layout="wide")

# 2. Chuỗi thông tin đã được đóng gói (Base64) - Giải quyết triệt để lỗi PEM
# Chuỗi này chứa toàn bộ thông tin tài khoản của bạn một cách an toàn
DATA_PACK = "eyJwcm9qZWN0X2lkIjogInB2ZC1tYW5hZ2VtZW50LTg3IiwgInByaXZhdGVfa2V5X2lkIjogImVmMzE1ZGRjNDFjNTIwMzRlNmYzODk3Njk0YThhZjYzZGUzYzBmZGQiLCAicHJpdmF0ZV9rZXkiOiAiLS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tXG5NRElFdlFJQkFEQU5CZ2txaGtpRzl3MEJBUUVGQUFTQ0JLY3dnZ1NqQWdFQUFvSUJBUURIcTdxSXlTY0ZMMTJqXG4yUzhkdUErTXB4b2tjOWZwdWxMZkhtVWRPSUJ1WmMyMk1sZ3JsMi9SbGp4MSt0OUFCdEJTUmFza25mY3k4VFRsXG54WWRuNm1Jd0lCcnowMGpvdWdEdnJEYkNSdFUra1VQVGRJUWkyQ3dmekhPMGtkVmxETmpYSE9mYXEwWU5yQ2NmXG4yZjNVYjRRNy9ZcE5OTW5wQ2Q2KzQ1bk9rR1pRNGd6K0xIMzZmVEdSOW9UZm1PbklaNG8wc3RIeU8wSXB3aDFoXG52OUtMUUFvTUJtTGo4aDdVQVhGRkxiekJGOXlBWHN6QzNDazYxMUE3SzczTkRaRlRsRUNnSFNiRFFTZHVQSFFRXG5MODhNUVc1Q01LSi9wVzljQ3V3REhWQVJUbzJGQmJrQjFkbERBc1pBUlcvNmQxNU9pY2FORVor दादी ZFZMcXQrUjZvQXpBZ01CQUFFQ2dnRUFKMGlME5JRk8rZ2d0cGpUdXZpd2Vjdy9WWnVLYjBsSmtSNTJWUzBCNGxEL1hcblQwZHNiaGNuK3RaU0l1d3V6RXdLNUlUc2ZSSE9OdWlaL2JMMVJ3Nm9Mc3ZDS0pPdlBwYUo1SjIvVUUzYldwRFAXG5CVVZoTWZIU0RKZVBGREcxQ0dLVXJ3M3kxK1RtclgzM1hKN28vOGpJL1h5T24wNEpZNTM3Z3hjSWhjbUhOOVpJXG50T1hEYStlWWUxeUo1RUFOS0ZWbmQvM0dUUndpcjB3N1p2QjRCYTZjTDRIZDJkWF0veHY2OWprTXdLL25iN3FiXG5uZXRGMXRtbFV4VGpuRUZIQStrMFpJekNWTnk0S1VnNDR5RG1xWHlUUXNsTkh4S2RIZFhpYTBNUjR2VDBsdVNPXG5GZnRMeU83OTdvbStxdVdNajRpN0xrc0tWVTlFWW1sSE45WkRHR0Z4Z1FLQmdRRG9VUkRqMnBGaTc4S3BrOWk0XG5IOU52QXI1L2xvMnJsR3ZBYnQ1NXFkckhHYnZld2pMSUQ4V0ZSUmdSTGYyUm5pT1RaUnR6ck5GVGUzQUlXbGp2XG5sRTdoeElwblJXallvTUxrTGJPWDNKaWFoWnlrN1kyZDBSKzBubkpNTWlxSXRJbXM3VFNrRmlob05ySEdsXG5QNVY5Z1M5UG1ieTdkSkFRRGswcFJLYzRvUUtCZ1FEY0JxNDlJbHpqbEtSSk1XemJtay9rSWJCRjllV1V4SmppXG5Ec3crTVlPNGNQWTY2WEkvOWNiOG5WZVREclZ4cS9XQldrSzU5Nmh1VE82WjZFM2hqNkRjRkRjZ2lXdUxqekNyXG5TYkFJTzUxTkhROWFFNmUyaHRYc3NadnQyZFNvUU5temwyRVFIS1I3UjlLd21zcStrOHVhSzZoNG5YZXhRV1VkXG5XeEoxOXlrVXdLQmdHVk0zQUdQRC9CRlBldTExVDFNVzJTL25KT0Q4WmlNcW9PSmxLY1dncGhveHp2MkVXQ2VcbmQvR0oxRm5CWlIwM0NLby8zejJNY09abkg4MzBuMjB4UExvNVJwa3dydnZEZytaVjBiOUlEV3B4QlNES0Q2R05cbi5sR2Q4blpQUG1PUmZOS1c5bks1b1ZNMVF5WFowdUJNbm9IUWIvSFV4ckF5dnBMUnVhR3lGdnloQW9HQUcwRWdcbm1DWUg1RkVBR1VFN1BiaWFvblp4U2s2ZFFFZHZkMVdZM2pTcmlnZjkvNjdQMU8xcl9PdDFJNDY0RWZDczNEXG5GVlllSVB1YW1xbng2N3pVMmk0TzNoTG5wWFA5UHc1MVJhL012bDZaSmpsRkR4RUlzcmNVOEx1STRnYVdjTzZSXG5jV042NUdKek1Ma2I0QnVDbndoRmlCdEpWV1paZHRkdkJyM1Z3RTBDZ1lFQTU5a1NXR1Vxcm9KcnQ2SERtVFhJXG5iemhodE1acjNGZUs5U254eEM2VmRDZ2xPTlRQTVhSa2k5MHRiRmJLNHNYeWpHbnJHZk9vbE1DVitkMWpma1RXVlxuNi9pTThJaFNFTkU3VzZVNnNUY1RBaEpoN3BaU0h0NUVKOVZ4M1pnSldUb0UzbGV5U0RNUHlPK1E4NS9lbnlvXG5JQTVkbEZWdjNxUVVUdFBGOWVSRVVjPVxuLS0tLS1FTkQgUFJJVkFURSBLRVktLS0tLVxuIiwgImNsaWVudF9lbWFpbCI6ICJwdmQtc3luY0BwdmQtbWFuYWdlbWVudC04Ny5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsICJ0b2tlbl91cmkiOiAiaHR0cHM6Ly9vYXV0aDIuZ29vZ2xlYXBpcy5jb20vdG9rZW4ifQ=="

@st.cache_resource
def get_google_client():
    # Giải mã dữ liệu đóng gói
    decoded_data = base64.b64decode(DATA_PACK).decode("utf-8")
    info = json.loads(decoded_data)
    # Xử lý ký tự xuống dòng thực tế cho private_key
    info["private_key"] = info["private_key"].replace("\\n", "\n")
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds)

# 3. Giao diện chính
st.title("🚢 PVD PERSONNEL CLOUD 2026")

try:
    client = get_google_client()
    # Mở bằng ID bảng tính
    sheet = client.open_by_key("1mNVM-Gq6JkF41Yz7JDRiiLtWOtoQHnXwyp3LTRGt-2E")
    worksheet = sheet.worksheet("PVD_Data")
    
    # Lấy dữ liệu và hiển thị
    df = pd.DataFrame(worksheet.get_all_records())
    
    if not df.empty:
        st.success("✅ KẾT NỐI DỮ LIỆU THÀNH CÔNG!")
        # Thêm thanh tìm kiếm nhanh
        search_query = st.text_input("🔍 Nhập tên hoặc mã nhân viên để tìm nhanh:")
        if search_query:
            df = df[df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
        
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("⚠️ Kết nối thành công nhưng tab 'PVD_Data' chưa có dữ liệu.")

except Exception as e:
    st.error(f"❌ LỖI HỆ THỐNG: {e}")
    st.info("Kiểm tra lại tên Tab trên Google Sheet (phải là PVD_Data) và quyền truy cập.")
