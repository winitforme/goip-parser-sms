# https_sender/https_sender.py
import requests
import logging
import hmac
import hashlib
import base64
import json
from typing import Union
from typing import Optional

class HttpsSender:
    def __init__(self, url, location, salt):
        self.url = url
        self.goip_location = location
        self.salt = salt

    def calculate_mobile_api_simbank_signature(self, payload: dict, key: str) -> str:

        body_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
        body_bytes = body_str.encode("utf-8")
        key_bytes = key.encode("utf-8")

        # HMAC-SHA512
        h = hmac.new(key_bytes, body_bytes, hashlib.sha512)

        return base64.b64encode(h.digest()).decode("utf-8")

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
            payload["sim_info"] = {
                "channel_id":   sim_info.get("channel_id"),
                "operator":     sim_info.get("operator"),
                "phone":        sim_info.get("phone"),
                "name":         sim_info.get("name"),
                "pin":          sim_info.get("pin"),
                "imsi":         sim_info.get("imsi"),
                "last_digits":  sim_info.get("last_digits"),
            }

        signature = self.calculate_mobile_api_simbank_signature(payload, self.salt)

        payload['signature'] = signature

        try:
            response = requests.post(self.url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                logging.info(f"✅ Message '{message.get('text')}' forwarded from SIM {sim} to {self.url}")
                return True
            else:
                logging.error(f"❌ Failed to send message from SIM {sim}. Status: {response.status_code} Body: {response.text[:200]}")
                return False
        except requests.RequestException as e:
            logging.error(f"❌ Error sending message from SIM {sim}: {e}")
            return False
        except Exception as e:
            logging.error(f"❌ Error sending callback from SIM {sim}: {e}")
            return False
