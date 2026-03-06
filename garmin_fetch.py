from garminconnect import Garmin
import os
import datetime

EMAIL = os.environ["GARMIN_EMAIL"]
PASSWORD = os.environ["GARMIN_PASSWORD"]

def login():
    client = Garmin(EMAIL, PASSWORD, is_cn=True)
    client.login()
    return client


def get_all_runs(days=365):
    client = login()

    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)

    activities = client.get_activities_by_date(
        start.isoformat(),
        end.isoformat()
    )

    runs = [a for a in activities if a["activityType"]["typeKey"] == "running"]

    return runs


def get_activity_detail(activity_id):
    client = login()

    summary = client.get_activity(activity_id)
    splits = client.get_activity_splits(activity_id)
    metrics = client.get_activity_hr_in_timezones(activity_id)

    return {
        "summary": summary,
        "splits": splits,
        "hr": metrics
    }


def get_health_data():
    client = login()

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    stats = client.get_stats(yesterday.isoformat())

    return stats
