## routes.py
from flask import Blueprint, request, jsonify, g
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AppUser, Conversation, UserQueryHistory, Receptacle, MailItem
from datetime import datetime
import uuid
import pandas as pd
import plotly.express as px
import base64
from .auth import generate_token, verify_user_credentials, login_required, get_authenticated_user
from .history import save_to_history
from .gemini import ask_gemini

main = Blueprint('main', __name__)

@main.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password required"}), 400

    user = verify_user_credentials(data['email'], data['password'])
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    token = generate_token(str(user['user_id']))
    return jsonify({
        "token": token,
        "user_id": str(user['user_id']),
        "role": user['role'],
        "expires_in": "24 hours"
    })

@main.route('/start_conversation', methods=['POST'])
@login_required
def start_conversation():
    db: Session = next(get_db())
    user_id = get_authenticated_user()
    # Create a new conversation for authenticated user
    conv = Conversation(user_id=user_id)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return jsonify({
        "conversation_id": str(conv.conversation_id),
        "user_id": user_id
    })

@main.route('/chat', methods=['POST'])
@login_required
def chat():
    db: Session = next(get_db())
    data = request.get_json()
    question = data.get('question')
    if not question:
        return jsonify({"error": "Question is required"}), 400

    user_id = get_authenticated_user()
    conversation_id = data.get('conversation_id')

    # create conversation if missing
    if not conversation_id:
        conv = Conversation(user_id=user_id)
        db.add(conv)
        db.commit()
        db.refresh(conv)
        conversation_id = str(conv.conversation_id)

    # Fetch relevant data from database as context
    df = pd.read_sql(
        """
        SELECT mi.mail_item_identifier, et.event_code, et.event_name, me.event_timestamp, me.facility, me.next_facility
        FROM mail_item_event me
        JOIN mail_item mi ON me.mail_item_id = mi.mail_item_id
        JOIN event_type et ON me.event_type_id = et.event_type_id
        ORDER BY me.event_timestamp DESC
        LIMIT 10
        """, db.bind
    )
    data_string = df.to_string(index=False)

    # Construct prompt with context
    prompt = f"""
You are a logistics assistant with access to this recent parcel event data from the database:

{data_string}

The user asks: \"{question}\"
Provide a clear, concise answer based on the data above.
"""

    # LLM integration
    response = ask_gemini(prompt, user_id, conversation_id)

    # Save chat history
    save_to_history(db, user_id, conversation_id, question, response)

    return jsonify({
        "response": response,
        "conversation_id": conversation_id
    })



@main.route('/visualize', methods=['POST'])
@login_required
def visualize():
    db: Session = next(get_db())
    data = request.json
    # Fetch aggregated receptacle data
    df = pd.read_sql("""
        SELECT 
            r.receptacle_identifier,
            r.status,
            r.origin_facility,
            r.destination_facility,
            COUNT(m.mail_item_id) as items_count,
            EXTRACT(DAY FROM (r.last_updated - r.created_at)) as days_in_transit
        FROM receptacle r
        LEFT JOIN mail_item m ON r.receptacle_id = m.receptacle_id
        GROUP BY r.receptacle_id
        LIMIT 500
    """, db.bind)

    # Clean data: drop rows where both origin and destination are null
    df = df.dropna(subset=['origin_facility', 'destination_facility'], how='all')
    # Fill missing with 'Unknown'
    df['origin_facility'] = df['origin_facility'].fillna('Unknown')
    df['destination_facility'] = df['destination_facility'].fillna('Unknown')

    fig = px.sunburst(
        df,
        path=['origin_facility', 'status', 'destination_facility'],
        values='items_count',
        title="Shipment Flow Analysis"
    )

    img_bytes = fig.to_image(format="png")
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')

    return jsonify({
        "image": f"data:image/png;base64,{img_b64}",
        "conversation_id": data.get('conversation_id', str(uuid.uuid4()))
    })

@main.route('/conversations/<user_id>', methods=['GET'])
@login_required
def get_user_conversations(user_id):
    db: Session = next(get_db())
    conversations = db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).order_by(Conversation.started_at.desc()).all()

    return jsonify([
        {
            "conversation_id": str(c.conversation_id),
            "started_at": c.started_at.isoformat()
        } for c in conversations
    ])

@main.route('/history/<user_id>', methods=['GET'])
@login_required
def get_user_history(user_id):
    db: Session = next(get_db())
    limit = int(request.args.get('limit', 20))

    history = db.query(UserQueryHistory).filter(
        UserQueryHistory.user_id == user_id
    ).order_by(UserQueryHistory.timestamp.desc()).limit(limit).all()

    return jsonify([
        {
            "question": h.question,
            "response": h.response,
            "timestamp": h.timestamp.isoformat(),
            "conversation_id": str(h.conversation_id)
        } for h in history
    ])