import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. Thiết lập giao diện
st.set_page_config(page_title="PVD Personnel 2026", layout="wide")

# 2. XỬ LÝ MÃ KHÓA (Ép định dạng chuẩn trong bộ nhớ)
# Chuỗi này được thiết kế để máy tính đọc mà không bị lỗi byte
RAW_PK = (
    "-----BEGIN PRIVATE KEY-----\n"
    "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDHq7qIyScFL12j\n"
    "2S8duA+Mpxokc9fpulLfHmUdOIBuZc22Mlgrl2/Rljx1+t9ABtBSRasknfcy8TTl\n"
    "xYdn6mIwIBpz00jougDvrDbCRtU+EUPTdIQi2CwfzHO0kdVlDNjXHOfaq0YNrCcf\n"
    "2f3Ub4Q7/YpNNMnpCd6+45nOkGZQ4gz+LH36fTGR9oTfmOnIZ4o0stHyO0Ipwh1h\n"
    "v9KLQAoMBmLj8h7UAxFFLbIzBF9yAXszC3k611A7K73NDZFTlECgHSbDQSduPHUQ\n"
    "L8HfMQW5CMkJ/pW9cCuwDHVARTo2GBbkB1dlDAsZARW/6d15OicaNEZ+yoQsCzVL\n"
    "xt+r6oAzAgMBAAECggEAJ0i0NIFO+ggtpjTuviwecw/VZuKb0lJkR52VS0B4lD/X\n"
    "T0dsbXcn+tZSIuwuzEwK5ITsfRHPNuiZ/bL1Rw6oLsvCKJOjPpaJ5J2/UE3bWpDP\n"
    "BWVhMfHSDJePFDG1CGKUrw3y1+TmrX33XJ7o/8jI/XyOn04Jg537gxcIhcmHN9ZI\n"
    "tOXDa+eYe1yJ5EANKFVnd/3GTRwir0w7ZvB4Ba6cL4HD2dXM/xv69jkMwK/nb7qb\n"
    "netF1tmlUxTjnEFHAkl0ZIzCVNy4KUg44yDmqXyTQslNHxKdHdXia0MR4vT0luSO\n"
    "FftLyO797om+quWGj4i7LksKVU9EYmlHN9ZDGDFxgQKBgQDoURDj2pFi78Kpk9i4\n"
    "H9NvAr5/lo2rlGvAbt55qdrHGbvewjLID8WFRRgRLf2RniOTZRtzrNFTe3AIWljv\n"
    "leE7hxIpnRWjYEoMLkLbOX3JiahZyk7Y2d0R+0nmJNMiqItIms7TSkFihOhnrHGl\n"
    "P5V9gS9Pmby7dJAQDk0pRKc4oQKBgQDcBq49IlzjlKRJMWzbmk/kIbBf9eWUxJyi\n"
    "Dsw+MYO4cPY6XI/9cb8nVeTjLdVxq/WBWKk596huTO6Z6E3hj6DcFDcgiWuLjzCr\n"\
    "SbAIO51NHQ9aE6e2htXssZft2dSoQNmzl2EQHKR7R9Kwmsq+k8uaK6h4nXexQWUd\n"
    "WxGJ9eykUwKBgGVM3AGPD/BFPeu11T1MW2S/nJOD8ZiMqoOJlKcWgphoxzv2EDCe\n"
    "nd/GJ1FnBZR03CKo/3z2McOZnH830n20xPLo5RpkwrvvDg+ZV0b9IDWpxBSDKD6GN\n"
    "NlGd8nZRPmORfNKW9nK5oVM1QyXZ0uBMnoHQb/HUxrAyvpLRuaGyFvyhAoGAG0Eg\n"
    "mCYHh5FEAGUE7PbiaonZxSk6dQEdvd1DY3jSrigf9/67P1O1r/Ot1I464EfCs3D+\n"
    "FVYeIPuamqnx67zU2i4O3hLnpXPpPW51Ra/Mvl6ZJjlFDxEIsrcU8LuI4gaWcO6R\n"
    "cWN65GJzMLkb4BuCnuhFiBtJVkWZdtdvBr3VwE0CgYEA59kSWGUqroJrt6HDmTXI\n"
    "izhhtMZr3FeK9SnxxC6VdCglONTPMXRk90tbFbK4sXyjGnrGfOolMCV+d1jfkTWf\n"
    "6/iM8IhSENE7W6U6sTcTAhJh7tZSHt5EJ9V83ZgJWToE3leySDMPyO+Q85/enyoq\n"
    "IA5dlFVv3qQUTFtPG9REUuc=\n"
    "-----END PRIVATE KEY-----\n"
)

# Cấu hình Credentials
cred_info = {
    "type": "service_account",
    "project_id": "pvd-management-87",
    "private_key_id": "ef315ddc41c52034e6f3897694a8af63de3c0fdd",
    "private_key": RAW_PK,
    "client_email": "pvd-sync@pvd-management-87.iam.gserviceaccount.com",
    "token_uri": "https://oauth2.googleapis.com/token",
}

@st.cache_resource
def fetch_data():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(cred_info, scopes=scopes)
    gc = gspread.authorize(creds)
    # Mở bằng ID file cho chính xác tuyệt đối
    sh = gc.open_by_key("1mNVM-Gq6JkF41Yz7JDRiiLtWOtoQHnXwyp3LTRGt-2E")
    ws = sh.worksheet("PVD_Data")
    return pd.DataFrame(ws.get_all_records())

st.title("🚢 PVD PERSONNEL CLOUD 2026")

try:
    df = fetch_data()
    st.success("✅ KẾT NỐI HỆ THỐNG THÀNH CÔNG!")
    
    # Tính năng tìm kiếm nhanh
    search = st.text_input("🔍 Tìm kiếm nhân sự (Tên, MSNV, Đơn vị...):")
    if search:
        df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
    
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"❌ LỖI TRUY XUẤT: {e}")
    st.info("Kiểm tra: Bạn đã cấp quyền 'Editor' cho email: pvd-sync@pvd-management-87.iam.gserviceaccount.com chưa?")
