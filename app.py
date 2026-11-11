import os
from flask import Flask
from config import Config

# Import distinct blueprints
from home import home_bp
from products import products_bp
from services import services_bp
from interactions import interactions_bp
from core.sheets_service import cache_bp
from auth.routes import auth_bp
from recharge import recharge_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register decoupled feature blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(interactions_bp)
    app.register_blueprint(cache_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(recharge_bp)
    

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)