from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os
load_dotenv()

def create_app():
    load_dotenv()
    app = Flask(__name__)
    
    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:5173"],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })
    
    from app.routes import main
    app.register_blueprint(main)
    
    return app