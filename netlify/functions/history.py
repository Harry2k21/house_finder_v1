import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils import execute_query, create_response, get_user_from_token

def handler(event, context):
    """Get user search history"""
    if event.get('httpMethod') == 'OPTIONS':
        return create_response(200, {})
    
    if event.get('httpMethod') != 'GET':
        return create_response(405, {'error': 'Method not allowed'})
    
    user_data = get_user_from_token(event)
    if not user_data:
        return create_response(401, {'error': 'Unauthorized'})

    user_id = user_data.get('user_id')

    try:
        result = execute_query(
            "SELECT url, date, results FROM user_history WHERE user_id = ? ORDER BY date DESC, created_at DESC",
            [user_id]
        )
        rows = result[0].get("results", {}).get("rows", [])
        history = [{"url": r[0], "date": r[1], "results": r[2]} for r in rows]
        return create_response(200, history)
    except Exception as e:
        return create_response(500, {'error': str(e)})

