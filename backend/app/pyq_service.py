import time
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

BASE='https://www.upsc.gov.in'
EXAM_PAGES={
    ('prelims',2026):'https://www.upsc.gov.in/examinations/Civil%20Services%20%28Preliminary%29%20Examination%2C%202026',
    ('mains',2026):'https://www.upsc.gov.in/examinations/Civil%20Services%20%28Main%29%20Examination%2C%202026',
}
_CACHE={}
TTL_SECONDS=6*60*60


def _kind(title:str):
    t=title.lower()
    if 'essay' in t:return 'essay'
    if 'general studies' in t:return 'general'
    if 'paper' in t:return 'optional_or_language'
    return 'other'


def fetch_official_pyq(exam:str='mains',year:int=2026,subject:str|None=None):
    key=(exam.lower(),int(year))
    now=time.time()
    cached=_CACHE.get(key)
    if cached and now-cached['at']<TTL_SECONDS:
        rows=cached['rows']
    else:
        page=EXAM_PAGES.get(key)
        if not page:
            return {'source':'UPSC','exam':exam,'year':year,'source_page':'https://www.upsc.gov.in/examinations/previous-question-papers','papers':[],'note':'Direct exam-page parser is currently configured for 2026; use the official previous-papers page for older years.'}
        rows=[]
        try:
            with httpx.Client(timeout=30,follow_redirects=True,headers={'User-Agent':'MeraUPSC/1.0'}) as client:
                r=client.get(page);r.raise_for_status()
            soup=BeautifulSoup(r.text,'html.parser')
            seen=set()
            for a in soup.find_all('a',href=True):
                title=' '.join(a.get_text(' ',strip=True).split())
                href=urljoin(page,a['href'])
                low=(title+' '+href).lower()
                if not title or href in seen:continue
                if '.pdf' not in low and '/sites/default/files/' not in low:continue
                if key[0]=='prelims' and not any(x in title.lower() for x in ['general studies','question paper']):continue
                if key[0]=='mains' and not any(x in title.lower() for x in ['paper','essay','general studies']):continue
                seen.add(href)
                rows.append({'title':title,'url':href,'kind':_kind(title)})
        except Exception:
            rows=[]
        _CACHE[key]={'at':now,'rows':rows}
    if subject:
        s=subject.lower()
        rows=[x for x in rows if s in x['title'].lower()]
    return {'source':'UPSC','exam':key[0],'year':key[1],'source_page':EXAM_PAGES.get(key,'https://www.upsc.gov.in/examinations/previous-question-papers'),'papers':rows}
