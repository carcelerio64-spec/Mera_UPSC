import html,random,json,secrets
from datetime import datetime,timezone
from typing import Optional
from fastapi import APIRouter,Depends,HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from .study_system import SessionStudy,CompletedTopic,QuestionBank,GeneratedPaper,PaperResponse,question_detail_map
from .optional_syllabus_registry import get_optional_subject
PRELIMS_NEGATIVE_FRACTION=1/3;PRELIMS_GS_QUESTIONS=100;PRELIMS_GS_MARKS_PER_QUESTION=2.0;PRELIMS_CSAT_QUESTIONS=80;PRELIMS_CSAT_MARKS_PER_QUESTION=2.5;MAINS_GS_QUESTIONS=50;OPTIONAL_QUESTIONS=50
class MockSubmitIn(BaseModel):paper_code:str;question_ids:list[int];answers:dict[str,str]
def _completed_keys(s,user_id,exam,paper=None):
 q=s.query(CompletedTopic).filter(CompletedTopic.user_id==user_id,CompletedTopic.exam==exam)
 if paper:q=q.filter(CompletedTopic.paper==paper)
 return {(r.paper,r.subject,r.topic) for r in q.all()}
def _eligible_questions(s,user_id,exam,paper=None,completed_only=False,subject=None):
 q=s.query(QuestionBank).filter(QuestionBank.exam==exam)
 if paper:q=q.filter(QuestionBank.paper==paper)
 if subject:q=q.filter(QuestionBank.subject==subject)
 rows=q.order_by(QuestionBank.id.asc()).all()
 if not completed_only:return rows
 keys=_completed_keys(s,user_id,exam,paper);return[r for r in rows if(r.paper,r.subject,r.topic)in keys]
def _balanced_sample(rows,count):
 by={}
 for r in rows:by.setdefault((r.paper,r.subject,r.topic),[]).append(r)
 for v in by.values():random.shuffle(v)
 chosen=[]
 while len(chosen)<count and any(by.values()):
  for k in list(by):
   if len(chosen)>=count:break
   if by[k]:chosen.append(by[k].pop())
 random.shuffle(chosen);return chosen
def _written_html(title,paper,questions,code):
 blocks=[]
 for i,q in enumerate(questions,1):
  words=150 if i<=25 else 250;marks=10 if i<=25 else 15;lines=18 if words==150 else 28;answer=''.join('<div class="answer-line"></div>'for _ in range(lines));blocks.append(f'<section class="question-block"><div class="qhead"><b>प्रश्न {i}.</b><span>{marks} अंक</span></div><div class="question">{html.escape(q["question"])}</div><div class="limit">उत्तर {words} शब्दों से अधिक न हो।</div><div class="answer-space">{answer}</div></section>')
 return f'''<!doctype html><html lang="hi"><head><meta charset="utf-8"><title>{html.escape(title)} - {html.escape(paper)}</title><style>@page{{size:A4;margin:14mm}}body{{font-family:system-ui,sans-serif;position:relative}}body:before{{content:"AMIT";position:fixed;inset:0;display:flex;align-items:center;justify-content:center;font-size:92pt;font-weight:800;letter-spacing:12px;color:rgba(0,0,0,.055);transform:rotate(-35deg);z-index:-1;pointer-events:none}}.cover{{text-align:center;padding:18mm 8mm;page-break-after:always}}.meta{{margin:28px auto;max-width:520px;border:1px solid;padding:14px;text-align:left}}.question-block{{page-break-inside:avoid;margin-bottom:12mm}}.qhead{{display:flex;justify-content:space-between;border-top:1.5px solid;padding-top:5px}}.question{{line-height:1.55;margin:6px 0}}.limit{{font-size:9.5pt;font-style:italic}}.answer-space{{border:1px solid #888;padding:5mm}}.answer-line{{height:8mm;border-bottom:1px solid #bbb}}@media print{{button{{display:none}}}}</style></head><body><section class="cover"><h1>{html.escape(title)}</h1><h2>{html.escape(paper)}</h2><div class="meta"><b>पेपर आईडी:</b> {code}<br><b>कुल प्रश्न:</b> {len(questions)}</div><p>यह AI द्वारा तैयार अभ्यास प्रश्नपत्र है; आधिकारिक UPSC प्रश्न अलग PYQ बैंक में हैं।</p><button onclick="window.print()">प्रिंट / PDF में सहेजें</button></section>{''.join(blocks)}</body></html>'''
