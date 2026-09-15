import re
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

from .current_affairs import SessionCA, CurrentAffair

# Only first-party/public-authority domains are accepted as evidence for changing facts.
OFFICIAL_DOMAIN_SUFFIXES=(
    'upsc.gov.in','pib.gov.in','rbi.org.in','sebi.gov.in','indiabudget.gov.in','mospi.gov.in',
    'niti.gov.in','eci.gov.in','mpa.gov.in','darpg.gov.in','mea.gov.in','moef.gov.in','imd.gov.in',
    'isro.gov.in','dst.gov.in','dbtindia.gov.in','meity.gov.in','agriwelfare.gov.in','icar.gov.in',
    'mohfw.gov.in','education.gov.in','wcd.gov.in','socialjustice.gov.in','tribal.nic.in','rural.gov.in',
    'indiaculture.gov.in','asi.nic.in'
)

STOPWORDS={
    'what','when','where','which','who','whom','whose','why','how','is','are','was','were','be','been','being',
    'the','a','an','and','or','of','to','in','on','for','from','with','about','tell','explain','current','latest',
    'क्या','कब','कहाँ','कौन','किस','क्यों','कैसे','है','हैं','था','थे','की','का','के','को','से','में','पर','और',
    'या','बताओ','बताइए','समझाओ','वर्तमान','नवीनतम','आज','अभी'
}

def is_official_url(url:str)->bool:
    try: host=(urlparse(url).hostname or '').lower().strip('.')
    except Exception:return False
    return any(host==d or host.endswith('.'+d) for d in OFFICIAL_DOMAIN_SUFFIXES)

def _tokens(text:str):
    words=re.findall(r'[a-z0-9\u0900-\u097f]+',(text or '').lower())
    return {w for w in words if len(w)>=3 and w not in STOPWORDS}

def _phrase(text:str):return ' '.join((text or '').lower().split())

def _relevance(row,subject:str,topic:str,question:str):
    hay=_phrase(f'{row.subject} {row.title} {row.summary}')
    hay_tokens=_tokens(hay)
    subject_phrase=_phrase(subject);topic_phrase=_phrase(topic)
    subject_tokens=_tokens(subject);topic_tokens=_tokens(topic);question_tokens=_tokens(question)
    score=0
    if subject_phrase and subject_phrase in hay:score+=6
    elif subject_tokens & hay_tokens:score+=2
    if topic_phrase and topic_phrase in hay:score+=8
    elif topic_tokens:
        overlap=len(topic_tokens & hay_tokens)
        if overlap:score+=min(6,overlap*2)
    q_overlap=len(question_tokens & hay_tokens)
    if q_overlap:score+=min(10,q_overlap*2)
    return score,q_overlap

def latest_verified_context(subject:str='',topic:str='',question:str='',max_items:int=12,max_age_days:int=30):
    """Return recent, official and query-relevant evidence. Empty context means changing facts must not be asserted."""
    now=datetime.now(timezone.utc);cutoff=now-timedelta(days=max(1,max_age_days))
    requested=bool(_tokens(subject) or _tokens(topic) or _tokens(question))
    s=SessionCA()
    try:
        rows=s.query(CurrentAffair).filter(CurrentAffair.fetched_at>=cutoff).order_by(CurrentAffair.published_at.desc(),CurrentAffair.id.desc()).limit(400).all()
        ranked=[]
        for r in rows:
            if not is_official_url(r.source_url):continue
            score,q_overlap=_relevance(r,subject,topic,question)
            if requested and score<=0:continue
            # When the user supplied a meaningful question, prefer evidence that actually overlaps it.
            if _tokens(question) and q_overlap==0 and not (_phrase(topic) and _phrase(topic) in _phrase(f'{r.title} {r.summary}')):continue
            ranked.append((score,r.published_at or r.fetched_at or now,r))
        ranked.sort(key=lambda x:(x[0],x[1]),reverse=True)
        out=[]
        for score,_,r in ranked[:max(1,max_items)]:
            out.append({'source_name':r.source_name,'source_url':r.source_url,'title':r.title,'summary':(r.summary or '')[:1200],'subject':r.subject,'published_at':r.published_at.isoformat() if r.published_at else None,'fetched_at':r.fetched_at.isoformat() if r.fetched_at else None,'relevance_score':score})
        newest=max((x['fetched_at'] for x in out if x['fetched_at']),default=None)
        return {'verified':bool(out),'checked_at':now.isoformat(),'newest_fetch':newest,'max_age_days':max_age_days,'items':out}
    finally:s.close()

def evidence_text(bundle:dict)->str:
    if not bundle.get('items'):return 'NO RECENT RELEVANT OFFICIAL EVIDENCE AVAILABLE.'
    parts=[]
    for i,x in enumerate(bundle['items'],1):
        parts.append(f"[{i}] {x['source_name']} | published={x['published_at']} | fetched={x['fetched_at']} | relevance={x.get('relevance_score',0)} | {x['title']} | {x['summary']} | {x['source_url']}")
    return '\n'.join(parts)
