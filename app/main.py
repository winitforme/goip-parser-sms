import time
import logging, json
from time import sleep
from datetime import datetime
from utils.utils import Vars
from sms_parser.sms_parser import GoipGateway
from slack_sender.slack_sender import SlackSender
from https_sender.https_sender import HttpsSender
from postgres.postgres import DbWriter
from email_sender.email_sender import EmailSender
from siminfo_loader.siminfo_loader import SimInfoLoader

vars = Vars()
Goip = GoipGateway(vars.goip_addr, vars.goip_user, vars.goip_password)
Database = DbWriter(vars.db_host, vars.db_port, vars.db_name, vars.db_user, vars.db_password, vars.max_retries, vars.retry_delay)
Slack = SlackSender(slack_channel=vars.slack_channel, slack_token=vars.slack_token, location=vars.goip_location)
Email = EmailSender(smtp_login=vars.smtp_login, smtp_password=vars.smtp_password, email=vars.email, smtphost=vars.smtphost, smtpport=vars.smtpport, location=vars.goip_location)
Https = HttpsSender(vars.http_addr, location=vars.goip_location, salt=vars.secret)
loader = SimInfoLoader(sheet_url=vars.sheet_url, shared_dir=vars.shared_dir, db_writer=Database)
last_loader_run = 0

logging.basicConfig(level=vars.loglevel, format="%(asctime)s %(levelname)s: %(message)s")
logging.warning(f"🟢 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] running for {vars.goip_location}...")

while True:

    now = time.time()
    if now - last_loader_run >= 300:
        last_loader_run = now
        path, n = loader.run()
        logging.info(f"Saved: {path}, rows parsed: {n}")
        
    messages = Goip._receive_messages()

    if not any(messages): 
        logging.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No messages")
    else:

        sim_info_map = Database.load_sim_info_current_map()
        logging.debug("sim_info_current map:\n%s", json.dumps(sim_info_map, indent=2, ensure_ascii=False))

        for i, ch_line_messages in enumerate(messages):
            sim_name = vars.get_port_names(i)
            channel_id = i + 1 
            sim_info = sim_info_map.get(channel_id)

            for message in ch_line_messages:

                logging.debug("message:\n%s", json.dumps(message, indent=2, ensure_ascii=False))
                logging.debug("sim_info:\n%s", json.dumps(sim_info, indent=2, ensure_ascii=False))

                if Database.message_exists_and_send(message):
                    continue

                if Database.write(message, new_is_sent_http=False, new_is_sent_email=False):  
                    logging.warning(f"📩 New SMS message for channel {sim_name} from {message['from']}")
                    
                    is_send = Https.send(message, sim_name, sim_info)
                    if is_send:
                        Database.write(message, new_is_sent_http=True)
                        logging.warning(f"📤 SMS callback for channel {sim_name} from {message['from']} was successfully send")

                    try:
                        if Email.send(message, sim_name, sim_info):
                            Database.write(message, new_is_sent_email=True)
                    except Exception as e:
                        logging.error(f"❌ Email send error: {e}")

    sleep(vars.timeout)




