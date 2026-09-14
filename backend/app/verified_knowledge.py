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

def is_official_url(url:str)->bool:
    try: host=(urlparse(url).hostname or '').lower().strip('.')
    except Exception:return False
    return any(host==d or host.endswith('.'+d) for d in OFFICIAL_DOMAIN_SUFFIXES)

def latest_verified_context(subject:str='',topic:str='',question:str='',max_items:int=12,max_age_days:int=30):
    """Return recent official-source records only. Empty context means changing facts must not be asserted."""
    now=datetime.now(timezone.utc);cutoff=now-timedelta(days=max(1,max_age_days));terms=[x.lower() for x in (subject,topic) if x and x.strip()]
    s=SessionCA()
    try:
        rows=s.query(CurrentAffair).filter(CurrentAffair.fetched_at>=cutoff).order_by(CurrentAffair.published_at.desc(),CurrentAffair.id.desc()).limit(250).all()
        out=[]
        for r in rows:
            if not is_official_url(r.source_url):continue
            hay=f'{r.subject} {r.title} {r.summary}'.lower()
            if terms and not any(t in hay for t in terms):continue
            out.append({'source_name':r.source_name,'source_url':r.source_url,'title':r.title,'summary':r.summary[:1200],'subject':r.subject,'published_at':r.published_at.isoformat() if r.published_at else None,'fetched_at':r.fetched_at.isoformat() if r.fetched_at else None})
            if len(out)>=max_items:break
        newest=max((x['fetched_at'] for x in out if x['fetched_at']),default=None)
        return {'verified':bool(out),'checked_at':now.isoformat(),'newest_fetch':newest,'items':out}
    finally:s.close()

def evidence_text(bundle:dict)->str:
    if not bundle.get('items'):return 'NO RECENT OFFICIAL EVIDENCE AVAILABLE.'
    parts=[]
    for i,x in enumerate(bundle['items'],1):
        parts.append(f"[{i}] {x['source_name']} | published={x['published_at']} | fetched={x['fetched_at']} | {x['title']} | {x['summary']} | {x['source_url']}")
    return '\n'.join(parts)
