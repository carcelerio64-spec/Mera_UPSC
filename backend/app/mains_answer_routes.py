import os
import re
import uuid
from pathlib import Path

from fastapi import APIRouter,Depends,File,Form,HTTPException,UploadFile
from pydantic import BaseModel
from .study_system import SessionStudy,QuestionBank,QuestionDetail,MainsAnswerSubmission,MainsAnswerEvaluation

UPLOAD_DIR=Path(os.getenv('UPLOAD_DIR','./uploads'))
UPLOAD_DIR.mkdir(parents=True,exist_ok=True)
MAX_ANSWER_BYTES=25*1024*1024
ALLOWED_EXTENSIONS={'.pdf','.jpg','.jpeg','.png','.webp','.heic','.heif'}

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
            return {'submission_id':row.id,'question_id':q.id,'max_marks':marks,'word_limit':words,'status':'submitted','evaluation_status':'pending'}
        finally:s.close()

    @router.post('/mains/answers/upload')
    async def submit_file(question_id:int=Form(...),file:UploadFile=File(...),u=Depends(current_user)):
        ext=Path(file.filename or '').suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:raise HTTPException(400,'Only PDF or photo answer uploads are allowed')
        data=await file.read(MAX_ANSWER_BYTES+1);await file.close()
        if not data:raise HTTPException(400,'Uploaded answer is empty')
        if len(data)>MAX_ANSWER_BYTES:raise HTTPException(413,'Answer file exceeds 25 MB')
        s=SessionStudy()
        try:q,marks,words=question_meta(s,question_id)
        finally:s.close()
        safe=re.sub(r'[^a-zA-Z0-9_-]+','-',Path(file.filename or 'answer').stem).strip('-')[:50] or 'answer'
        stored=f'u{u.id}_answer_{uuid.uuid4().hex}_{safe}{ext}'
        path=UPLOAD_DIR/stored
        path.write_bytes(data)
        s=SessionStudy()
        try:
            row=MainsAnswerSubmission(user_id=u.id,question_id=q.id,file_type='pdf' if ext=='.pdf' else 'photo',file_url=f'/uploads/{stored}',status='submitted');s.add(row);s.commit();s.refresh(row)
            return {'submission_id':row.id,'question_id':q.id,'max_marks':marks,'word_limit':words,'file_type':row.file_type,'file_url':row.file_url,'status':'submitted','evaluation_status':'pending'}
        except Exception:
            s.rollback();path.unlink(missing_ok=True);raise
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
                out.append({'submission_id':sub.id,'question_id':q.id,'question':q.question,'paper':q.paper,'subject':q.subject,'topic':q.topic,'status':sub.status,'max_marks':marks,'word_limit':words,'file_type':sub.file_type,'file_url':sub.file_url,'has_typed_answer':bool(sub.answer_text),'marks_awarded':ev.marks_awarded if ev else None,'evaluation_status':'evaluated' if ev else 'pending'})
            return out
        finally:s.close()
    return router
