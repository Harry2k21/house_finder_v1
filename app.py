from dotenv import load_dotenv
load_dotenv()
import secrets

import os
import json
from datetime import date, datetime, timedelta
from groq import Groq
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import requests
from bs4 import BeautifulSoup


app = Flask(__name__)
CORS(app)

# Configure Turso SQLite database

TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")


# -------------------------
# Turso Database Helper
# -------------------------

def execute_query(sql, params=None):
    """Execute SQL query on Turso database via HTTP API"""
    url = TURSO_DATABASE_URL.replace("libsql://", "https://")
    
    headers = {
        "Authorization": f"Bearer {TURSO_AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "statements": [
            {
                "q": sql,
                "params": params or []
            }
        ]
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# -------------------------
# Database Models (Manual)
# -------------------------

def init_db():
    """Initialize database tables"""
    # Create Users table
    execute_query("""
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create History table
    execute_query("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            results TEXT NOT NULL
        )
    """)

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

    # Check if username exists
    result = execute_query("SELECT * FROM user WHERE username = ?", [username])
    if result[0]["results"]["rows"]:
        return jsonify({"error": "Username already exists"}), 400

    # Check if email exists
    result = execute_query("SELECT * FROM user WHERE email = ?", [email])
    if result[0]["results"]["rows"]:
        return jsonify({"error": "Email already exists"}), 400

    try:
        password_hash = generate_password_hash(password)
        execute_query(
            "INSERT INTO user (username, email, password_hash) VALUES (?, ?, ?)",
            [username, email, password_hash]
        )
        return jsonify({"message": "Registration successful! Please log in."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    result = execute_query("SELECT * FROM user WHERE username = ?", [username])
    rows = result[0]["results"]["rows"]
    
    if not rows:
        return jsonify({"error": "Invalid username or password"}), 401
    
    user = rows[0]
    user_id = user[0]
    stored_username = user[1]
    password_hash = user[3]

    if not check_password_hash(password_hash, password):
        return jsonify({"error": "Invalid username or password"}), 401

    try:
        token = jwt.encode(
            {
                "user_id": user_id,
                "username": stored_username,
                "exp": datetime.utcnow() + timedelta(hours=24)
            },
            app.config["SECRET_KEY"],
            algorithm="HS256"
        )
        return jsonify({
            "message": "Login successful",
            "token": token,
            "username": stored_username
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


@app.route("/debug_data")
def debug_data():
    result = execute_query("SELECT * FROM history")
    rows = result[0]["results"]["rows"]
    return jsonify([{"date": row[1], "results": row[2]} for row in rows])

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

@app.route('/index')
def serve_index():
    return send_from_directory('.', 'index.html')

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

    # Check if entry exists
    result = execute_query("SELECT * FROM history WHERE date = ?", [today])
    
    if result[0]["results"]["rows"]:
        execute_query("UPDATE history SET results = ? WHERE date = ?", [count_text, today])
    else:
        execute_query("INSERT INTO history (date, results) VALUES (?, ?)", [today, count_text])

    # Get all history
    result = execute_query("SELECT * FROM history")
    rows = result[0]["results"]["rows"]
    history_data = [{"date": row[1], "results": row[2]} for row in rows]

    return jsonify({"results": count_text, "history": history_data})

@app.route("/history", methods=["GET"])
def history():
    result = execute_query("SELECT * FROM history")
    rows = result[0]["results"]["rows"]
    return jsonify([{"date": row[1], "results": row[2]} for row in rows])



# -------------------------
# 🧠  "Ask an Expert" Feature
# -------------------------

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")


if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found in .env")

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

@app.route("/ask_expert", methods=["POST"])
def ask_expert():
    try:
        data = request.get_json()
        question = data.get("question")

        if not question:
            return jsonify({"error": "No question provided"}), 400

        print(f"📥 Question: {question}")

        response = client.chat.completions.create(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional real estate advisor. Give clear, practical, and honest advice about house buying in the UK."
                },
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=1024,
        )

        answer = response.choices[0].message.content
        print(f"✅ Answer generated: {answer[:100]}...")

        return jsonify({"answer": answer})

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    init_db()  # Initialize tables
    app.run(debug=True)


