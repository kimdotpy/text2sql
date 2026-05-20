import os
import json
import requests
from dotenv import load_dotenv, find_dotenv
from prompts.templates import DECOMPOSITION_PROMPT, GENERATION_PROMPT, FIX_PROMPT, SCHEMA_CONTEXT

load_dotenv(find_dotenv())

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def call_llm(prompt: str, is_json: bool = False) -> str:
    """Helper to call OpenRouter API."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    }
    
    if is_json:
        data["response_format"] = {"type": "json_object"}
        
    response = requests.post(OPENROUTER_URL, headers=headers, json=data)
    if not response.ok:
        raise Exception(f"API Error {response.status_code}: {response.text}")
        
    result = response.json()
    if "choices" not in result or len(result["choices"]) == 0:
        raise Exception(f"Unexpected response from OpenRouter: {json.dumps(result)}")
        
    content = result["choices"][0]["message"].get("content")
    if content is None:
        raise Exception(f"Unexpected response from OpenRouter (Content is None): {json.dumps(result)}")
        
    return content.strip()

import re

def decompose_query(question: str) -> dict:
    """Call LLM to decompose question into JSON structure."""
    prompt = DECOMPOSITION_PROMPT.format(question=question)
    response_str = call_llm(prompt, is_json=True)
    
    # Strip potential markdown blocks
    clean_str = response_str.strip()
    if clean_str.startswith("```json"): clean_str = clean_str[7:]
    elif clean_str.startswith("```"): clean_str = clean_str[3:]
    if clean_str.endswith("```"): clean_str = clean_str[:-3]
    clean_str = clean_str.strip()
    
    try:
        return json.loads(clean_str)
    except json.JSONDecodeError:
        # Fallback: try to extract JSON object using regex
        match = re.search(r'\{.*\}', response_str, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        print("Failed to decode JSON from LLM:", response_str)
        return {"error": "Failed to decode JSON"}

def generate_sql(question: str, decomposition: dict) -> str:
    """Call LLM to generate SQL based on decomposition."""
    prompt = GENERATION_PROMPT.format(
        schema=SCHEMA_CONTEXT,
        decomposition=json.dumps(decomposition, indent=2),
        question=question
    )
    return call_llm(prompt)

def fix_sql(failed_query: str, error_message: str) -> str:
    """Call LLM to fix a failed SQL query."""
    prompt = FIX_PROMPT.format(
        schema=SCHEMA_CONTEXT,
        failed_query=failed_query,
        error_message=error_message
    )
    return call_llm(prompt)
