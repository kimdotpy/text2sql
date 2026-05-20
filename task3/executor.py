import json
import os
from datetime import datetime
from sql_generator import decompose_query, generate_sql, fix_sql
from validator import validate_sql
from database import execute_query

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOG_DIR, "query_logs.json")

def _log_execution(log_entry: dict):
    """Appends execution details to logs/query_logs.json"""
    os.makedirs(LOG_DIR, exist_ok=True)
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            logs = []
            
    logs.append(log_entry)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2, default=str)

def run_pipeline(question: str) -> dict:
    """
    Orchestrates the Prompt Chaining Pipeline:
    1. Decompose -> 2. Generate -> 3. Validate -> 4. Execute -> 5. Retry (if fail)
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "decomposition": None,
        "generated_sql": None,
        "retry_needed": False,
        "fixed_sql": None,
        "execution_status": "failed",
        "error": None,
        "result": []
    }
    
    result = {
        "question": question,
        "sql": "",
        "result": [],
        "status": "failed"
    }

    try:
        # Step 1: Decompose
        decomposition = decompose_query(question)
        log_entry["decomposition"] = decomposition
        
        # Step 2: Generate
        sql = generate_sql(question, decomposition)
        # Strip potential markdown blocks if LLM failed instructions
        if sql.startswith("```sql"): sql = sql[6:]
        if sql.startswith("```"): sql = sql[3:]
        if sql.endswith("```"): sql = sql[:-3]
        sql = sql.strip()
        
        log_entry["generated_sql"] = sql
        
        # Step 3: Validate
        validate_sql(sql)
        
        # Step 4: Execute
        try:
            db_result = execute_query(sql)
            log_entry["execution_status"] = "success"
            log_entry["result"] = db_result
            
            result["sql"] = sql
            result["result"] = db_result
            result["status"] = "success"
            
        except Exception as e:
            error_msg = str(e)
            log_entry["retry_needed"] = True
            log_entry["error"] = error_msg
            
            # Step 5: Retry / Fix
            fixed_sql = fix_sql(sql, error_msg)
            # Strip markdown again
            if fixed_sql.startswith("```sql"): fixed_sql = fixed_sql[6:]
            if fixed_sql.startswith("```"): fixed_sql = fixed_sql[3:]
            if fixed_sql.endswith("```"): fixed_sql = fixed_sql[:-3]
            fixed_sql = fixed_sql.strip()
            
            log_entry["fixed_sql"] = fixed_sql
            
            # Validate fixed SQL
            validate_sql(fixed_sql)
            
            # Execute fixed SQL
            try:
                db_result = execute_query(fixed_sql)
                log_entry["execution_status"] = "success"
                log_entry["result"] = db_result
                log_entry["error"] = None # Clear error on success
                
                result["sql"] = fixed_sql
                result["result"] = db_result
                result["status"] = "success"
                
            except Exception as retry_e:
                log_entry["execution_status"] = "failed"
                log_entry["error"] = str(retry_e)
                result["status"] = "failed"
                result["sql"] = fixed_sql
                result["error"] = str(retry_e)

    except Exception as pipe_error:
        log_entry["execution_status"] = "failed"
        log_entry["error"] = str(pipe_error)
        result["status"] = "failed"
        result["error"] = str(pipe_error)
        
    finally:
        _log_execution(log_entry)
        
    return result
