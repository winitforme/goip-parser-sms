# https_sender/https_sender.py
import requests
import curlify
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

    def _hmac512_b64(self, body_bytes: bytes, key: str) -> str:
        return base64.b64encode(hmac.new(key.encode('utf-8'), body_bytes, hashlib.sha512).digest()).decode('utf-8')

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

        body_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False, sort_keys=True)
        body_bytes = body_str.encode('utf-8')

        headers['signature'] = self._hmac512_b64(body_bytes, self.salt)

        try:
            response = requests.post(self.url, headers=headers, data=body_bytes, timeout=15)
            logging.debug(curlify.to_curl(response.request))
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
