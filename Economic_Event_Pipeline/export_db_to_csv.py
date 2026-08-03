import sqlite3
import pandas as pd

conn = sqlite3.connect(
    "data/database/economic_events.db"
)

df = pd.read_sql_query(
    "SELECT * FROM economic_events",
    conn
)

df.to_csv(
    "economic_events_export.csv",
    index=False
)

conn.close()

print("CSV exported successfully")