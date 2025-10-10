import json
from datetime import date
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import os
from flask import send_from_directory

app = Flask(__name__)
CORS(app)

HISTORY_FILE = "results_history.json"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

@app.route('/index')
def serve_index():
    return send_from_directory('.', 'index.html')

def load_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

# -------------------------
# 🕷️ Web Scraper
# -------------------------
@app.route("/scrape", methods=["GET"])
def scrape():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")
    result_count = soup.find("div", class_="ResultsCount_resultsCount__Kqeah")

    if result_count:
        count_text = result_count.text.strip()
        today = str(date.today())

        history = load_history()
        existing = next((entry for entry in history if entry["date"] == today), None)

        if existing:
            existing["results"] = count_text
        else:
            history.append({"date": today, "results": count_text})

        save_history(history)
        return jsonify({"results": count_text, "history": history})
    else:
        return jsonify({"error": "Could not find results count"}), 500

@app.route("/history", methods=["GET"])
def history():
    return jsonify(load_history())


# -------------------------
# 🧠  "Ask an Expert" Feature
# -------------------------

@app.route("/ask_expert", methods=["POST"])
def ask_expert():
    data = request.get_json()
    question = data.get("question")

    if not question:
        return jsonify({"error": "No question provided"}), 400

    try:
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional real estate advisor. Give clear, practical, and honest advice about house buying in the UK."
                },
                {"role": "user", "content": question},
            ],
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )

        if response.status_code != 200:
            return jsonify({
                "error": "Groq API request failed",
                "status": response.status_code,
                "details": response.text
            }), 500

        data = response.json()
        answer = data["choices"][0]["message"]["content"]

        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
if __name__ == "__main__":
    app.run(debug=True)


