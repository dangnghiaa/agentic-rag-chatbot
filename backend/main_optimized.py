from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
import hashlib
import time
import json
import os
import requests

from retriever import get_retriever
from generator import generate_answer, GROQ_KEY

# ================= LOG =================
def log(step, msg):
    print(f"[{step}] {msg}", flush=True)

# ================= CACHE =================
CACHE_FILE = "answer_cache.json"
answer_cache = {}

if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            answer_cache = json.load(f)
    except:
        pass

def cache_key(q):
    return hashlib.md5(q.lower().strip().encode()).hexdigest()

def get_cached_answer(q):
    return answer_cache.get(cache_key(q))

def save_to_cache(q, ans):
    answer_cache[cache_key(q)] = ans
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(answer_cache, f, ensure_ascii=False, indent=2)

# ================= RATE LIMIT =================
last_request_time = 0
MIN_INTERVAL = 1.5

def rate_limit():
    global last_request_time
    now = time.time()
    elapsed = now - last_request_time

    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)

    last_request_time = time.time()

# ================= LOAD RETRIEVER =================
log("SYSTEM", "Loading retriever")
law_retriever = get_retriever(k=6)
faq_retriever = get_retriever(k=6)
log("SYSTEM", "Retriever ready")

# ================= STATE =================
class State(TypedDict):
    question: str
    rewritten_question: str
    route: str
    context: Annotated[list, operator.add]
    answer: str
    final: bool
    retry_count: int
    max_retries: int

# ================= AGENTS =================

def route_question(state):

    q = state["question"]
    log("ROUTE", q)

    url = "https://api.groq.com/openai/v1/chat/completions"

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "Phân loại câu hỏi: law / faq / none"},
            {"role": "user", "content": q}
        ],
        "temperature": 0,
        "max_tokens": 5
    }

    try:
        r = requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {GROQ_KEY}"},
            timeout=10
        )

        route = r.json()["choices"][0]["message"]["content"].strip().lower()

        if route not in ["law", "faq", "none"]:
            route = "law"

    except:
        route = "law"

    log("ROUTE_RESULT", route)

    return {"route": route}


def rewrite_question(state):

    q = state["question"]

    log("REWRITE", q)

    return {"rewritten_question": q}


def retrieve(state):

    log("RETRIEVE", f"route={state['route']}")

    if state["route"] == "none":
        return {"context": [""]}

    q = state["rewritten_question"]

    if state["route"] == "faq":
        docs = faq_retriever.invoke(q)
    else:
        docs = law_retriever.invoke(q)

    log("RETRIEVE_DOCS", len(docs))

    context = "\n\n".join([d.page_content for d in docs])

    return {"context": [context]}


def generate(state):

    log("GENERATE", "start")

    ctx = "\n\n".join(state["context"])
    q = state["question"]

    prompt = f"""
Bạn là trợ lý tư vấn luật giao thông Việt Nam.

QUY TẮC BẮT BUỘC:
Yêu cầu bắt buộc:
- Chỉ trả lời KẾT LUẬN CUỐI CÙNG
- Không giải thích, không so sánh, không liệt kê quá trình
- Không dùng các cụm như: "so sánh", "dựa trên", "xem xét", "quá trình"
- Văn phong tự nhiên, giống người thật tư vấn
- Nếu hỏi mức cao nhất / thấp nhất: chỉ nêu 1 mức tương ứng



Câu hỏi:
{q}
"""

    answer = generate_answer(prompt, ctx)

    log("GENERATE", "done")

    return {"answer": answer}


def critic(state):

    log("CRITIC", "final")

    return {"final": True}


# ================= GRAPH =================
graph = StateGraph(State)

graph.add_node("route", route_question)
graph.add_node("rewrite", rewrite_question)
graph.add_node("retrieve", retrieve)
graph.add_node("generate", generate)
graph.add_node("critic", critic)

graph.set_entry_point("route")

graph.add_edge("route", "rewrite")
graph.add_edge("rewrite", "retrieve")
graph.add_edge("retrieve", "generate")
graph.add_edge("generate", "critic")

graph.add_conditional_edges("critic", lambda _: END)

rag_graph = graph.compile()

# ================= MAIN FUNCTION =================
def run_rag(question):

    cached = get_cached_answer(question)

    if cached:
        log("CACHE", "hit")
        return cached

    rate_limit()

    result = rag_graph.invoke({
        "question": question,
        "context": [],
        "route": "",
        "answer": "",
        "rewritten_question": "",
        "final": False,
        "retry_count": 0,
        "max_retries": 2
    })

    answer = result["answer"]

    save_to_cache(question, answer)

    return answer