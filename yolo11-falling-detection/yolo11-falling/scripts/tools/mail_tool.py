"""邮件发送工具"""
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr


def send_mail(to_email, subject, body, sender, password, smtp_host="smtp.qq.com", smtp_port=465):
    """发送邮件"""
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = formataddr(["Alert", sender])
    msg["To"] = formataddr(["User", to_email])
    msg["Subject"] = subject

    server = smtplib.SMTP_SSL(smtp_host, smtp_port)
    server.login(sender, password)
    server.sendmail(sender, [to_email], msg.as_string())
    server.quit()
    return True


if __name__ == "__main__":
    send_mail(
        to_email="receiver@example.com",
        subject="预警通知",
        body="检测到异常事件，请及时处理。",
        sender="sender@qq.com",
        password="your_smtp_password"
    )
