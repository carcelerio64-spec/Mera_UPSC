import os,re,uuid
from datetime import datetime,timezone
from pathlib import Path
from typing import Optional
from fastapi import APIRouter,Depends,HTTPException,UploadFile,File,Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from .current_affairs import ingest_daily,list_items
from .official_sources import ingest_official_sources
from .study_system import SessionStudy,OPTIONAL_SUBJECTS,OptionalSelection,ClassNote,QuestionBank,save_unique_question
from .syllabus_catalog import syllabus_for,topic_is_loaded
from .optional_syllabus_registry import get_optional_subject,optional_topic_is_verified,optional_coverage
from .upsc_cse_structure import MAINS_QUALIFYING_PAPERS,MAINS_COMPULSORY_MERIT_PAPERS,PRELIMS_PAPERS,OFFICIAL_NOTIFICATION_SOURCE
ADMIN_EMAILS={x.strip().lower() for x in os.getenv('ADMIN_EMAILS','').split(',') if x.strip()};UPLOAD_DIR=Path(os.getenv('UPLOAD_DIR','./uploads'));UPLOAD_DIR.mkdir(parents=True,exist_ok=True);MAX_UPLOAD_BYTES=20*1024*1024;ALLOWED_EXTENSIONS={'.pdf','.jpg','.jpeg','.png','.webp','.heic','.heif'}
class OptionalIn(BaseModel):subject:str
class QuestionIn(BaseModel):exam:str;paper:str;subject:str;topic:str;question:str;subtopic:str='';difficulty:str='moderate';source:str='AI-generated'
class NoteIn(BaseModel):exam:str;paper:str='';subject:str;topic:str;subtopic:str='';title:str;file_type:str;file_url:str

def _topic_is_loaded(exam,paper,subject,topic,subtopic=''):
    key=(exam or '').lower()
    if key in {'prelims','mains'}:return topic_is_loaded(key,paper,subject,topic,subtopic or None)
    return key=='optional' and optional_topic_is_verified(subject,paper,topic,subtopic)
def _coverage():
    prelims=syllabus_for('prelims');mains=syllabus_for('mains');opt=optional_coverage(OPTIONAL_SUBJECTS)
    pre_ok=all(bool(x.get('topics')) for x in prelims);main_ok=all(bool(x.get('topics')) for x in mains);qualifying=set(MAINS_QUALIFYING_PAPERS).issubset({x.get('paper') for x in mains})
    return {'source_url':OFFICIAL_NOTIFICATION_SOURCE,'prelims':{'required_papers':list(PRELIMS_PAPERS),'sections':len(prelims),'sections_with_topics':sum(bool(x.get('topics')) for x in prelims),'complete_navigation':pre_ok},'mains':{'required_merit_papers':list(MAINS_COMPULSORY_MERIT_PAPERS),'required_qualifying_papers':list(MAINS_QUALIFYING_PAPERS),'sections':len(mains),'sections_with_topics':sum(bool(x.get('topics')) for x in mains),'complete_navigation':main_ok,'qualifying_detail_loaded':qualifying},'optional':opt,'fully_verified_complete':False,'status':'अधूरा — सभी Optional Paper-I/Paper-II सत्यापित होने तक complete नहीं माना जाएगा।'}

