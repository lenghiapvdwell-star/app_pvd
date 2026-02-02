import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. Cấu hình trang
st.set_page_config(page_title="PVD Management 2026", layout="wide")

# 2. Khai báo thông tin tài khoản (Dán cứng để dứt điểm)
# Lưu ý: private_key đã được xử lý \n ngay trong chuỗi
cred_info = {
    "type": "service_account",
    "project_id": "pvd-management-87",
    "private_key_id": "ef315ddc41c52034e6f3897694a8af63de3c0fdd",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDHq7qIyScFL12j\n2S8duA+Mpxokc9fpulLfHmUdOIBuZc22Mlgrl2/Rljx1+t9ABtBSRasknfcy8TTl\nxYdn6mIwIBpz00jougDvrDbCRtU+EUPTdIQi2CwfzHO0kdVlDNjXHOfaq0YNrCcf\n2f3Ub4Q7/YpNNMnpCd6+45nOkGZQ4gz+LH36fTGR9oTfmOnIZ4o0stHyO0Ipwh1h\nv9KLQAoMBmLj8h7UAxFFLbIzBF9yAXszC3k611A7K73NDZFTlECgHSbDQSduPHUQ\nL8HfMQW5CMkJ/pW9cCuwDHVARTo2GBbkB1dlDAsZARW/6d15OicaNEZ+yoQsCzVL\nxt+r6oAzAgMBAAECggEAJ0i0NIFO+ggtpjTuviwecw/VZuKb0lJkR52VS0B4lD/X\nT0dsbXcn+tZSIuwuzEwK5ITsfRHPNuiZ/bL1Rw6oLsvCKJOjPpaJ5J2/UE3bWpDP\nBWVhMfHSDJePFDG1CGKUrw3y1+TmrX33XJ7o/8jI/XyOn04Jg537gxcIhcmHN9ZI\ntOXDa+eYe1yJ5EANKFVnd/3GTRwir0w7ZvB4Ba6cL4HD2dXM/xv69jkMwK/nb7qb\nnetF1tmlUxTjnEFHAkl0ZIzCVNy4KUg44yDmqXyTQslNHxKdHdXia0MR4vT0luSO\nFftLyO797om+quWGj4i7LksKVU9EYmlHN9ZDGDFxgQKBgQDoURDj2pFi78Kpk9i4\nH9NvAr5/lo2rlGvAbt55qdrHGbvewjLID8WFRRgRLf2RniOTZRtzrNFTe3AIWljv\leE7hxIpnRWjYEoMLkLbOX3JiahZyk7Y2d0R+0nmJNMiqItIms7TSkFihOhnrHGl\nP5V9gS9Pmby7dJAQDk0pRKc4oQKBgQDcBq49IlzjlKRJMWzbmk/kIbBf9eWUxJyi\nDsw+MYO4cPY6XI/9cb8nVeTjLdVxq/WBWKk596huTO6Z6E3hj6DcFDcgiWuLjzCr\nSbAIO51NHQ9aE6e2htXssZft2dSoQNmzl2EQHKR7R9Kwmsq+k8uaK6h4nXexQWUd\WxGJ9eykUwKBgGVM3AGPD/BFPeu11T1MW2S/nJOD8ZiMqoOJlKcWgphoxzv2EDCe\nd/GJ1FnBZR03CKo/3z2McOZnH830n20xPLo5RpkwrvvDg+ZV0b9IDWpxBSDKD6GN\nNlGd8nZRPmORfNKW9nK5oVM1QyXZ0uBMnoHQb/HUxrAyvpLRuaGyFvyhAoGAG0Eg\nmCYHh5FEAGUE7PbiaonZxSk6dQEdvd1DY3jSrigf9/67P1O1r/Ot1I464EfCs3D+\nFVYeIPuamqnx67zU2i4O3hLnpXPpPW51Ra/Mvl6ZJjlFDxEIsrcU8LuI4gaWcO6R\ncWN65GJzMLkb4BuCnuhFiBtJVkWZdtdvBr3VwE0CgYEA59kSWGUqroJrt6HDmTXI\nizhhtMZr3FeK9SnxxC6VdCglONTPMXRk90tbFbK4sXyjGnrGfOolMCV+d1jfkTWf\n6/iM8IhSENE7W6U6sTcTAhJh7tZSHt5EJ9V83ZgJWToE3leySDMPyO+Q85/enyoq\nIA5dlFVv3qQUTFtPG9REUuc=\n-----END PRIVATE KEY-----\n",
    "client_email": "pvd-sync@pvd-management-87.iam.gserviceaccount.com",
    "token_uri": "https://oauth2.googleapis.com/token",
}

# 3. Kết nối thủ công qua gspread
@st.cache_resource
def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    # Tự động thay thế \n để dứt điểm lỗi PEM
    cred_info["private_key"] = cred_info["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(cred_info, scopes=scopes)
    return gspread.authorize(creds)

try:
    client = get_gspread_client()
    # Mở Spreadsheet bằng ID (Dùng ID cho chắc chắn nhất)
    # ID lấy từ link của bạn: 1mNVM-Gq6JkF41Yz7JDRiiLtWOtoQHnXwyp3LTRGt-2E
    sheet = client.open_by_key("1mNVM-Gq6JkF41Yz7JDRiiLtWOtoQHnXwyp3LTRGt-2E")
    worksheet = sheet.worksheet("PVD_Data")
    
    # Lấy toàn bộ dữ liệu
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)

    st.title("PVD PERSONNEL 2026")
    st.success("✅ KẾT NỐI TRỰC TIẾP THÀNH CÔNG!")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"❌ LỖI KẾT NỐI: {e}")
    st.info("Hãy đảm bảo Tab trong Google Sheet được đặt tên chính xác là: PVD_Data")
