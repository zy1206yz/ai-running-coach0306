from garmin_fetch import get_all_runs,get_activity_detail,get_health_data
from analysis import build_long_term_profile,analyze_single_run
from feishu_push import push

print("AI Running Coach starting")

runs = get_all_runs()

profile = build_long_term_profile(runs)

latest = runs[0]["activityId"]

detail = get_activity_detail(latest)

run_report = analyze_single_run(detail)

health = get_health_data()

health_text = f"""
昨日健康状态

静息心率: {health.get("restingHeartRate")}
压力: {health.get("stressLevel")}
睡眠: {health.get("sleepDuration")}
"""

message = f"""
AI跑步教练日报

——————
【健康状态】
{health_text}

——————
【长期能力画像】
{profile}

——————
【昨日训练分析】
{run_report}
"""

push(message)

print("done")
