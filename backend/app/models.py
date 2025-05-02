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
    file_id = Column(String(36), nullable=True)  # Added to track which CSV file was used

class CSVFileRecord(Base):
    __tablename__ = "csv_file_record"
    file_id = Column(String(36), primary_key=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey('app_user.user_id', ondelete='CASCADE'), nullable=False)
    filename = Column(String(255), nullable=False)
    upload_path = Column(String(512), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    row_count = Column(Integer, nullable=True)
    columns = Column(JSON, nullable=True)
