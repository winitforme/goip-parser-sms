import smtplib
import logging
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from smtplib import SMTPAuthenticationError

class EmailSender:
    def __init__(self, smtp_login, smtp_password, email, smtphost, smtpport, location, debug=False):
        self.smtp_login = smtp_login            
        self.smtp_password = smtp_password      
        self.email = email                      
        self.smtphost = smtphost                
        self.smtpport = int(smtpport)           
        self.goip_location = location
        self.debug = debug

    def send(self, message, sim) -> bool:
        msg = MIMEMultipart()
        msg["From"] = self.smtp_login
        msg["To"] = self.email
        msg["Subject"] = f"New SMS for {sim}"
        body = (
            f"[{self.goip_location}] New message:\n"
            f"  Date: {message.get('date')}\n"
            f"  Client: {message.get('from')}\n"
            f"  Text: {message.get('text')}\n"
        )
        msg.attach(MIMEText(body, "plain"))

        logging.info("Email -> %s (from: %s)", self.email, message.get("from"))

        try:
            if self.smtpport == 465:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.smtphost, self.smtpport, context=context, timeout=30)
            else:
                server = smtplib.SMTP(self.smtphost, self.smtpport, timeout=30)
                if self.debug:
                    server.set_debuglevel(1)
                server.ehlo()
                if self.smtpport == 587:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                    server.ehlo()

            # у большинства провайдеров логин = полный email
            server.login(self.smtp_login, self.smtp_password)

            server.sendmail(self.smtp_login, [self.email], msg.as_string())
            server.quit()
            logging.info("✅ Email sent successfully")
            return True

        except SMTPAuthenticationError as e:
            logging.error("❌ SMTP auth failed: %s", e, exc_info=True)
            return False
        except Exception as e:
            logging.error("❌ Error sending email: %s", e, exc_info=True)
            return False
