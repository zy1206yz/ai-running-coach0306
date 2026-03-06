import requests
import os

WEBHOOK = os.environ["FEISHU_WEBHOOK"]

def push(text):

    data = {
        "msg_type": "text",
        "content": {
            "text": text
        }
    }

    requests.post(WEBHOOK, json=data)
