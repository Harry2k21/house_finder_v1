import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils import execute_query, create_response, get_request_body, generate_password_hash

def handler(event, context):
    """Handle user registration"""
    if event.get('httpMethod') == 'OPTIONS':
        return create_response(200, {})
    
    if event.get('httpMethod') != 'POST':
        return create_response(405, {'error': 'Method not allowed'})
    
    try:
        data = get_request_body(event)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if not username or not email or not password:
            return create_response(400, {'error': 'All fields are required'})

        if password != confirm_password:
            return create_response(400, {'error': 'Passwords do not match'})

        if len(password) < 6:
            return create_response(400, {'error': 'Password must be at least 6 characters'})

        # Check if username exists
        result = execute_query("SELECT * FROM user WHERE username = ?", [username])
        if result and result[0].get("results", {}).get("rows"):
            return create_response(400, {'error': 'Username already exists'})

        # Check if email exists
        result = execute_query("SELECT * FROM user WHERE email = ?", [email])
        if result and result[0].get("results", {}).get("rows"):
            return create_response(400, {'error': 'Email already exists'})

        password_hash = generate_password_hash(password)
        execute_query(
            "INSERT INTO user (username, email, password_hash) VALUES (?, ?, ?)",
            [username, email, password_hash]
        )
        return create_response(201, {'message': 'Registration successful! Please log in.'})
    except Exception as e:
        return create_response(500, {'error': str(e)})

