import os
from datetime import datetime, timedelta

from garminconnect import Garmin
from google import genai


# ------------------------
# 1 读取环境变量
# ------------------------

EMAIL = os.environ["GARMIN_EMAIL"]
PASSWORD = os.environ["GARMIN_PASSWORD"]
API_KEY = os.environ["GEMINI_API_KEY"]


# ------------------------
# 2 登录 Garmin
# ------------------------

print("Connecting Garmin...")

client = Garmin(EMAIL, PASSWORD)
client.login()

today = datetime.now().date()
yesterday = today - timedelta(days=1)


# ------------------------
# 3 获取健康数据
# ------------------------

print("Fetching health data...")

stats = client.get_stats(str(today))

resting_hr = stats.get("restingHeartRate")
steps = stats.get("totalSteps")
calories = stats.get("totalKilocalories")


# ------------------------
# 4 获取 Body Battery
# ------------------------

try:
    body = client.get_body_battery(str(today), str(today))
    body_battery = body["bodyBatteryValues"][-1]["bodyBattery"]
except:
    body_battery = "unknown"


# ------------------------
# 5 获取睡眠
# ------------------------

try:
    sleep = client.get_sleep_data(str(yesterday))
    sleep_score = sleep.get("sleepScore")
    sleep_time = sleep.get("sleepTimeSeconds")
except:
    sleep_score = "unknown"
    sleep_time = "unknown"


# ------------------------
# 6 获取最近一次活动
# ------------------------

print("Fetching last activity...")

activities = client.get_activities(0, 1)

if activities:
    act = activities[0]

    activity_type = act["activityType"]["typeKey"]
    distance = act.get("distance", 0) / 1000
    duration = act.get("duration", 0) / 60
    avg_hr = act.get("averageHR")
    avg_pace = act.get("averageSpeed")

else:
    activity_type = "none"
    distance = 0
    duration = 0
    avg_hr = "unknown"
    avg_pace = "unknown"


# ------------------------
# 7 构建 AI Prompt
# ------------------------

prompt = f"""
You are a professional marathon coach.

Analyze the athlete's daily health data and latest training.

Health data today:
Resting HR: {resting_hr}
Steps: {steps}
Calories: {calories}
Body Battery: {body_battery}

Sleep:
Sleep score: {sleep_score}
Sleep seconds: {sleep_time}

Latest activity:
Type: {activity_type}
Distance km: {distance:.2f}
Duration minutes: {duration:.1f}
Average HR: {avg_hr}

Please provide:

1. Recovery status today
2. Quality of the latest run
3. Potential fatigue risk
4. Training recommendation
5. Estimated fitness trend
"""


# ------------------------
# 8 调用 Gemini
# ------------------------

print("Calling AI coach...")

ai = genai.Client(api_key=API_KEY)

response = ai.models.generate_content(
    model="gemini-2.0-flash",
    contents=prompt
)

report = response.text


# ------------------------
# 9 输出报告
# ------------------------

print("\n========== AI RUNNING COACH ==========\n")

print(report)

print("\n======================================")
