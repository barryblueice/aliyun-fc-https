import json
import subprocess
from datetime import datetime, timedelta
import time
import schedule
import sys
import pyfiglet
from loguru import logger
from update import updating_main_process

# This python script needs superuser(root) permission to run!

ascii_art = pyfiglet.figlet_format("Aliyun FC HTTPS")

def get_expired_date():
    try:
        with open("db.json", "r") as file:
            data = json.load(file)
            expired_date_str = data.get("expired-date")
            if expired_date_str:
                expired_date = datetime.fromisoformat(expired_date_str)
                return expired_date
            else:
                logger.error("expired-date not found in db.json")
                sys.exit(e)
    except FileNotFoundError as e:
        logger.error("db.json file not found")
        sys.exit(e)
    except json.JSONDecodeError as e:
        logger.error("Error decoding JSON from db.json")
        sys.exit(e)

def calculate_future_date(expired_date):
    future_date = expired_date - timedelta(days=1)
    return future_date

def schedule_next_run(future_date):
    def job():
        updating_main_process()

    schedule_time = future_date.strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Next update will be scheduled at: {schedule_time}")

    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    
    updating_main_process()

    expired_date = get_expired_date()
    if expired_date:
        future_date = calculate_future_date(expired_date)
        schedule_next_run(future_date)

if __name__ == "__main__":
    logger.info("Project: https://github.com/barryblueice/aliyun-fc-https")
    logger.info("Powered by barryblueice.")
    logger.info(f'''

{ascii_art}
''')
    time.sleep(1)
    main()
