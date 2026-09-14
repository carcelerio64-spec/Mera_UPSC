from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from .current_affairs import list_items
from .study_system import SessionStudy, ClassNote, QuestionBank
from .syllabus_catalog import syllabus_for
from .optional_syllabus_registry import optional_topic_is_verified


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

    @router.get('/study/topic')
    def topic_study(
        exam:str,
        paper:str,
        subject:str,
        topic:str,
        u=Depends(current_user),
    ):
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
            q=s.query(QuestionBank).filter(
                QuestionBank.exam==exam,
                QuestionBank.paper==paper,
                QuestionBank.subject==subject,
                QuestionBank.topic==topic,
            )
            question_count=q.count()
            return {
                'exam':exam,
                'paper':paper,
                'subject':subject,
                'topic':topic,
                'question_bank_count':question_count,
                'class_notes':[
                    {
                        'id':n.id,
                        'title':n.title,
                        'file_type':n.file_type,
                        'file_url':n.file_url,
                        'uploaded_at':n.uploaded_at.isoformat(),
                    }
                    for n in notes
                ],
                'current_affairs':list_items(subject=subject,limit=10),
            }
        finally:
            s.close()

    return router
