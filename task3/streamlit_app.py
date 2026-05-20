import streamlit as st
import pandas as pd
from executor import run_pipeline
import json
import os

st.set_page_config(page_title="Text-to-SQL Pipeline", layout="wide")

st.title("Text-to-SQL Pipeline (Prompt Chaining)")
st.markdown("A pure Python implementation of Prompt Chaining for executing natural language database queries safely.")

# Chat input
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sql" in message and message["sql"]:
            st.code(message["sql"], language="sql")
        if "data" in message and message["data"] is not None:
            if message["data"]:
                st.dataframe(pd.DataFrame(message["data"]))
            else:
                st.info("Query returned 0 rows.")

# User input
if prompt := st.chat_input("Ask a question about the classicmodels database (e.g., 'List all products')"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process question
    with st.chat_message("assistant"):
        with st.spinner("Processing pipeline..."):
            result = run_pipeline(prompt)
            
            # Check logs to see if retry was needed
            log_file = os.path.join(os.path.dirname(__file__), "logs", "query_logs.json")
            retry_needed = False
            
            if os.path.exists(log_file):
                 try:
                     with open(log_file, "r") as f:
                         logs = json.load(f)
                         last_log = logs[-1]
                         retry_needed = last_log.get("retry_needed", False)
                 except:
                     pass
                     
            status_text = "✅ Success" if result["status"] == "success" else "❌ Failed"
            if retry_needed:
                status_text += " (after Retry)"
                
            response_content = f"**Status:** {status_text}"
            if result.get("error"):
                response_content += f"\n\n**Error:** {result['error']}"
                
            st.markdown(response_content)
            if result.get("sql"):
                st.code(result["sql"], language="sql")
                
            if result["status"] == "success":
                if result["result"]:
                    st.dataframe(pd.DataFrame(result["result"]))
                else:
                    st.info("Query returned 0 rows.")
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response_content,
                "sql": result.get("sql"),
                "data": result.get("result") if result["status"] == "success" else None
            })
