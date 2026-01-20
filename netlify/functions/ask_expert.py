import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils import create_response, get_request_body
from groq import Groq
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables")

client = Groq(api_key=GROQ_API_KEY)

def handler(event, context):
    """Handle expert chat questions"""
    if event.get('httpMethod') == 'OPTIONS':
        return create_response(200, {})
    
    if event.get('httpMethod') != 'POST':
        return create_response(405, {'error': 'Method not allowed'})
    
    try:
        data = get_request_body(event)
        question = data.get('question')

        if not question:
            return create_response(400, {'error': 'No question provided'})

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
        return create_response(200, {"answer": answer})

    except Exception as e:
        return create_response(500, {'error': str(e)})

