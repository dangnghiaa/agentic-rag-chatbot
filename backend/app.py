"""
Flask API Server cho Chatbot Luật Giao Thông
- Chỉ hiển thị kết luận trên giao diện
- Log đầy đủ pipeline trong terminal
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import webbrowser
from threading import Timer
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from main_optimized import run_rag

# ================= FLASK =================
app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)

@app.route("/")
def index():
    return send_from_directory("../frontend", "index.html")

@app.route("/api/chat", methods=["POST"])
def chat():

    q = request.json.get("question", "").strip()

    if not q:
        return jsonify({"error": "empty"}), 400

    print(f"\n[CHAT] {q}", flush=True)

    try:
        q_lower = q.lower()

        # Greeting
        if q_lower in ["hi", "hello", "xin chào", "chào", "hey"]:
            return jsonify({
                "answer": "Xin chào! 👋 Tôi là trợ lý tư vấn luật giao thông. Bạn muốn hỏi về lỗi vi phạm nào?"
            })

        # Goodbye
        if q_lower in ["bye", "tạm biệt", "goodbye"]:
            return jsonify({
                "answer": "Tạm biệt! 👋 Chúc bạn tham gia giao thông an toàn."
            })

        answer = run_rag(q)
    except Exception as e:
        return jsonify({"error": str(e)})

    return jsonify({"answer": answer})

# ================= RUN =================
if __name__ == "__main__":
    Timer(1.2, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(debug=True, port=5000)