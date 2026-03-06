import os
import requests
from garminconnect import Garmin

# =========================
# Garmin 登录
# =========================
email = os.environ["GARMIN_EMAIL"]
password = os.environ["GARMIN_PASSWORD"]

garmin = Garmin(email, password)
garmin.login()

activities = garmin.get_activities(0, 1)

if not activities:
    print("No activities found.")
    exit()

run = activities[0]

distance = run.get("distance", 0) / 1000
duration = run.get("duration", 0) / 60
avg_hr = run.get("averageHR", "N/A")

summary = f"""
Today's run data:
Distance: {distance:.2f} km
Duration: {duration:.1f} minutes
Average Heart Rate: {avg_hr}

Please analyze my running condition and give short training advice.
"""

# =========================
# DeepSeek API
# =========================

api_key = os.environ["DEEPSEEK_API_KEY"]

url = "https://api.deepseek.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "deepseek-chat",
    "messages": [
        {"role": "system", "content": "You are a professional running coach."},
        {"role": "user", "content": summary}
    ]
}

response = requests.post(url, headers=headers, json=payload)

result = response.json()

# =========================
# 防止API报错
# =========================

if "choices" not in result:
    print("DeepSeek API error:")
    print(result)
    exit()

analysis = result["choices"][0]["message"]["content"]

print("===== AI Running Coach =====")
print(analysis)
