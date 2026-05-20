from typing import List, Dict, Any
from tools.db_tools import run_read_query


class Executor:
    def __init__(self):
        pass

    def execute(self, sql: str) -> List[Dict[str, Any]]:
        return run_read_query(sql)
