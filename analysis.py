import requests
import os
import json

API_KEY = os.environ["DEEPSEEK_API_KEY"]

def ai_analysis(prompt):

    url = "https://api.deepseek.com/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "你是一名专业马拉松教练，擅长分析跑步数据、训练负荷和运动表现。你的回答必须专业、具体、中文输出。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7
    }

    r = requests.post(url, headers=headers, json=data)

    try:
        result = r.json()
    except Exception:
        return f"AI接口返回异常：{r.text}"

    # 如果API报错
    if "error" in result:
        return f"DeepSeek API错误：{result['error']}"

    # 正常结果
    if "choices" in result:
        return result["choices"][0]["message"]["content"]

    # 其他未知情况
    return f"未知返回：{result}"


def build_long_term_profile(runs):

    prompt = f"""
以下是一个跑者过去的跑步活动数据：

{json.dumps(runs[:50], ensure_ascii=False)}

请分析：

1 该跑者整体水平
2 有氧能力
3 配速区间能力
4 心率控制能力
5 跑步经济性
6 训练结构是否合理
7 预测10km、半马、全马成绩

要求：
分析要专业、具体、像真正教练写的。
"""

    return ai_analysis(prompt)


def analyze_single_run(detail):

    prompt = f"""
以下是一场跑步训练完整数据：

{json.dumps(detail, ensure_ascii=False)}

请从专业教练角度分析：

1 每公里配速变化趋势
2 心率变化趋势
3 是否存在体能衰减
4 步频步幅是否合理
5 心率与配速关系
6 跑姿稳定性
7 垂直振幅与触地时间
8 给出训练建议

输出为详细中文报告。
"""

    return ai_analysis(prompt)
