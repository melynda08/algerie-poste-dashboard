## history.py
from app.models import UserQueryHistory, Conversation
from sqlalchemy.orm import Session

def save_to_history(db: Session, user_id, conversation_id, question: str, response: str, file_id: str = None):
    """
    Save a query and response to the history table
    Now includes optional file_id parameter to track which CSV file was used
    """
    try:
        entry = UserQueryHistory(
            user_id=user_id,
            conversation_id=conversation_id,
            question=question,
            response=response,
            file_id=file_id
        )
        db.add(entry)
        db.commit()
        return entry
    except Exception:
        db.rollback()
        raise

def get_conversation_history(db: Session, conversation_id: str, limit: int = 10):
    """Get the history for a specific conversation"""
    return db.query(UserQueryHistory).filter(
        UserQueryHistory.conversation_id == conversation_id
    ).order_by(UserQueryHistory.timestamp.desc()).limit(limit).all()
