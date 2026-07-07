"""短信发送工具 (smsbao.com)"""
import hashlib
import urllib.request
import urllib.parse


def send_sms(phone, content, user, password):
    """通过 SMSBao API 发送短信"""
    api_url = "http://api.smsbao.com/"
    pwd_hash = hashlib.md5(password.encode("utf8")).hexdigest()
    params = urllib.parse.urlencode({"u": user, "p": pwd_hash, "m": phone, "c": content})
    resp = urllib.request.urlopen(api_url + "sms?" + params)
    status = {
        "0": "发送成功", "30": "密码错误", "40": "账号不存在",
        "41": "余额不足", "42": "账户已过期", "43": "IP限制", "50": "敏感词"
    }
    code = resp.read().decode("utf-8")
    print(status.get(code, f"未知状态: {code}"))


if __name__ == "__main__":
    send_sms(
        phone="13800138000",
        content="检测到异常事件，请及时处理！",
        user="your_account",
        password="your_password"
    )
