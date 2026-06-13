from app.rag.llm_service import ask_llm

response = ask_llm(
    "What is a repo rate?"
)

print(response)