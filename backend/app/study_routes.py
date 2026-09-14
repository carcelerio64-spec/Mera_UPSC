import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from .current_affairs import list_items
from .study_system import SessionStudy, ClassNote, QuestionBank
from .syllabus_catalog import syllabus_for
from .optional_syllabus_registry import optional_topic_is_verified
from .pyq_service import fetch_official_pyq

ADMIN_EMAILS={x.strip().lower() for x in os.getenv('ADMIN_EMAILS','').split(',') if x.strip()}
CA_SUBJECT_MAP={
    'Current Affairs':'समसामयिकी',
    'History & Culture':'इतिहास एवं संस्कृति',
    'Indian Heritage & Culture':'इतिहास एवं संस्कृति',
    'Modern Indian History':'इतिहास एवं संस्कृति',
    'World History':'इतिहास एवं संस्कृति',
    'Geography':'भूगोल',
    'Polity & Governance':'राजव्यवस्था',
    'Constitution & Polity':'राजव्यवस्था',
    'Governance & Social Justice':'सामाजिक मुद्दे',
    'Economy & Social Development':'अर्थव्यवस्था',
    'Economy':'अर्थव्यवस्था',
    'Environment':'पर्यावरण',
    'Environment & Disaster Management':'पर्यावरण',
    'General Science':'विज्ञान एवं प्रौद्योगिकी',
    'Science & Technology':'विज्ञान एवं प्रौद्योगिकी',
    'International Relations':'अंतरराष्ट्रीय संबंध',
    'Indian Society':'सामाजिक मुद्दे',
    'Internal Security':'आंतरिक सुरक्षा',
}


def _valid_topic(exam: str, paper: str, subject: str, topic: str) -> bool:
    key=(exam or '').lower()
    if key in {'prelims','mains'}:
        for section in syllabus_for(key):
            if section.get('paper')==paper and section.get('subject')==subject and topic in section.get('topics',[]):
                return True
        return False
    if key=='optional':
        return optional_topic_is_verified(subject,paper,topic)
    return False


def build_study_router(current_user):
    router=APIRouter()

    @router.get('/admin/status')
    def admin_status(u=Depends(current_user)):
        return {'is_admin':bool(ADMIN_EMAILS and u.email.lower() in ADMIN_EMAILS)}

    @router.get('/study/topic')
    def topic_study(exam:str,paper:str,subject:str,topic:str,u=Depends(current_user)):
        if not _valid_topic(exam,paper,subject,topic):
            raise HTTPException(status_code=404,detail='Topic is not in the loaded verified syllabus')
        s=SessionStudy()
        try:
            notes=s.query(ClassNote).filter(
                ClassNote.user_id==u.id,
                ClassNote.exam==exam,
                ClassNote.subject==subject,
                ClassNote.topic==topic,
            ).order_by(ClassNote.uploaded_at.desc()).all()
            question_count=s.query(QuestionBank).filter(
                QuestionBank.exam==exam,
                QuestionBank.paper==paper,
                QuestionBank.subject==subject,
                QuestionBank.topic==topic,
            ).count()
            ca_subject=CA_SUBJECT_MAP.get(subject,subject)
            return {
                'exam':exam,
                'paper':paper,
                'subject':subject,
                'topic':topic,
                'official_syllabus_match':True,
                'question_bank_count':question_count,
                'class_notes':[
                    {
                        'id':n.id,
                        'exam':n.exam,
                        'paper':n.paper,
                        'subject':n.subject,
                        'topic':n.topic,
                        'subtopic':n.subtopic,
                        'title':n.title,
                        'file_type':n.file_type,
                        'file_url':n.file_url,
                        'uploaded_at':n.uploaded_at.isoformat(),
                    }
                    for n in notes
                ],
                'current_affairs':list_items(subject=ca_subject,limit=10),
            }
        finally:
            s.close()

    @router.get('/question-bank/topic')
    def topic_questions(
        exam:str,
        paper:str,
        subject:str,
        topic:str,
        difficulty:Optional[str]=None,
        limit:int=100,
        u=Depends(current_user),
    ):
        if not _valid_topic(exam,paper,subject,topic):
            raise HTTPException(status_code=404,detail='Topic is not in the loaded verified syllabus')
        s=SessionStudy()
        try:
            q=s.query(QuestionBank).filter(
                QuestionBank.exam==exam,
                QuestionBank.paper==paper,
                QuestionBank.subject==subject,
                QuestionBank.topic==topic,
            )
            if difficulty:
                q=q.filter(QuestionBank.difficulty==difficulty)
            rows=q.order_by(QuestionBank.id.asc()).limit(max(1,min(limit,200))).all()
            return [
                {
                    'id':r.id,
                    'exam':r.exam,
                    'paper':r.paper,
                    'subject':r.subject,
                    'topic':r.topic,
                    'subtopic':r.subtopic,
                    'question':r.question,
                    'difficulty':r.difficulty,
                    'source':r.source,
                    'created_at':r.created_at.isoformat(),
                }
                for r in rows
            ]
        finally:
            s.close()

    @router.get('/pyq')
    def official_pyq(exam:str='mains',year:int=2026,subject:Optional[str]=None,u=Depends(current_user)):
        if exam not in {'prelims','mains'}:
            raise HTTPException(status_code=400,detail='exam must be prelims or mains')
        if year<2011 or year>2100:
            raise HTTPException(status_code=400,detail='Invalid year')
        return fetch_official_pyq(exam=exam,year=year,subject=subject)

    return router
