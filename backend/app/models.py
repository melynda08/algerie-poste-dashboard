from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from app.database import Base
import uuid

class AppUser(Base):
    __tablename__ = "app_user"
    user_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    role = Column(String(50), nullable=False, default='Viewer')

class Conversation(Base):
    __tablename__ = "conversation"
    conversation_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey('app_user.user_id', ondelete='CASCADE'), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())

class UserQueryHistory(Base):
    __tablename__ = "user_query_history"
    history_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey('app_user.user_id', ondelete='CASCADE'), nullable=False)
    conversation_id = Column(PG_UUID(as_uuid=True), ForeignKey('conversation.conversation_id', ondelete='CASCADE'), nullable=False)
    question = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class Receptacle(Base):
    __tablename__ = "receptacle"
    receptacle_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receptacle_identifier = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    origin_facility = Column(String(100))
    destination_facility = Column(String(100))
    status = Column(String(50), nullable=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())

class MailItem(Base):
    __tablename__ = "mail_item"
    mail_item_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mail_item_identifier = Column(String(100), unique=True, nullable=False)
    receptacle_id = Column(PG_UUID(as_uuid=True), ForeignKey('receptacle.receptacle_id', ondelete='SET NULL'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    origin_facility = Column(String(100))
    destination_facility = Column(String(100))
    status = Column(String(50), nullable=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())

class EventType(Base):
    __tablename__ = "event_type"
    event_type_id = Column(Integer, primary_key=True)
    event_code = Column(String(10), unique=True, nullable=False)
    event_name = Column(String(255), nullable=False)
    event_description = Column(Text)
    is_receptacle_event = Column(Boolean, default=False)
    is_mail_item_event = Column(Boolean, default=False)

class ReceptacleEvent(Base):
    __tablename__ = "receptacle_event"
    event_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receptacle_id = Column(PG_UUID(as_uuid=True), ForeignKey('receptacle.receptacle_id', ondelete='CASCADE'), nullable=False)
    event_type_id = Column(Integer, ForeignKey('event_type.event_type_id', ondelete='CASCADE'), nullable=False)
    event_timestamp = Column(DateTime(timezone=True), nullable=False)
    facility = Column(String(100))
    next_facility = Column(String(100))
    event_details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MailItemEvent(Base):
    __tablename__ = "mail_item_event"
    event_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mail_item_id = Column(PG_UUID(as_uuid=True), ForeignKey('mail_item.mail_item_id', ondelete='CASCADE'), nullable=False)
    event_type_id = Column(Integer, ForeignKey('event_type.event_type_id', ondelete='CASCADE'), nullable=False)
    event_timestamp = Column(DateTime(timezone=True), nullable=False)
    facility = Column(String(100))
    next_facility = Column(String(100))
    event_details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
