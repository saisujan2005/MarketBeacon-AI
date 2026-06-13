from app.embeddings.search_service import (
    search_news
)

results = search_news(
    "interest rates"
)

for result in results:
    print(result.payload["title"])