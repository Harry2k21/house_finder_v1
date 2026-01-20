import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils import execute_query, create_response, get_request_body, check_password_hash, SECRET_KEY
from datetime import datetime, timedelta
import jwt

def handler(event, context):
    """Handle user login"""
    if event.get('httpMethod') == 'OPTIONS':
        return create_response(200, {})
    
    if event.get('httpMethod') != 'POST':
        return create_response(405, {'error': 'Method not allowed'})
    
    try:
        data = get_request_body(event)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return create_response(400, {'error': 'Username and password are required'})

        result = execute_query("SELECT * FROM user WHERE username = ?", [username])
        rows = result[0].get("results", {}).get("rows", [])
        
        if not rows:
            return create_response(401, {'error': 'Invalid username or password'})
        
        user = rows[0]
        user_id = user[0]
        stored_username = user[1]
        password_hash = user[3]

        if not check_password_hash(password_hash, password):
            return create_response(401, {'error': 'Invalid username or password'})

        token = jwt.encode(
            {
                "user_id": user_id,
                "username": stored_username,
                "exp": datetime.utcnow() + timedelta(hours=24)
            },
            SECRET_KEY,
            algorithm="HS256"
        )
        return create_response(200, {
            'message': 'Login successful',
            'token': token,
            'username': stored_username
        })
    except Exception as e:
        return create_response(500, {'error': str(e)})

