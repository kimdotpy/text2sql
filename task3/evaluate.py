import time
import pandas as pd
import json
import os
from executor import run_pipeline
from database import execute_query

def compare_results(expected, generated):
    if expected == generated:
        return True
    
    # Try more lenient comparison (ignoring row order)
    if not isinstance(expected, list) or not isinstance(generated, list):
        return False
        
    if len(expected) != len(generated):
        return False
        
    # Convert lists of dicts to sets of tuples of values to ignore column name differences
    try:
        def hashable_values(rows):
            # Compare just the raw values in the order they were selected
            return set(tuple(row.values()) for row in rows)
            
        if hashable_values(expected) == hashable_values(generated):
            return True
            
        # Fallback: if columns were selected in a different order, sort the values as strings
        def hashable_sorted_values(rows):
            return set(tuple(sorted(str(v) for v in row.values())) for row in rows)
            
        return hashable_sorted_values(expected) == hashable_sorted_values(generated)
        
    except Exception:
        return False

def run_evaluation():
    csv_path = os.path.join(os.path.dirname(__file__), "data", "sql_qa.csv")
    if not os.path.exists(csv_path):
        print(f"Dataset not found at {csv_path}")
        return
        
    # Manually parse the CSV to handle unquoted commas in the SQL queries
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        headers = lines[0].strip().split(',')
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            # Split by first comma
            parts = line.split(',', 1)
            if len(parts) == 2:
                q = parts[0].strip()
                sql = parts[1].strip()
                # Remove surrounding quotes if they exist
                if sql.startswith('"') and sql.endswith('"'):
                    sql = sql[1:-1]
                rows.append({"question": q, "sql_query": sql})
                
    df = pd.DataFrame(rows)
    
    print("-" * 150)
    print(f"{'Question':<45} | {'Generated SQL (Truncated)':<35} | {'Executed':<8} | {'Correct':<8} | {'Retry':<5} | {'Status':<15}")
    print("-" * 150)
    
    total_queries = len(df)
    success_count = 0
    correct_count = 0
    retry_success_count = 0
    failed_count = 0
    total_latency = 0.0
    
    log_file = os.path.join(os.path.dirname(__file__), "logs", "query_logs.json")
    
    # Store detailed results
    eval_results = []
    queries_tested = 0
    
    eval_report_path = os.path.join(os.path.dirname(__file__), "data", "evaluation.csv")
    os.makedirs(os.path.dirname(eval_report_path), exist_ok=True)
    
    try:
        for index, row in df.iterrows():
            question = row['question']
            expected_sql = row['sql_query']
            
            # 1. Get expected result
            expected_result = None
            expected_executed = False
            try:
                expected_result = execute_query(expected_sql)
                expected_executed = True
            except Exception as e:
                pass
                
            # 2. Run pipeline and measure latency
            start_time = time.time()
            result = run_pipeline(question)
            latency = time.time() - start_time
            total_latency += latency
            
            # 3. Read log for retry info
            retry_needed = False
            execution_status = "failed"
            
            if os.path.exists(log_file):
                 with open(log_file, "r") as f:
                     try:
                         logs = json.load(f)
                         last_log = logs[-1]
                         retry_needed = last_log.get("retry_needed", False)
                         execution_status = last_log.get("execution_status", "failed")
                     except:
                         pass
                         
            executed_successfully = (execution_status == "success")
            
            # 4. Check correctness
            is_correct = False
            if executed_successfully and expected_executed:
                generated_result = result.get('result', [])
                is_correct = compare_results(expected_result, generated_result)
                if is_correct:
                    correct_count += 1
                    
            # 5. Update metrics
            if executed_successfully:
                if retry_needed:
                    retry_success_count += 1
                else:
                    success_count += 1
            else:
                failed_count += 1
                
            final_status = "Success" if executed_successfully else "Failed"
            if executed_successfully and not is_correct:
                 final_status = "Wrong Result"
                 
            gen_sql_str = result.get('sql', 'N/A')
            trunc_sql = (gen_sql_str[:32] + '...') if len(gen_sql_str) > 35 else gen_sql_str
                 
            print(f"{question:<45} | {trunc_sql:<35} | {'Yes' if executed_successfully else 'No':<8} | {'Yes' if is_correct else 'No':<8} | {'Yes' if retry_needed else 'No':<5} | {final_status:<15}")
            
            eval_results.append({
                "Question": question,
                "Expected SQL": expected_sql,
                "Generated SQL": gen_sql_str,
                "Executed Successfully": "Yes" if executed_successfully else "No",
                "Correct Result": "Yes" if is_correct else "No",
                "Retry Needed": "Yes" if retry_needed else "No",
                "Final Status": final_status,
                "Latency (s)": round(latency, 2)
            })
            queries_tested += 1
            
            # Save evaluation report incrementally
            eval_df = pd.DataFrame(eval_results)
            eval_df.to_csv(eval_report_path, index=False)
            
    except KeyboardInterrupt:
        print("\n[!] Evaluation interrupted by user. Saving partial results...")

    print("-" * 150)
    
    if queries_tested == 0:
        print("No queries were tested.")
        return
        
    print(f"\nDetailed evaluation report saved to {eval_report_path}")
        
    print("\n=== FINAL EVALUATION METRICS ===")
    print(f"Total Queries Tested: {queries_tested} out of {total_queries}")
    total_success = success_count + retry_success_count
    print(f"SQL Execution Success Rate: {(total_success / queries_tested) * 100:.2f}% ({total_success}/{queries_tested})")
    print(f"Query Result Accuracy: {(correct_count / queries_tested) * 100:.2f}% ({correct_count}/{queries_tested})")
    print(f"Retry/Self-Correction Success Rate: {(retry_success_count / queries_tested) * 100:.2f}% ({retry_success_count}/{queries_tested})")
    print(f"Total Failed Queries: {failed_count}")
    print(f"Average Query Generation Latency: {total_latency / queries_tested:.2f} seconds")

if __name__ == "__main__":
    run_evaluation()