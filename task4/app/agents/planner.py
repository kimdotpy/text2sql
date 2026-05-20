from typing import Any
from agents.llm import LLM
from pathlib import Path


class Planner:
    def __init__(self, llm: LLM):
        self.llm = llm
        schema = Path(__file__).parents[1] / "sql" / "seed.sql"
        self.schema_text = schema.read_text() if schema.exists() else ""

    def plan(self, user_query: str) -> str:
        """Return a short strategic plan describing which tables/joins/filters to use."""
        return self.llm.generate_plan(user_query=user_query, schema=self.schema_text)
