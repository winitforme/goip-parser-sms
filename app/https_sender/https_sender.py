import requests

class HttpsSender:
    def __init__(self, url, location):
        self.url = url
        self.goip_location = location

    def send(self, message, sim):
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        payload = {
            "text": message,
            "location": self.goip_location
        }

        try:
            response = requests.post(self.url, headers=headers, json=payload)
            if response.status_code == 200:
                print(f"✅ Message '{message}' successfully forward from SIM {sim} to host {self.url}")
            else:
                print(f"❌ Failed to send message from SIM {sim}. Status code: {response.status_code}")
        except requests.RequestException as e:
            print(f"❌ Error sending message from SIM {sim}: {e}")
