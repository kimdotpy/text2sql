from typing import List, Dict, Any
from sqlalchemy import text
from db import get_engine


def run_read_query(sql: str) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        rows = [dict(r._mapping) for r in result]
    return rows
