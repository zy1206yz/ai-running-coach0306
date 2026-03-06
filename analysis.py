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
            {"role": "system",
             "content": "你是一名专业马拉松教练，擅长通过跑步数据分析运动员状态"},
            {"role": "user", "content": prompt}
        ]
    }

    r = requests.post(url, headers=headers, json=data)
    return r.json()["choices"][0]["message"]["content"]


def build_long_term_profile(runs):

    prompt = f"""
    以下是一个跑者过去所有跑步数据：

    {json.dumps(runs, ensure_ascii=False)}

    请分析：

    1 该跑者真实水平
    2 配速能力
    3 心率区间能力
    4 跑步经济性
    5 长期训练结构
    6 可能的马拉松成绩
    """

    return ai_analysis(prompt)


def analyze_single_run(detail):

    prompt = f"""
    以下是一次跑步的完整数据：

    {json.dumps(detail, ensure_ascii=False)}

    请重点分析：

    1 每公里配速变化趋势
    2 心率变化趋势
    3 步频步幅变化
    4 心率与步频步幅的关联
    5 跑姿稳定性
    6 垂直振幅和触地时间
    7 是否出现体能崩溃点
    8 给出专业训练建议

    输出为中文详细分析。
    """

    return ai_analysis(prompt)
