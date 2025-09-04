import base64
import requests
import logging
import re
import csv


class GoipGateway:
    def __init__(self, goip_addr, goip_user, goip_password):
        self.goip_addr = goip_addr
        self.goip_user = goip_user
        self.goip_password = goip_password

    def _receive_messages(self):
        auth_string = f"{self.goip_user}:{self.goip_password}"
        auth_header = {
            "Authorization": f"Basic {base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')}"
        }

        try:
            response = requests.get(
                f"{self.goip_addr}/default/en_US/tools.html?type=sms_inbox",
                headers=auth_header,
                timeout=5
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Ошибка при подключении к GoIP ({self.goip_addr}): {e}")
            return []

        try:
            data = response.content.decode('utf-8')
        except UnicodeDecodeError:
            data = response.content.decode('latin1')
        except Exception as e:
            logging.error(f"❌ Incorrect decode: {e}")
            return []

        all_messages = [[] for _ in range(32)]  
        pattern = re.compile(r'sms= \[(.*?)\];\s*sms_row_insert\(.*?,\s*pos,\s*(\d+)\);', re.DOTALL)

        for match in pattern.finditer(data):
            raw_sms, port_str = match.groups()

            logging.debug(f"Find {port_str}: {raw_sms}")

            port_index = int(port_str) - 1

            if not raw_sms.strip():
                continue

            split_sms = re.findall(r'"(.*?)"', raw_sms)

            for msg in split_sms:
                logging.debug(f"msg: {msg}")

                parts = msg.split(",", 2)  # date, from, text

                logging.debug(f"parts[0]: {parts[0]}")

                if len(parts) == 3:
                    all_messages[port_index].append({
                        'date': parts[0].strip(),
                        'from': parts[1].strip(),
                        'text': parts[2].strip(),
                        'line': port_index + 1
                    })

        return all_messages
