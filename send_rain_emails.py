import smtplib
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from numbers import Number
from os import getenv
from smtplib import SMTP_SSL
from typing import Tuple

import prefect
import requests
from prefect import Flow, Parameter, task
from prefect.schedules import CronSchedule
from prefect.tasks.control_flow.conditional import ifelse


@task
def dummy_task():
    pass


@task(max_retries=5, retry_delay=timedelta(1))
def send_email(amount: Number, length_of_time: int) -> None:
    """
    Send an email with the predicted precipiation for the next `length_of_time` hours.
    """
    # based on https://gist.github.com/scottsweb/79fc6433c3f308ce1cd5

    msg = MIMEMultipart()
    msg["From"] = "lukereding@gmail.com"
    msg["To"] = "lukereding@gmail.com"
    msg["Subject"] = "☔️"

    body = f"""
    As a heads up, there's precipitation in the forecast.

    Expected precipitation is {amount:.2f} inches in the next {length_of_time} hours.

    More info at https://forecast.weather.gov/MapClick.php?lat=38.9038&lon=-76.9823&unit=0&lg=english&FcstType=graphical.
    """

    msg.attach(MIMEText(body))

    server = SMTP_SSL("smtp.gmail.com", 465)
    server.login("lukereding@gmail.com", getenv("gmail"))
    server.sendmail("lukereding@gmail.com", "lukereding@gmail.com", msg.as_string())
    # server.quit()
    server.close()


@task(max_retries=5, retry_delay=timedelta(5))
def get_estimated_precipitation(hours: int = 18) -> Tuple[Number, int]:
    """
    Download the weather from the NOAA API and compute the estimate precipitation
    in the next 18 hours.
    """

    def mm_to_in(mm: Number) -> float:
        """Convert mm to inches."""
        return mm / 25.4

    # https://api.weather.gov/points/38.85,-77.03 suggests to use
    url = "https://api.weather.gov/gridpoints/LWX/96,68"
    res = requests.get(url)

    if res.ok:
        # get precipitation amount forcasts
        # note theat these come in four blocks of six hours
        # here, I want what's going to happen during the day, not the night, so I want the first three blocks,
        # or 18 hours
        periods = hours // 6
        total_estimated_precip = sum(
            [
                res.json()["properties"]["quantitativePrecipitation"]["values"][i][
                    "value"
                ]
                for i in range(periods)
            ]
        )
    else:
        raise Expection("Could not download weather data.")
    # the estimate precipitation is reported in mm, bot inches like we want
    return mm_to_in(total_estimated_precip), periods * 6


# create schedule for the Flow
daily_schedule = CronSchedule("0 5 * * *")

with Flow("weather_email", schedule=daily_schedule) as flow:
    result = get_estimated_precipitation()
    ifelse(result[0] < 0.05, dummy_task, send_email(result[0], result[1]))

flow.run()
