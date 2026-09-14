import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .study_system import SessionStudy, QuestionBank, QuestionAttempt, question_detail_map, save_question_detail, save_attempt
from .syllabus_catalog import syllabus_for
from .optional_syllabus_registry import optional_topic_is_verified
from .pyq_service import fetch_official_pyq
from .exam_routes import build_exam_router

ADMIN_EMAILS={x.strip().lower() for x in os.getenv('ADMIN_EMAILS','').split(',') if x.strip()}

class QuestionDetailIn(BaseModel):
    question_type:str='mains'
    options:list[str]=[]
    correct_answer:str=''
    explanation:str=''
    marks:int=0
    word_limit:int=0
    model_outline:str=''

class AttemptIn(BaseModel):
    answer:str=''


def _valid_topic(exam:str,paper:str,subject:str,topic:str)->bool:
    key=(exam or '').lower()
    if key in {'prelims','mains'}:
        return any(section.get('paper')==paper and section.get('subject')==subject and topic in section.get('topics',[]) for section in syllabus_for(key))
    if key=='optional':return optional_topic_is_verified(subject,paper,topic)
    return False

def _norm_answer(v:str)->str:return ' '.join((v or '').strip().lower().split())


def build_study_router(current_user):
    router=APIRouter()

    def require_admin(u=Depends(current_user)):
        if not ADMIN_EMAILS or u.email.lower() not in ADMIN_EMAILS:raise HTTPException(status_code=403,detail='Admin access required')
        return u

    @router.get('/admin/status')
    def admin_status(u=Depends(current_user)):return {'is_admin':bool(ADMIN_EMAILS and u.email.lower() in ADMIN_EMAILS)}

    @router.get('/question-bank/topic')
    def topic_questions(exam:str,paper:str,subject:str,topic:str,difficulty:Optional[str]=None,limit:int=100,u=Depends(current_user)):
        if not _valid_topic(exam,paper,subject,topic):raise HTTPException(status_code=404,detail='Topic is not in the loaded verified syllabus')
        s=SessionStudy()
        try:
            q=s.query(QuestionBank).filter(QuestionBank.exam==exam,QuestionBank.paper==paper,QuestionBank.subject==subject,QuestionBank.topic==topic)
            if difficulty:q=q.filter(QuestionBank.difficulty==difficulty)
            rows=q.order_by(QuestionBank.id.asc()).limit(max(1,min(limit,200))).all();details=question_detail_map([r.id for r in rows]);out=[]
            for r in rows:
                d=details.get(r.id,{})
                out.append({'id':r.id,'exam':r.exam,'paper':r.paper,'subject':r.subject,'topic':r.topic,'subtopic':r.subtopic,'question':r.question,'difficulty':r.difficulty,'source':r.source,'created_at':r.created_at.isoformat(),'question_type':d.get('question_type','mains'),'options':d.get('options',[]),'marks':d.get('marks',0),'word_limit':d.get('word_limit',0)})
            return out
        finally:s.close()

    @router.put('/question-bank/{question_id}/detail')
    def put_question_detail(question_id:int,x:QuestionDetailIn,u=Depends(require_admin)):
        if x.question_type=='mcq' and len(x.options)!=4:raise HTTPException(status_code=400,detail='MCQ requires exactly 4 options')
        if not save_question_detail(question_id=question_id,**x.model_dump()):raise HTTPException(status_code=404,detail='Question not found or detail could not be saved')
        return {'ok':True,'question_id':question_id}

    @router.post('/question-bank/{question_id}/attempt')
    def submit_attempt(question_id:int,x:AttemptIn,u=Depends(current_user)):
        s=SessionStudy()
        try:q=s.get(QuestionBank,question_id)
        finally:s.close()
        if not q:raise HTTPException(status_code=404,detail='Question not found')
        d=question_detail_map([question_id]).get(question_id,{})
        qtype=d.get('question_type','mains')
        if qtype=='mcq':
            correct=d.get('correct_answer','')
            if not correct:raise HTTPException(status_code=422,detail='MCQ answer key is not configured')
            result_code=1 if _norm_answer(x.answer)==_norm_answer(correct) else 0
        else:result_code=-1
        attempt_id=save_attempt(u.id,question_id,x.answer,result_code)
        if not attempt_id:raise HTTPException(status_code=500,detail='Attempt could not be saved')
        response={'attempt_id':attempt_id,'question_id':question_id,'result':'correct' if result_code==1 else 'wrong' if result_code==0 else 'ungraded'}
        if qtype=='mcq':response.update({'correct_answer':d.get('correct_answer',''),'explanation':d.get('explanation','')})
        return response

    @router.get('/wrong-questions')
    def wrong_questions(limit:int=100,u=Depends(current_user)):
        s=SessionStudy()
        try:
            attempts=s.query(QuestionAttempt).filter(QuestionAttempt.user_id==u.id).order_by(QuestionAttempt.question_id.asc(),QuestionAttempt.attempted_at.desc(),QuestionAttempt.id.desc()).all()
            latest={}
            for a in attempts:
                if a.question_id not in latest:latest[a.question_id]=a
            wrong_ids=[qid for qid,a in latest.items() if a.result_code==0][:max(1,min(limit,200))]
            rows=s.query(QuestionBank).filter(QuestionBank.id.in_(wrong_ids)).all() if wrong_ids else []
            by_id={r.id:r for r in rows};details=question_detail_map(wrong_ids);out=[]
            for qid in wrong_ids:
                r=by_id.get(qid)
                if not r:continue
                d=details.get(qid,{})
                out.append({'id':r.id,'exam':r.exam,'paper':r.paper,'subject':r.subject,'topic':r.topic,'question':r.question,'difficulty':r.difficulty,'options':d.get('options',[]),'last_answer':latest[qid].answer_text,'attempted_at':latest[qid].attempted_at.isoformat()})
            return out
        finally:s.close()

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

    router.include_router(build_exam_router(current_user))
    return router
