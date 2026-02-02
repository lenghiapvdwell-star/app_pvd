import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. Cấu hình trang
st.set_page_config(page_title="PVD Personnel 2026", layout="wide")

# 2. Gia cố mã khóa bằng danh sách dòng (Dứt điểm lỗi PEM)
key_lines = [
    "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDHq7qIyScFL12j",
    "2S8duA+Mpxokc9fpulLfHmUdOIBuZc22Mlgrl2/Rljx1+t9ABtBSRasknfcy8TTl",
    "xYdn6mIwIBpz00jougDvrDbCRtU+EUPTdIQi2CwfzHO0kdVlDNjXHOfaq0YNrCcf",
    "2f3Ub4Q7/YpNNMnpCd6+45nOkGZQ4gz+LH36fTGR9oTfmOnIZ4o0stHyO0Ipwh1h",
    "v9KLQAoMBmLj8h7UAxFFLbIzBF9yAXszC3k611A7K73NDZFTlECgHSbDQSduPHUQ",
    "L8HfMQW5CMkJ/pW9cCuwDHVARTo2GBbkB1dlDAsZARW/6d15OicaNEZ+yoQsCzVL",
    "xt+r6oAzAgMBAAECggEAJ0i0NIFO+ggtpjTuviwecw/VZuKb0lJkR52VS0B4lD/X",
    "T0dsbXcn+tZSIuwuzEwK5ITsfRHPNuiZ/bL1Rw6oLsvCKJOjPpaJ5J2/UE3bWpDP",
    "BWVhMfHSDJePFDG1CGKUrw3y1+TmrX33XJ7o/8jI/XyOn04Jg537gxcIhcmHN9ZI",
    "tOXDa+eYe1yJ5EANKFVnd/3GTRwir0w7ZvB4Ba6cL4HD2dXM/xv69jkMwK/nb7qb",
    "netF1tmlUxTjnEFHAkl0ZIzCVNy4KUg44yDmqXyTQslNHxKdHdXia0MR4vT0luSO",
    "FftLyO797om+quWGj4i7LksKVU9EYmlHN9ZDGDFxgQKBgQDoURDj2pFi78Kpk9i4",
    "H9NvAr5/lo2rlGvAbt55qdrHGbvewjLID8WFRRgRLf2RniOTZRtzrNFTe3AIWljv",
    "leE7hxIpnRWjYEoMLkLbOX3JiahZyk7Y2d0R+0nmJNMiqItIms7TSkFihOhnrHGl",
    "P5V9gS9Pmby7dJAQDk0pRKc4oQKBgQDcBq49IlzjlKRJMWzbmk/kIbBf9eWUxJyi",
    "Dsw+MYO4cPY6XI/9cb8nVeTjLdVxq/WBWKk596huTO6Z6E3hj6DcFDcgiWuLjzCr",
    "SbAIO51NHQ9aE6e2htXssZft2dSoQNmzl2EQHKR7R9Kwmsq+k8uaK6h4nXexQWUd",
    "WxGJ9eykUwKBgGVM3AGPD/BFPeu11T1MW2S/nJOD8ZiMqoOJlKcWgphoxzv2EDCe",
    "nd/GJ1FnBZR03CKo/3z2McOZnH830n20xPLo5RpkwrvvDg+ZV0b9IDWpxBSDKD6GN",
    "NlGd8nZRPmORfNKW9nK5oVM1QyXZ0uBMnoHQb/HUxrAyvpLRuaGyFvyhAoGAG0Eg",
    "mCYHh5FEAGUE7PbiaonZxSk6dQEdvd1DY3jSrigf9/67P1O1r/Ot1I464EfCs3D+",
    "FVYeIPuamqnx67zU2i4O3hLnpXPpPW51Ra/Mvl6ZJjlFDxEIsrcU8LuI4gaWcO6R",
    "cWN65GJzMLkb4BuCnuhFiBtJVkWZdtdvBr3VwE0CgYEA59kSWGUqroJrt6HDmTXI",
    "izhhtMZr3FeK9SnxxC6VdCglONTPMXRk90tbFbK4sXyjGnrGfOolMCV+d1jfkTWf",
    "6/iM8IhSENE7W6U6sTcTAhJh7tZSHt5EJ9V83ZgJWToE3leySDMPyO+Q85/enyoq",
    "IA5dlFVv3qQUTFtPG9REUuc="
]

# Tái cấu trúc chuỗi PEM chuẩn từ danh sách
PRIVATE_KEY = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(key_lines) + "\n-----END PRIVATE KEY-----\n"

@st.cache_resource
def get_gspread_client():
    cred_info = {
        "type": "service_account",
        "project_id": "pvd-management-87",
        "private_key_id": "ef315ddc41c52034e6f3897694a8af63de3c0fdd",
        "private_key": PRIVATE_KEY,
        "client_email": "pvd-sync@pvd-management-87.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(cred_info, scopes=scopes)
    return gspread.authorize(creds)

st.title("🚢 PVD PERSONNEL CLOUD 2026")

try:
    client = get_gspread_client()
    # Mở bảng tính bằng ID
    sheet = client.open_by_key("1mNVM-Gq6JkF41Yz7JDRiiLtWOtoQHnXwyp3LTRGt-2E")
    worksheet = sheet.worksheet("PVD_Data")
    
    # Đọc dữ liệu
    df = pd.DataFrame(worksheet.get_all_records())
    
    if not df.empty:
        st.success("✅ KẾT NỐI DỮ LIỆU ĐÁM MÂY THÀNH CÔNG!")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("⚠️ Đã kết nối nhưng không thấy dữ liệu trong Tab 'PVD_Data'.")

except Exception as e:
    st.error(f"❌ LỖI HỆ THỐNG: {e}")
    st.info("Nhắc nhở: Hãy đảm bảo tên Tab trong Google Sheet là 'PVD_Data'.")
