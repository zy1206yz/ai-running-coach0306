import os
import json
import requests
import datetime
from garminconnect import Garmin

# =========================
# 基础配置
# =========================

PROFILE_FILE = "data/athlete_profile.json"

EMAIL = os.environ["GARMIN_EMAIL"]
PASSWORD = os.environ["GARMIN_PASSWORD"]
DEEPSEEK_KEY = os.environ["DEEPSEEK_API_KEY"]
FEISHU_WEBHOOK = os.environ["FEISHU_WEBHOOK"]

# =========================
# Garmin 登录（中国区）
# =========================

def login():
    client = Garmin(EMAIL, PASSWORD, is_cn=True)
    client.login()
    return client

# =========================
# 获取数据
# =========================

def get_runs(client, limit=50):
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
# DeepSeek调用
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
            {"role": "system", "content": "你是专业马拉松教练"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    r = requests.post(url, headers=headers, json=data)
    result = r.json()

    if "choices" not in result:
        return f"AI错误: {result}"

    return result["choices"][0]["message"]["content"]

# =========================
# 飞书卡片推送
# =========================

def push_to_feishu(title, content):

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
                    "text": {
                        "tag": "lark_md",
                        "content": content
                    }
                }
            ]
        }
    }

    requests.post(FEISHU_WEBHOOK, json=card)

# =========================
# 主逻辑
# =========================

client = login()

# 1️⃣ 长期画像（如果不存在）
profile = load_profile()

if profile is None:
    runs = get_runs(client, 200)

    prompt = f"根据以下历史跑步数据建立运动员长期能力画像：{json.dumps(runs[:100], ensure_ascii=False)}"

    profile = {"summary": ai(prompt)}
    save_profile(profile)

# 2️⃣ 每日健康
health = get_health(client)

health_report = f"""
🟢 昨日健康状态

静息心率：{health.get('restingHeartRate')}
压力指数：{health.get('stressLevel')}
睡眠时长：{health.get('sleepDuration')}
"""

# 3️⃣ 最近一次训练
latest = get_runs(client, 1)[0]
activity_id = latest["activityId"]

detail = client.get_activity(activity_id)

prompt_run = f"""
基于已有运动员画像：
{profile}

分析以下训练数据：
{json.dumps(detail, ensure_ascii=False)}
"""

run_analysis = ai(prompt_run)

# 4️⃣ 推送
push_to_feishu("AI教练日报 - 健康", health_report)
push_to_feishu("AI教练日报 - 训练", run_analysis)

print("完成")
