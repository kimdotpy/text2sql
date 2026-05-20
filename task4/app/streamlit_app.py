import os
import sys
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))
from graph.workflow import GraphWorkflow

st.set_page_config(page_title="Agentic Text-to-SQL", layout="wide")

st.title("Agentic Text-to-SQL Explorer")

workflow = GraphWorkflow()

query = st.text_area("Enter a natural language query", height=120)
if st.button("Run") and query.strip():
    with st.spinner("Planning and generating SQL..."):
        state = workflow.run(query)

    st.subheader("Plan")
    st.code(state.plan or "(no plan)")

    st.subheader("Generated SQL")
    st.code(state.generated_sql or "(no sql)")

    st.subheader("Validation")
    st.write("Valid:" , state.is_valid_sql)
    if state.errors:
        st.warning(state.errors)

    st.subheader("Results")
    if state.execution_results:
        st.dataframe(state.execution_results)
    else:
        st.write("No rows returned")

    st.subheader("Answer")
    st.write(state.final_answer or "(no summary)")
