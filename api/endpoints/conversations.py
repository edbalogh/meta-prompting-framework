import os
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Database setup
DB_NAME=os.environ['POSTGRES_DB']
DB_USER=os.environ['POSTGRES_USER']
DB_PWD=os.environ['POSTGRES_PASSWORD']

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PWD}@db/{DB_NAME}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class ConversationModel(Base):
    __tablename__ = "conversations"

    thread_id = Column(String, primary_key=True, index=True)
    name = Column(String)

# Create the table
Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/api/conversations")

class Conversation(BaseModel):
    thread_id: str
    name: str

    class Config:
        orm_mode = True

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get('/', response_model=List[Conversation])
async def get_all_conversations(db: Session = Depends(get_db)):
    return db.query(ConversationModel).all()

@router.post('/', response_model=Conversation, status_code=status.HTTP_201_CREATED)
async def create_conversation(conversation: Conversation, db: Session = Depends(get_db)):
    db_conversation = ConversationModel(**conversation.dict())
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

@router.delete('/{thread_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(thread_id: str, db: Session = Depends(get_db)):
    conversation = db.query(ConversationModel).filter(ConversationModel.thread_id == thread_id).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conversation)
    db.commit()
    return

@router.put('/{thread_id}', response_model=Conversation)
async def update_conversation(thread_id: str, updated_conversation: Conversation, db: Session = Depends(get_db)):
    conversation = db.query(ConversationModel).filter(ConversationModel.thread_id == thread_id).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    for key, value in updated_conversation.dict().items():
        setattr(conversation, key, value)
    
    db.commit()
    db.refresh(conversation)
    return conversation
