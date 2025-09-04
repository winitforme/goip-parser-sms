# https_sender/https_sender.py
import requests
from typing import Optional

class HttpsSender:
    def __init__(self, url, location):
        self.url = url
        self.goip_location = location

    def send(self, message: dict, sim: str, sim_info: Optional[dict] = None):

        headers = {"Content-Type": "application/json; charset=utf-8"}

        payload = {
            "location": self.goip_location,
            "sim": sim,
            "message": {
                "from": message.get("from"),
                "text": message.get("text"),
                "date": message.get("date"),
            }
        }
        if sim_info:
            # Пример структуры; поля бери из твоей sim_info_current
            payload["sim_info"] = {
                "channel_id":   sim_info.get("channel_id"),
                "operator":     sim_info.get("operator"),
                "phone":        sim_info.get("phone"),
                "name":         sim_info.get("name"),
                "pin":          sim_info.get("pin"),
                "imsi":         sim_info.get("imsi"),
                "last_digits":  sim_info.get("last_digits"),
            }

        try:
            response = requests.post(self.url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                print(f"✅ Message '{message.get('text')}' forwarded from SIM {sim} to {self.url}")
            else:
                print(f"❌ Failed to send message from SIM {sim}. Status: {response.status_code} Body: {response.text[:200]}")
        except requests.RequestException as e:
            print(f"❌ Error sending message from SIM {sim}: {e}")
