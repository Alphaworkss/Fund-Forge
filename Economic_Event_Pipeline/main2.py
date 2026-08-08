import subprocess
from datetime import datetime


def run_script(script_path):
    print(f"\nRunning: {script_path}")

    result = subprocess.run(
        ["python", script_path],
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.stderr:
        print(result.stderr)


print("=" * 50)
print("Economic Event Pipeline")
print("Started:", datetime.now())
print("=" * 50)

# Budget
run_script("scraper/budget_scraper.py")
run_script("validation/validate_budget_data.py")

print("\nPipeline Finished")
print("Completed:", datetime.now())
run_script("scraper/earnings_scraper.py")
run_script("validation/validate_earnings_data.py")

run_script("scraper/elections_scraper.py")
run_script("validation/validate_elections_data.py")