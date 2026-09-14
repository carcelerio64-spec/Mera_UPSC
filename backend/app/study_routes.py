import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .current_affairs import list_items
from .study_system import SessionStudy, ClassNote, QuestionBank, question_detail_map, save_question_detail
from .syllabus_catalog import syllabus_for
from .optional_syllabus_registry import optional_topic_is_verified
from .pyq_service import fetch_official_pyq

ADMIN_EMAILS={x.strip().lower() for x in os.getenv('ADMIN_EMAILS','').split(',') if x.strip()}
CA_SUBJECT_MAP={
    'Current Affairs':'समसामयिकी','History & Culture':'इतिहास एवं संस्कृति','Indian Heritage & Culture':'इतिहास एवं संस्कृति',
    'Modern Indian History':'इतिहास एवं संस्कृति','World History':'इतिहास एवं संस्कृति','Geography':'भूगोल',
    'Polity & Governance':'राजव्यवस्था','Constitution & Polity':'राजव्यवस्था','Governance & Social Justice':'सामाजिक मुद्दे',
    'Economy & Social Development':'अर्थव्यवस्था','Economy':'अर्थव्यवस्था','Environment':'पर्यावरण',
    'Environment & Disaster Management':'पर्यावरण','General Science':'विज्ञान एवं प्रौद्योगिकी','Science & Technology':'विज्ञान एवं प्रौद्योगिकी',
    'International Relations':'अंतरराष्ट्रीय संबंध','Indian Society':'सामाजिक मुद्दे','Internal Security':'आंतरिक सुरक्षा',
}

class QuestionDetailIn(BaseModel):
    question_type:str='mains'
    options:list[str]=[]
    correct_answer:str=''
    explanation:str=''
    marks:int=0
    word_limit:int=0
    model_outline:str=''


def _valid_topic(exam:str,paper:str,subject:str,topic:str)->bool:
    key=(exam or '').lower()
    if key in {'prelims','mains'}:
        return any(section.get('paper')==paper and section.get('subject')==subject and topic in section.get('topics',[]) for section in syllabus_for(key))
    if key=='optional':return optional_topic_is_verified(subject,paper,topic)
    return False


def build_study_router(current_user):
    router=APIRouter()

    def require_admin(u=Depends(current_user)):
        if not ADMIN_EMAILS or u.email.lower() not in ADMIN_EMAILS:
            raise HTTPException(status_code=403,detail='Admin access required')
        return u

    @router.get('/admin/status')
    def admin_status(u=Depends(current_user)):
        return {'is_admin':bool(ADMIN_EMAILS and u.email.lower() in ADMIN_EMAILS)}

    @router.get('/study/topic')
    def topic_study(exam:str,paper:str,subject:str,topic:str,u=Depends(current_user)):
        if not _valid_topic(exam,paper,subject,topic):raise HTTPException(status_code=404,detail='Topic is not in the loaded verified syllabus')
        s=SessionStudy()
        try:
            notes=s.query(ClassNote).filter(ClassNote.user_id==u.id,ClassNote.exam==exam,ClassNote.subject==subject,ClassNote.topic==topic).order_by(ClassNote.uploaded_at.desc()).all()
            question_count=s.query(QuestionBank).filter(QuestionBank.exam==exam,QuestionBank.paper==paper,QuestionBank.subject==subject,QuestionBank.topic==topic).count()
            ca_subject=CA_SUBJECT_MAP.get(subject,subject)
            return {'exam':exam,'paper':paper,'subject':subject,'topic':topic,'official_syllabus_match':True,'question_bank_count':question_count,
                'class_notes':[{'id':n.id,'exam':n.exam,'paper':n.paper,'subject':n.subject,'topic':n.topic,'subtopic':n.subtopic,'title':n.title,'file_type':n.file_type,'file_url':n.file_url,'uploaded_at':n.uploaded_at.isoformat()} for n in notes],
                'current_affairs':list_items(subject=ca_subject,limit=10)}
        finally:s.close()

    @router.get('/question-bank/topic')
    def topic_questions(exam:str,paper:str,subject:str,topic:str,difficulty:Optional[str]=None,limit:int=100,u=Depends(current_user)):
        if not _valid_topic(exam,paper,subject,topic):raise HTTPException(status_code=404,detail='Topic is not in the loaded verified syllabus')
        s=SessionStudy()
        try:
            q=s.query(QuestionBank).filter(QuestionBank.exam==exam,QuestionBank.paper==paper,QuestionBank.subject==subject,QuestionBank.topic==topic)
            if difficulty:q=q.filter(QuestionBank.difficulty==difficulty)
            rows=q.order_by(QuestionBank.id.asc()).limit(max(1,min(limit,200))).all();details=question_detail_map([r.id for r in rows])
            out=[]
            for r in rows:
                d=details.get(r.id,{})
                out.append({'id':r.id,'exam':r.exam,'paper':r.paper,'subject':r.subject,'topic':r.topic,'subtopic':r.subtopic,'question':r.question,'difficulty':r.difficulty,'source':r.source,'created_at':r.created_at.isoformat(),
                    'question_type':d.get('question_type','mains'),'options':d.get('options',[]),'marks':d.get('marks',0),'word_limit':d.get('word_limit',0)})
            return out
        finally:s.close()

    @router.put('/question-bank/{question_id}/detail')
    def put_question_detail(question_id:int,x:QuestionDetailIn,u=Depends(require_admin)):
        if x.question_type=='mcq' and len(x.options)!=4:raise HTTPException(status_code=400,detail='MCQ requires exactly 4 options')
        if not save_question_detail(question_id=question_id,**x.model_dump()):raise HTTPException(status_code=404,detail='Question not found or detail could not be saved')
        return {'ok':True,'question_id':question_id}

    @router.get('/question-bank/{question_id}/solution')
    def question_solution(question_id:int,u=Depends(current_user)):
        s=SessionStudy()
        try:
            if not s.get(QuestionBank,question_id):raise HTTPException(status_code=404,detail='Question not found')
        finally:s.close()
        d=question_detail_map([question_id]).get(question_id)
        if not d:return {'question_id':question_id,'available':False}
        return {'question_id':question_id,'available':True,'correct_answer':d.get('correct_answer',''),'explanation':d.get('explanation',''),'model_outline':d.get('model_outline',''),'marks':d.get('marks',0),'word_limit':d.get('word_limit',0)}

    @router.get('/pyq')
    def official_pyq(exam:str='mains',year:int=2026,subject:Optional[str]=None,u=Depends(current_user)):
        if exam not in {'prelims','mains'}:raise HTTPException(status_code=400,detail='exam must be prelims or mains')
        if year<2011 or year>2100:raise HTTPException(status_code=400,detail='Invalid year')
        return fetch_official_pyq(exam=exam,year=year,subject=subject)

    return router
