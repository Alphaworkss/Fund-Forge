import pandas as pd

FILE = "predictions/MUFAP/MUFAP_NAV_PREDICTIONS.csv"

df = pd.read_csv(FILE)

targets = [
    "15D",
    "30D",
    "90D",
    "180D",
    "270D",
    "365D",
    "730D",
    "1095D"
]

print()
print("Prediction change ranges:")
print("-" * 70)

for h in targets:

    column = f"Change_NAV_{h}_Percent"

    print(
        f"{h:>5}: "
        f"min={df[column].min():.2f}% | "
        f"max={df[column].max():.2f}% | "
        f"avg={df[column].mean():.2f}%"
    )

print()