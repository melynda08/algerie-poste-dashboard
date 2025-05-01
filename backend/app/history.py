## history.py
from app.models import UserQueryHistory, Conversation
from sqlalchemy.orm import Session

def save_to_history(db: Session, user_id, conversation_id, question: str, response: str):
    try:
        entry = UserQueryHistory(
            user_id=user_id,
            conversation_id=conversation_id,
            question=question,
            response=response
        )
        db.add(entry)
        db.commit()
        return entry
    except Exception:
        db.rollback()
        raise