from time import sleep
from datetime import datetime
from utils.utils import Vars
from sms_parser.sms_parser import GoipGateway
from slack_sender.slack_sender import SlackSender
from https_sender.https_sender import HttpsSender
from postgres.postgres import DbWriter
from email_sender.email_sender import EmailSender


vars = Vars()
Goip = GoipGateway(vars.goip_addr, vars.goip_user, vars.goip_password)
Database = DbWriter(vars.db_host, vars.db_port, vars.db_name, vars.db_user, vars.db_password, vars.max_retries, vars.retry_delay)
Slack = SlackSender(slack_channel=vars.slack_channel, slack_token=vars.slack_token)
Email = EmailSender(smtp_login=vars.smtp_login, smtp_password=vars.smtp_password, email=vars.email, smtphost=vars.smtphost, smtpport=vars.smtpport)
Https = HttpsSender(vars.http_addr)

print(f"🟢 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] main.py running...")

while True:
    
    messages = Goip._receive_messages()

    print(messages)

    if not messages:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No messages")

    for i, ch_line_messages in enumerate(messages):
        sim = vars.get_port_names(i)
        # print(sim)
        for message in ch_line_messages:
            print(message)
            _write_status = Database.write(message)
            print(_write_status)
            if _write_status:
                print(f"+ New SMS message for channel {sim} from {message['from']}")
                # Slack._send(message, sim)
                Https.send(message, sim)
                Email.send(message, sim)
            # else: 
            #     print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] The last SMS message from {message['from']} is already acknowledged")

    sleep(vars.timeout)




