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

    answer = data.get(
        "response",
        "No response returned from Ollama"
    )

    # Remove reasoning if present
    if "</think>" in answer:
        answer = answer.split("</think>")[-1].strip()

    print(
        f"LLM Time: {time.time() - start:.2f} sec"
    )

    return answer