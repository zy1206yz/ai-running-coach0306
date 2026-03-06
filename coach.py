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
# 基础信息
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

def get_runs(client, limit=200):
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
# 训练负荷 + FIS
# =========================

def calculate_load(runs, client):

    loads = []

    for r in runs[:30]:
        detail = client.get_activity(r["activityId"])

        if not detail.get("distance") or not detail.get("duration"):
            continue

        load = (detail["distance"]/1000) * (detail.get("averageHR") or 0)
        loads.append(load)

    if len(loads) < 7:
        return None

    loads = np.array(loads)

    acute = np.mean(loads[:7])
    chronic = np.mean(loads)

    if chronic == 0:
        acwr = 0
    else:
        acwr = acute / chronic

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

    cadence = detail.get("averageRunCadence") or 0
    vert_ratio = detail.get("verticalRatio") or 0
    gct = detail.get("avgGroundContactTime") or 999

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
# 马拉松预测
# =========================

def predict_marathon(pace):

    if not pace or pace <= 0:
        return None

    return pace * (42.195 ** 1.06)

# =========================
# AI 调用
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
        return f"AI错误: {res}"

    return res["choices"][0]["message"]["content"]

# =========================
# 主流程
# =========================

client = login()

profile = load_profile()

# 第一次建立画像
if profile is None:
    runs = get_runs(client, 500)

    profile = {
        "basic_info": BASE_INFO,
        "created_at": str(datetime.date.today())
    }

    save_profile(profile)

# 健康数据
health = get_health(client)

health_report = f"""
## 🟢 昨日健康状态
- 静息心率: {health.get('restingHeartRate') or '无数据'}
- 压力指数: {health.get('stressLevel') or '无数据'}
- 睡眠: {health.get('sleepDuration') or '无数据'}
"""

# 最新训练
latest = get_runs(client,1)[0]
detail = client.get_activity(latest["activityId"])

# 跑姿
posture = posture_score(detail)

# 配速计算（安全）
marathon_text = "预测全马时间: 数据不足"

if detail.get("duration") and detail.get("distance"):
    pace = (detail["duration"]/60)/(detail["distance"]/1000)
    marathon_time = predict_marathon(pace)
    if marathon_time:
        marathon_text = f"预测全马时间: {marathon_time:.1f} 分钟"

# 负荷
load = calculate_load(get_runs(client,30), client)

if load:
    acwr = load["acwr"]
    if acwr > 1.5:
        load_status = "⚠️ 高疲劳风险"
    elif acwr < 0.8:
        load_status = "恢复期/训练不足"
    else:
        load_status = "训练负荷正常"

    load_text = f"""
## 📊 训练负荷
- ACWR: {acwr:.2f}
- 状态: {load_status}
"""
else:
    load_text = ""

# AI分析
prompt = f"""
基于运动员画像:
{profile}

分析今日训练数据:
{json.dumps(detail, ensure_ascii=False)}
"""

analysis = ai(prompt)

run_report = f"""
## 🏃 昨日训练分析

跑姿评分: {posture}/100

{marathon_text}

{load_text}

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
