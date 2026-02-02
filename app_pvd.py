import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. Cấu hình giao diện
st.set_page_config(page_title="PVD Personnel 2026", layout="wide")

# 2. MÃ KHÓA SIÊU SẠCH (Đã gộp thành 1 dòng để xóa bỏ lỗi PEM)
# Tuyệt đối không tự ý xuống dòng ở biến PK_RAW này
PK_RAW = "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDHq7qIyScFL12j2S8duA+Mpxokc9fpulLfHmUdOIBuZc22Mlgrl2/Rljx1+t9ABtBSRasknfcy8TTlxYdn6mIwIBpz00jougDvrDbCRtU+EUPTdIQi2CwfzHO0kdVlDNjXHOfaq0YNrCcf2f3Ub4Q7/YpNNMnpCd6+45nOkGZQ4gz+LH36fTGR9oTfmOnIZ4o0stHyO0Ipwh1hv9KLQAoMBmLj8h7UAxFFLbIzBF9yAXszC3k611A7K73NDZFTlECgHSbDQSduPHUQL8HfMQW5CMkJ/pW9cCuwDHVARTo2GBbkB1dlDAsZARW/6d15OicaNEZ+yoQsCzVLxt+r6oAzAgMBAAECggEAJ0i0NIFO+ggtpjTuviwecw/VZuKb0lJkR52VS0B4lD/XT0dsbXcn+tZSIuwuzEwK5ITsfRHPNuiZ/bL1Rw6oLsvCKJOjPpaJ5J2/UE3bWpDPBWVhMfHSDJePFDG1CGKUrw3y1+TmrX33XJ7o/8jI/XyOn04Jg537gxcIhcmHN9ZItOXDa+eYe1yJ5EANKFVnd/3GTRwir0w7ZvB4Ba6cL4HD2dXM/xv69jkMwK/nb7qbnetF1tmlUxTjnEFHAkl0ZIzCVNy4KUg44yDmqXyTQslNHxKdHdXia0MR4vT0luSOFftLyO797om+quWGj4i7LksKVU9EYmlHN9ZDGDFxgQKBgQDoURDj2pFi78Kpk9i4H9NvAr5/lo2rlGvAbt55qdrHGbvewjLID8WFRRgRLf2RniOTZRtzrNFTe3AIWljvleE7hxIpnRWjYEoMLkLbOX3JiahZyk7Y2d0R+0nmJNMiqItIms7TSkFihOhnrHGlP5V9gS9Pmby7dJAQDk0pRKc4oQKBgQDcBq49IlzjlKRJMWzbmk/kIbBf9eWUxJyiDsw+MYO4cPY6XI/9cb8nVeTjLdVxq/WBWKk596huTO6Z6E3hj6DcFDcgiWuLjzCrSbAIO51NHQ9aE6e2htXssZft2dSoQNmzl2EQHKR7R9Kwmsq+k8uaK6h4nXexQWUdWxGJ9eykUwKBgGVM3AGPD/BFPeu11T1MW2S/nJOD8ZiMqoOJlKcWgphoxzv2EDCend/GJ1FnBZR03CKo/3z2McOZnH830n20xPLo5RpkwrvvDg+ZV0b9IDWpxBSDKD6GNNlGd8nZRPmORfNKW9nK5oVM1QyXZ0uBMnoHQb/HUxrAyvpLRuaGyFvyhAoGAG0EgmCYHh5FEAGUE7PbiaonZxSk6dQEdvd1DY3jSrigf9/67P1O1r/Ot1I464EfCs3D+FVYeIPuamqnx67zU2i4O3hLnpXPpPW51Ra/Mvl6ZJjlFDxEIsrcU8LuI4gaWcO6RcWN65GJzMLkb4BuCnuhFiBtJVkWZdtdvBr3VwE0CgYEA59kSWGUqroJrt6HDmTXIizhhtMZr3FeK9SnxxC6VdCglONTPMXRk90tbFbK4sXyjGnrGfOolMCV+d1jfkTWf6/iM8IhSENE7W6U6sTcTAhJh7tZSHt5EJ9V83ZgJWToE3leySDMPyO+Q85/enyoqIA5dlFVv3qQUTFtPG9REUuc="

# Tự động dựng lại định dạng PEM đúng tiêu chuẩn trong bộ nhớ
FINAL_PRIVATE_KEY = f"-----BEGIN PRIVATE KEY-----\n{PK_RAW}\n-----END PRIVATE KEY-----\n"

cred_dict = {
    "type": "service_account",
    "project_id": "pvd-management-87",
    "private_key_id": "ef315ddc41c52034e6f3897694a8af63de3c0fdd",
    "private_key": FINAL_PRIVATE_KEY,
    "client_email": "pvd-sync@pvd-management-87.iam.gserviceaccount.com",
    "token_uri": "https://oauth2.googleapis.com/token",
}

# 3. Kết nối trực tiếp
@st.cache_resource
def get_data_from_cloud():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(cred_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    # Mở Sheet bằng ID (ID này trích xuất từ link của bạn)
    sheet = client.open_by_key("1mNVM-Gq6JkF41Yz7JDRiiLtWOtoQHnXwyp3LTRGt-2E")
    worksheet = sheet.worksheet("PVD_Data")
    return pd.DataFrame(worksheet.get_all_records())

# 4. Hiển thị ứng dụng
st.title("🚢 PVD PERSONNEL CLOUD 2026")

try:
    df = get_data_from_cloud()
    st.success("✅ KẾT NỐI DỮ LIỆU ĐÁM MÂY THÀNH CÔNG!")
    
    # Thêm bộ lọc tìm kiếm cho chuyên nghiệp
    search = st.text_input("🔍 Tìm kiếm nhân viên (Tên, MSNV, Chức danh...):")
    if search:
        df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
    
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"❌ LỖI HỆ THỐNG: {e}")
    st.info("Vui lòng kiểm tra lại tên Tab trong Google Sheet (phải chính xác là: PVD_Data)")
