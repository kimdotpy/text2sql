from .llm import LLM


class Summarizer:
    def __init__(self, llm: LLM):
        self.llm = llm

    def summarize(self, user_query: str, results: list) -> str:
        return self.llm.summarize(user_query=user_query, results=results)
