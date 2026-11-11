import os
from dotenv import load_dotenv
load_dotenv()  # Ye command automatically root folder se .env ko memory me load kar leti hai

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "nexus-super-secure-production-key-2026")
    APPS_SCRIPT_URL = os.environ.get("APPS_SCRIPT_URL", "https://script.google.com/macros/s/AKfycbx2RQx52goHsx5XjfaQ_gZS9jZaNP43dkBGQdCqmJGg0-mrx-PBMhxK-O0tRQAsgDD_/exec")
    CACHE_TIMEOUT = int(os.environ.get("CACHE_TIMEOUT", 21600))  # 6 hours in seconds
    TEMPLATES_AUTO_RELOAD = True
    
        # Cashfree Configurations
    CASHFREE_APP_ID = os.environ.get("CASHFREE_APP_ID")
    CASHFREE_SECRET_KEY = os.environ.get("CASHFREE_SECRET_KEY")
    CASHFREE_API_VERSION = os.environ.get("CASHFREE_API_VERSION", "2023-08-01")
    CASHFREE_ENV = os.environ.get("CASHFREE_ENV", "SANDBOX")  # "SANDBOX" or "PRODUCTION"
    
    
    
    
 
