import os
import requests
from datetime import datetime

# DeepSeek API Key
API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# 跑步数据（你之后可以改成自动读取）
distance = 10
pace = "5:20"
heartrate = 150

prompt = f"""
今天跑步数据：

距离: {distance} km
配速: {pace} /km
平均心率: {heartrate}

请像专业跑步教练一样分析：
1. 今天训练强度
2. 是否有提升
3. 下一次训练建议
"""

url = "https://api.deepseek.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "deepseek-chat",
    "messages": [
        {"role": "system", "content": "You are a professional running coach."},
        {"role": "user", "content": prompt}
    ]
}

response = requests.post(url, headers=headers, json=data)
result = response.json()

analysis = result["choices"][0]["message"]["content"]

print("AI Running Coach")
print("----------------")
print(analysis)

# 保存到文件（GitHub Actions 可以存日志）
with open("result.txt", "w") as f:
    f.write(analysis)
