import hashlib
import re
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, Integer, ForeignKey, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
import os

DATABASE_URL=os.getenv('DATABASE_URL','sqlite:///./upsc.db')
connect_args={'check_same_thread':False} if DATABASE_URL.startswith('sqlite') else {}
engine=create_engine(DATABASE_URL,connect_args=connect_args)
SessionStudy=sessionmaker(bind=engine,autocommit=False,autoflush=False)
class StudyBase(DeclarativeBase): pass

class QuestionBank(StudyBase):
    __tablename__='question_bank'
    id:Mapped[int]=mapped_column(primary_key=True)
    exam:Mapped[str]=mapped_column(String(30),index=True) # prelims/mains/optional
    paper:Mapped[str]=mapped_column(String(80),index=True)
    subject:Mapped[str]=mapped_column(String(160),index=True)
    topic:Mapped[str]=mapped_column(String(240),index=True)
    subtopic:Mapped[str]=mapped_column(String(240),default='')
    question:Mapped[str]=mapped_column(Text)
    normalized_hash:Mapped[str]=mapped_column(String(64),unique=True,index=True)
    difficulty:Mapped[str]=mapped_column(String(30),default='moderate')
    source:Mapped[str]=mapped_column(String(300),default='AI-generated')
    created_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))

class OptionalSelection(StudyBase):
    __tablename__='optional_selections'
    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int]=mapped_column(Integer,unique=True,index=True)
    subject:Mapped[str]=mapped_column(String(160),index=True)
    updated_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))

class ClassNote(StudyBase):
    __tablename__='class_notes'
    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int]=mapped_column(Integer,index=True)
    exam:Mapped[str]=mapped_column(String(30),index=True)
    paper:Mapped[str]=mapped_column(String(80),default='')
    subject:Mapped[str]=mapped_column(String(160),index=True)
    topic:Mapped[str]=mapped_column(String(240),index=True)
    subtopic:Mapped[str]=mapped_column(String(240),default='')
    title:Mapped[str]=mapped_column(String(240))
    file_type:Mapped[str]=mapped_column(String(20)) # pdf/photo
    file_url:Mapped[str]=mapped_column(String(1000))
    uploaded_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))

StudyBase.metadata.create_all(engine)

OPTIONAL_SUBJECTS=['Agriculture','Animal Husbandry & Veterinary Science','Anthropology','Botany','Chemistry','Civil Engineering','Commerce & Accountancy','Economics','Electrical Engineering','Geography','Geology','History','Law','Management','Mathematics','Mechanical Engineering','Medical Science','Philosophy','Physics','Political Science & International Relations','Psychology','Public Administration','Sociology','Statistics','Zoology','Assamese Literature','Bengali Literature','Bodo Literature','Dogri Literature','Gujarati Literature','Hindi Literature','Kannada Literature','Kashmiri Literature','Konkani Literature','Maithili Literature','Malayalam Literature','Manipuri Literature','Marathi Literature','Nepali Literature','Odia Literature','Punjabi Literature','Sanskrit Literature','Santhali Literature','Sindhi Literature','Tamil Literature','Telugu Literature','Urdu Literature','English Literature']

def normalize_question(text:str)->str:
    return re.sub(r'[^a-z0-9\u0900-\u097f]+',' ',(text or '').lower()).strip()

def question_hash(text:str)->str:
    return hashlib.sha256(normalize_question(text).encode('utf-8')).hexdigest()

def save_unique_question(exam,paper,subject,topic,question,subtopic='',difficulty='moderate',source='AI-generated'):
    h=question_hash(question); s=SessionStudy()
    try:
        if s.query(QuestionBank).filter(QuestionBank.normalized_hash==h).first(): return None
        row=QuestionBank(exam=exam,paper=paper,subject=subject,topic=topic,subtopic=subtopic,question=question,normalized_hash=h,difficulty=difficulty,source=source)
        s.add(row);s.commit();s.refresh(row);return row.id
    finally:s.close()
