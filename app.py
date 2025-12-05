from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

# ========= CONFIG CỦA BẠN =========
ELASTIC_HOST = "https://xdrview.dc.turkuamk.fi:9200"
ELASTIC_INDEX = "botsv1_ctf_answers"
ELASTIC_PIPELINE = "ctf_answer_checker"
ELASTIC_API_KEY = os.environ.get("ELASTIC_API_KEY")
# ===================================

app = Flask(__name__)
CORS(app)

# Danh sách câu hỏi và đáp án (tạm thời viết thẳng trong code)
questions = {
    1: {
        "question": "Q1: In the bots1_firewall_log index, find the event with action='ALLOW', rule.id=79 and port=19. What is the source.ip?",
        "answer": "209.35.99.117"
    },
    2: {
        "question": "Q2: .... (bạn sẽ điền câu hỏi thật sau này)",
        "answer": "ANSWER_Q2"
    },
    3: {
        "question": "Q3: ....",
        "answer": "ANSWER_Q3"
    },
    4: {
        "question": "Q4: ....",
        "answer": "ANSWER_Q4"
    },
    5: {
        "question": "Q5: ....",
        "answer": "ANSWER_Q5"
    }
}

@app.route("/", methods=["GET"])
def home():
    return "SOC1 CTF Backend Running!"

@app.route("/question/<int:q_id>", methods=["GET"])
def get_question(q_id):
    q = questions.get(q_id)
    if not q:
        return jsonify({"done": True})

    return jsonify({
        "id": q_id,
        "question": q["question"],
        "done": False
    })

@app.route("/submit", methods=["POST"])
def submit():
    """
    Nhận JSON: { "question_id": 1, "answer": "..." }
    """
    data = request.get_json()
    q_id = data.get("question_id")
    user_answer = (data.get("answer") or "").strip()

    q = questions.get(q_id)
    if not q:
        return jsonify({"error": "Invalid question_id"}), 400

    is_correct = (user_answer == q["answer"])

    if is_correct:
        next_q = q_id + 1
        return jsonify({
            "correct": True,
            "next_question": next_q
        })
    else:
        return jsonify({
            "correct": False
        })
@app.route("/finish", methods=["POST"])
def finish():
    data = request.get_json()
    username = data.get("username")
    score = data.get("score", 0)
    finished_time = data.get("finished_time")

    if not username:
        return jsonify({"error": "Missing username"}), 400

    doc = {
        "username": username,
        "score": score,
        "finished_time": finished_time,
        "player_ip": request.remote_addr
    }

    # Gửi vào elastic
    if ELASTIC_API_KEY:
        es_url = f"{ELASTIC_HOST}/{ELASTIC_INDEX}/_doc"
        es_headers = {
            "Content-Type": "application/json",
            "Authorization": f"ApiKey {ELASTIC_API_KEY}"
        }
        try:
            requests.post(es_url, json=doc, headers=es_headers, timeout=5)
        except:
            print("Error ES")

    return jsonify({"status": "saved"})
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
