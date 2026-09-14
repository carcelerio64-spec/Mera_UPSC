import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .current_affairs import ingest_daily, list_items
from .official_sources import ingest_official_sources
from .study_system import (
    SessionStudy,
    OPTIONAL_SUBJECTS,
    OptionalSelection,
    ClassNote,
    QuestionBank,
    save_unique_question,
)

ADMIN_EMAILS = {
    x.strip().lower()
    for x in os.getenv('ADMIN_EMAILS', '').split(',')
    if x.strip()
}


class OptionalIn(BaseModel):
    subject: str


class QuestionIn(BaseModel):
    exam: str
    paper: str
    subject: str
    topic: str
    question: str
    subtopic: str = ''
    difficulty: str = 'moderate'
    source: str = 'AI-generated'


class NoteIn(BaseModel):
    exam: str
    paper: str = ''
    subject: str
    topic: str
    subtopic: str = ''
    title: str
    file_type: str
    file_url: str


def build_feature_router(current_user):
    router = APIRouter()

    def require_admin(u=Depends(current_user)):
        if not ADMIN_EMAILS or u.email.lower() not in ADMIN_EMAILS:
            raise HTTPException(status_code=403, detail='Admin access required')
        return u

    @router.get('/current-affairs/date-wise')
    def current_affairs_date_wise(
        subject: Optional[str] = None,
        date: Optional[str] = None,
        limit: int = 50,
        u=Depends(current_user),
    ):
        return list_items(subject=subject, limit=limit, on_date=date)

    @router.post('/admin/current-affairs/update-now')
    def update_current_affairs_now(
        backfill_days: int = 7,
        u=Depends(require_admin),
    ):
        days = max(1, min(backfill_days, 30))
        return {
            'ok': True,
            'backfill_days': days,
            'core': ingest_daily(days),
            'official_sources': ingest_official_sources(),
        }

    @router.get('/optional/subjects')
    def optional_subjects(u=Depends(current_user)):
        return OPTIONAL_SUBJECTS

    @router.get('/optional/selection')
    def get_optional_selection(u=Depends(current_user)):
        s = SessionStudy()
        try:
            row = s.query(OptionalSelection).filter(
                OptionalSelection.user_id == u.id
            ).first()
            return {'subject': row.subject if row else None}
        finally:
            s.close()

    @router.put('/optional/selection')
    def save_optional_selection(x: OptionalIn, u=Depends(current_user)):
        if x.subject not in OPTIONAL_SUBJECTS:
            raise HTTPException(status_code=400, detail='Invalid optional subject')
        s = SessionStudy()
        try:
            row = s.query(OptionalSelection).filter(
                OptionalSelection.user_id == u.id
            ).first()
            if not row:
                row = OptionalSelection(user_id=u.id, subject=x.subject)
                s.add(row)
            row.subject = x.subject
            row.updated_at = datetime.now(timezone.utc)
            s.commit()
            return {'ok': True, 'subject': x.subject}
        finally:
            s.close()

    @router.post('/question-bank')
    def add_question(x: QuestionIn, u=Depends(require_admin)):
        qid = save_unique_question(**x.model_dump())
        if not qid:
            raise HTTPException(status_code=409, detail='Duplicate question blocked')
        return {'ok': True, 'id': qid}

    @router.get('/question-bank/count')
    def question_bank_count(u=Depends(current_user)):
        s = SessionStudy()
        try:
            return {
                'total': s.query(QuestionBank).count(),
                'prelims': s.query(QuestionBank).filter(QuestionBank.exam == 'prelims').count(),
                'mains': s.query(QuestionBank).filter(QuestionBank.exam == 'mains').count(),
                'optional': s.query(QuestionBank).filter(QuestionBank.exam == 'optional').count(),
            }
        finally:
            s.close()

    @router.post('/class-notes')
    def add_class_note(x: NoteIn, u=Depends(current_user)):
        if x.file_type not in {'pdf', 'photo'}:
            raise HTTPException(status_code=400, detail='Only pdf/photo allowed')
        s = SessionStudy()
        try:
            row = ClassNote(user_id=u.id, **x.model_dump())
            s.add(row)
            s.commit()
            s.refresh(row)
            return {'ok': True, 'id': row.id}
        finally:
            s.close()

    @router.get('/class-notes')
    def list_class_notes(
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        u=Depends(current_user),
    ):
        s = SessionStudy()
        try:
            q = s.query(ClassNote).filter(ClassNote.user_id == u.id)
            if subject:
                q = q.filter(ClassNote.subject == subject)
            if topic:
                q = q.filter(ClassNote.topic == topic)
            rows = q.order_by(ClassNote.uploaded_at.desc()).all()
            return [
                {
                    'id': r.id,
                    'exam': r.exam,
                    'paper': r.paper,
                    'subject': r.subject,
                    'topic': r.topic,
                    'subtopic': r.subtopic,
                    'title': r.title,
                    'file_type': r.file_type,
                    'file_url': r.file_url,
                    'uploaded_at': r.uploaded_at.isoformat(),
                }
                for r in rows
            ]
        finally:
            s.close()

    return router
