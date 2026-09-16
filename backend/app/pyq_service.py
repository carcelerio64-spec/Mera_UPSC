import re,time
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup
BASE='https://www.upsc.gov.in';ARCHIVE_PAGE=BASE+'/examinations/previous-question-papers';_CACHE={};TTL_SECONDS=21600

def _clean(v):return ' '.join((v or '').split())
def _roman_paper(t):
    t=t.lower().replace('paper-i','paper i').replace('paper-ii','paper ii')
    if re.search(r'\bpaper\s*ii\b',t):return 'Paper-II'
    if re.search(r'\bpaper\s*i\b',t):return 'Paper-I'
    return None
def _kind(title):
    t=title.lower()
    if 'essay' in t:return 'essay'
    if 'general studies' in t:return 'general_studies'
    if 'english' in t:return 'qualifying_english'
    if any(x in t for x in ('compulsory','language')):return 'qualifying_language'
    if _roman_paper(t):return 'optional_or_language'
    return 'other'
def _exam_kind(text):
    t=text.lower()
    if 'civil services' not in t:return None
    if 'preliminary' in t or 'prelims' in t:return 'prelims'
    if 'main' in t or 'mains' in t:return 'mains'
def _year(text):
    m=re.search(r'\b(19\d{2}|20\d{2})\b',text);return int(m.group(1)) if m else None
def _fetch_html(c,url):
    r=c.get(url);r.raise_for_status();return BeautifulSoup(r.text,'html.parser')
def _paper_links(soup,page_url,exam,year):
    rows=[];seen=set()
    for a in soup.find_all('a',href=True):
        title=_clean(a.get_text(' ',strip=True));href=urljoin(page_url,a['href']);low=(title+' '+href).lower()
        if not title or href in seen or ('.pdf' not in low and '/sites/default/files/' not in low):continue
        if exam=='prelims' and not any(x in low for x in ('general studies','question paper','paper-i','paper-ii','paper i','paper ii')):continue
        if exam=='mains' and not any(x in low for x in ('paper','essay','general studies','compulsory','english','language')):continue
        seen.add(href);kind=_kind(title);paper=_roman_paper(title)
        rows.append({'year':year,'exam':exam,'title':title,'paper':paper,'url':href,'kind':kind,'source':'UPSC','source_page':page_url,'is_official_pyq':True,'ai_generated':False})
    return rows
def _discover_exam_pages(c):
    soup=_fetch_html(c,ARCHIVE_PAGE);pages=[];seen=set()
    for a in soup.find_all('a',href=True):
        title=_clean(a.get_text(' ',strip=True));href=urljoin(ARCHIVE_PAGE,a['href']);combined=title+' '+href;exam=_exam_kind(combined);year=_year(combined)
        if not exam or not year or href in seen:continue
        seen.add(href);pages.append({'exam':exam,'year':year,'title':title,'url':href})
    return pages

def fetch_official_pyq(exam='mains',year=None,subject=None):
    exam=exam.lower().strip()
    if exam not in {'prelims','mains'}:return {'source':'UPSC','papers':[],'archive_reachable':False,'error':'परीक्षा प्रकार prelims या mains होना चाहिए।'}
    now=time.time();cached=_CACHE.get(('archive',));archive_error=None
    if cached and now-cached['at']<TTL_SECONDS:pages=cached['pages'];archive_error=cached.get('error')
    else:
        try:
            with httpx.Client(timeout=30,follow_redirects=True,headers={'User-Agent':'MeraUPSC/1.0'}) as c:pages=_discover_exam_pages(c)
            if not pages:archive_error='UPSC archive से परीक्षा पृष्ठ नहीं मिले।'
        except Exception as e:pages=[];archive_error=f'{type(e).__name__}: UPSC archive उपलब्ध नहीं है।'
        _CACHE[('archive',)]={'at':now,'pages':pages,'error':archive_error}
    selected=[p for p in pages if p['exam']==exam and (year is None or p['year']==int(year))];papers=[];failed_pages=[]
    try:
        with httpx.Client(timeout=30,follow_redirects=True,headers={'User-Agent':'MeraUPSC/1.0'}) as c:
            for page in selected:
                key=('page',page['url']);pc=_CACHE.get(key)
                if pc and now-pc['at']<TTL_SECONDS:rows=pc['rows']
                else:
                    try:rows=_paper_links(_fetch_html(c,page['url']),page['url'],page['exam'],page['year'])
                    except Exception:rows=[];failed_pages.append(page['url'])
                    _CACHE[key]={'at':now,'rows':rows}
                papers.extend(rows)
    except Exception:failed_pages.extend(p['url'] for p in selected)
    if subject:
        needle=subject.lower().strip();papers=[r for r in papers if needle in r['title'].lower()]
    papers.sort(key=lambda r:(r['year'],r['title']),reverse=True);years=sorted({p['year'] for p in pages if p['exam']==exam},reverse=True)
    return {'source':'UPSC','source_page':ARCHIVE_PAGE,'exam':exam,'year':year,'papers':papers,'paper_count':len(papers),'years_available':years,'year_count':len(years),'archive_reachable':bool(pages),'archive_error':archive_error,'failed_source_pages':failed_pages,'bank_type':'official_pyq','ai_generated':False,'separate_from_ai_bank':True,'note':'केवल UPSC की आधिकारिक वेबसाइट से मिले प्रश्नपत्र दिखाए जाते हैं; AI प्रश्न अलग प्रश्न बैंक में रहते हैं।'}