def build_exam_router(current_user):
 router=APIRouter()
 @router.get('/prelims/combined-mock')
 def combined_prelims_mock(paper:str='GS Paper-I',u=Depends(current_user)):
  s=SessionStudy()
  try:
   rows=_eligible_questions(s,u.id,'prelims',paper);details=question_detail_map([r.id for r in rows]);eligible=[r for r in rows if details.get(r.id,{}).get('question_type')=='mcq' and len(details.get(r.id,{}).get('options',[]))==4];required=PRELIMS_CSAT_QUESTIONS if'CSAT'in paper.upper()or'II'in paper else PRELIMS_GS_QUESTIONS;marks=PRELIMS_CSAT_MARKS_PER_QUESTION if required==80 else PRELIMS_GS_MARKS_PER_QUESTION
   if len(eligible)<required:return{'paper':paper,'required_questions':required,'available_questions':len(eligible),'generation_needed':required-len(eligible),'questions':[]}
   chosen=_balanced_sample(eligible,required);code='PRE-'+secrets.token_hex(6).upper();s.add(GeneratedPaper(paper_code=code,user_id=u.id,exam='prelims',paper=paper,question_ids_json=json.dumps([r.id for r in chosen])));s.commit();return{'paper_code':code,'paper':paper,'required_questions':required,'marks_per_question':marks,'negative_marking':{'wrong_fraction':PRELIMS_NEGATIVE_FRACTION,'blank_penalty':0,'multiple_answers_treated_as_wrong':True},'questions':[{'id':r.id,'subject':r.subject,'topic':r.topic,'subtopic':r.subtopic,'question':r.question,'options':details[r.id]['options']}for r in chosen]}
  finally:s.close()
 @router.post('/prelims/combined-mock/submit')
 def submit_combined_mock(x:MockSubmitIn,u=Depends(current_user)):
  s=SessionStudy()
  try:
   gp=s.query(GeneratedPaper).filter(GeneratedPaper.paper_code==x.paper_code,GeneratedPaper.user_id==u.id,GeneratedPaper.exam=='prelims').first()
   if not gp:raise HTTPException(404,'प्रश्नपत्र नहीं मिला')
   if gp.status=='submitted':raise HTTPException(409,'प्रश्नपत्र पहले ही जमा किया जा चुका है')
   expected=json.loads(gp.question_ids_json);submitted=[int(i)for i in x.question_ids]
   if submitted!=expected:raise HTTPException(400,'जमा किए गए प्रश्न तैयार प्रश्नपत्र से मेल नहीं खाते')
   rows={r.id:r for r in s.query(QuestionBank).filter(QuestionBank.id.in_(expected)).all()};details=question_detail_map(expected);correct=wrong=blank=0;score=0.0
   for qid in expected:
    d=details.get(qid,{});right=str(d.get('correct_answer','')).strip();ans=str(x.answers.get(str(qid),'')).strip();row=rows[qid];marks=2.5 if('CSAT'in row.paper.upper()or'II'in row.paper)else 2.0
    if not ans:blank+=1;result=-1;awarded=0
    elif right and ans.casefold()==right.casefold():correct+=1;score+=marks;result=1;awarded=marks
    else:wrong+=1;awarded=-(marks*PRELIMS_NEGATIVE_FRACTION);score+=awarded;result=0
    s.add(PaperResponse(paper_id=gp.id,user_id=u.id,question_id=qid,answer_text=ans,result_code=result,marks_awarded=round(awarded,4)))
   gp.status='submitted';gp.submitted_at=datetime.now(timezone.utc);s.commit();return{'paper_code':gp.paper_code,'correct':correct,'wrong':wrong,'blank':blank,'negative_fraction':PRELIMS_NEGATIVE_FRACTION,'score':round(score,2)}
  finally:s.close()
 @router.get('/history')
 def history(exam:Optional[str]=None,u=Depends(current_user)):
  s=SessionStudy()
  try:
   q=s.query(GeneratedPaper).filter(GeneratedPaper.user_id==u.id)
   if exam:q=q.filter(GeneratedPaper.exam==exam)
   return[{'paper_code':r.paper_code,'exam':r.exam,'paper':r.paper,'status':r.status,'question_count':len(json.loads(r.question_ids_json)),'created_at':r.created_at.isoformat(),'submitted_at':r.submitted_at.isoformat()if r.submitted_at else None}for r in q.order_by(GeneratedPaper.created_at.desc()).all()]
  finally:s.close()
 @router.get('/mains/combined-paper')
 def mains_combined_paper(paper:str='GS-II',u=Depends(current_user)):
  if paper not in{'GS-I','GS-II','GS-III','GS-IV'}:raise HTTPException(400,'GS-I, GS-II, GS-III या GS-IV चुनें')
  s=SessionStudy()
  try:
   rows=_eligible_questions(s,u.id,'mains',paper)
   if len(rows)<MAINS_GS_QUESTIONS:return{'paper':paper,'required_questions':MAINS_GS_QUESTIONS,'available_questions':len(rows),'generation_needed':MAINS_GS_QUESTIONS-len(rows),'ready':False}
   chosen=_balanced_sample(rows,MAINS_GS_QUESTIONS);code='MAIN-'+secrets.token_hex(6).upper();s.add(GeneratedPaper(paper_code=code,user_id=u.id,exam='mains',paper=paper,question_ids_json=json.dumps([r.id for r in chosen])));s.commit();return{'paper_code':code,'paper':paper,'ready':True,'question_count':MAINS_GS_QUESTIONS,'questions':[{'number':i,'id':r.id,'subject':r.subject,'topic':r.topic,'subtopic':r.subtopic,'question':r.question,'marks':10 if i<=25 else 15,'word_limit':150 if i<=25 else 250}for i,r in enumerate(chosen,1)]}
  finally:s.close()
 @router.get('/mains/combined-paper/print',response_class=HTMLResponse)
 def mains_print(paper_code:str,u=Depends(current_user)):
  return _print_saved(u,'mains',paper_code,'सिविल सेवा (मुख्य) अभ्यास प्रश्न बैंक')
 @router.get('/optional/combined-paper')
 def optional_combined_paper(subject:str,paper:str='Paper-I',u=Depends(current_user)):
  if paper not in{'Paper-I','Paper-II'}:raise HTTPException(400,'Paper-I या Paper-II चुनें')
  syllabus=get_optional_subject(subject)
  if not syllabus.get('official_subject'):raise HTTPException(404,'वैकल्पिक विषय नहीं मिला')
  if not syllabus.get('generation_ready'):raise HTTPException(422,'इस वैकल्पिक विषय का Paper-I और Paper-II syllabus अभी पूरी तरह सत्यापित नहीं है; प्रश्नपत्र generation बंद है।')
  s=SessionStudy()
  try:
   rows=_eligible_questions(s,u.id,'optional',paper,subject=subject)
   if len(rows)<OPTIONAL_QUESTIONS:return{'subject':subject,'paper':paper,'required_questions':OPTIONAL_QUESTIONS,'available_questions':len(rows),'generation_needed':OPTIONAL_QUESTIONS-len(rows),'ready':False}
   chosen=_balanced_sample(rows,OPTIONAL_QUESTIONS);code='OPT-'+secrets.token_hex(6).upper();s.add(GeneratedPaper(paper_code=code,user_id=u.id,exam='optional',paper=f'{subject} {paper}',question_ids_json=json.dumps([r.id for r in chosen])));s.commit();return{'paper_code':code,'subject':subject,'paper':paper,'ready':True,'question_count':OPTIONAL_QUESTIONS,'questions':[{'number':i,'id':r.id,'topic':r.topic,'subtopic':r.subtopic,'question':r.question,'marks':10 if i<=25 else 15,'word_limit':150 if i<=25 else 250}for i,r in enumerate(chosen,1)]}
  finally:s.close()
 @router.get('/optional/combined-paper/print',response_class=HTMLResponse)
 def optional_print(paper_code:str,u=Depends(current_user)):
  return _print_saved(u,'optional',paper_code,'सिविल सेवा वैकल्पिक विषय अभ्यास प्रश्न बैंक')
 def _print_saved(u,exam,paper_code,title):
  s=SessionStudy()
  try:
   gp=s.query(GeneratedPaper).filter(GeneratedPaper.paper_code==paper_code,GeneratedPaper.user_id==u.id,GeneratedPaper.exam==exam).first()
   if not gp:raise HTTPException(404,'तैयार प्रश्नपत्र नहीं मिला')
   ids=json.loads(gp.question_ids_json);rows={r.id:r for r in s.query(QuestionBank).filter(QuestionBank.id.in_(ids)).all()};return HTMLResponse(_written_html(title,gp.paper,[{'question':rows[i].question}for i in ids],gp.paper_code))
  finally:s.close()
 return router