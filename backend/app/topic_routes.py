from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from .current_affairs import list_items
from .study_system import SessionStudy, ClassNote, QuestionBank, CompletedTopic, question_detail_map
from .syllabus_catalog import topic_is_loaded
from .optional_syllabus_registry import optional_topic_is_verified
PRELIMS_TARGET=100;MAINS_TARGET=50;OPTIONAL_TARGET=50
class TopicCompletionIn(BaseModel):exam:str;paper:str;subject:str;topic:str;completed:bool=True

def _find_topic(exam,paper,subject,topic):
    exam_key=(exam or '').lower()
    if exam_key=='optional':return {'paper':paper,'subject':subject} if optional_topic_is_verified(subject,paper,topic) else None
    if exam_key not in {'prelims','mains'}:return None
    return {'paper':paper,'subject':subject} if topic_is_loaded(exam_key,paper,subject,topic) else None
def _is_completed(s,user_id,exam,paper,subject,topic):return s.query(CompletedTopic).filter(CompletedTopic.user_id==user_id,CompletedTopic.exam==exam.lower(),CompletedTopic.paper==paper,CompletedTopic.subject==subject,CompletedTopic.topic==topic).first() is not None
def _target(exam):return PRELIMS_TARGET if exam.lower()=='prelims' else OPTIONAL_TARGET if exam.lower()=='optional' else MAINS_TARGET

def build_topic_router(current_user):
    router=APIRouter()
    @router.put('/study/topic/completion')
    def set_topic_completion(x:TopicCompletionIn,u=Depends(current_user)):
        exam=x.exam.lower()
        if not _find_topic(exam,x.paper,x.subject,x.topic):raise HTTPException(404,'टॉपिक सत्यापित UPSC पाठ्यक्रम में उपलब्ध नहीं है।')
        s=SessionStudy()
        try:
            row=s.query(CompletedTopic).filter(CompletedTopic.user_id==u.id,CompletedTopic.exam==exam,CompletedTopic.paper==x.paper,CompletedTopic.subject==x.subject,CompletedTopic.topic==x.topic).first()
            if x.completed:
                if not row:s.add(CompletedTopic(user_id=u.id,exam=exam,paper=x.paper,subject=x.subject,topic=x.topic,completed_at=datetime.now(timezone.utc)))
                else:row.completed_at=datetime.now(timezone.utc)
            elif row:s.delete(row)
            s.commit();count=s.query(QuestionBank).filter(QuestionBank.exam==exam,QuestionBank.paper==x.paper,QuestionBank.subject==x.subject,QuestionBank.topic==x.topic).count();target=_target(exam)
            return {'ok':True,'completed':x.completed,'exam':exam,'paper':x.paper,'subject':x.subject,'topic':x.topic,'question_target':target,'saved_questions':count,'generation_needed':max(0,target-count) if x.completed else 0,'section_key':f'{exam}|{x.paper}|{x.subject}|{x.topic}'}
        finally:s.close()
    @router.get('/study/question-sections')
    def completed_topic_question_sections(exam:str,u=Depends(current_user)):
        exam=exam.lower()
        if exam not in {'prelims','mains','optional'}:raise HTTPException(400,'परीक्षा prelims, mains या optional होनी चाहिए।')
        s=SessionStudy()
        try:
            completed=s.query(CompletedTopic).filter(CompletedTopic.user_id==u.id,CompletedTopic.exam==exam).order_by(CompletedTopic.paper,CompletedTopic.subject,CompletedTopic.completed_at).all();target=_target(exam);sections=[]
            for c in completed:
                count=s.query(QuestionBank).filter(QuestionBank.exam==exam,QuestionBank.paper==c.paper,QuestionBank.subject==c.subject,QuestionBank.topic==c.topic).count();sections.append({'section_key':f'{exam}|{c.paper}|{c.subject}|{c.topic}','exam':exam,'paper':c.paper,'subject':c.subject,'topic':c.topic,'completed_at':c.completed_at.isoformat(),'question_target':target,'saved_questions':count,'generation_needed':max(0,target-count),'ready':count>=target})
            return {'exam':exam,'target_per_topic':target,'sections':sections}
        finally:s.close()
    @router.get('/study/topic')
    def topic_study(exam:str,paper:str,subject:str,topic:str,u=Depends(current_user)):
        exam=exam.lower()
        if not _find_topic(exam,paper,subject,topic):raise HTTPException(404,'टॉपिक सत्यापित UPSC पाठ्यक्रम में उपलब्ध नहीं है।')
        s=SessionStudy()
        try:
            notes=s.query(ClassNote).filter(ClassNote.user_id==u.id,ClassNote.exam==exam,ClassNote.subject==subject,ClassNote.topic==topic).order_by(ClassNote.uploaded_at.desc()).all();question_count=s.query(QuestionBank).filter(QuestionBank.exam==exam,QuestionBank.paper==paper,QuestionBank.subject==subject,QuestionBank.topic==topic).count();completed=_is_completed(s,u.id,exam,paper,subject,topic);target=_target(exam)
            return {'exam':exam,'paper':paper,'subject':subject,'topic':topic,'official_syllabus_match':True,'completed':completed,'question_section_unlocked':completed,'question_target':target,'question_bank_count':question_count,'generation_needed':max(0,target-question_count) if completed else 0,'class_notes':[{'id':n.id,'exam':n.exam,'paper':n.paper,'subject':n.subject,'topic':n.topic,'subtopic':n.subtopic,'title':n.title,'file_type':n.file_type,'file_url':n.file_url,'uploaded_at':n.uploaded_at.isoformat()} for n in notes],'current_affairs':list_items(subject=subject,limit=10)}
        finally:s.close()
    @router.get('/question-bank/by-topic')
    def questions_by_topic(exam:str,paper:str,subject:str,topic:str,limit:int=100,u=Depends(current_user)):
        exam=exam.lower()
        if not _find_topic(exam,paper,subject,topic):raise HTTPException(404,'टॉपिक सत्यापित UPSC पाठ्यक्रम में उपलब्ध नहीं है।')
        s=SessionStudy()
        try:
            if not _is_completed(s,u.id,exam,paper,subject,topic):raise HTTPException(403,'पहले यह टॉपिक पूरा करें; उसके बाद अलग प्रश्न अनुभाग खुलेगा।')
            rows=s.query(QuestionBank).filter(QuestionBank.exam==exam,QuestionBank.paper==paper,QuestionBank.subject==subject,QuestionBank.topic==topic).order_by(QuestionBank.id.asc()).limit(max(1,min(limit,_target(exam)))).all();details=question_detail_map([r.id for r in rows]);questions=[]
            for r in rows:
                d=details.get(r.id,{});questions.append({'id':r.id,'subtopic':r.subtopic,'question':r.question,'difficulty':r.difficulty,'source':r.source,'question_type':d.get('question_type','mcq' if exam=='prelims' else 'mains'),'options':d.get('options',[]),'marks':d.get('marks',0),'word_limit':d.get('word_limit',0)})
            return {'section_key':f'{exam}|{paper}|{subject}|{topic}','exam':exam,'paper':paper,'subject':subject,'topic':topic,'target':_target(exam),'questions':questions}
        finally:s.close()
    return router