import time
from main import main

print("=" * 50)
print("FundForge Scheduler Started")
print("=" * 50)

while True:

    print("\nRunning scraper...")

    try:
        main()

    except Exception as e:
        print("ERROR:", e)

    print("\nSleeping for 1 hour...")

    time.sleep(3600)