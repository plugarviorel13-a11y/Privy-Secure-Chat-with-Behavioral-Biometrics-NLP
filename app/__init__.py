from flask import Flask
from app.routes import api
from app.db import close_db
from flask_cors import CORS  

def create_app():
    app = Flask(__name__)
    
    # 1. SECRET KEY (Must be FIXED)
    app.config['SECRET_KEY'] = 'cheia_demo_super_secreta'
    
    # 2. COOKIE CONFIGURATION (CRITICAL FOR LOCALHOST!)
    # This tells the browser: "It's ok to use the cookie even if we don't have https"
    app.config['SESSION_COOKIE_SECURE'] = False 
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # 3. CORS (Allow everything from localhost with credentials)
    CORS(app, supports_credentials=True) 

    
    app.register_blueprint(api)
    app.teardown_appcontext(close_db)
    
    return app