import csv
import json
import os
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-oss-120b:free"

INPUT_FILE = "data/sql_ques.csv"
OUTPUT_FILE = "data/sql_decomposition.csv"

SYSTEM_PROMPT = """You are an expert SQL analyst. Your task is to decompose a natural language question into structured SQL components.

For each question, identify:
1. Intent: What the question is asking for (e.g., "Retrieve all records", "Count total", "Calculate average")
2. Tables: Which database table(s) are involved (use classicmodels schema: customers, products, orders, orderdetails, employees, offices, payments, productlines)
3. Columns: Which specific columns are needed (use actual column names like customerNumber, productName, buyPrice, etc.)
4. Filters: Any WHERE clause conditions (write "None" if no filters)
5. Joins: Any JOIN operations needed (specify table1.column = table2.column format, or "None" if no joins)

Respond ONLY in this exact JSON format with no extra text:
{"intent": "...", "tables": "...", "columns": "...", "filters": "...", "joins": "..."}
"""


def call_openrouter(question):
    """Send a question to the OpenRouter API and get decomposition."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Decompose this question: {question}"},
        ],
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return parse_response(content)
    except requests.exceptions.RequestException as e:
        print(f"  API error: {e}")
        return None
    except (KeyError, IndexError) as e:
        print(f"  Response parsing error: {e}")
        return None


def parse_response(content):
    """Parse the JSON response from the model."""
    # Strip markdown code fences if present
    cleaned = content.strip()
    if cleaned.startswith("```"):
        # Remove opening fence (```json or ```)
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
        # Remove closing fence
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
        return {
            "intent": data.get("intent", "ERROR"),
            "tables": data.get("tables", "ERROR"),
            "columns": data.get("columns", "ERROR"),
            "filters": data.get("filters", "ERROR"),
            "joins": data.get("joins", "ERROR"),
        }
    except json.JSONDecodeError:
        print(f"  Failed to parse JSON: {cleaned[:100]}...")
        return None


def read_questions(filepath):
    """Read questions from the input CSV file."""
    questions = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append(row["question"].strip())
    return questions


def write_decompositions(filepath, results):
    """Write decomposition results to the output CSV file."""
    fieldnames = ["question", "intent", "tables", "columns", "filters", "joins"]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)


def main():
    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY not found in .env file.")
        return

    print(f"Reading questions from {INPUT_FILE}...")
    questions = read_questions(INPUT_FILE)
    print(f"Found {len(questions)} questions.\n")

    results = []

    for i, question in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] Decomposing: {question}")
        decomposition = call_openrouter(question)

        if decomposition:
            row = {"question": question, **decomposition}
            print(f"  Intent: {decomposition['intent']}")
        else:
            # Fallback to ERROR values on failure
            row = {
                "question": question,
                "intent": "ERROR",
                "tables": "ERROR",
                "columns": "ERROR",
                "filters": "ERROR",
                "joins": "ERROR",
            }
            print("  Failed — writing ERROR values.")

        results.append(row)

        # Small delay to respect rate limits on free tier
        if i < len(questions):
            time.sleep(1)

    write_decompositions(OUTPUT_FILE, results)
    print(f"\nDone! Decompositions saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
