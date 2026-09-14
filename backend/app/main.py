import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from jose import jwt, JWTError
from passlib.context import CryptContext

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./upsc.db')
SECRET_KEY = os.getenv('JWT_SECRET', 'change-this-in-production')
INGEST_KEY = os.getenv('INGEST_KEY', '')
ALGORITHM = 'HS256'
ACCESS_MINUTES = 60 * 24 * 7

connect_args = {'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    target_year: Mapped[int] = mapped_column(Integer, default=2027)
    language: Mapped[str] = mapped_column(String(20), default='hi')

class Topic(Base):
    __tablename__ = 'topics'
    id: Mapped[int] = mapped_column(primary_key=True)
    exam: Mapped[str] = mapped_column(String(20))
    paper: Mapped[str] = mapped_column(String(60))
    subject: Mapped[str] = mapped_column(String(120))
    title_hi: Mapped[str] = mapped_column(String(200))
    title_en: Mapped[str] = mapped_column(String(200))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

class Progress(Base):
    __tablename__ = 'progress'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey('topics.id'), index=True)
    status: Mapped[str] = mapped_column(String(30), default='not_started')
    percent: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class MockResult(Base):
    __tablename__ = 'mock_results'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    paper: Mapped[str] = mapped_column(String(60))
    total_questions: Mapped[int] = mapped_column(Integer)
    correct: Mapped[int] = mapped_column(Integer)
    wrong: Mapped[int] = mapped_column(Integer)
    unattempted: Mapped[int] = mapped_column(Integer)
    marks_per_question: Mapped[float] = mapped_column(Float)
    negative_fraction: Mapped[float] = mapped_column(Float, default=1 / 3)
    score: Mapped[float] = mapped_column(Float)
    duration_seconds: Mapped[int] = mapped_column(Integer)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

Base.metadata.create_all(engine)

from .current_affairs import ingest_daily, list_items
from .official_sources import ingest_official_sources

pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2 = OAuth2PasswordBearer(tokenUrl='/auth/token')
app = FastAPI(title='UPSC Prep API', version='1.1.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

def db():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()

def token_for(uid: int):
    exp = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_MINUTES)
    return jwt.encode({'sub': str(uid), 'exp': exp}, SECRET_KEY, algorithm=ALGORITHM)

def current_user(tok: str = Depends(oauth2), s: Session = Depends(db)):
    try:
        payload = jwt.decode(tok, SECRET_KEY, algorithms=[ALGORITHM])
        uid = int(payload['sub'])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail='Invalid session')
    u = s.get(User, uid)
    if not u:
        raise HTTPException(status_code=401, detail='User not found')
    return u

class Signup(BaseModel):
    name: str
    email: EmailStr
    password: str
    target_year: int = 2027
    language: str = 'hi'

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    target_year: int
    language: str

class ProgressIn(BaseModel):
    topic_id: int
    status: str
    percent: int

class MockIn(BaseModel):
    paper: str = 'GS Paper-I'
    total_questions: int = 100
    correct: int
    wrong: int
    unattempted: int
    marks_per_question: float = 2.0
    negative_fraction: float = 1 / 3
    duration_seconds: int

@app.on_event('startup')
def seed():
    s = SessionLocal()
    if s.query(Topic).count() == 0:
        data = [
            ('prelims','GS Paper-I','राजव्यवस्था','संविधान की मूल बातें','Constitution Basics'),
            ('prelims','GS Paper-I','राजव्यवस्था','मौलिक अधिकार','Fundamental Rights'),
            ('prelims','GS Paper-I','इतिहास एवं संस्कृति','प्राचीन भारत','Ancient India'),
            ('prelims','GS Paper-I','भूगोल','भारतीय भौतिक भूगोल','Physical Geography of India'),
            ('prelims','GS Paper-I','अर्थव्यवस्था','मुद्रास्फीति','Inflation'),
            ('prelims','GS Paper-I','पर्यावरण','जैव विविधता','Biodiversity'),
            ('prelims','GS Paper-I','विज्ञान एवं प्रौद्योगिकी','अंतरिक्ष एवं प्रौद्योगिकी','Space and Technology'),
            ('prelims','GS Paper-I','कृषि','भारतीय कृषि','Indian Agriculture'),
            ('prelims','GS Paper-I','सामाजिक मुद्दे','स्वास्थ्य एवं शिक्षा','Health and Education'),
            ('prelims','GS Paper-I','अंतरराष्ट्रीय संबंध','अंतरराष्ट्रीय संगठन','International Organisations'),
            ('prelims','CSAT','CSAT','रीडिंग कॉम्प्रिहेंशन','Reading Comprehension'),
            ('mains','GS-I','इतिहास एवं संस्कृति','भारतीय संस्कृति','Indian Culture'),
            ('mains','GS-I','भूगोल','भारतीय एवं विश्व भूगोल','Indian and World Geography'),
            ('mains','GS-I','सामाजिक मुद्दे','भारतीय समाज की विशेषताएँ','Salient Features of Indian Society'),
            ('mains','GS-II','राजव्यवस्था','संघवाद','Federalism'),
            ('mains','GS-II','अंतरराष्ट्रीय संबंध','भारत और विश्व','India and the World'),
            ('mains','GS-III','अर्थव्यवस्था','समावेशी विकास','Inclusive Growth'),
            ('mains','GS-III','कृषि','कृषि एवं खाद्य प्रबंधन','Agriculture and Food Management'),
            ('mains','GS-III','पर्यावरण','पर्यावरण एवं जलवायु परिवर्तन','Environment and Climate Change'),
            ('mains','GS-III','विज्ञान एवं प्रौद्योगिकी','विज्ञान एवं प्रौद्योगिकी','Science and Technology'),
            ('mains','GS-IV','नीतिशास्त्र','ईमानदारी और निष्पक्षता','Integrity and Impartiality'),
            ('mains','Essay','निबंध','समसामयिक एवं दार्शनिक विषय','Contemporary and Philosophical Themes'),
        ]
        for i, (e, p, sub, hi, en) in enumerate(data):
            s.add(Topic(exam=e, paper=p, subject=sub, title_hi=hi, title_en=en, sort_order=i))
        s.commit()
    s.close()

