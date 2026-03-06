import os
import google.generativeai as genai
from garminconnect import Garmin

# 读取环境变量
email = os.environ["GARMIN_EMAIL"]
password = os.environ["GARMIN_PASSWORD"]
api_key = os.environ["GEMINI_API_KEY"]

# 登录 Garmin
client = Garmin(email, password)
client.login()

# 获取最近活动
activities = client.get_activities(0, 1)

activity = activities[0]

distance = activity["distance"]
duration = activity["duration"]
avg_hr = activity.get("averageHR", "unknown")

summary = f"""
Distance: {distance} meters
Duration: {duration} seconds
Average HR: {avg_hr}
"""

# 初始化 Gemini
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-1.5-flash")

prompt = f"""
You are a professional running coach.

Here is my latest running data:

{summary}

Give a short training suggestion.
"""

response = model.generate_content(prompt)

print(response.text)
