import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import base64
import json

# 1. Cấu hình trang
st.set_page_config(page_title="PVD Personnel 2026", layout="wide")

# 2. DỮ LIỆU ĐÃ MÃ HÓA (Để tránh lỗi InvalidByte PEM)
# Đây là toàn bộ thông tin Service Account của bạn đã được đóng gói an toàn
B64_DATA = "eyJ0eXBlIjogInNlcnZpY2VhY2NvdW50IiwgInByb2plY3RfaWQiOiAicHZkLW1hbmFnZW1lbnQtODciLCAicHJpdmF0ZV9rZXlfaWQiOiAiZWYzMTVkZGM0MWM1MjAzNGU2ZjM4OTc2OTRhOGFmNjNkZTNjMGZkZCIsICJwcml2YXRlX2tleSI6ICItLS0tLUJFR0lOIFBSSVZBVEUgS0VZLS0tLS1cbU1JSUV2UUlCQURBTkJna3Foa2lHOXcwQkFRRUZBQVNDQktjd2dnU2pBZ0VBQW9JQkFRREhxN3FJeVNjRkwxMmpcbjJTOGR1QStNcHhva2M5ZnB1bExmSG1VZE9JQnVaYzIyTWxndnJsMi9SbGp4MSt0OUFCdEJTUmFza25mY3k4VFRsXG54WWRuNm1Jd0lCcnowMGpvdWdEdnJEYkNSdFUra1VQVGRJUWkyQ3dmekhPMGtkVmxETmpYSE9mYXEwWU5yQ2NmXG4yZjNVYjRRNy9ZcE5OTW5wQ2Q2KzQ1bk9rR1pRNGd6K0xIMzZmVEdSOW9UZm1PbklaNG8wc3RIeU8wSXB3aDFoXG52OUtMUUFvTUJtTGo4aDdVQVhGRkxiekJGOXlBWHN6QzNDazYxMUE3SzczTkRaRlRsRUNnSFNiRFFTZHVQSFFRXG5MODhNUVc1Q01LSi9wVzljQ3V3REhWQVJUbzJGQmJrQjFkbERBc1pBUlcvNmQxNU9pY2FORVoreW9RU3pWTHh0K3I2b0F6QWdNQkFBRUNnZ0VBSjBpME5JRk8rZ2d0cGpUdXZpd2Vjdy9WWnVLYjBsSmtSNTJWUzBCNGxEL1hcblQwZHNiaGNuK3RaU0l1d3V6RXdLNUlUc2ZSSE9OdWlaL2JMMVJ3Nm9Mc3ZDS0pPdlBwYUo1SjIvVUUzYldwRFBcbkJVVZoTWZIU0RKZVBGREcxQ0dLVXJ3M3kxK1RtclgzM1hKN28vOGpJL1h5T24wNEpZNTM3Z3hjSWhjbUhOOVpJXG50T1hEYStlWWUxeUo1RUFOS0ZWbmQvM0dUUndpcjB3N1p2QjRCYTZjTDRIZDJkWF0veHY2OWprTXdLL25iN3FiXG5uZXRGMXRtbFV4VGpuRUZIQWtsMFpJekNWTnk0S1VnNDR5RG1xWHlUUXNsTkh4S2RIZFhpYTBNUjR2VDBsdVNPXG5GZnRMeU83OTdvbStxdVdNajRpN0xrc0tWVTlFWW1sSE45WkRHR0Z4Z1FLQmdRRG9VUkRqMnBGaTc4S3BrOWk0XG5IOU52QXI1L2xvMnJsR3ZBYnQ1NXFkckhHYnZld2pMSUQ4V0ZSUmdSTGYyUm5pT1RaUnR6ck5GVGUzQUlXbGp2XG5sRTdoeElwblJXallvTUxrTGJPWDNKaWFoWnlrN1kyZDBSKzBubkpNTWlxSXRJbXM3VFNrRmlob05ySEdsXG5QNVY5Z1M5UG1ieTdkSkFRRGswcFJLYzRvUUtCZ1FEY0JxNDlJbHpqbEtSSk1XemJtay9rSWJCRjllV1V4SmppXG5Ec3crTVlPNGNQWTY2WEkvOWNiOG5WZVREclZ4cS9XQldrSzU5Nmh1VE82WjZFM2hqNkRjRkRjZ2lXdUxqekNyXG5TYkFJTzUxTkhROWFFNmUyaHRYc3NadnQyZFNvUU5temwyRVFIS1I3UjlLd21zcStrOHVhSzZoNG5YZXhRV1VkXG5XeEoxOXlrVXdLQmdHVk0zQUdQRC9CRlBldTExVDFNVzJTL25KT0Q4WmlNcW9PSmxLY1dncGhveHp2MkVXQ2VcbmQvR0oxRm5CWlIwM0NLby8zejJNY09abkg4MzBuMjB4UExvNVJwa3dydnZEZytaVjBiOUlEV3B4QlNES0Q2R05cbi5sR2Q4blpQUG1PUmZOS1c5bks1b1ZNMVF5WFowdUJNbm9IUWIvSFV4ckF5dnBMUnVhR3lGdnloQW9HQUcwRWdcbm1DWUg1RkVBR1VFN1BiaWFvblp4U2s2ZFFFZHZkMVdZM2pTcmlnZjkvNjdQMU8xcl9PdDFJNDY0RWZDczNEXG5GVlllSVB1YW1xbng2N3pVMmk0TzNoTG5wWFA5UHc1MVJhL012bDZaSmpsRkR4RUlzcmNVOEx1STRnYVdjTzZSXG5jV042NUdKek1Ma2I0QnVDbndoRmlCdEpWV1paZHRkdkJyM1Z3RTBDZ1lFQTU5a1NXR1Vxcm9KcnQ2SERtVFhJXG5iemhodE1acjNGZUs5U254eEM2VmRDZ2xPTlRQTVhSa2k5MHRiRmJLNHNYeWpHbnJHZk9vbE1DVitkMWpma1RXVlxuNi9pTThJaFNFTkU3VzZVNnNUY1RBaEpoN3BaU0h0NUVKOVZ4M1pnSldUb0UzbGV5U0RNUHlPK1E4NS9lbnlvXG5JQTVkbEZWdjNxUVVUdFBGOWVSRVVjPVxuLS0tLS1FTkQgUFJJVkFURSBLRVktLS0tLVxuIiwgImNsaWVudF9lbWFpbCI6ICJwdmQtc3luY0BwdmQtbWFuYWdlbWVudC04Ny5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsICJ0b2tlbl91cmkiOiAiaHR0cHM6Ly9vYXV0aDIuZ29vZ2xlYXBpcy5jb20vdG9rZW4ifQ=="

