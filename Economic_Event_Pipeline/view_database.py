import sqlite3
import pandas as pd

conn = sqlite3.connect(
    "data/database/economic_events.db"
)

df = pd.read_sql_query(
    "SELECT * FROM economic_events",
    conn
)

print(df)

conn.close()