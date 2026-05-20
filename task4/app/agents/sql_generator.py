from .llm import LLM


class SQLGenerator:
    def __init__(self, llm: LLM):
        self.llm = llm

    def generate(self, plan: str, schema: str) -> str:
        """Generate strict PostgreSQL read-only SQL according to the plan and schema."""
        sql = self.llm.generate_sql(plan=plan, schema=schema)
        return sql.strip()
