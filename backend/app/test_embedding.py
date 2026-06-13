from app.embeddings.embedder import generate_embedding

embedding = generate_embedding(
    "RBI increases repo rate by 25 basis points"
)

print(len(embedding))