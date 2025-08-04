import base64
import requests
import re

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
            print(f"❌ Ошибка при подключении к GoIP ({self.goip_addr}): {e}")
            return []

        try:
            data = response.content.decode('utf-8')
        except UnicodeDecodeError:
            data = response.content.decode('latin1')

        data = data.replace('\\"', '"')
        sms_dump_arr = re.findall(r'sms= \[(.*?)\]', data, re.IGNORECASE | re.DOTALL)

        all_messages = []

        for sim_index, sim_raw in enumerate(sms_dump_arr):
            sim_messages = []
            items = [x.strip("'") for x in re.findall(r"'(.*?)'", sim_raw)]

            # Разбиваем на блоки по 3 (дата, отправитель, текст)
            for i in range(0, len(items) - 2, 3):
                date = items[i]
                sender = items[i + 1]
                text = items[i + 2]
                sim_messages.append({
                    'date': date,
                    'from': sender,
                    'text': text,
                    'line': i + 1
                })

            all_messages.append(sim_messages)

        return all_messages
