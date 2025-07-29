import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailSender:
    def __init__(self, smtp_login, smtp_password, email, smtphost, smtpport):
        self.smtp_login = smtp_login
        self.smtp_password = smtp_password
        self.email = email
        self.smtphost = smtphost
        self.smtpport = smtpport

    def send(self, message, sim):
        msg = MIMEMultipart()
        msg['From'] = self.smtp_login
        msg['To'] = self.email
        msg['Subject'] = f"New SMS for {sim}"
        body = f"New message:\n  Date: {message['date']}\n  Client: {message['from']}\n  Text: {message['text']}\n"
        msg.attach(MIMEText(body, 'plain'))

        print(msg)
        try:
            server = smtplib.SMTP(self.smtphost, self.smtpport)
            server.starttls()
            server.login(self.smtp_login, self.smtp_password)
            text = msg.as_string()
            server.sendmail(self.smtp_login, self.email, text)
            server.quit()
            print("♻️ Email sent successfully!")
        except Exception as e:
            print("❗️ Error sending email:", e)
