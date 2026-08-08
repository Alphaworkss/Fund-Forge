import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.blocking import BlockingScheduler
from main import run_pipeline

sched = BlockingScheduler()
sched.add_job(run_pipeline, "cron", hour=6)

if __name__ == "__main__":
    print("Scheduler started — pipeline will run daily at 06:00. Ctrl+C to stop.")
    sched.start()
