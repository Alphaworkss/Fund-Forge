print("=" * 50)
print("ECONOMIC EVENT PIPELINE STARTED")
print("=" * 50)

print("Running FOMC Validation...")

from validation.validate_data import validate_dataset

validate_dataset()

print("=" * 50)
print("PIPELINE COMPLETED SUCCESSFULLY")
print("=" * 50)