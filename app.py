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
        );
    """)

    # Create User History table (renamed from history)
    execute_query("""
        CREATE TABLE IF NOT EXISTS user_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            date TEXT NOT NULL,
            results TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Create User Requirements table
    execute_query("""
        CREATE TABLE IF NOT EXISTS user_requirements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            requirements TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Create User Shortlist table
    execute_query("""
        CREATE TABLE IF NOT EXISTS user_shortlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            shortlist TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Add useful indexes for performance
    execute_query("CREATE INDEX IF NOT EXISTS idx_user_history_user_id ON user_history(user_id);")
    execute_query("CREATE INDEX IF NOT EXISTS idx_user_history_date ON user_history(user_id, date);")
    execute_query("CREATE INDEX IF NOT EXISTS idx_requirements_user_id ON user_requirements(user_id);")
    execute_query("CREATE INDEX IF NOT EXISTS idx_shortlist_user_id ON user_shortlist(user_id);")

    print("✅ Database tables initialized successfully")

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
    print("🔍 Debug endpoint called")
    try:
        # Test user_history table
        result = execute_query("SELECT * FROM user_history")
        print(f"📊 user_history query result: {result}")
        
        if result and result[0].get("results"):
            rows = result[0]["results"].get("rows", [])
            history_data = [{"id": row[0], "user_id": row[1], "url": row[2], "date": row[3], "results": row[4]} for row in rows]
            return jsonify({
                "user_history": history_data,
                "raw_response": result
            })
        else:
            return jsonify({"error": "No results", "raw_response": result})
    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

@app.route('/index')
def serve_index():
    return send_from_directory('.', 'index.html')

# -------------------------
# Helper function to get user data from token
# -------------------------

def get_user_from_token():
    """Extract user_id and username from JWT token"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    
    if not token:
        return None
    
    user_data = verify_token(token)
    
    if not user_data:
        return None
    
    return user_data

# -------------------------
# 🕷️ Web Scraper (User-Specific)
# -------------------------
@app.route("/scrape", methods=["GET"])
def scrape():
    # Get user data from token
    user_data = get_user_from_token()
    if not user_data:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = user_data.get("user_id")
    username = user_data.get("username")

    print(f"🔐 User authenticated - user_id: {user_id}, username: {username}")

    url = request.args.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        print(f"🌐 Fetching URL: {url}")
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        result_count = soup.find("div", class_="ResultsCount_resultsCount__Kqeah")

        count_text = result_count.text.strip() if result_count else "0"
        today = str(date.today())

        print(f"🔍 Scraping for user_id: {user_id}, URL: {url}, Date: {today}, Results: {count_text}")

        # Check if entry exists for same user, date, and URL
        check_query = "SELECT * FROM user_history WHERE user_id = ? AND date = ? AND url = ?"
        check_result = execute_query(check_query, [user_id, today, url])

        # ✅ Handle results correctly
        existing_rows = []
        if check_result and "results" in check_result[0] and "rows" in check_result[0]["results"]:
            existing_rows = check_result[0]["results"]["rows"]

        if existing_rows:
            update_query = "UPDATE user_history SET results = ? WHERE user_id = ? AND date = ? AND url = ?"
            execute_query(update_query, [count_text, user_id, today, url])
            print("✏️ Updated existing entry")
        else:
            insert_query = "INSERT INTO user_history (user_id, url, date, results) VALUES (?, ?, ?, ?)"
            execute_query(insert_query, [user_id, url, today, count_text])
            print("➕ Inserted new entry")

        # ✅ Now fetch ALL history for this user (not just today)
        history_query = """
            SELECT url, date, results
            FROM user_history
            WHERE user_id = ?
            ORDER BY date DESC, created_at DESC
        """
        history_result = execute_query(history_query, [user_id])

        # Format results properly
        history_data = []
        if history_result and "results" in history_result[0] and "rows" in history_result[0]["results"]:
            for row in history_result[0]["results"]["rows"]:
                history_data.append({
                    "url": row[0],
                    "date": row[1],
                    "results": row[2]
                })

        print(f"📋 Returning history data: {len(history_data)} entries")

        return jsonify({"results": count_text, "history": history_data})

    except Exception as e:
        print(f"❌ Scrape error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/history", methods=["GET"])
def history():
    user_data = get_user_from_token()
    if not user_data:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = user_data.get("user_id")

    try:
        result = execute_query(
            "SELECT url, date, results FROM user_history WHERE user_id = ? ORDER BY date DESC, created_at DESC",
            [user_id]
        )
        rows = result[0]["results"]["rows"]
        return jsonify([{"url": r[0], "date": r[1], "results": r[2]} for r in rows])
    except Exception as e:
        print(f"History error: {e}")
        return jsonify({"error": str(e)}), 500


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
    

# -------------------------
# 📋 Requirements & Shortlist Routes
# -------------------------

@app.route('/requirements', methods=['GET'])
def get_requirements():
    user_data = get_user_from_token()
    
    if not user_data:
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = user_data.get("username")
    print(f"📋 Fetching requirements for username: {username}")
    
    try:
        result = execute_query(
            "SELECT requirements FROM user_requirements WHERE username = ? ORDER BY updated_at DESC LIMIT 1",
            [username]
        )
        
        print(f"📊 Requirements query result: {result}")
        
        rows = result[0]["results"]["rows"]
        
        if rows:
            requirements = json.loads(rows[0][0])
            print(f"✅ Found requirements: {requirements}")
            return jsonify(requirements), 200
        else:
            print(f"⚠️ No requirements found for username: {username}")
            return jsonify([]), 200
            
    except Exception as e:
        print(f"❌ Error fetching requirements: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to fetch requirements'}), 500

@app.route('/requirements', methods=['POST'])
def save_requirements():
    user_data = get_user_from_token()
    
    if not user_data:
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = user_data.get("username")
    
    data = request.get_json()
    print(f"💾 Saving requirements for username: {username}, data: {data}")
    
    if 'requirements' not in data:
        return jsonify({'error': 'Missing requirements data'}), 400
    
    try:
        requirements_json = json.dumps(data['requirements'])
        
        # Check if user already has requirements
        result = execute_query(
            "SELECT id FROM user_requirements WHERE username = ?",
            [username]
        )
        
        print(f"📊 Check existing requirements: {result}")
        
        existing = result[0]["results"]["rows"]
        
        if existing:
            # Update existing
            update_result = execute_query(
                "UPDATE user_requirements SET requirements = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?",
                [requirements_json, username]
            )
            print(f"✏️ Updated requirements: {update_result}")
        else:
            # Insert new
            insert_result = execute_query(
                "INSERT INTO user_requirements (username, requirements) VALUES (?, ?)",
                [username, requirements_json]
            )
            print(f"➕ Inserted requirements: {insert_result}")
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"❌ Error saving requirements: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to save requirements'}), 500

@app.route('/shortlist', methods=['GET'])
def get_shortlist():
    user_data = get_user_from_token()
    
    if not user_data:
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = user_data.get("username")
    print(f"📋 Fetching shortlist for username: {username}")
    
    try:
        result = execute_query(
            "SELECT shortlist FROM user_shortlist WHERE username = ? ORDER BY updated_at DESC LIMIT 1",
            [username]
        )
        
        print(f"📊 Shortlist query result: {result}")
        
        rows = result[0]["results"]["rows"]
        
        if rows:
            shortlist = json.loads(rows[0][0])
            print(f"✅ Found shortlist: {shortlist}")
            return jsonify(shortlist), 200
        else:
            print(f"⚠️ No shortlist found for username: {username}")
            return jsonify([]), 200
            
    except Exception as e:
        print(f"❌ Error fetching shortlist: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to fetch shortlist'}), 500

@app.route('/shortlist', methods=['POST'])
def save_shortlist():
    user_data = get_user_from_token()
    
    if not user_data:
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = user_data.get("username")
    
    data = request.get_json()
    print(f"💾 Saving shortlist for username: {username}, data: {data}")
    
    if 'shortlist' not in data:
        return jsonify({'error': 'Missing shortlist data'}), 400
    
    try:
        shortlist_json = json.dumps(data['shortlist'])
        
        # Check if user already has shortlist
        result = execute_query(
            "SELECT id FROM user_shortlist WHERE username = ?",
            [username]
        )
        
        print(f"📊 Check existing shortlist: {result}")
        
        existing = result[0]["results"]["rows"]
        
        if existing:
            # Update existing
            update_result = execute_query(
                "UPDATE user_shortlist SET shortlist = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?",
                [shortlist_json, username]
            )
            print(f"✏️ Updated shortlist: {update_result}")
        else:
            # Insert new
            insert_result = execute_query(
                "INSERT INTO user_shortlist (username, shortlist) VALUES (?, ?)",
                [username, shortlist_json]
            )
            print(f"➕ Inserted shortlist: {insert_result}")
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"❌ Error saving shortlist: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to save shortlist'}), 500

# -------------------------
# 🗺️ Geocoding Route (for Map Feature)
# -------------------------

@app.route('/geocode', methods=['POST'])
def geocode():
    """Convert address to coordinates using Nominatim (OpenStreetMap)"""
    user_data = get_user_from_token()
    
    if not user_data:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    address = data.get('address')
    
    if not address:
        return jsonify({'error': 'Address is required'}), 400
    
    try:
        # Use Nominatim API (free OpenStreetMap geocoding)
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'gb'  # Restrict to UK
        }
        headers = {
            'User-Agent': 'HouseHuntingApp/1.0'  # Required by Nominatim
        }
        
        response = requests.get(url, params=params, headers=headers)
        results = response.json()
        
        if results:
            return jsonify({
                'lat': float(results[0]['lat']),
                'lon': float(results[0]['lon']),
                'display_name': results[0]['display_name']
            }), 200
        else:
            return jsonify({'error': 'Address not found'}), 404
            
    except Exception as e:
        print(f"Geocoding error: {e}")
        return jsonify({'error': 'Failed to geocode address'}), 500


if __name__ == "__main__":
    init_db()  # Initialize tables
    app.run(debug=True)