import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .current_affairs import ingest_daily, list_items
from .official_sources import ingest_official_sources
from .study_system import SessionStudy, OPTIONAL_SUBJECTS, OptionalSelection, ClassNote, QuestionBank, save_unique_question
from .syllabus_catalog import syllabus_for

ADMIN_EMAILS={x.strip().lower() for x in os.getenv('ADMIN_EMAILS','').split(',') if x.strip()}
UPLOAD_DIR=Path(os.getenv('UPLOAD_DIR','./uploads'))
UPLOAD_DIR.mkdir(parents=True,exist_ok=True)
MAX_UPLOAD_BYTES=20*1024*1024
ALLOWED_EXTENSIONS={'.pdf','.jpg','.jpeg','.png','.webp','.heic','.heif'}

class OptionalIn(BaseModel):
    subject:str
class QuestionIn(BaseModel):
    exam:str; paper:str; subject:str; topic:str; question:str; subtopic:str=''; difficulty:str='moderate'; source:str='AI-generated'
class NoteIn(BaseModel):
    exam:str; paper:str=''; subject:str; topic:str; subtopic:str=''; title:str; file_type:str; file_url:str

def build_feature_router(current_user):
    router=APIRouter()

    def require_admin(u=Depends(current_user)):
        if not ADMIN_EMAILS or u.email.lower() not in ADMIN_EMAILS:
            raise HTTPException(status_code=403,detail='Admin access required')
        return u

    @router.get('/syllabus')
    def get_syllabus(exam:Optional[str]=None,u=Depends(current_user)):
        return syllabus_for(exam or 'all')

    @router.get('/syllabus/{exam}')
    def get_exam_syllabus(exam:str,u=Depends(current_user)):
        if exam.lower() not in {'prelims','mains','optional'}:
            raise HTTPException(status_code=404,detail='Unknown exam section')
        return syllabus_for(exam)

    @router.get('/current-affairs/date-wise')
    def current_affairs_date_wise(subject:Optional[str]=None,date:Optional[str]=None,limit:int=50,u=Depends(current_user)):
        return list_items(subject=subject,limit=limit,on_date=date)

    @router.post('/admin/current-affairs/update-now')
    def update_current_affairs_now(backfill_days:int=7,u=Depends(require_admin)):
        days=max(1,min(backfill_days,30))
        return {'ok':True,'backfill_days':days,'core':ingest_daily(days),'official_sources':ingest_official_sources()}

    @router.get('/optional/subjects')
    def optional_subjects(u=Depends(current_user)):
        return OPTIONAL_SUBJECTS

    @router.get('/optional/selection')
    def get_optional_selection(u=Depends(current_user)):
        s=SessionStudy()
        try:
            row=s.query(OptionalSelection).filter(OptionalSelection.user_id==u.id).first()
            return {'subject':row.subject if row else None}
        finally:s.close()

    @router.put('/optional/selection')
    def save_optional_selection(x:OptionalIn,u=Depends(current_user)):
        if x.subject not in OPTIONAL_SUBJECTS: raise HTTPException(status_code=400,detail='Invalid optional subject')
        s=SessionStudy()
        try:
            row=s.query(OptionalSelection).filter(OptionalSelection.user_id==u.id).first()
            if not row:
                row=OptionalSelection(user_id=u.id,subject=x.subject);s.add(row)
            row.subject=x.subject;row.updated_at=datetime.now(timezone.utc);s.commit()
            return {'ok':True,'subject':x.subject}
        finally:s.close()

    @router.post('/question-bank')
    def add_question(x:QuestionIn,u=Depends(require_admin)):
        qid=save_unique_question(**x.model_dump())
        if not qid: raise HTTPException(status_code=409,detail='Duplicate or near-duplicate question blocked')
        return {'ok':True,'id':qid}

    @router.get('/question-bank/count')
    def question_bank_count(u=Depends(current_user)):
        s=SessionStudy()
        try:
            return {'total':s.query(QuestionBank).count(),'prelims':s.query(QuestionBank).filter(QuestionBank.exam=='prelims').count(),'mains':s.query(QuestionBank).filter(QuestionBank.exam=='mains').count(),'optional':s.query(QuestionBank).filter(QuestionBank.exam=='optional').count()}
        finally:s.close()

    @router.post('/uploads/class-note')
    async def upload_class_note(file:UploadFile=File(...),exam:str=Form(...),subject:str=Form(...),topic:str=Form(...),title:str=Form(...),paper:str=Form(''),subtopic:str=Form(''),u=Depends(current_user)):
        ext=Path(file.filename or '').suffix.lower()
        if ext not in ALLOWED_EXTENSIONS: raise HTTPException(status_code=400,detail='Only PDF/JPG/JPEG/PNG/WEBP/HEIC allowed')
        data=await file.read(MAX_UPLOAD_BYTES+1)
        await file.close()
        if len(data)>MAX_UPLOAD_BYTES: raise HTTPException(status_code=413,detail='File too large. Maximum 20 MB')
        safe_base=re.sub(r'[^a-zA-Z0-9_-]+','-',Path(file.filename or 'note').stem).strip('-')[:60] or 'note'
        stored=f'u{u.id}_{uuid.uuid4().hex}_{safe_base}{ext}'
        (UPLOAD_DIR/stored).write_bytes(data)
        file_type='pdf' if ext=='.pdf' else 'photo'
        file_url=f'/uploads/{stored}'
        s=SessionStudy()
        try:
            row=ClassNote(user_id=u.id,exam=exam,paper=paper,subject=subject,topic=topic,subtopic=subtopic,title=title,file_type=file_type,file_url=file_url)
            s.add(row);s.commit();s.refresh(row)
            return {'ok':True,'id':row.id,'file_type':file_type,'file_url':file_url}
        except Exception:
            s.rollback();(UPLOAD_DIR/stored).unlink(missing_ok=True);raise
        finally:s.close()

    @router.get('/uploads/{stored_name}')
    def get_uploaded_file(stored_name:str,u=Depends(current_user)):
        if '/' in stored_name or '\\' in stored_name or '..' in stored_name: raise HTTPException(status_code=400,detail='Invalid file name')
        prefix=f'u{u.id}_'
        if not stored_name.startswith(prefix): raise HTTPException(status_code=403,detail='Not allowed')
        path=UPLOAD_DIR/stored_name
        if not path.exists(): raise HTTPException(status_code=404,detail='File not found')
        return FileResponse(path)

    @router.post('/class-notes')
    def add_class_note(x:NoteIn,u=Depends(current_user)):
        if x.file_type not in {'pdf','photo'}: raise HTTPException(status_code=400,detail='Only pdf/photo allowed')
        s=SessionStudy()
        try:
            row=ClassNote(user_id=u.id,**x.model_dump());s.add(row);s.commit();s.refresh(row);return {'ok':True,'id':row.id}
        finally:s.close()

    @router.get('/class-notes')
    def list_class_notes(subject:Optional[str]=None,topic:Optional[str]=None,u=Depends(current_user)):
        s=SessionStudy()
        try:
            q=s.query(ClassNote).filter(ClassNote.user_id==u.id)
            if subject:q=q.filter(ClassNote.subject==subject)
            if topic:q=q.filter(ClassNote.topic==topic)
            rows=q.order_by(ClassNote.uploaded_at.desc()).all()
            return [{'id':r.id,'exam':r.exam,'paper':r.paper,'subject':r.subject,'topic':r.topic,'subtopic':r.subtopic,'title':r.title,'file_type':r.file_type,'file_url':r.file_url,'uploaded_at':r.uploaded_at.isoformat()} for r in rows]
        finally:s.close()

    return router
