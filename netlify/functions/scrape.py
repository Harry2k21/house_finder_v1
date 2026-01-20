import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils import execute_query, create_response, get_query_params, get_user_from_token
from datetime import date
import requests
from bs4 import BeautifulSoup

def handler(event, context):
    """Handle property scraping"""
    if event.get('httpMethod') == 'OPTIONS':
        return create_response(200, {})
    
    if event.get('httpMethod') != 'GET':
        return create_response(405, {'error': 'Method not allowed'})
    
    user_data = get_user_from_token(event)
    if not user_data:
        return create_response(401, {'error': 'Unauthorized'})

    user_id = user_data.get('user_id')
    
    params = get_query_params(event)
    url = params.get('url')
    
    if not url:
        return create_response(400, {'error': 'No URL provided'})

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        result_count = soup.find("div", class_="ResultsCount_resultsCount__Kqeah")

        count_text = result_count.text.strip() if result_count else "0"
        today = str(date.today())

        # Check if entry exists for same user, date, and URL
        check_query = "SELECT * FROM user_history WHERE user_id = ? AND date = ? AND url = ?"
        check_result = execute_query(check_query, [user_id, today, url])

        existing_rows = []
        if check_result and "results" in check_result[0] and "rows" in check_result[0]["results"]:
            existing_rows = check_result[0]["results"]["rows"]

        if existing_rows:
            update_query = "UPDATE user_history SET results = ? WHERE user_id = ? AND date = ? AND url = ?"
            execute_query(update_query, [count_text, user_id, today, url])
        else:
            insert_query = "INSERT INTO user_history (user_id, url, date, results) VALUES (?, ?, ?, ?)"
            execute_query(insert_query, [user_id, url, today, count_text])

        # Fetch ALL history for this user
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

        return create_response(200, {"results": count_text, "history": history_data})

    except Exception as e:
        return create_response(500, {'error': str(e)})

