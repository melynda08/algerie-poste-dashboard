# app/__init__.py
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os
from app.routes import main
from app.database import Base, engine

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configurations
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 * 1024  # 5GB

    # Enable CORS
    CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)

    # Register Blueprints
    app.register_blueprint(main)

    # Create DB Tables
    Base.metadata.create_all(bind=engine)

    return app
