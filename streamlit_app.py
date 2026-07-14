# Import necessary modules
import os
import streamlit as st
from agent.graph import app
from langchain_core.messages import HumanMessage, AIMessage
from agent.nodes import initial_state
from agent.graph import app

# Bridge secrets to environments
os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
os.environ["READMISSION_API_URL"] = st.secrets["READMISSION_API_URL"]




# UI Title
st.title("Post-discharge Follow-up Assistant")

# App explanation markdown
st.markdown("""This assistant helps you check in after your hospital discharge.
            Tell me how you're feeling, and I'll guide you on whether to rest, monitor, or seek care.
            This is not a substitute for emergency services — if you feel very unwell, call 999.
            """)

# Page configuration
st.set_page_config(page_title="Post-discharge Follow-up Assistant", page_icon="🏥", layout="centered")


# Initialization : ONLY the first time
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "closed" not in st.session_state:
    st.session_state["closed"] = False
    
if "outcome" not in st.session_state:
    st.session_state["outcome"] = None


# Chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"], avatar="🩺" if msg["role"]=="assistant" else "🧑"):
        st.write(msg["content"])

if not st.session_state["closed"]:
    if prompt := st.chat_input("👋Hello, how are you feeling today?"):
        st.session_state["messages"].append({"role": "user", "content": prompt})
        
        with st.spinner("Checking your symptoms..."):
            result = app.invoke(initial_state(2, HumanMessage(prompt)))
        
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
    if st.button("💬New conversation"):
        st.session_state["messages"] = []
        st.session_state["closed"] = False
        st.session_state["outcome"] = None
        st.rerun()
    
        
        
        
    