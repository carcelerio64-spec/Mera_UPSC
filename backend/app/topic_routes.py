from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .current_affairs import list_items
from .study_system import SessionStudy, ClassNote, QuestionBank, CompletedTopic
from .syllabus_catalog import syllabus_for

PRELIMS_TARGET=100
MAINS_TARGET=50

class TopicCompletionIn(BaseModel):
    exam:str
    paper:str
    subject:str
    topic:str
    completed:bool=True


def _find_topic(exam: str, paper: str, subject: str, topic: str):
    exam_key=(exam or '').lower()
    if exam_key not in {'prelims','mains'}:
        return None
    for section in syllabus_for(exam_key):
        if section.get('paper')!=paper or section.get('subject')!=subject:
            continue
        if topic in section.get('topics',[]):
            return section
    return None


def _is_completed(s,user_id:int,exam:str,paper:str,subject:str,topic:str)->bool:
    return s.query(CompletedTopic).filter(
        CompletedTopic.user_id==user_id,
        CompletedTopic.exam==exam.lower(),
        CompletedTopic.paper==paper,
        CompletedTopic.subject==subject,
        CompletedTopic.topic==topic,
    ).first() is not None


def _target(exam:str)->int:
    return PRELIMS_TARGET if exam.lower()=='prelims' else MAINS_TARGET


def build_topic_router(current_user):
    router=APIRouter()

    @router.put('/study/topic/completion')
    def set_topic_completion(x:TopicCompletionIn,u=Depends(current_user)):
        exam=x.exam.lower()
        if not _find_topic(exam,x.paper,x.subject,x.topic):
            raise HTTPException(status_code=404,detail='Topic is not in the loaded UPSC syllabus')
        s=SessionStudy()
        try:
            row=s.query(CompletedTopic).filter(
                CompletedTopic.user_id==u.id,
                CompletedTopic.exam==exam,
                CompletedTopic.paper==x.paper,
                CompletedTopic.subject==x.subject,
                CompletedTopic.topic==x.topic,
            ).first()
            if x.completed:
                if not row:
                    row=CompletedTopic(user_id=u.id,exam=exam,paper=x.paper,subject=x.subject,topic=x.topic,completed_at=datetime.now(timezone.utc))
                    s.add(row)
                else:
                    row.completed_at=datetime.now(timezone.utc)
            elif row:
                s.delete(row)
            s.commit()
            count=s.query(QuestionBank).filter(
                QuestionBank.exam==exam,
                QuestionBank.paper==x.paper,
                QuestionBank.subject==x.subject,
                QuestionBank.topic==x.topic,
            ).count()
            target=_target(exam)
            return {
                'ok':True,
                'completed':x.completed,
                'exam':exam,
                'paper':x.paper,
                'subject':x.subject,
                'topic':x.topic,
                'question_target':target,
                'saved_questions':count,
                'generation_needed':max(0,target-count) if x.completed else 0,
                'section_key':f'{exam}|{x.paper}|{x.subject}|{x.topic}',
            }
        finally:
            s.close()

    @router.get('/study/question-sections')
    def completed_topic_question_sections(exam:str,u=Depends(current_user)):
        exam=exam.lower()
        if exam not in {'prelims','mains'}:
            raise HTTPException(status_code=400,detail='exam must be prelims or mains')
        s=SessionStudy()
        try:
            completed=s.query(CompletedTopic).filter(
                CompletedTopic.user_id==u.id,
                CompletedTopic.exam==exam,
            ).order_by(CompletedTopic.paper,CompletedTopic.subject,CompletedTopic.completed_at).all()
            target=_target(exam)
            sections=[]
            for c in completed:
                count=s.query(QuestionBank).filter(
                    QuestionBank.exam==exam,
                    QuestionBank.paper==c.paper,
                    QuestionBank.subject==c.subject,
                    QuestionBank.topic==c.topic,
                ).count()
                sections.append({
                    'section_key':f'{exam}|{c.paper}|{c.subject}|{c.topic}',
                    'exam':exam,
                    'paper':c.paper,
                    'subject':c.subject,
                    'topic':c.topic,
                    'completed_at':c.completed_at.isoformat(),
                    'question_target':target,
                    'saved_questions':count,
                    'generation_needed':max(0,target-count),
                    'ready':count>=target,
                })
            return {'exam':exam,'target_per_topic':target,'sections':sections}
        finally:
            s.close()

    @router.get('/study/topic')
    def topic_study(exam:str,paper:str,subject:str,topic:str,u=Depends(current_user)):
        exam=exam.lower()
        if not _find_topic(exam,paper,subject,topic):
            raise HTTPException(status_code=404,detail='Topic is not in the loaded UPSC syllabus')
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
            completed=_is_completed(s,u.id,exam,paper,subject,topic)
            target=_target(exam)
            return {
                'exam':exam,
                'paper':paper,
                'subject':subject,
                'topic':topic,
                'official_syllabus_match':True,
                'completed':completed,
                'question_section_unlocked':completed,
                'question_target':target,
                'question_bank_count':question_count,
                'generation_needed':max(0,target-question_count) if completed else 0,
                'class_notes':[{
                    'id':n.id,'title':n.title,'file_type':n.file_type,'file_url':n.file_url,'uploaded_at':n.uploaded_at.isoformat()
                } for n in notes],
                'current_affairs':list_items(subject=subject,limit=10),
            }
        finally:
            s.close()

    @router.get('/question-bank/by-topic')
    def questions_by_topic(exam:str,paper:str,subject:str,topic:str,limit:int=100,u=Depends(current_user)):
        exam=exam.lower()
        if not _find_topic(exam,paper,subject,topic):
            raise HTTPException(status_code=404,detail='Topic is not in the loaded UPSC syllabus')
        s=SessionStudy()
        try:
            if not _is_completed(s,u.id,exam,paper,subject,topic):
                raise HTTPException(status_code=403,detail='Complete this topic first. Its separate question section unlocks after completion.')
            rows=s.query(QuestionBank).filter(
                QuestionBank.exam==exam,
                QuestionBank.paper==paper,
                QuestionBank.subject==subject,
                QuestionBank.topic==topic,
            ).order_by(QuestionBank.id.asc()).limit(max(1,min(limit,_target(exam)))).all()
            return {
                'section_key':f'{exam}|{paper}|{subject}|{topic}',
                'exam':exam,
                'paper':paper,
                'subject':subject,
                'topic':topic,
                'target':_target(exam),
                'questions':[{
                    'id':r.id,'subtopic':r.subtopic,'question':r.question,'difficulty':r.difficulty,'source':r.source
                } for r in rows],
            }
        finally:
            s.close()

    return router
