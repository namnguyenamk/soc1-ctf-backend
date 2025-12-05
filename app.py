from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

# ========= CONFIG CỦA BẠN =========
ELASTIC_HOST = "https://xdrview.dc.turkuamk.fi:9200"
ELASTIC_INDEX = "botsv1_ctf_answers"
ELASTIC_PIPELINE = "ctf_answer_checker"  # nếu bạn tạo ingest pipeline
ELASTIC_API_KEY = os.environ.get("ELASTIC_API_KEY")
# ===================================

app = Flask(__name__)
CORS(app)  # Cho phép gọi từ GitHub Pages

# Danh sách câu hỏi và đáp án
questions = {
    1: {
        "question": "Question1: In the bots1_firewall_log index, find the event with action='ALLOW', rule.id=79 and port=19. What is the source.ip?",
        "answer": "209.35.99.117"
    },
    2: {
        "question": "Question2— Firewall Log Analysis
In **bots1_firewall_log**, what is the:➡ **destination.ip** of the session **denied by the firewall (action = DENY)**?
👉 Enter the answer in the form:**
`192.168.xxx.xxx`",
        "answer": "ANSWER_Q2"
    },
    3: {
        "question": "Question 3 — Firewall Log Analysis: In **bots1_firewall_log**, determine:➡ Which **destination port (destination.port)** is blocked the most by the **firewall**?
👉 Please provide the **destination.port** of this event.",
        "answer": "ANSWER_Q3"
    },
    4: {
        "question": "**Question4:**In the `bots1_firewall_log`.Firewall Behavior  find:➡ Which **Source IP** was **rejected the most times** by the firewall?
👉 Please provide the **source.ip** of this event",
        "answer": "ANSWER_Q4"
    },
    5: {
        "question": "Question 5 — Protocol Inspection.Based on **bots1_firewall_log**, determine:➡ Which **protocol** appears in the **DENY** logs?
👉 Please provide the **protocal** of this event.",
        "answer": "ANSWER_Q5"
    }
}

@app.route("/", methods=["GET"])
def home():
    return "SOC1 CTF Backend Running!"

# -------------------------------------------------------
# API LẤY CÂU HỎI
# -------------------------------------------------------
@app.route("/question/<int:q_id>", methods=["GET"])
def get_question(q_id):
    q = questions.get(q_id)
    if not q:
        return jsonify({"done": True})  # Không còn câu hỏi → trả done

    return jsonify({
        "id": q_id,
        "question": q["question"],
        "done": False
    })

# -------------------------------------------------------
# API SUBMIT TRẢ LỜI
# -------------------------------------------------------
@app.route("/submit", methods=["POST"])
def submit_answer():
    data = request.get_json()
    q_id = data.get("question_id")
    user_answer = (data.get("answer") or "").strip()
    username = data.get("username") or "unknown"

    q = questions.get(q_id)
    if not q:
        return jsonify({"error": "Invalid question_id"}), 400

    is_correct = (user_answer == q["answer"])

    # Gửi log vào Elasticsearch
    if ELASTIC_API_KEY:
        doc = {
            "username": username,
            "question": q_id,
            "submitted_answer": user_answer,
            "correct_answer": q["answer"],
            "is_correct": is_correct,
            "player_ip": request.remote_addr
        }

        es_url = f"{ELASTIC_HOST}/{ELASTIC_INDEX}/_doc"
        es_headers = {
            "Content-Type": "application/json",
            "Authorization": f"ApiKey {ELASTIC_API_KEY}"
        }

        try:
            requests.post(es_url, json=doc, headers=es_headers, timeout=5)
        except Exception as e:
            print("Error sending to Elasticsearch:", e)

    if is_correct:
        next_q = q_id + 1
        return jsonify({"correct": True, "next_question": next_q})

    return jsonify({"correct": False})

# -------------------------------------------------------
# API FINISH — LƯU KẾT QUẢ
# -------------------------------------------------------
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

    # Send to Elastic
    if ELASTIC_API_KEY:
        es_url = f"{ELASTIC_HOST}/{ELASTIC_INDEX}/_doc"
        es_headers = {
            "Content-Type": "application/json",
            "Authorization": f"ApiKey {ELASTIC_API_KEY}"
        }

        try:
            requests.post(es_url, json=doc, headers=es_headers, timeout=5)
        except:
            print("Error saving score to ES")

    return jsonify({"status": "saved"})

# -------------------------------------------------------
# API RANKING — TOP 10
# -------------------------------------------------------
@app.route("/ranking", methods=["GET"])
def ranking():
    es_url = f"{ELASTIC_HOST}/{ELASTIC_INDEX}/_search"
    query = {
        "size": 10,
        "sort": [
            {"score": {"order": "desc"}},
            {"finished_time": {"order": "asc"}}
        ],
        "query": {
            "exists": { "field": "score" }
        }
    }

    es_headers = {
        "Content-Type": "application/json",
        "Authorization": f"ApiKey {ELASTIC_API_KEY}"
    }

    res = requests.get(es_url, json=query, headers=es_headers)
    result = res.json()

    ranking_list = []

    for hit in result["hits"]["hits"]:
        src = hit["_source"]
        ranking_list.append({
            "username": src.get("username"),
            "score": src.get("score"),
            "finished_time": src.get("finished_time")
        })

    return jsonify(ranking_list)

# -------------------------------------------------------
# RUN APP
# -------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
