import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from .study_system import SessionStudy, QuestionBank, QuestionAttempt, MainsAnswerSubmission, question_detail_map, save_question_detail, save_attempt
from .syllabus_catalog import syllabus_for
from .optional_syllabus_registry import optional_topic_is_verified
from .pyq_service import fetch_official_pyq
from .exam_routes import build_exam_router

ADMIN_EMAILS={x.strip().lower() for x in os.getenv('ADMIN_EMAILS','').split(',') if x.strip()}
class QuestionDetailIn(BaseModel):
    question_type:str='mains';options:list[str]=Field(default_factory=list);correct_answer:str='';explanation:str='';marks:int=0;word_limit:int=0;model_outline:str=''
class AttemptIn(BaseModel):answer:str=''

def _valid_topic(exam,paper,subject,topic):
    key=(exam or '').lower()
    if key in {'prelims','mains'}:return any(x.get('paper')==paper and x.get('subject')==subject and topic in x.get('topics',[]) for x in syllabus_for(key))
    return key=='optional' and optional_topic_is_verified(subject,paper,topic)
def _norm_answer(v):return ' '.join((v or '').strip().lower().split())

def build_study_router(current_user):
    router=APIRouter()
    def require_admin(u=Depends(current_user)):
        if not ADMIN_EMAILS or u.email.lower() not in ADMIN_EMAILS:raise HTTPException(403,'Admin access required')
        return u
    @router.get('/admin/status')
    def admin_status(u=Depends(current_user)):return {'is_admin':bool(ADMIN_EMAILS and u.email.lower() in ADMIN_EMAILS)}
    @router.get('/question-bank/topic')
    def topic_questions(exam:str,paper:str,subject:str,topic:str,difficulty:Optional[str]=None,limit:int=100,u=Depends(current_user)):
        if not _valid_topic(exam,paper,subject,topic):raise HTTPException(404,'Topic is not in the loaded verified syllabus')
        s=SessionStudy()
        try:
            q=s.query(QuestionBank).filter(QuestionBank.exam==exam,QuestionBank.paper==paper,QuestionBank.subject==subject,QuestionBank.topic==topic)
            if difficulty:q=q.filter(QuestionBank.difficulty==difficulty)
            rows=q.order_by(QuestionBank.id.asc()).limit(max(1,min(limit,200))).all();details=question_detail_map([r.id for r in rows])
            return [{'id':r.id,'exam':r.exam,'paper':r.paper,'subject':r.subject,'topic':r.topic,'subtopic':r.subtopic,'question':r.question,'difficulty':r.difficulty,'source':r.source,'created_at':r.created_at.isoformat(),'question_type':details.get(r.id,{}).get('question_type','mains'),'options':details.get(r.id,{}).get('options',[]),'marks':details.get(r.id,{}).get('marks',0),'word_limit':details.get(r.id,{}).get('word_limit',0)} for r in rows]
        finally:s.close()
    @router.put('/question-bank/{question_id}/detail')
    def put_question_detail(question_id:int,x:QuestionDetailIn,u=Depends(require_admin)):
        if x.question_type=='mcq' and len(x.options)!=4:raise HTTPException(400,'MCQ requires exactly 4 options')
        if not save_question_detail(question_id=question_id,**x.model_dump()):raise HTTPException(404,'Question not found or detail could not be saved')
        return {'ok':True,'question_id':question_id}
    @router.post('/question-bank/{question_id}/attempt')
    def submit_attempt(question_id:int,x:AttemptIn,u=Depends(current_user)):
        s=SessionStudy()
        try:q=s.get(QuestionBank,question_id)
        finally:s.close()
        if not q:raise HTTPException(404,'Question not found')
        d=question_detail_map([question_id]).get(question_id,{});qtype=d.get('question_type','mains')
        if qtype=='mcq':
            correct=d.get('correct_answer','')
            if not correct:raise HTTPException(422,'MCQ answer key is not configured')
            result_code=1 if _norm_answer(x.answer)==_norm_answer(correct) else 0
        else:result_code=-1
        attempt_id=save_attempt(u.id,question_id,x.answer,result_code)
        if not attempt_id:raise HTTPException(500,'Attempt could not be saved')
        out={'attempt_id':attempt_id,'question_id':question_id,'result':'correct' if result_code==1 else 'wrong' if result_code==0 else 'ungraded'}
        if qtype=='mcq':out.update(correct_answer=d.get('correct_answer',''),explanation=d.get('explanation',''))
        return out
    @router.get('/wrong-questions')
    def wrong_questions(limit:int=100,u=Depends(current_user)):
        s=SessionStudy()
        try:
            attempts=s.query(QuestionAttempt).filter(QuestionAttempt.user_id==u.id).order_by(QuestionAttempt.question_id.asc(),QuestionAttempt.attempted_at.desc(),QuestionAttempt.id.desc()).all();latest={}
            for a in attempts:
                if a.question_id not in latest:latest[a.question_id]=a
            ids=[qid for qid,a in latest.items() if a.result_code==0][:max(1,min(limit,200))];rows=s.query(QuestionBank).filter(QuestionBank.id.in_(ids)).all() if ids else [];by={r.id:r for r in rows};details=question_detail_map(ids)
            return [{'id':by[qid].id,'exam':by[qid].exam,'paper':by[qid].paper,'subject':by[qid].subject,'topic':by[qid].topic,'question':by[qid].question,'difficulty':by[qid].difficulty,'options':details.get(qid,{}).get('options',[]),'last_answer':latest[qid].answer_text,'attempted_at':latest[qid].attempted_at.isoformat()} for qid in ids if qid in by]
        finally:s.close()
    @router.get('/question-bank/{question_id}/solution')
    def question_solution(question_id:int,u=Depends(current_user)):
        s=SessionStudy()
        try:
            q=s.get(QuestionBank,question_id)
            if not q:raise HTTPException(404,'Question not found')
            d=question_detail_map([question_id]).get(question_id)
            if not d:return {'question_id':question_id,'available':False}
            protected=(d.get('question_type') or 'mains').lower()!='mcq' and (q.exam or '').lower() in {'mains','optional'}
            if protected:
                uploaded=s.query(MainsAnswerSubmission).filter(MainsAnswerSubmission.user_id==u.id,MainsAnswerSubmission.question_id==question_id,MainsAnswerSubmission.file_url!='',MainsAnswerSubmission.file_type.in_(['pdf','photo'])).order_by(MainsAnswerSubmission.submitted_at.desc()).first()
                if not uploaded:return {'question_id':question_id,'available':False,'model_answer_unlocked':False,'requires_handwritten_upload':True,'detail':'इस प्रश्न का मॉडल उत्तर हस्तलिखित PDF/फोटो उत्तर अपलोड करने के बाद ही खुलेगा।'}
            return {'question_id':question_id,'available':True,'model_answer_unlocked':True,'requires_handwritten_upload':False,'correct_answer':d.get('correct_answer',''),'explanation':d.get('explanation',''),'model_outline':d.get('model_outline',''),'marks':d.get('marks',0),'word_limit':d.get('word_limit',0)}
        finally:s.close()
    @router.get('/pyq')
    def official_pyq(exam:str='mains',year:Optional[int]=None,subject:Optional[str]=None,u=Depends(current_user)):
        exam=exam.lower()
        if exam not in {'prelims','mains'}:raise HTTPException(400,'exam must be prelims or mains')
        if year is not None and (year<2011 or year>2100):raise HTTPException(400,'Invalid year')
        data=fetch_official_pyq(exam=exam,year=year,subject=subject)
        if isinstance(data,dict):data.update({'bank_type':'official_pyq','ai_generated':False,'separate_from_ai_bank':True})
        return data
    # Exam routes live inside the /features namespace through feature_routes.
    # Keep an explicit /exam segment so frontend and backend paths remain stable.
    router.include_router(build_exam_router(current_user),prefix='/exam')
    return router