from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from .current_affairs import list_items
from .study_system import SessionStudy, ClassNote, QuestionBank
from .syllabus_catalog import syllabus_for


def _find_topic(exam: str, paper: str, subject: str, topic: str):
    exam_key = (exam or '').lower()
    if exam_key not in {'prelims', 'mains'}:
        return None
    for section in syllabus_for(exam_key):
        if section.get('paper') != paper or section.get('subject') != subject:
            continue
        for item in section.get('topics', []):
            if item == topic:
                return section
    return None


def build_topic_router(current_user):
    router = APIRouter()

    @router.get('/study/topic')
    def topic_study(
        exam: str,
        paper: str,
        subject: str,
        topic: str,
        u=Depends(current_user),
    ):
        section = _find_topic(exam, paper, subject, topic)
        if not section:
            raise HTTPException(status_code=404, detail='Topic is not in the loaded UPSC syllabus')

        s = SessionStudy()
        try:
            notes = s.query(ClassNote).filter(
                ClassNote.user_id == u.id,
                ClassNote.exam == exam.lower(),
                ClassNote.subject == subject,
                ClassNote.topic == topic,
            ).order_by(ClassNote.uploaded_at.desc()).all()
            question_count = s.query(QuestionBank).filter(
                QuestionBank.exam == exam.lower(),
                QuestionBank.paper == paper,
                QuestionBank.subject == subject,
                QuestionBank.topic == topic,
            ).count()
        finally:
            s.close()

        return {
            'exam': exam.lower(),
            'paper': paper,
            'subject': subject,
            'topic': topic,
            'official_syllabus_match': True,
            'class_notes': [
                {
                    'id': n.id,
                    'title': n.title,
                    'file_type': n.file_type,
                    'file_url': n.file_url,
                    'uploaded_at': n.uploaded_at.isoformat(),
                }
                for n in notes
            ],
            'question_bank_count': question_count,
            'current_affairs': list_items(subject=subject, limit=10),
        }

    @router.get('/question-bank/by-topic')
    def questions_by_topic(
        exam: str,
        paper: str,
        subject: str,
        topic: str,
        limit: int = 50,
        u=Depends(current_user),
    ):
        if not _find_topic(exam, paper, subject, topic):
            raise HTTPException(status_code=404, detail='Topic is not in the loaded UPSC syllabus')
        s = SessionStudy()
        try:
            rows = s.query(QuestionBank).filter(
                QuestionBank.exam == exam.lower(),
                QuestionBank.paper == paper,
                QuestionBank.subject == subject,
                QuestionBank.topic == topic,
            ).order_by(QuestionBank.id.desc()).limit(max(1, min(limit, 200))).all()
            return [
                {
                    'id': r.id,
                    'exam': r.exam,
                    'paper': r.paper,
                    'subject': r.subject,
                    'topic': r.topic,
                    'subtopic': r.subtopic,
                    'question': r.question,
                    'difficulty': r.difficulty,
                    'source': r.source,
                }
                for r in rows
            ]
        finally:
            s.close()

    return router
