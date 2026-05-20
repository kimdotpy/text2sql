import os
import sys
from fastapi import FastAPI
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(__file__))
from graph.workflow import GraphWorkflow

app = FastAPI(title="Agentic Text-to-SQL")
workflow = GraphWorkflow()


class QueryRequest(BaseModel):
    query: str


@app.post("/query")
def run_query(payload: QueryRequest):
    state = workflow.run(payload.query)
    return {
        "plan": state.plan,
        "sql": state.generated_sql,
        "valid": state.is_valid_sql,
        "results": state.execution_results,
        "answer": state.final_answer,
        "errors": state.errors,
    }
