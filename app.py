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
import json
from datetime import date, datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

app = Flask(__name__)
CORS(app)

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your-secret-key-change-this")

db = SQLAlchemy(app)

# -------------------------
# Database Models
# -------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# -------------------------
# Authentication Routes
# -------------------------

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    confirm_password = data.get("confirm_password")

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    if password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400

    try:
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "Registration successful! Please log in."}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid username or password"}), 401

    try:
        token = jwt.encode(
            {
                "user_id": user.id,
                "username": user.username,
                "exp": datetime.utcnow() + timedelta(hours=24)
            },
            app.config["SECRET_KEY"],
            algorithm="HS256"
        )
        return jsonify({
            "message": "Login successful",
            "token": token,
            "username": user.username
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def verify_token(token):
    try:
        data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        return data
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@app.route("/verify_token", methods=["GET"])
def verify_token_route():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    
    if not token:
        return jsonify({"error": "No token provided"}), 401
    
    user_data = verify_token(token)
    
    if not user_data:
        return jsonify({"error": "Invalid or expired token"}), 401
    
    return jsonify({"valid": True, "user_id": user_data.get("user_id"), "username": user_data.get("username")}), 200


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


