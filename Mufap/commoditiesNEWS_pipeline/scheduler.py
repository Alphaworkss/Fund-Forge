import schedule
import time
from main import main


def run_pipeline():
    print("\nRunning scheduled pipeline...\n")
    main()


schedule.every().day.at("09:00").do(run_pipeline)

print("Scheduler started...")
print("Waiting for scheduled time...")

while True:
    schedule.run_pending()
    time.sleep(60)