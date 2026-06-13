import time
import requests


def ask_llm(prompt):

    start = time.time()

    response = requests.post(
        "http://127.0.0.1:11434/api/generate",
        json={
            "model": "qwen3:4b",
            "prompt": prompt,
            "stream": False,

            # Disable reasoning mode
            "think": False,

            "options": {
                "num_predict": 300,
                "temperature": 0.3
            }
        },
        timeout=300
    )

    data = response.json()

    print("\n===== OLLAMA RESPONSE =====")
    print(data)
    print("===========================\n")

    print(
        f"LLM Time: {time.time() - start:.2f} sec"
    )

    return data.get(
        "response",
        "No response returned from Ollama"
    )