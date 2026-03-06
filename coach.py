import os
import json
import requests
from datetime import date
from garminconnect import Garmin

# ======================
# 1 读取环境变量
# ======================

garmin_email = os.environ["GARMIN_EMAIL"]
garmin_password = os.environ["GARMIN_PASSWORD"]
deepseek_key = os.environ["DEEPSEEK_API_KEY"]
feishu_webhook = os.environ["FEISHU_WEBHOOK"]

# ======================
# 2 登录Garmin
# ======================

client = Garmin(garmin_email, garmin_password)
client.login()

activities = client.get_activities(0, 1)

activity = activities[0]

distance = activity["distance"] / 1000
duration = activity["duration"]
avg_hr = activity.get("averageHR", "未知")
calories = activity.get("calories", "未知")
pace = duration / distance / 60

# ======================
# 3 生成训练描述
# ======================

training_text = f"""
今天跑步数据：

距离：{distance:.2f} km
时间：{duration/60:.1f} 分钟
平均配速：{pace:.2f} min/km
平均心率：{avg_hr} bpm
消耗热量：{calories}

请像一个专业耐力运动教练一样，用中文详细分析这次训练，包括：

1 训练强度判断
2 心率与配速关系
3 当前体能水平推测
4 对恢复情况的判断
5 对下一次训练的建议
6 长期训练趋势建议

语气要自然，不要AI感。
"""

# ======================
# 4 调用DeepSeek
# ======================

headers = {
    "Authorization": f"Bearer {deepseek_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "deepseek-chat",
    "messages": [
        {"role": "system", "content": "你是一名专业跑步教练"},
        {"role": "user", "content": training_text}
    ]
}

response = requests.post(
    "https://api.deepseek.com/v1/chat/completions",
    headers=headers,
    json=payload
)

result = response.json()

analysis = result["choices"][0]["message"]["content"]

# ======================
# 5 发送到飞书
# ======================

message = f"""
🏃 AI跑步教练报告

距离：{distance:.2f} km
时间：{duration/60:.1f} 分钟
平均配速：{pace:.2f} min/km
平均心率：{avg_hr} bpm

————————

{analysis}
"""

feishu_data = {
    "msg_type": "text",
    "content": {
        "text": message
    }
}

requests.post(
    feishu_webhook,
    data=json.dumps(feishu_data),
    headers={"Content-Type": "application/json"}
)

print("报告已发送到飞书")
