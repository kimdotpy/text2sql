from dataclasses import dataclass, field
from typing import Any, List, Optional
from agents import LLM, Planner, SQLGenerator, Validator, Executor, Summarizer
from pathlib import Path
import time

# Optional LangGraph integration: if langgraph is installed, we can wire nodes into a graph.
try:
    import langgraph  # type: ignore
    HAS_LANGGRAPH = True
except Exception:
    HAS_LANGGRAPH = False


@dataclass
class WorkflowState:
    user_query: str
    plan: Optional[str] = None
    generated_sql: Optional[str] = None
    is_valid_sql: bool = False
    execution_results: List[dict] = field(default_factory=list)
    final_answer: Optional[str] = None
    errors: List[str] = field(default_factory=list)


class GraphWorkflow:
    def __init__(self):
        # instantiate agents
        self.llm = LLM()
        self.planner = Planner(self.llm)
        self.generator = SQLGenerator(self.llm)
        self.validator = Validator()
        self.executor = Executor()
        self.summarizer = Summarizer(self.llm)
        schema_path = Path(__file__).parents[1] / "sql" / "seed.sql"
        self.schema = schema_path.read_text() if schema_path.exists() else ""

    def run(self, user_query: str, max_retries: int = 2) -> WorkflowState:
        state = WorkflowState(user_query=user_query)

        # Planner
        try:
            state.plan = self.planner.plan(user_query)
        except Exception as e:
            state.errors.append(f"Planner error: {e}")
            return state

        # Generator -> Validator loop
        for attempt in range(max_retries + 1):
            try:
                state.generated_sql = self.generator.generate(state.plan or "", self.schema)
            except Exception as e:
                state.errors.append(f"Generator error: {e}")
                return state

            try:
                valid, msg = self.validator.validate(state.generated_sql)
                state.is_valid_sql = valid
                if not valid:
                    state.errors.append(f"Validation failed: {msg}")
                    # allow regeneration with feedback
                    state.plan = (state.plan or "") + f"\nValidation feedback: {msg}"
                    continue
                break
            except Exception as e:
                state.errors.append(f"Validator error: {e}")
                return state

        if not state.is_valid_sql:
            return state

        # Executor
        try:
            state.execution_results = self.executor.execute(state.generated_sql)
        except Exception as e:
            state.errors.append(f"Execution error: {e}")
            return state

        # Summarizer
        try:
            state.final_answer = self.summarizer.summarize(user_query, state.execution_results)
        except Exception as e:
            state.errors.append(f"Summarizer error: {e}")

        return state
