# app/test_ollama.py

from app.rag.llm_service import ask_llm

response = ask_llm(
    "Say hello in one sentence."
)

print(response)