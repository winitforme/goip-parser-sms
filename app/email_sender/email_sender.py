import smtplib
import logging
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from smtplib import SMTPAuthenticationError
from typing import Union
from typing import Optional

class EmailSender:
    def __init__(self, smtp_login, smtp_password, email, smtphost, smtpport, location, debug=False):
        self.smtp_login = smtp_login            
        self.smtp_password = smtp_password      
        self.email = email                      
        self.smtphost = smtphost                
        self.smtpport = int(smtpport)           
        self.goip_location = location
        self.debug = debug

    def send(self, message, sim, sim_info: Optional[dict] = None) -> bool:

        if sim_info:
            sim_info_text = ""
            sim_info_text += f"\nchannel_id: {sim_info.get('channel_id') }"
            sim_info_text += f"\noperator: {sim_info.get('operator')}" 
            sim_info_text += f"\nphone: {sim_info.get('phone')}" 
            sim_info_text += f"\nname: {sim_info.get('name')}" 
            sim_info_text += f"\npin: {sim_info.get('pin')}" 
            sim_info_text += f"\nimsi: {sim_info.get('imsi')}" 
            sim_info_text += f"\nlast_digits: {sim_info.get('last_digits')}" 

        msg = MIMEMultipart()
        msg["From"] = self.smtp_login
        msg["To"] = self.email
        msg["Subject"] = f"[{self.goip_location}] New SMS for channel {sim}"
        body = (
            f"[{self.goip_location}] New message:\n"
            f"  \nDate: {message.get('date')}\n"
            f"  \nClient: {message.get('from')}\n"
            f"  \nText: {message.get('text')}\n"
            f"  \nsim_info: {sim_info_text}\n"
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

            server.login(self.smtp_login, self.smtp_password)

            server.sendmail(self.smtp_login, [self.email], msg.as_string())
            server.quit()
            logging.warning("✅ Email sent successfully")
            return True

        except SMTPAuthenticationError as e:
            logging.error("❌ SMTP auth failed: %s", e, exc_info=True)
            return False
        except Exception as e:
            logging.error("❌ Error sending email: %s", e, exc_info=True)
            return False
