from app.rag.market_agent import answer_question

response = answer_question(
    "What are the major market events today?"
)

print(response)