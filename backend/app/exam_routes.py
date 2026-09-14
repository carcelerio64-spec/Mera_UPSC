import html
import random
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .study_system import SessionStudy, CompletedTopic, QuestionBank, QuestionDetail, question_detail_map

PRELIMS_NEGATIVE_FRACTION=1/3
PRELIMS_GS_QUESTIONS=100
PRELIMS_GS_MARKS_PER_QUESTION=2.0
PRELIMS_CSAT_QUESTIONS=80
PRELIMS_CSAT_MARKS_PER_QUESTION=2.5
MAINS_GS_QUESTIONS=20


class MockSubmitIn(BaseModel):
    question_ids:list[int]
    answers:dict[str,str]


def _completed_keys(s,user_id:int,exam:str,paper:Optional[str]=None):
    q=s.query(CompletedTopic).filter(CompletedTopic.user_id==user_id,CompletedTopic.exam==exam)
    if paper:q=q.filter(CompletedTopic.paper==paper)
    return {(r.paper,r.subject,r.topic) for r in q.all()}


def _eligible_questions(s,user_id:int,exam:str,paper:Optional[str]=None):
    keys=_completed_keys(s,user_id,exam,paper)
    if not keys:return []
    q=s.query(QuestionBank).filter(QuestionBank.exam==exam)
    if paper:q=q.filter(QuestionBank.paper==paper)
    return [r for r in q.order_by(QuestionBank.id.asc()).all() if (r.paper,r.subject,r.topic) in keys]


def _balanced_sample(rows,count:int):
    by_topic={}
    for r in rows:
        by_topic.setdefault((r.paper,r.subject,r.topic),[]).append(r)
    for values in by_topic.values():random.shuffle(values)
    chosen=[]
    while len(chosen)<count and any(by_topic.values()):
        for key in list(by_topic):
            if len(chosen)>=count:break
            if by_topic[key]:chosen.append(by_topic[key].pop())
    random.shuffle(chosen)
    return chosen


def _mains_qca_html(paper:str,questions:list[dict]):
    blocks=[]
    for i,q in enumerate(questions,1):
        words=150 if i<=10 else 250
        marks=10 if i<=10 else 15
        lines=18 if words==150 else 28
        answer_lines=''.join('<div class="answer-line"></div>' for _ in range(lines))
        blocks.append(f'''<section class="question-block">
          <div class="qhead"><b>Q{i}.</b><span>{marks} Marks</span></div>
          <div class="question">{html.escape(q['question'])}</div>
          <div class="limit">Answer in not more than {words} words.</div>
          <div class="answer-space">{answer_lines}</div>
        </section>''')
    return f'''<!doctype html><html><head><meta charset="utf-8"><title>UPSC-style {html.escape(paper)} Practice QCA</title>
    <style>
    @page{{size:A4;margin:14mm 14mm 16mm}}
    body{{font-family:system-ui,"Noto Sans Devanagari","Nirmala UI",sans-serif;color:#111;margin:0}}
    .cover{{text-align:center;padding:18mm 8mm 12mm;page-break-after:always}}
    .cover h1{{font-size:20pt;margin:12px 0}} .cover h2{{font-size:15pt;margin:8px 0}}
    .meta{{margin:28px auto 18px;max-width:520px;border:1px solid #222;padding:14px;text-align:left;line-height:1.7}}
    .instructions{{text-align:left;max-width:650px;margin:24px auto;font-size:10.5pt;line-height:1.55}}
    .question-block{{page-break-inside:avoid;margin:0 0 12mm}}
    .qhead{{display:flex;justify-content:space-between;border-top:1.5px solid #111;padding-top:5px;font-size:11pt}}
    .question{{font-size:11.5pt;line-height:1.55;margin:6px 0}}
    .limit{{font-size:9.5pt;font-style:italic;margin-bottom:7px}}
    .answer-space{{border:1px solid #888;padding:5mm 6mm}}
    .answer-line{{height:8mm;border-bottom:1px solid #bbb}}
    @media print{{button{{display:none}}}}
    </style></head><body>
    <section class="cover"><h1>CIVIL SERVICES (MAIN) PRACTICE EXAMINATION</h1><h2>{html.escape(paper)}</h2>
      <div class="meta"><b>Time Allowed:</b> Three Hours<br><b>Maximum Marks:</b> 250<br><b>Total Questions:</b> 20</div>
      <div class="instructions"><b>QUESTION PAPER SPECIFIC INSTRUCTIONS</b><br>
      All questions are compulsory. Questions 1 to 10 carry 10 marks each and should be answered in about 150 words. Questions 11 to 20 carry 15 marks each and should be answered in about 250 words. Keep the indicated word limit in mind. This is a practice paper generated only from your completed topics.</div>
      <button onclick="window.print()">Print / Save as PDF</button></section>
      {''.join(blocks)}
    </body></html>'''


