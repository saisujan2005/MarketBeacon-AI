import os
import time
import logging
import threading
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Thread-safe rate limiting variables
_rate_limit_lock = threading.Lock()
_last_request_time = 0.0

# Circuit breaker variables
_circuit_breaker_lock = threading.Lock()
_consecutive_failures = 0
_disabled_until = 0.0
COOLDOWN_PERIOD_SECONDS = 300  # 5 minutes


def ask_llm(prompt, article_title="Unknown Article", attempt=1):
    """
    Queries the Groq API for a given prompt.
    Includes throttling (2s rate limiter), circuit breaker, fail-fast status codes,
    and detailed logging.
    """
    global _last_request_time, _consecutive_failures, _disabled_until

    start_time = time.time()

    # 1. Check Circuit Breaker
    with _circuit_breaker_lock:
        if start_time < _disabled_until:
            cooldown_remaining = int(_disabled_until - start_time)
            logger.warning(
                f"[CIRCUIT BREAKER] LLM service temporarily disabled due to repeated failures. "
                f"Remaining cooldown: {cooldown_remaining} seconds. Title: '{article_title}'"
            )
            raise Exception("LLM service disabled (Circuit Breaker active)")

    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    if not api_key:
        logger.error("GROQ_API_KEY is not set.")
        raise Exception("GROQ_API_KEY is not set.")

    # 2. Rate Limiting (1 request every 2 seconds)
    with _rate_limit_lock:
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < 2.0:
            sleep_time = 2.0 - elapsed
            logger.info(
                f"[RATE LIMITER] Throttling API request for '{article_title}' (Attempt {attempt}). "
                f"Sleeping for {sleep_time:.2f} seconds..."
            )
            time.sleep(sleep_time)
        _last_request_time = time.time()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    logger.info(f"[LLM REQUEST] Processing article: '{article_title}' | Attempt {attempt}")

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        duration = time.time() - start_time

        # 3. Fail Fast Check (non-200 responses)
        if response.status_code != 200:
            logger.warning(
                f"[LLM FAILURE] API returned non-200 status: {response.status_code} "
                f"for '{article_title}' (Duration: {duration:.2f}s)"
            )
            raise requests.exceptions.HTTPError(
                f"API Status {response.status_code}", response=response
            )

        data = response.json()
        answer = data["choices"][0]["message"]["content"]

        # Clean reasoning tags if any
        if "</think>" in answer:
            answer = answer.split("</think>")[-1].strip()

        # Success - Reset circuit breaker failures
        with _circuit_breaker_lock:
            _consecutive_failures = 0

        logger.info(
            f"[LLM SUCCESS] Status: {response.status_code} | "
            f"Article: '{article_title}' | Attempt: {attempt} | Duration: {duration:.2f}s"
        )
        return answer

    except Exception as e:
        duration = time.time() - start_time
        status_code = "Unknown"
        if isinstance(e, requests.exceptions.HTTPError) and hasattr(e, "response") and e.response is not None:
            status_code = e.response.status_code

        # Increment consecutive failures
        with _circuit_breaker_lock:
            _consecutive_failures += 1
            if _consecutive_failures >= 5:
                _disabled_until = time.time() + COOLDOWN_PERIOD_SECONDS
                logger.error(
                    f"[CIRCUIT BREAKER TRIGGERED] 5 consecutive failures reached. "
                    f"Disabling LLM calls for {COOLDOWN_PERIOD_SECONDS // 60} minutes."
                )

        logger.error(
            f"[LLM ERROR] Status Code: {status_code} | "
            f"Article: '{article_title}' | Attempt: {attempt} | "
            f"Duration: {duration:.2f}s | Error: {e}"
        )
        raise e