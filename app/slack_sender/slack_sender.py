import requests

class SlackSender:
    def __init__(self, slack_token, slack_channel):
        self.slack_token = slack_token
        self.slack_channel = slack_channel

    def _send(self, message, sim):
        url = "https://slack.com/api/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {self.slack_token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        m = f"New SMS for {sim}:\n  Date: {message['date']}\n  Client: {message['from']}\n  Text: {message['text']}\n"
        payload = {
            "channel": self.slack_channel,
            "text": m
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"Failed to send message")