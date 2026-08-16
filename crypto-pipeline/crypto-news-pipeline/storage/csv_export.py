"""
CSV export: read the full current DB table and write/overwrite
data/pipeline_output.csv with all schema columns. Runs automatically as
the last step of every pipeline run.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy.engine import Engine

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import CSV_PATH, SCHEMA_FIELDS  # noqa: E402
from storage.db import get_all_records, get_engine  # noqa: E402

logger = logging.getLogger(__name__)


def export_to_csv(engine: Optional[Engine] = None, csv_path: Optional[Path] = None) -> Path:
    """
    Dump the entire records table to CSV with column headers matching the
    unified schema exactly. Overwrites the file each time so the CSV is
    always a fresh snapshot of the DB.
    """
    engine = engine or get_engine()
    path = Path(csv_path or CSV_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)

    records = get_all_records(engine)
    df = pd.DataFrame(records, columns=SCHEMA_FIELDS)
    df.to_csv(path, index=False)

    logger.info("CSV export: wrote %d rows to %s", len(df), path)
    return path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    export_to_csv()
