from garminconnect import Garmin
from openai import OpenAI

import os

email = os.environ["GARMIN_EMAIL"]
password = os.environ["GARMIN_PASSWORD"]
openai_key = os.environ["OPENAI_KEY"]

client = Garmin(email, password)
client.login()

activities = client.get_activities(0,1)
run = activities[0]

distance = run["distance"]
duration = run["duration"]

data = f"distance {distance} duration {duration}"

ai = OpenAI(api_key=openai_key)

response = ai.chat.completions.create(
model="gpt-4.1-mini",
messages=[
{"role":"system","content":"You are a professional marathon coach"},
{"role":"user","content":f"Analyze this run: {data}"}
]
)

print(response.choices[0].message.content)
