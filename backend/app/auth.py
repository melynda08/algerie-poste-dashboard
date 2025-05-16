## auth.py
import jwt
from datetime import datetime, timedelta
import os
from functools import wraps
from flask import request, jsonify, g
from werkzeug.security import check_password_hash
from sqlalchemy import text
from app.database import get_db
import secrets

# Load or generate JWT secret
JWT_SECRET = os.getenv('JWT_SECRET')
if not JWT_SECRET:
    JWT_SECRET = secrets.token_urlsafe(32)
    print("⚠️  Warning: No JWT_SECRET env var found. Using auto-generated secret!")
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

def generate_token(user_id):
    payload = {
        'sub': user_id,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload['sub']
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.split()[1] if auth_header.startswith('Bearer ') else None
        if not token:
            return jsonify({"error": "Authorization token is missing"}), 401
        user_id = verify_token(token)
        if not user_id:
            return jsonify({"error": "Invalid or expired token"}), 401
        g.user_id = user_id
        return f(*args, **kwargs)
    return decorated_function

def get_authenticated_user():
    return getattr(g, 'user_id', None)

def verify_user_credentials(email: str, password: str) -> dict:
    # Use SQLAlchemy session to run parameterized query
    db = next(get_db())
    stmt = text(
        "SELECT user_id, password_hash, role FROM app_user WHERE email = :email"
    )
    result = db.execute(stmt, {'email': email}).first()
    if result and check_password_hash(result.password_hash, password):
        return {"user_id": result.user_id, "role": result.role}
    return None