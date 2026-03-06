import os
import json
import requests
import datetime
import numpy as np
import pandas as pd
from garminconnect import Garmin

PROFILE_FILE = "data/athlete_profile.json"

EMAIL = os.environ["GARMIN_EMAIL"]
PASSWORD = os.environ["GARMIN_PASSWORD"]
DEEPSEEK_KEY = os.environ["DEEPSEEK_API_KEY"]
FEISHU_WEBHOOK = os.environ["FEISHU_WEBHOOK"]

# =========================
# 基础运动员信息
# =========================

BASE_INFO = {
    "height_cm": 178,
    "weight_kg": 70,
    "max_hr": 188,
    "resting_hr": 45
}

# =========================
# 登录（中国区）
# =========================

def login():
    client = Garmin(EMAIL, PASSWORD, is_cn=True)
    client.login()
    return client

# =========================
# 数据获取
# =========================

def get_runs(client, limit=1000):
    return client.get_activities(0, limit)

def get_health(client):
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    return client.get_stats(yesterday)

# =========================
# 画像管理
# =========================

def load_profile():
    if not os.path.exists(PROFILE_FILE):
        return None
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_profile(profile):
    os.makedirs("data", exist_ok=True)
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

# =========================
# 训练负荷
# =========================

def calculate_load(runs, client):
    loads = []

    for r in runs[:30]:
        detail = client.get_activity(r["activityId"])
        if detail.get("distance") and detail.get("duration"):
            load = (detail["distance"]/1000) * (detail.get("averageHR",0))
            loads.append(load)

    if len(loads) < 7:
        return None

    acute = np.mean(loads[:7])
    chronic = np.mean(loads)
    acwr = acute / chronic if chronic else 0

    return {
        "acute": float(acute),
        "chronic": float(chronic),
        "acwr": float(acwr)
    }

# =========================
# 跑姿评分
# =========================

def posture_score(detail):
    score = 0

    cadence = detail.get("averageRunCadence",0)
    vert_ratio = detail.get("verticalRatio",0)
    gct = detail.get("avgGroundContactTime",999)

    if 170 <= cadence <= 190:
        score += 25
    if vert_ratio and vert_ratio < 8:
        score += 25
    if gct and gct < 260:
        score += 25
    if cadence > 0:
        score += 25

    return score

# =========================
# 成绩预测（Riegel）
# =========================

def predict_marathon(pace_min_per_km):
    return pace_min_per_km * (42.195 ** 1.06)

# =========================
# AI调用
# =========================

def ai(prompt):
    url = "https://api.deepseek.com/chat/completions"

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role":"system","content":"你是专业马拉松教练"},
            {"role":"user","content":prompt}
        ],
        "temperature":0.6
    }

    r = requests.post(url, headers=headers, json=data)
    res = r.json()

    if "choices" not in res:
        return f"API错误: {res}"

    return res["choices"][0]["message"]["content"]

# =========================
# 主流程
# =========================

client = login()

profile = load_profile()

# 第一次建立完整画像
if profile is None:
    runs = get_runs(client, 1000)

    profile = {
        "basic_info": BASE_INFO,
        "created_at": str(datetime.date.today())
    }

    save_profile(profile)

# 健康数据
health = get_health(client)

health_report = f"""
## 🟢 昨日健康状态
- 静息心率: {health.get('restingHeartRate')}
- 压力指数: {health.get('stressLevel')}
- 睡眠: {health.get('sleepDuration')}
"""

# 最新训练
latest = get_runs(client,1)[0]
detail = client.get_activity(latest["activityId"])

# 跑姿评分
posture = posture_score(detail)

# 预测成绩
if detail.get("duration") and detail.get("distance"):
    pace = (detail["duration"]/60)/(detail["distance"]/1000)
    marathon_time = predict_marathon(pace)
else:
    marathon_time = None

prompt = f"""
基于以下运动员信息：
{profile}

分析今日训练数据：
{json.dumps(detail, ensure_ascii=False)}

要求：
- 训练负荷判断
- 疲劳状态
- 跑姿分析
- VO2max趋势推测
- 全马预测参考
"""

analysis = ai(prompt)

run_report = f"""
## 🏃 昨日训练分析

跑姿评分: {posture}/100

预测全马时间: {marathon_time:.1f} 分钟

{analysis}
"""

# 飞书卡片
card = {
    "msg_type":"interactive",
    "card":{
        "header":{
            "title":{"tag":"plain_text","content":"AI教练日报"},
            "template":"blue"
        },
        "elements":[
            {"tag":"div","text":{"tag":"lark_md","content":health_report}},
            {"tag":"div","text":{"tag":"lark_md","content":run_report}}
        ]
    }
}

requests.post(FEISHU_WEBHOOK, json=card)

print("完成")