@st.cache_resource
def get_cloud_data():
    # Giải mã dữ liệu và xử lý ký tự xuống dòng
    decoded = base64.b64decode(B64_DATA).decode("utf-8")
    info = json.loads(decoded)
    info["private_key"] = info["private_key"].replace("\\n", "\n")
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    gc = gspread.authorize(creds)
    
    # Mở bằng ID bảng tính
    sh = gc.open_by_key("1mNVM-Gq6JkF41Yz7JDRiiLtWOtoQHnXwyp3LTRGt-2E")
    ws = sh.worksheet("PVD_Data")
    return pd.DataFrame(ws.get_all_records())

st.title("🚢 PVD PERSONNEL CLOUD 2026")

try:
    df = get_cloud_data()
    st.success("🚀 KẾT NỐI ĐÁM MÂY THÀNH CÔNG!")
    
    # Hiển thị bảng dữ liệu
    st.dataframe(df, use_container_width=True)
    
    # Thêm bộ lọc tìm kiếm cho chuyên nghiệp
    search = st.text_input("🔍 Tìm nhanh nhân sự:")
    if search:
        st.write(df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)])

except Exception as e:
    st.error(f"❌ LỖI HỆ THỐNG: {e}")
    st.info("Gợi ý: Hãy chắc chắn Tab trong Google Sheet tên là PVD_Data.")
