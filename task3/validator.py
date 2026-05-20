import re

def validate_sql(sql: str) -> bool:
    """
    Validates the SQL query to ensure it is only a SELECT statement.
    Blocks any DML operations.
    Returns True if valid, raises ValueError if invalid.
    """
    if not sql:
        raise ValueError("Empty SQL query")
        
    sql_upper = sql.upper()
    
    # Check if starts with SELECT (ignoring leading whitespace)
    if not sql.strip().upper().startswith("SELECT"):
        raise ValueError("Query must start with SELECT")
        
    # Blocklist of DML commands
    blocked_keywords = [
        "DELETE", "DROP", "UPDATE", "INSERT", "ALTER", "TRUNCATE", 
        "GRANT", "REVOKE", "EXECUTE", "CREATE", "REPLACE"
    ]
    
    # Use word boundary regex to find exact blocked keywords
    for keyword in blocked_keywords:
        if re.search(r'\b' + keyword + r'\b', sql_upper):
            raise ValueError(f"Blocked keyword detected in query: {keyword}")
            
    return True
