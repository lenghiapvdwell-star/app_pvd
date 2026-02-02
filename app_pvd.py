import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import base64
import json

# 1. Cấu hình trang
st.set_page_config(page_title="PVD Personnel 2026", layout="wide")

# 2. Giải mã thông tin tài khoản (Dứt điểm lỗi PEM/Ký tự lạ)
# Chuỗi này đã được mã hóa an toàn, không chứa ký tự xuống dòng gây lỗi
encoded_creds = "eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsICJwcm9qZWN0X2lkIjogInB2ZC1tYW5hZ2VtZW50LTg3IiwgInByaXZhdGVfa2V5X2lkIjogImVmMzE1ZGRjNDFjNTIwMzRlNmYzODk3Njk0YThhZjYzZGUzYzBmZGQiLCAicHJpdmF0ZV9rZXkiOiAiLS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tXG5NSUlFdlFJQkFEQU5CZ2txaGtpRzl3MEJBUUVGQUFTQ0JLY3dnZ1NqQWdFQUFvSUJBUURIcTdxSXlTY0ZMMTJqXG4yUzhkdUErTXB4b2tjOWZwdWxMZkhtVWRPSUJ1WmMyMk1sZ3JsMi9SbGp4MSt0OUFCdEJTUmFza25mY3k4VFRsXG54WWRuNm1Jd0lCcnowMGpvdWdEdnJEYkNSdFUra1VQVGRJUWkyQ3dmekhPMGtkVmxETmpYSE9mYXEwWU5yQ2NmXG4yZjNVYjRRNy9ZcE5OTW5wQ2Q2KzQ1bk9rR1pRNGd6K0xIMzZmVEdSOW9UZm1PbklaNG8wc3RIeU8wSXB3aDFoXG52OUtMUUFvTUJtTGo4aDdVQVhGRkxiekJGOXlBWHN6QzNDazYxMUE3SzczTkRaRlRsRUNnSFNiRFFTZHVQSFFRXG5MODhNUVc1Q01LSi9wVzljQ3V3REhWQVJUbzJGQmJrQjFkbERBc1pBUlcvNmQxNU9pY2FORVor दादी ZFZMcXQrUjZvQXpBZ01CQUFFQ2dnRUFKMGlME5JRk8rZ2d0cGpUdXZpd2Vjdy9WWnVLYjBsSmtSNTJWUzBCNGxEL1hcblQwZHNiaGNuK3RaU0l1d3V6RXdLNUlUc2ZSSE9OdWlaL2JMMVJ3Nm9Mc3ZDS0pPdlBwYUo1SjIvVUUzYldwRFAXG5CVVZoTWZIU0RKZVBGREcxQ0dLVXJ3M3kxK1RtclgzM1hKN28vOGpJL1h5T24wNEpZNTM3Z3hjSWhjbUhOOVpJXG50T1hEYStlWWUxeUo1RUFOS0ZWbmQvM0dUUndpcjB3N1p2QjRCYTZjTDRIZDJkWF0veHY2OWprTXdLL25iN3FiXG5uZXRGMXRtbFV4VGpuRUZIQStrMFpJekNWTnk0S1VnNDR5RG1xWHlUUXNsTkh4S2RIZFhpYTBNUjR2VDBsdVNPXG5GZnRMeU83OTdvbStxdVdNajRpN0xrc0tWVTlFWW1sSE45WkRHR0Z4Z1FLQmdRRG9VUkRqMnBGaTc4S3BrOWk0XG5IOU52QXI1L2xvMnJsR3ZBYnQ1NXFkckhHYnZld2pMSUQ4V0ZSUmdSTGYyUm5pT1RaUnR6ck5GVGUzQUlXbGp2XG5sRTdoeElwblJXallvTUxrTGJPWDNKaWFoWnlrN1kyZDBSKzBubkpNTWlxSXRJbXM3VFNrRmlob05ySEdsXG5QNVY5Z1M5UG1ieTdkSkFRRGswcFJLYzRvUUtCZ1FEY0JxNDlJbHpqbEtSSk1XemJtay9rSWJCRjllV1V4SmppXG5Ec3crTVlPNGNQWTY2WEkvOWNiOG5WZVREclZ4cS9XQldrSzU5Nmh1VE82WjZFM2hqNkRjRkRjZ2lXdUxqekNyXG5TYkFJTzUxTkhROWFFNmUyaHRYc3NadnQyZFNvUU5temwyRVFIS1I3UjlLd21zcStrOHVhSzZoNG5YZXhRV1VkXG5XeEoxOXlrVXdLQmdHVk0zQUdQRC9CRlBldTExVDFNVzJTL25KT0Q4WmlNcW9PSmxLY1dncGhveHp2MkVXQ2VcbmQvR0oxRm5CWlIwM0NLby8zejJNY09abkg4MzBuMjB4UExvNVJwa3dydnZEZytaVjBiOUlEV3B4QlNES0Q2R05cbi5sR2Q4blpQUG1PUmZOS1c5bks1b1ZNMVF5WFowdUJNbm9IUWIvSFV4ckF5dnBMUnVhR3lGdnloQW9HQUcwRWdcbm1DWUg1RkVBR1VFN1BiaWFvblp4U2s2ZFFFZHZkMVdZM2pTcmlnZjkvNjdQMU8xcl9PdDFJNDY0RWZDczNEXG5GVlllSVB1YW1xbng2N3pVMmk0TzNoTG5wWFA5UHc1MVJhL012bDZaSmpsRkR4RUlzcmNVOEx1STRnYVdjTzZSXG5jV042NUdKek1Ma2I0QnVDbndoRmlCdEpWV1paZHRkdkJyM1Z3RTBDZ1lFQTU5a1NXR1Vxcm9KcnQ2SERtVFhJXG5iemhodE1acjNGZUs5U254eEM2VmRDZ2xPTlRQTVhSa2k5MHRiRmJLNHNYeWpHbnJHZk9vbE1DVitkMWpma1RXVlxuNi9pTThJaFNFTkU3VzZVNnNUY1RBaEpoN3BaU0h0NUVKOVZ4M1pnSldUb0UzbGV5U0RNUHlPK1E4NS9lbnlvXG5JQTVkbEZWdjNxUVVUdFBGOWVSRVVjPQotLS0tLUVORCBQUklWQVRFIEtFWS0tLS0tXG4iLCAiY2xpZW50X2VtYWlsIjogInB2ZC1zeW5jQHB2ZC1tYW5hZ2VtZW50LTg3LmlhbS5nc2VydmljZWFjY291bnQuY29tIiwgImNsaWVudF9pZCI6ICIxMDExNDk1NzI5Mjk1MTQ1NjA5NTMiLCAiYXV0aF91cmkiOiAiaHR0cHM6Ly9hY2NvdW50cy5nb29nbGUuY29tL28vb2F1dGgyL2F1dGgiLCAidG9rZW5fdXJpIjogImh0dHBzOi8vb2F1dGgyLmdvb2dsZWFwaXMuY29tL3Rva2VuIiwgImF1dGhfcHJvdmlkZXJfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9vYXV0aDIvdjEvY2VydHMiLCAiY2xpZW50X3g1MDlfY2VydF91cmwiOiAiaHR0cHM6Ly93d3cuZ29vZ2xlYXBpcy5jb20vcm9ib3QvdjEvbWV0YWRhdGEveDUwOS9wdmQtc3luYyU0MHB2ZC1tYW5hZ2VtZW50LTg3LmlhbS5nc2VydmljZWFjY291bnQuY29tIn0="

@st.cache_resource
def get_authenticated_client():
    # Giải mã Base64 sang JSON
    decoded_bytes = base64.b64decode(encoded_creds)
    creds_dict = json.loads(decoded_bytes)
    # Xử lý ký tự xuống dòng thực tế
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(credentials)

# 3. Giao diện và Đọc dữ liệu
st.title("PVD PERSONNEL CLOUD 2026")

try:
    client = get_authenticated_client()
    # Mở bằng ID file đã biết
    spreadsheet_id = "1mNVM-Gq6JkF41Yz7JDRiiLtWOtoQHnXwyp3LTRGt-2E"
    sheet = client.open_by_key(spreadsheet_id)
    worksheet = sheet.worksheet("PVD_Data")
    
    # Đọc dữ liệu
    records = worksheet.get_all_records()
    df = pd.DataFrame(records)
    
    st.success("🚀 KẾT NỐI CLOUD THÀNH CÔNG!")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"❌ LỖI: {e}")
    st.info("Kiểm tra xem tên Tab có đúng là 'PVD_Data' không.")
