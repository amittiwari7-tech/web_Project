import time
import requests
from config import Config
from flask import Blueprint, jsonify, redirect, url_for, flash

cache_bp = Blueprint('cache', __name__)

_cache = {
    "products": None,
    "timestamp": 0
}

def get_products():
    """Fetches product catalogue from Google Sheets Apps Script with fallback caching."""
    current_time = time.time()
    
    if _cache["products"] is not None and (current_time - _cache["timestamp"]) < Config.CACHE_TIMEOUT:
        return _cache["products"]
    
    try:
        response = requests.get(Config.APPS_SCRIPT_URL, timeout=8)
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                _cache["products"] = data
                _cache["timestamp"] = current_time
                return data
    except Exception as e:
        print(f"[Core Cache] Database fetch error: {e}")
        
    return _cache["products"] if _cache["products"] is not None else []


def get_product_by_id(product_id):
    """Finds a single product by string ID."""
    all_products = get_products()
    return next((p for p in all_products if str(p.get("id")) == str(product_id)), None)


def post_to_sheets(action, payload):
    """Submits form data (custom order or feedback) back to Google Sheets."""
    try:
        url = f"{Config.APPS_SCRIPT_URL}?action={action}"
        response = requests.post(url, json=payload, timeout=8)
        return response.status_code == 200 and response.json().get("status") == "success"
    except Exception as e:
        print(f"[Core Post] Submission error ({action}): {e}")
        return False


# --- FIXED ROUTE ---
@cache_bp.route('/clear-cache')
def clear_cache_route():
    # 1. Reset the cache
    _cache["products"] = None
    _cache["timestamp"] = 0

    # 2. Return a response (JSON or Redirect)
    return jsonify({
        "status": "success",
        "message": "Product cache cleared successfully."
    }), 200

    # OR if you prefer redirecting to your home page:
    # return redirect('/')
    
    


def authUser(email, password):
    try:
        # Pass action and credentials to your Google Apps Script backend
        # Using GET with params (matching your existing structure)
        response = requests.get(
            Config.APPS_SCRIPT_URL, 
            params={"action": "authUser", "email": email, "password": password},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Expecting Apps Script to return something like: {"status": "success", "user": {...}} 
            if data.get("status") == "success":
                return data.get("status")
            else:
                return None
        else:
            print(f"Auth request failed with status code: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Network or connection error during authentication: {e}")
        return None