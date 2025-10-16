import json
from datetime import date
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import os
from flask import send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    results = db.Column(db.String(100), nullable=False)

@app.route("/debug_data")
def debug_data():
    all_data = History.query.all()
    return jsonify([{"date": h.date, "results": h.results} for h in all_data])

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

    # --- Save to database instead of JSON ---
    existing = History.query.filter_by(date=today).first()

    if existing:
        existing.results = count_text
    else:
        new_entry = History(date=today, results=count_text)
        db.session.add(new_entry)

    db.session.commit()

    # Optional: return all history from the database
    all_data = History.query.all()
    history_data = [{"date": h.date, "results": h.results} for h in all_data]

    return jsonify({"results": count_text, "history": history_data})

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
    with app.app_context():
        db.create_all()
    app.run(debug=True)


