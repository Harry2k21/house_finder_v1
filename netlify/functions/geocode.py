import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils import create_response, get_request_body, get_user_from_token
import requests

def handler(event, context):
    """Handle geocoding requests"""
    if event.get('httpMethod') == 'OPTIONS':
        return create_response(200, {})
    
    if event.get('httpMethod') != 'POST':
        return create_response(405, {'error': 'Method not allowed'})
    
    user_data = get_user_from_token(event)
    if not user_data:
        return create_response(401, {'error': 'Unauthorized'})
    
    data = get_request_body(event)
    address = data.get('address')
    
    if not address:
        return create_response(400, {'error': 'Address is required'})
    
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
            return create_response(200, {
                'lat': float(results[0]['lat']),
                'lon': float(results[0]['lon']),
                'display_name': results[0]['display_name']
            })
        else:
            return create_response(404, {'error': 'Address not found'})
            
    except Exception as e:
        return create_response(500, {'error': 'Failed to geocode address'})

