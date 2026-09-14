import os
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,Header,HTTPException
from pydantic import BaseModel
from .study_system import SessionStudy,QuestionBank,QuestionDetail,MainsAnswerSubmission,MainsAnswerEvaluation

EVALUATION_KEY=os.getenv('EVALUATION_KEY','')

class MarkingIn(BaseModel):
    marks_awarded:float
    demand_score:float=0
    structure_score:float=0
    analysis_score:float=0
    evidence_score:float=0
    presentation_score:float=0
    word_limit_score:float=0
    strengths:str=''
    improvements:str=''
    model_framework:str=''

def build_mains_marking_router(current_user):
    router=APIRouter()

    @router.put('/internal/mains/answers/{submission_id}/evaluation')
    def mark(submission_id:int,x:MarkingIn,x_evaluation_key:str=Header(default='')):
        if not EVALUATION_KEY or x_evaluation_key!=EVALUATION_KEY:raise HTTPException(403,'Evaluator access required')
        s=SessionStudy()
        try:
            sub=s.get(MainsAnswerSubmission,submission_id)
            if not sub:raise HTTPException(404,'Submission not found')
            q=s.get(QuestionBank,sub.question_id)
            if not q:raise HTTPException(404,'Question not found')
            d=s.query(QuestionDetail).filter(QuestionDetail.question_id==sub.question_id).first()
            max_marks=d.marks if d and d.marks in {10,15} else 10
            row=s.query(MainsAnswerEvaluation).filter(MainsAnswerEvaluation.submission_id==sub.id).first()
            if not row:row=MainsAnswerEvaluation(submission_id=sub.id,question_id=sub.question_id,user_id=sub.user_id,max_marks=max_marks);s.add(row)
            row.marks_awarded=max(0,min(max_marks,x.marks_awarded));row.max_marks=max_marks
            row.demand_score=max(0,min(10,x.demand_score));row.structure_score=max(0,min(10,x.structure_score));row.analysis_score=max(0,min(10,x.analysis_score));row.evidence_score=max(0,min(10,x.evidence_score));row.presentation_score=max(0,min(10,x.presentation_score));row.word_limit_score=max(0,min(10,x.word_limit_score));row.strengths=x.strengths;row.improvements=x.improvements;row.model_framework=x.model_framework;row.evaluator='UPSC-pattern AI';row.evaluated_at=datetime.now(timezone.utc);sub.status='evaluated';s.commit()
            return {'submission_id':sub.id,'question_id':q.id,'marks_awarded':row.marks_awarded,'max_marks':max_marks,'label':'UPSC-pattern AI Evaluation','official_upsc_marks':False}
        finally:s.close()

    @router.get('/mains/answers/{submission_id}/evaluation')
    def result(submission_id:int,u=Depends(current_user)):
        s=SessionStudy()
        try:
            sub=s.get(MainsAnswerSubmission,submission_id)
            if not sub or sub.user_id!=u.id:raise HTTPException(404,'Submission not found')
            e=s.query(MainsAnswerEvaluation).filter(MainsAnswerEvaluation.submission_id==submission_id).first()
            if not e:return {'submission_id':submission_id,'status':'pending'}
            return {'submission_id':submission_id,'status':'evaluated','marks_awarded':e.marks_awarded,'max_marks':e.max_marks,'demand_score':e.demand_score,'structure_score':e.structure_score,'analysis_score':e.analysis_score,'evidence_score':e.evidence_score,'presentation_score':e.presentation_score,'word_limit_score':e.word_limit_score,'strengths':e.strengths,'improvements':e.improvements,'model_framework':e.model_framework,'evaluator':e.evaluator,'official_upsc_marks':False}
        finally:s.close()
    return router
