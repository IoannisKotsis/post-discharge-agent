# Import necessary modules
import streamlit as st
from agent.graph import app
from langchain_core.messages import HumanMessage, AIMessage
from agent.nodes import initial_state
from agent.graph import app

# UI Title
st.title("Post-discharge Follow-up Assistant")

# Initialization : ONLY the first time
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "closed" not in st.session_state:
    st.session_state["closed"] = False
    
if "outcome" not in st.session_state:
    st.session_state["outcome"] = None


# Chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if not st.session_state["closed"]:
    if prompt := st.chat_input("👋Hello, how are you feeling today?"):
        st.session_state["messages"].append({"role": "user", "content": prompt})
        result = app.invoke(initial_state(8, HumanMessage(prompt)))
        print("DEBUG outcome:", result["outcome"])
        st.session_state["messages"].append(
            {"role": "assistant", "content": result["messages"][-1].content}
        )
        if result["outcome"] != "followup":
            st.session_state["closed"] = True
            st.session_state["outcome"] = result["outcome"]
        st.rerun()
else:
    if st.session_state["outcome"] == "reassure":
        st.info("No need to worry. Have a great day!")
    elif st.session_state["outcome"] == "escalate":
        st.info("Please follow the guidance above and seek care as advised. Take care.")
    
        
        
        
    