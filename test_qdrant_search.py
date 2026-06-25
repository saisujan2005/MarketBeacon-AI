from qdrant_client import QdrantClient
import inspect

client = QdrantClient(":memory:")
print("QdrantClient base classes:", QdrantClient.__bases__)
print("client._client class:", type(client._client))
print("Is 'search' in dir(client._client)?", "search" in dir(client._client))

# Let's inspect __getattr__ on QdrantClient
print("Has __getattr__ on QdrantClient?", hasattr(QdrantClient, "__getattr__"))
