from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from .study_system import SessionStudy,QuestionBank,QuestionDetail,MainsAnswerSubmission,MainsAnswerEvaluation

class TypedAnswerIn(BaseModel):
    question_id:int
    answer_text:str

def build_mains_answer_router(current_user):
    router=APIRouter()
    def question_meta(s,qid):
        q=s.get(QuestionBank,qid)
        if not q or q.exam not in {'mains','optional'}:raise HTTPException(404,'Mains/Optional question not found')
        d=s.query(QuestionDetail).filter(QuestionDetail.question_id==qid).first()
        marks=d.marks if d and d.marks in {10,15} else 10
        words=d.word_limit if d and d.word_limit else (150 if marks==10 else 250)
        return q,marks,words

    @router.post('/mains/answers/typed')
    def submit_typed(x:TypedAnswerIn,u=Depends(current_user)):
        if not x.answer_text.strip():raise HTTPException(400,'Answer is empty')
        s=SessionStudy()
        try:
            q,marks,words=question_meta(s,x.question_id)
            row=MainsAnswerSubmission(user_id=u.id,question_id=q.id,answer_text=x.answer_text.strip(),status='submitted');s.add(row);s.commit();s.refresh(row)
            return {'submission_id':row.id,'question_id':q.id,'max_marks':marks,'word_limit':words,'status':'submitted'}
        finally:s.close()

    @router.get('/mains/answers')
    def history(u=Depends(current_user)):
        s=SessionStudy()
        try:
            subs=s.query(MainsAnswerSubmission).filter(MainsAnswerSubmission.user_id==u.id).order_by(MainsAnswerSubmission.submitted_at.desc()).limit(200).all();ids=[x.id for x in subs]
            evs={e.submission_id:e for e in s.query(MainsAnswerEvaluation).filter(MainsAnswerEvaluation.submission_id.in_(ids)).all()} if ids else {}
            out=[]
            for sub in subs:
                q,marks,words=question_meta(s,sub.question_id);ev=evs.get(sub.id)
                out.append({'submission_id':sub.id,'question_id':q.id,'question':q.question,'paper':q.paper,'subject':q.subject,'topic':q.topic,'status':sub.status,'max_marks':marks,'word_limit':words,'marks_awarded':ev.marks_awarded if ev else None})
            return out
        finally:s.close()
    return router
