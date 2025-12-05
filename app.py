from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

# ========= CONFIG CỦA BẠN =========
ELASTIC_HOST = "https://xdrview.dc.turkuamk.fi:9200"
ELASTIC_INDEX = "botsv1_ctf_answers"
ELASTIC_PIPELINE = "ctf_answer_checker"
# API key sẽ lấy từ biến môi trường ELASTIC_API_KEY trên Railway
ELASTIC_API_KEY = os.environ.get("ELASTIC_API_KEY")
# ===================================

# BẢNG ĐÁP ÁN — tạm, bạn sẽ sửa lại sau cho đúng
CORRECT_ANSWERS = {
    "1": "209.35.99.117",
    "2": "ANSWER_Q2",
    "3": "ANSWER_Q3",
    "4": "ANSWER_Q4",
    "5": "ANSWER_Q5"
}

app = Flask(__name__)
CORS(app)  # cho phép gọi từ GitHub Pages

@app.route("/submit-answer", methods=["POST"])
def submit_answer():
    question = request.form.get("question")
    answer = request.form.get("answer")

    if not question or not answer:
        return jsonify({"correct": False, "message": "Missing question or answer"}), 400

    # Gửi log vào Elasticsearch (dù đúng hay sai)
    doc = {
        "question": question,
        "answer": answer,
        "player_ip": request.remote_addr
    }

    if ELASTIC_API_KEY:
        es_url = f"{ELASTIC_HOST}/{ELASTIC_INDEX}/_doc?pipeline={ELASTIC_PIPELINE}"
        es_headers = {
            "Content-Type": "application/json",
            "Authorization": f"ApiKey {ELASTIC_API_KEY}"
        }
        try:
            requests.post(es_url, json=doc, headers=es_headers, timeout=5)
        except Exception as e:
            # Không block player, nhưng trả thông báo lỗi để debug nếu cần
            print("Error sending to Elasticsearch:", e)

    # Tự check đúng/sai dựa vào CORRECT_ANSWERS
    correct_answer = CORRECT_ANSWERS.get(str(question))
    is_correct = (correct_answer is not None and answer.strip() == correct_answer)

    return jsonify({
        "correct": is_correct
    })

@app.route("/", methods=["GET"])
def home():
    return "SOC1 CTF Backend Running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
