import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils import execute_query, create_response, get_request_body, get_user_from_token
import json

def handler(event, context):
    """Handle requirements GET and POST"""
    if event.get('httpMethod') == 'OPTIONS':
        return create_response(200, {})
    
    user_data = get_user_from_token(event)
    if not user_data:
        return create_response(401, {'error': 'Unauthorized'})
    
    user_id = user_data.get("user_id")
    
    if event.get('httpMethod') == 'GET':
        try:
            result = execute_query(
                "SELECT requirements FROM user_requirements WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1",
                [user_id]
            )
            
            rows = result[0].get("results", {}).get("rows", [])
            
            if rows:
                requirements = json.loads(rows[0][0])
                return create_response(200, requirements)
            else:
                return create_response(200, [])
                
        except Exception as e:
            return create_response(500, {'error': 'Failed to fetch requirements'})
    
    elif event.get('httpMethod') == 'POST':
        try:
            data = get_request_body(event)
            
            if 'requirements' not in data:
                return create_response(400, {'error': 'Missing requirements data'})
            
            requirements_json = json.dumps(data['requirements'])
            
            # Check if user already has requirements
            result = execute_query(
                "SELECT id FROM user_requirements WHERE user_id = ?",
                [user_id]
            )
            
            existing = result[0].get("results", {}).get("rows", [])
            
            if existing:
                # Update existing
                execute_query(
                    "UPDATE user_requirements SET requirements = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    [requirements_json, user_id]
                )
            else:
                # Insert new
                execute_query(
                    "INSERT INTO user_requirements (user_id, requirements) VALUES (?, ?)",
                    [user_id, requirements_json]
                )
            
            return create_response(200, {'success': True})
            
        except Exception as e:
            return create_response(500, {'error': 'Failed to save requirements'})
    
    else:
        return create_response(405, {'error': 'Method not allowed'})

