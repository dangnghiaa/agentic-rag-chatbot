import requests
from main_optimized import run_rag


# =========================
# GROK CONFIG
# =========================

import requests

API_KEY = "AIzaSyCfiasYU9xdYxPR_PU6mpkrzDtTnOP_sZE"

def ask_gemini(question):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": [
            {
                "parts": [
                    {"text": question}
                ]
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    print(result)  # debug

    if "candidates" not in result:
        print("Gemini API error:", result)
        return "ERROR"

    return result["candidates"][0]["content"]["parts"][0]["text"]

# =========================
# Similarity đơn giản
# =========================

def simple_similarity(a, b):

    a_words = set(a.lower().split())
    b_words = set(b.lower().split())

    common = a_words.intersection(b_words)

    if len(a_words) == 0:
        return 0

    return len(common) / len(a_words) * 100


# =========================
# MAIN LOOP
# =========================

while True:

    print("\n=============================")

    question = input("Nhập câu hỏi (exit để thoát): ")

    if question.lower() == "exit":
        break

    print("\nĐang hỏi LLM...")
    llm_answer = ask_gemini(question)

    print("Đang chạy Agentic RAG...")
    rag_answer = run_rag(question)

    print("\n=============================")

    print("\nLLM ANSWER:\n")
    print(llm_answer)

    print("\nRAG ANSWER:\n")
    print(rag_answer)

    similarity = simple_similarity(llm_answer, rag_answer)

    print("\n=============================")
    print(f"Độ giống nhau: {similarity:.2f}%")