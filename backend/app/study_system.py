import hashlib
import json
import re
from difflib import SequenceMatcher
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import create_engine, String, Integer, DateTime, Text
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
    exam:Mapped[str]=mapped_column(String(30),index=True)
    paper:Mapped[str]=mapped_column(String(80),index=True)
    subject:Mapped[str]=mapped_column(String(160),index=True)
    topic:Mapped[str]=mapped_column(String(240),index=True)
    subtopic:Mapped[str]=mapped_column(String(240),default='')
    question:Mapped[str]=mapped_column(Text)
    normalized_hash:Mapped[str]=mapped_column(String(64),unique=True,index=True)
    difficulty:Mapped[str]=mapped_column(String(30),default='moderate')
    source:Mapped[str]=mapped_column(String(300),default='AI-generated')
    created_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))

class QuestionDetail(StudyBase):
    __tablename__='question_details'
    id:Mapped[int]=mapped_column(primary_key=True)
    question_id:Mapped[int]=mapped_column(Integer,unique=True,index=True)
    question_type:Mapped[str]=mapped_column(String(30),default='mains')
    options_json:Mapped[str]=mapped_column(Text,default='[]')
    correct_answer:Mapped[str]=mapped_column(Text,default='')
    explanation:Mapped[str]=mapped_column(Text,default='')
    marks:Mapped[int]=mapped_column(Integer,default=0)
    word_limit:Mapped[int]=mapped_column(Integer,default=0)
    model_outline:Mapped[str]=mapped_column(Text,default='')
    updated_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))

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
    file_type:Mapped[str]=mapped_column(String(20))
    file_url:Mapped[str]=mapped_column(String(1000))
    uploaded_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))

StudyBase.metadata.create_all(engine)

OPTIONAL_SUBJECTS=['Agriculture','Animal Husbandry & Veterinary Science','Anthropology','Botany','Chemistry','Civil Engineering','Commerce & Accountancy','Economics','Electrical Engineering','Geography','Geology','History','Law','Management','Mathematics','Mechanical Engineering','Medical Science','Philosophy','Physics','Political Science & International Relations','Psychology','Public Administration','Sociology','Statistics','Zoology','Assamese Literature','Bengali Literature','Bodo Literature','Dogri Literature','Gujarati Literature','Hindi Literature','Kannada Literature','Kashmiri Literature','Konkani Literature','Maithili Literature','Malayalam Literature','Manipuri Literature','Marathi Literature','Nepali Literature','Odia Literature','Punjabi Literature','Sanskrit Literature','Santhali Literature','Sindhi Literature','Tamil Literature','Telugu Literature','Urdu Literature','English Literature']

def normalize_question(text:str)->str:
    text=(text or '').lower().replace('।',' ')
    text=re.sub(r'\b(question|प्रश्न|q)\s*\d*\b',' ',text)
    return re.sub(r'[^a-z0-9\u0900-\u097f]+',' ',text).strip()

def question_hash(text:str)->str:
    return hashlib.sha256(normalize_question(text).encode('utf-8')).hexdigest()

def _token_set(text:str):
    return {x for x in normalize_question(text).split() if len(x)>1}

def _near_duplicate(a:str,b:str)->bool:
    na,nb=normalize_question(a),normalize_question(b)
    if not na or not nb:return False
    if SequenceMatcher(None,na,nb).ratio()>=0.90:return True
    ta,tb=_token_set(na),_token_set(nb)
    if ta and tb:
        j=len(ta & tb)/max(1,len(ta | tb))
        containment=len(ta & tb)/max(1,min(len(ta),len(tb)))
        if j>=0.82 or (containment>=0.90 and SequenceMatcher(None,na,nb).ratio()>=0.78):return True
    return False

def find_duplicate_question(question:str,exam:str=None):
    h=question_hash(question);s=SessionStudy()
    try:
        exact=s.query(QuestionBank).filter(QuestionBank.normalized_hash==h).first()
        if exact:return {'id':exact.id,'type':'exact'}
        q=s.query(QuestionBank)
        if exam:q=q.filter(QuestionBank.exam==exam)
        for row in q.yield_per(500):
            if _near_duplicate(question,row.question):return {'id':row.id,'type':'near'}
        return None
    finally:s.close()

def save_unique_question(exam,paper,subject,topic,question,subtopic='',difficulty='moderate',source='AI-generated'):
    dup=find_duplicate_question(question,exam)
    if dup:return None
    h=question_hash(question);s=SessionStudy()
    try:
        row=QuestionBank(exam=exam,paper=paper,subject=subject,topic=topic,subtopic=subtopic,question=question,normalized_hash=h,difficulty=difficulty,source=source)
        s.add(row);s.commit();s.refresh(row);return row.id
    except Exception:
        s.rollback();return None
    finally:s.close()

def save_question_detail(question_id:int,question_type:str='mains',options=None,correct_answer:str='',explanation:str='',marks:int=0,word_limit:int=0,model_outline:str=''):
    s=SessionStudy()
    try:
        if not s.get(QuestionBank,question_id):return False
        row=s.query(QuestionDetail).filter(QuestionDetail.question_id==question_id).first()
        if not row:
            row=QuestionDetail(question_id=question_id);s.add(row)
        row.question_type=question_type
        row.options_json=json.dumps(options or [],ensure_ascii=False)
        row.correct_answer=correct_answer or ''
        row.explanation=explanation or ''
        row.marks=max(0,int(marks or 0))
        row.word_limit=max(0,int(word_limit or 0))
        row.model_outline=model_outline or ''
        row.updated_at=datetime.now(timezone.utc)
        s.commit();return True
    except Exception:
        s.rollback();return False
    finally:s.close()

def question_detail_map(question_ids):
    ids=[int(x) for x in question_ids if x is not None]
    if not ids:return {}
    s=SessionStudy()
    try:
        out={}
        for r in s.query(QuestionDetail).filter(QuestionDetail.question_id.in_(ids)).all():
            try:options=json.loads(r.options_json or '[]')
            except Exception:options=[]
            out[r.question_id]={
                'question_type':r.question_type,'options':options,'correct_answer':r.correct_answer,
                'explanation':r.explanation,'marks':r.marks,'word_limit':r.word_limit,'model_outline':r.model_outline,
            }
        return out
    finally:s.close()
