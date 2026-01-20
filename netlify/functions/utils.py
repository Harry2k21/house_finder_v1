import os
import json
import requests
import jwt
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

# Re-export password hashing functions for convenience
__all__ = [
    'execute_query',
    'verify_token',
    'get_user_from_token',
    'create_response',
    'get_request_body',
    'get_query_params',
    'generate_password_hash',
    'check_password_hash',
    'SECRET_KEY',
    'TURSO_DATABASE_URL',
    'TURSO_AUTH_TOKEN'
]

# Environment variables
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")
SECRET_KEY = os.getenv("SECRET_KEY", "")

def execute_query(sql, params=None):
    """Execute SQL query on Turso database via HTTP API"""
    if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
        raise ValueError("TURSO_DATABASE_URL and TURSO_AUTH_TOKEN must be set")
    
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

def verify_token(token):
    """Verify JWT token and return user data"""
    try:
        if not SECRET_KEY:
            return None
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return data
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_user_from_token(event):
    """Extract user_id and username from JWT token in request headers"""
    headers = event.get('headers', {})
    auth_header = headers.get('authorization', '') or headers.get('Authorization', '')
    
    token = auth_header.replace("Bearer ", "").replace("bearer ", "")
    
    if not token:
        return None
    
    user_data = verify_token(token)
    return user_data

def create_response(status_code, body, headers=None):
    """Create a standardized Netlify Function response"""
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS"
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps(body)
    }

def get_request_body(event):
    """Extract and parse JSON body from event"""
    try:
        body = event.get('body', '{}')
        if isinstance(body, str):
            return json.loads(body)
        return body
    except json.JSONDecodeError:
        return {}

def get_query_params(event):
    """Extract query string parameters from event"""
    return event.get('queryStringParameters', {}) or {}

