import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils import create_response, verify_token

def handler(event, context):
    """Verify JWT token"""
    if event.get('httpMethod') == 'OPTIONS':
        return create_response(200, {})
    
    if event.get('httpMethod') != 'GET':
        return create_response(405, {'error': 'Method not allowed'})
    
    headers = event.get('headers', {})
    auth_header = headers.get('authorization', '') or headers.get('Authorization', '')
    token = auth_header.replace("Bearer ", "").replace("bearer ", "")
    
    if not token:
        return create_response(401, {'error': 'No token provided'})
    
    user_data = verify_token(token)
    
    if not user_data:
        return create_response(401, {'error': 'Invalid or expired token'})
    
    return create_response(200, {
        'valid': True,
        'user_id': user_data.get('user_id'),
        'username': user_data.get('username')
    })

