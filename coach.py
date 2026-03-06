import os
import json
import requests
import datetime
import pandas as pd
from garminconnect import Garmin

PROFILE_FILE = "data/athlete_profile.json"

EMAIL = os.environ["GARMIN_EMAIL"]
PASSWORD = os.environ["GARMIN_PASSWORD"]
DEEPSEEK_KEY = os.environ["DEEPSEEK_API_KEY"]
FEISHU_WEBHOOK = os.environ["FEISHU_WEBHOOK"]

# =====================
# 登录（中国区）
# =====================

def login():
    client = Garmin(EMAIL, PASSWORD, is_cn=True)
    client.login()
    return client

# =====================
# 数据获取
# =====================

def get_runs(client, limit=200):
    return client.get_activities(0, limit)

def get_health(client):
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    return client.get_stats(yesterday)

# =====================
# 画像管理
# =====================

def load_profile():
    if not os.path.exists(PROFILE_FILE):
        return None
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_profile(profile):
    os.makedirs("data", exist_ok=True)
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

# =====================
# AI调用
# =====================

def ai(prompt):
    url = "https://api.deepseek.com/chat/completions"

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是专业马拉松教练"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.6
    }

    r = requests.post(url, headers=headers, json=data)
    result = r.json()

    if "choices" not in result:
        return f"API错误: {result}"

    return result["choices"][0]["message"]["content"]

# =====================
# 构建结构化画像
# =====================

def build_profile(runs, client):

    distances = []
    hrs = []
    cadences = []
    paces = []

    for r in runs[:100]:
        detail = client.get_activity(r["activityId"])

        if detail.get("distance"):
            distances.append(detail["distance"] / 1000)

        if detail.get("averageHR"):
            hrs.append(detail["averageHR"])

        if detail.get("averageRunCadence"):
            cadences.append(detail["averageRunCadence"])

        if detail.get("duration") and detail.get("distance"):
            pace = (detail["duration"] / 60) / (detail["distance"] / 1000)
            paces.append(pace)

    profile = {
        "baseline": {
            "avg_distance": float(pd.Series(distances).mean()),
            "avg_hr": float(pd.Series(hrs).mean()),
            "avg_cadence": float(pd.Series(cadences).mean()),
            "avg_pace": float(pd.Series(paces).mean())
        }
    }

    return profile

# =====================
# 飞书卡片
# =====================

def push(title, content):

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": content}
                }
            ]
        }
    }

    requests.post(FEISHU_WEBHOOK, json=card)

# =====================
# 主流程
# =====================

client = login()

profile = load_profile()

# 第一次建立画像
if profile is None:
    runs = get_runs(client, 200)
    profile = build_profile(runs, client)
    save_profile(profile)

# 健康数据
health = get_health(client)

health_report = f"""
## 🟢 昨日健康状态

- 静息心率：{health.get('restingHeartRate')}
- 压力指数：{health.get('stressLevel')}
- 睡眠时长：{health.get('sleepDuration')}
"""

# 最新训练
latest = get_runs(client, 1)[0]
detail = client.get_activity(latest["activityId"])

prompt = f"""
已有运动员基线：
{profile}

今日训练数据：
{json.dumps(detail, ensure_ascii=False)}

请做基于基线的对比分析。
"""

run_analysis = ai(prompt)

run_report = f"""
## 🏃 昨日训练分析

{run_analysis}
"""

push("AI教练日报 - 健康", health_report)
push("AI教练日报 - 训练", run_report)

print("完成")