def build_feature_router(current_user):
    router=APIRouter(prefix='/features',tags=['features'])
    def require_admin(u=Depends(current_user)):
        if not ADMIN_EMAILS or u.email.lower() not in ADMIN_EMAILS:raise HTTPException(403,'प्रशासक अनुमति आवश्यक है')
        return u
    @router.get('/syllabus')
    def syllabus(exam:Optional[str]=None,u=Depends(current_user)):
        if exam:return syllabus_for(exam)
        return syllabus_for('prelims')+syllabus_for('mains')
    @router.get('/syllabus/coverage')
    def syllabus_coverage(u=Depends(current_user)):return _coverage()
    @router.get('/syllabus/structure')
    def syllabus_structure(u=Depends(current_user)):return {'prelims':syllabus_for('prelims'),'mains':syllabus_for('mains'),'coverage':_coverage()}
    @router.get('/optional/subjects')
    def optional_subjects(u=Depends(current_user)):return OPTIONAL_SUBJECTS
    @router.get('/optional/selection')
    def optional_selection(u=Depends(current_user)):
        s=SessionStudy()
        try:r=s.query(OptionalSelection).filter(OptionalSelection.user_id==u.id).first();return {'subject':r.subject if r else None}
        finally:s.close()
    @router.put('/optional/selection')
    def save_optional(x:OptionalIn,u=Depends(current_user)):
        if x.subject not in OPTIONAL_SUBJECTS:raise HTTPException(400,'अमान्य वैकल्पिक विषय')
        s=SessionStudy()
        try:
            r=s.query(OptionalSelection).filter(OptionalSelection.user_id==u.id).first()
            if not r:r=OptionalSelection(user_id=u.id,subject=x.subject);s.add(r)
            else:r.subject=x.subject;r.updated_at=datetime.now(timezone.utc)
            s.commit();return {'ok':True,'subject':x.subject}
        finally:s.close()
    @router.get('/optional/syllabus/{subject}')
    def optional_syllabus(subject:str,u=Depends(current_user)):
        row=get_optional_subject(subject)
        if not row:raise HTTPException(404,'वैकल्पिक विषय नहीं मिला')
        return row
    @router.get('/current-affairs/date-wise')
    def current_affairs_date_wise(subject:Optional[str]=None,limit:int=100,u=Depends(current_user)):return list_items(subject=subject,limit=limit)
    @router.post('/admin/current-affairs/ingest')
    def ingest(u=Depends(require_admin)):return {'ok':True,'pib_and_core':ingest_daily(),'official_sources':ingest_official_sources()}
    @router.post('/question-bank')
    def add_question(x:QuestionIn,u=Depends(require_admin)):
        if not _topic_is_loaded(x.exam,x.paper,x.subject,x.topic,x.subtopic):raise HTTPException(400,'प्रश्न का टॉपिक/उप-टॉपिक सत्यापित पाठ्यक्रम में नहीं है')
        qid=save_unique_question(**x.model_dump())
        if not qid:raise HTTPException(409,'डुप्लिकेट या बहुत समान प्रश्न पहले से मौजूद है')
        return {'ok':True,'id':qid}
    @router.get('/question-bank/topic')
    def questions(exam:str,paper:str,subject:str,topic:str,subtopic:str='',limit:int=100,u=Depends(current_user)):
        if not _topic_is_loaded(exam,paper,subject,topic,subtopic):raise HTTPException(404,'टॉपिक/उप-टॉपिक सत्यापित पाठ्यक्रम में नहीं है')
        s=SessionStudy()
        try:
            q=s.query(QuestionBank).filter(QuestionBank.exam==exam,QuestionBank.paper==paper,QuestionBank.subject==subject,QuestionBank.topic==topic)
            if subtopic:q=q.filter(QuestionBank.subtopic==subtopic)
            rows=q.order_by(QuestionBank.id.asc()).limit(max(1,min(limit,200))).all();return [{'id':r.id,'exam':r.exam,'paper':r.paper,'subject':r.subject,'topic':r.topic,'subtopic':r.subtopic,'question':r.question,'difficulty':r.difficulty,'source':r.source} for r in rows]
        finally:s.close()
    @router.post('/uploads')
    async def upload(file:UploadFile=File(...),u=Depends(current_user)):
        original=Path(file.filename or 'upload').name;ext=Path(original).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:raise HTTPException(400,'केवल PDF/फोटो फ़ाइल स्वीकार है')
        raw=await file.read(MAX_UPLOAD_BYTES+1)
        if not raw:raise HTTPException(400,'खाली फ़ाइल स्वीकार नहीं है')
        if len(raw)>MAX_UPLOAD_BYTES:raise HTTPException(413,'फ़ाइल 20 MB से बड़ी है')
        stored=f'u{u.id}_{uuid.uuid4().hex}{ext}';path=UPLOAD_DIR/stored;path.write_bytes(raw)
        return {'ok':True,'original_name':original,'stored_name':stored,'file_url':f'/features/uploads/{stored}','size_bytes':len(raw)}
    @router.get('/uploads/{stored_name}')
    def get_uploaded_file(stored_name:str,u=Depends(current_user)):
        if '/' in stored_name or '\\' in stored_name or '..' in stored_name:raise HTTPException(400,'अमान्य फ़ाइल नाम')
        if not stored_name.startswith(f'u{u.id}_'):raise HTTPException(403,'अनुमति नहीं है')
        path=UPLOAD_DIR/stored_name
        if not path.exists():raise HTTPException(404,'फ़ाइल नहीं मिली')
        return FileResponse(path)
    @router.post('/class-notes')
    def add_class_note(x:NoteIn,u=Depends(current_user)):
        if x.file_type not in {'pdf','photo'}:raise HTTPException(400,'केवल pdf/photo स्वीकार हैं')
        s=SessionStudy()
        try:row=ClassNote(user_id=u.id,**x.model_dump());s.add(row);s.commit();s.refresh(row);return {'ok':True,'id':row.id}
        finally:s.close()
    @router.get('/class-notes')
    def list_class_notes(subject:Optional[str]=None,topic:Optional[str]=None,u=Depends(current_user)):
        s=SessionStudy()
        try:
            q=s.query(ClassNote).filter(ClassNote.user_id==u.id)
            if subject:q=q.filter(ClassNote.subject==subject)
            if topic:q=q.filter(ClassNote.topic==topic)
            rows=q.order_by(ClassNote.uploaded_at.desc()).all();return [{'id':r.id,'exam':r.exam,'paper':r.paper,'subject':r.subject,'topic':r.topic,'subtopic':r.subtopic,'title':r.title,'file_type':r.file_type,'file_url':r.file_url,'uploaded_at':r.uploaded_at.isoformat()} for r in rows]
        finally:s.close()
    return router