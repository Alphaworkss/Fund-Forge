"""
test_export.py — Stage 8: Testing (export_excel.py)

Run with: pytest test_export.py
"""

import pandas as pd

from common_schema import enrich
from storage import get_connection, upsert_raw, upsert_common
from export_excel import export_to_excel


def test_export_writes_raw_features_and_common_sheets(tmp_path):
    conn = get_connection(":memory:")
    record = {"keyword": "PSX", "date": "2026-07-01", "interest": 40, "is_partial": False}
    upsert_raw(conn, [record])
    upsert_common(conn, [enrich(record)])
    out_path = tmp_path / "out.xlsx"

    export_to_excel(conn, excel_path=str(out_path))

    assert out_path.exists()
    raw = pd.read_excel(out_path, sheet_name="raw")
    assert len(raw) == 1
    features = pd.read_excel(out_path, sheet_name="features")
    assert len(features) == 0
    common = pd.read_excel(out_path, sheet_name="common")
    assert len(common) == 1
    assert common.iloc[0]["id"] == "google_trends:PSX:2026-07-01"
    conn.close()
