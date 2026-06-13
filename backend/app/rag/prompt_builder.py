def build_prompt(question, docs):

    context = "\n\n".join(docs)

    prompt = f"""
Answer directly.

Do NOT explain your reasoning.
Do NOT think step-by-step.
Keep the answer under 3 sentences.

News Articles:
{context}

Question:
{question}
"""
    return prompt