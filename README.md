# Post-Discharge Follow-up Assistant
An AI agent that provides conversational follow-up for discharged patients, built on top of a machine-learning readmission risk model.

The App is deployed and publicly accessible at:
[Live APP](https://post-discharge-agent-yhuu7jups6jwzdhily85lj.streamlit.app/)
[Connected to Hospital Readmission Prediction System:](https://hospital-readmission-prediction-production.up.railway.app)

## Overview / The Problem:
Hospital readmissions are costly and preventable. The first system predicts which patients are at risk within 30 days. But a prediction alone doesn't help the patient.
This assistant helps by providing conversational follow-up that acts on the risk score, triaging symptoms and guiding patients toward the right level of care.

## Architecture


## Key Design Decisions

Why state machine over ReAct?

Risk Score Usage: The application is using the patient's readmission risk in order to guide more relevantly. This score can only upgrade the severity of a patient profile and tries to avoid cases where risk is high but symptoms mild.

Agent calls Readmission Prediction API for information

What happens when API fails?
When the API fails and cannor retrieve the patient's readmission risk score, the App assumes maximum risk (100%) in order to not lose any critical case that had a hih risk and did not see it.

## Tech Stack

| Category | Technology |
|---|---|
| AI Agent | LangGraph, AnthropicAPI |
| API | FastAPI |
| Database | PostgreSQL, ChromaDB (RAG) |
| LLM | Claude |
| Deployment | Streamlit |
| Language | Python |

## Features

- Sympton triage - interprets free-text patient messages describing how they feel after discharge
- 4-level severity routing — classifies each interaction in 4 different symptoms-severity levels ( none / advice / urgent / emergency) and acts accordingly
- Risk-aware escalation — combines the patient's readmission risk score with reported symptoms; high risk alone can trigger escalation even when symptoms are mild
- RAG-grounded responses — answers are grounded in clinical guidelines (ChromaDB), with a safety fallback when no relevant guideline is found
- Conversation summaries for clinicians — generates a concise, clinical-style summary of each conversation and stores it for the care team
- Bounded conversation - the conversation ends when the situation is clear ad remains open only when the Assistant needs further information