@app.get('/health')
def health():
    return {'ok': True}

@app.post('/auth/signup')
def signup(x: Signup, s: Session = Depends(db)):
    if s.query(User).filter(User.email == x.email).first():
        raise HTTPException(409, 'Email already registered')
    u = User(
        name=x.name,
        email=x.email,
        password_hash=pwd.hash(x.password),
        target_year=x.target_year,
        language=x.language,
    )
    s.add(u)
    s.commit()
    s.refresh(u)
    return {'access_token': token_for(u.id), 'token_type': 'bearer'}

@app.post('/auth/token')
def login(form: OAuth2PasswordRequestForm = Depends(), s: Session = Depends(db)):
    u = s.query(User).filter(User.email == form.username).first()
    if not u or not pwd.verify(form.password, u.password_hash):
        raise HTTPException(401, 'Wrong email or password')
    return {'access_token': token_for(u.id), 'token_type': 'bearer'}

@app.get('/me', response_model=UserOut)
def me(u: User = Depends(current_user)):
    return u

@app.get('/topics')
def topics(exam: Optional[str] = None, u: User = Depends(current_user), s: Session = Depends(db)):
    q = s.query(Topic)
    if exam:
        q = q.filter(Topic.exam == exam)
    rows = q.order_by(Topic.sort_order).all()
    pmap = {p.topic_id: p for p in s.query(Progress).filter(Progress.user_id == u.id).all()}
    return [
        dict(
            id=t.id,
            exam=t.exam,
            paper=t.paper,
            subject=t.subject,
            title_hi=t.title_hi,
            title_en=t.title_en,
            status=pmap.get(t.id).status if t.id in pmap else 'not_started',
            percent=pmap.get(t.id).percent if t.id in pmap else 0,
        )
        for t in rows
    ]

@app.put('/progress')
def save_progress(x: ProgressIn, u: User = Depends(current_user), s: Session = Depends(db)):
    if not s.get(Topic, x.topic_id):
        raise HTTPException(404, 'Topic not found')
    p = s.query(Progress).filter(Progress.user_id == u.id, Progress.topic_id == x.topic_id).first()
    if not p:
        p = Progress(user_id=u.id, topic_id=x.topic_id)
        s.add(p)
    p.status = x.status
    p.percent = max(0, min(100, x.percent))
    p.updated_at = datetime.now(timezone.utc)
    s.commit()
    return {'ok': True}

@app.post('/prelims/mock/submit')
def submit_mock(x: MockIn, u: User = Depends(current_user), s: Session = Depends(db)):
    if x.correct + x.wrong + x.unattempted != x.total_questions:
        raise HTTPException(400, 'Counts must equal total questions')
    score = (x.correct * x.marks_per_question) - (x.wrong * x.marks_per_question * x.negative_fraction)
    r = MockResult(
        user_id=u.id,
        paper=x.paper,
        total_questions=x.total_questions,
        correct=x.correct,
        wrong=x.wrong,
        unattempted=x.unattempted,
        marks_per_question=x.marks_per_question,
        negative_fraction=x.negative_fraction,
        score=round(score, 2),
        duration_seconds=x.duration_seconds,
    )
    s.add(r)
    s.commit()
    s.refresh(r)
    return {
        'id': r.id,
        'score': r.score,
        'max_marks': round(x.total_questions * x.marks_per_question, 2),
        'accuracy': round((x.correct / max(1, x.correct + x.wrong)) * 100, 2),
    }

@app.get('/current-affairs')
def current_affairs(subject: Optional[str] = None, limit: int = 50, u: User = Depends(current_user)):
    return list_items(subject=subject, limit=limit)

@app.post('/admin/current-affairs/ingest')
def run_ingest(x_ingest_key: str = Header(default='')):
    if not INGEST_KEY or x_ingest_key != INGEST_KEY:
        raise HTTPException(status_code=403, detail='Not allowed')
    pib = ingest_daily()
    official = ingest_official_sources()
    return {'ok': True, 'pib_and_core': pib, 'official_sources': official}

@app.get('/dashboard')
def dashboard(u: User = Depends(current_user), s: Session = Depends(db)):
    ps = s.query(Progress).filter(Progress.user_id == u.id).all()
    done = sum(1 for p in ps if p.status == 'completed')
    total = s.query(Topic).count()
    overall = round(done / max(1, total) * 100)
    return {
        'name': u.name,
        'target_year': u.target_year,
        'overall_progress': overall,
        'revision_due': sum(1 for p in ps if p.status == 'revision_due'),
        'today_topics': 3,
        'continue_learning': 'मौलिक अधिकार',
    }
