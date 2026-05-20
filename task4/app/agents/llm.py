import os
from typing import List, Dict, Any
from openai import OpenAI
from prompts import PROMPTS


class LLM:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = os.getenv("OPENROUTER_MODEL", model)
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.0) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=1200,
        )
        # new OpenAI Python API may return message as a mapping or an object
        message = resp.choices[0].message
        try:
            return message["content"]
        except Exception:
            return getattr(message, "content", "")

    def generate_plan(self, user_query: str, schema: str) -> str:
        messages = [
            {"role": "system", "content": PROMPTS["planner_system"]},
            {"role": "user", "content": f"Schema:\n{schema}\n\nUser Query:\n{user_query}"},
        ]
        return self.chat(messages, temperature=0.0)

    def generate_sql(self, plan: str, schema: str) -> str:
        messages = [
            {"role": "system", "content": PROMPTS["generator_system"]},
            {"role": "user", "content": f"Schema:\n{schema}\n\nPlan:\n{plan}"},
        ]
        return self.chat(messages, temperature=0.0)

    def summarize(self, user_query: str, results: list) -> str:
        messages = [
            {"role": "system", "content": PROMPTS["summarizer_system"]},
            {"role": "user", "content": f"User Query:\n{user_query}\n\nResults:\n{results}"},
        ]
        return self.chat(messages, temperature=0.0)