def build_exam_router(current_user):
    router=APIRouter()

    @router.get('/prelims/combined-mock')
    def combined_prelims_mock(paper:str='GS Paper-I',u=Depends(current_user)):
        s=SessionStudy()
        try:
            rows=_eligible_questions(s,u.id,'prelims',paper)
            details=question_detail_map([r.id for r in rows])
            eligible=[]
            for r in rows:
                d=details.get(r.id,{})
                if d.get('question_type')=='mcq' and len(d.get('options',[]))==4:
                    eligible.append(r)
            required=PRELIMS_CSAT_QUESTIONS if 'CSAT' in paper.upper() or 'II' in paper else PRELIMS_GS_QUESTIONS
            marks=PRELIMS_CSAT_MARKS_PER_QUESTION if required==PRELIMS_CSAT_QUESTIONS else PRELIMS_GS_MARKS_PER_QUESTION
            chosen=_balanced_sample(eligible,min(required,len(eligible)))
            return {
                'paper':paper,'completed_topics_only':True,'required_questions':required,'available_questions':len(eligible),
                'generation_needed':max(0,required-len(eligible)),'marks_per_question':marks,
                'negative_marking':{'wrong_fraction':PRELIMS_NEGATIVE_FRACTION,'blank_penalty':0,'multiple_answers_treated_as_wrong':True},
                'questions':[{'id':r.id,'subject':r.subject,'topic':r.topic,'question':r.question,'options':details[r.id]['options']} for r in chosen],
            }
        finally:s.close()

    @router.post('/prelims/combined-mock/submit')
    def submit_combined_mock(x:MockSubmitIn,u=Depends(current_user)):
        if not x.question_ids:raise HTTPException(status_code=400,detail='No questions submitted')
        s=SessionStudy()
        try:
            rows=s.query(QuestionBank).filter(QuestionBank.id.in_(x.question_ids),QuestionBank.exam=='prelims').all()
            allowed={(r.id):(r.paper,r.subject,r.topic) for r in rows}
            completed=_completed_keys(s,u.id,'prelims')
            if any(key not in completed for key in allowed.values()):
                raise HTTPException(status_code=403,detail='Mock contains a topic that is not completed by this user')
            details=question_detail_map(list(allowed))
            correct=wrong=blank=0;score=0.0
            for qid in x.question_ids:
                d=details.get(qid,{})
                right=str(d.get('correct_answer','')).strip()
                ans=str(x.answers.get(str(qid),'')).strip()
                row=next((r for r in rows if r.id==qid),None)
                marks=PRELIMS_CSAT_MARKS_PER_QUESTION if row and ('CSAT' in row.paper.upper() or 'II' in row.paper) else PRELIMS_GS_MARKS_PER_QUESTION
                if not ans:blank+=1
                elif right and ans.casefold()==right.casefold():correct+=1;score+=marks
                else:wrong+=1;score-=marks*PRELIMS_NEGATIVE_FRACTION
            return {'correct':correct,'wrong':wrong,'blank':blank,'negative_fraction':PRELIMS_NEGATIVE_FRACTION,'score':round(score,2)}
        finally:s.close()

    @router.get('/mains/combined-paper')
    def mains_combined_paper(paper:str='GS-II',u=Depends(current_user)):
        if paper not in {'GS-I','GS-II','GS-III','GS-IV'}:
            raise HTTPException(status_code=400,detail='Use GS-I, GS-II, GS-III or GS-IV')
        s=SessionStudy()
        try:
            rows=_eligible_questions(s,u.id,'mains',paper)
            if len(rows)<MAINS_GS_QUESTIONS:
                return {'paper':paper,'required_questions':20,'available_questions':len(rows),'generation_needed':20-len(rows),'ready':False}
            chosen=_balanced_sample(rows,20)
            return {'paper':paper,'required_questions':20,'ready':True,'maximum_marks':250,'duration_minutes':180,
                'questions':[{'number':i,'id':r.id,'subject':r.subject,'topic':r.topic,'question':r.question,'marks':10 if i<=10 else 15,'word_limit':150 if i<=10 else 250} for i,r in enumerate(chosen,1)]}
        finally:s.close()

    @router.get('/mains/combined-paper/print',response_class=HTMLResponse)
    def mains_combined_paper_print(paper:str='GS-II',u=Depends(current_user)):
        if paper not in {'GS-I','GS-II','GS-III','GS-IV'}:
            raise HTTPException(status_code=400,detail='Use GS-I, GS-II, GS-III or GS-IV')
        s=SessionStudy()
        try:
            rows=_eligible_questions(s,u.id,'mains',paper)
            if len(rows)<20:
                raise HTTPException(status_code=409,detail=f'Need {20-len(rows)} more unique questions from completed topics before a full UPSC-style paper can be printed')
            chosen=_balanced_sample(rows,20)
            questions=[{'question':r.question} for r in chosen]
            return HTMLResponse(_mains_qca_html(paper,questions))
        finally:s.close()

    return router
