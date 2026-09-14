import os
from datetime import datetime, timezone, date, timedelta
from urllib.parse import urljoin
import feedparser, httpx
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, String, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
DATABASE_URL=os.getenv('DATABASE_URL','sqlite:///./upsc.db');connect_args={'check_same_thread':False} if DATABASE_URL.startswith('sqlite') else {};engine=create_engine(DATABASE_URL,connect_args=connect_args);SessionCA=sessionmaker(bind=engine,autocommit=False,autoflush=False)
class CABase(DeclarativeBase):pass
class CurrentAffair(CABase):
 __tablename__='current_affairs';id:Mapped[int]=mapped_column(primary_key=True);source_name:Mapped[str]=mapped_column(String(120),index=True);source_type:Mapped[str]=mapped_column(String(30),default='official');source_url:Mapped[str]=mapped_column(String(800),unique=True,index=True);title:Mapped[str]=mapped_column(String(600));summary:Mapped[str]=mapped_column(Text,default='');subject:Mapped[str]=mapped_column(String(120),index=True);prelims_relevance:Mapped[str]=mapped_column(Text,default='');mains_relevance:Mapped[str]=mapped_column(Text,default='');published_at:Mapped[datetime]=mapped_column(DateTime,index=True,default=lambda:datetime.now(timezone.utc));fetched_at:Mapped[datetime]=mapped_column(DateTime,index=True,default=lambda:datetime.now(timezone.utc))
CABase.metadata.create_all(engine)
SUBJECT_RULES={'राजव्यवस्था':['constitution','parliament','court','election','संविधान','चुनाव'],'अर्थव्यवस्था':['economy','finance','rbi','sebi','gdp','budget','अर्थव्यवस्था','बजट'],'पर्यावरण':['environment','climate','biodiversity','पर्यावरण','जलवायु'],'विज्ञान एवं प्रौद्योगिकी':['isro','space','technology','science','अंतरिक्ष','प्रौद्योगिकी'],'भूगोल':['earthquake','cyclone','monsoon','river','भूकंप','मानसून'],'इतिहास एवं संस्कृति':['culture','heritage','archaeology','संस्कृति','विरासत'],'अंतरराष्ट्रीय संबंध':['foreign','bilateral','summit','international','विदेश','द्विपक्षीय'],'सामाजिक मुद्दे':['health','education','women','child','स्वास्थ्य','शिक्षा'],'कृषि':['agriculture','farmer','crop','कृषि','किसान'],'आंतरिक सुरक्षा':['security','border','defence','सुरक्षा','सीमा']}
PIB_FEEDS=[('PIB Hindi','https://pib.gov.in/RssMain.aspx?ModId=6&Lang=2&Regid=3'),('PIB English','https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=1')]
HTML_SOURCES=[('ISRO Press','https://www.isro.gov.in/Press.html','isro.gov.in'),('SEBI Press Releases','https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=6&ssid=23','sebi.gov.in')]
def classify_subject(text):
 hay=(text or '').lower();best='समसामयिकी';score=0
 for sub,words in SUBJECT_RULES.items():
  n=sum(w in hay for w in words)
  if n>score:best,score=sub,n
 return best
def build_relevance(subject):return (f'{subject} से जुड़े तथ्य, संस्था, योजना, स्थान, रिपोर्ट और शब्दावली Prelims के लिए देखें।',f'{subject} के संदर्भ में पृष्ठभूमि, महत्व, चुनौतियाँ, सरकारी पहल और आगे की राह Mains के लिए तैयार करें।')
def save_item(source_name,url,title,summary='',published_at=None):
 title=' '.join((title or '').split())[:600]
 if not title or not url:return False
 s=SessionCA()
 try:
  if s.query(CurrentAffair).filter(CurrentAffair.source_url==url).first():return False
  sub=classify_subject(title+' '+summary);pre,mains=build_relevance(sub);s.add(CurrentAffair(source_name=source_name,source_url=url,title=title,summary=' '.join((summary or '').split())[:4000],subject=sub,prelims_relevance=pre,mains_relevance=mains,published_at=published_at or datetime.now(timezone.utc),fetched_at=datetime.now(timezone.utc)));s.commit();return True
 finally:s.close()
def fetch_pib(backfill_days=7):
 added=0;cutoff=datetime.now(timezone.utc)-timedelta(days=max(1,backfill_days))
 for source,feed_url in PIB_FEEDS:
  feed=feedparser.parse(feed_url)
  for e in feed.entries[:250]:
   parsed=e.get('published_parsed') or e.get('updated_parsed');pub=datetime(*parsed[:6],tzinfo=timezone.utc) if parsed else None
   if pub and pub<cutoff:continue
   if save_item(source,e.get('link',''),e.get('title',''),e.get('summary',''),pub):added+=1
 return added
def fetch_html_sources():
 added=0;headers={'User-Agent':'MeraUPSC/1.0 (+official-public-information-reader)'}
 with httpx.Client(timeout=30,follow_redirects=True,headers=headers) as client:
  for source,page,domain in HTML_SOURCES:
   try:r=client.get(page);r.raise_for_status()
   except Exception:continue
   soup=BeautifulSoup(r.text,'html.parser');seen=set()
   for a in soup.find_all('a',href=True):
    title=' '.join(a.get_text(' ',strip=True).split());href=urljoin(page,a['href'])
    if not title or len(title)<18 or domain not in href or href in seen:continue
    seen.add(href)
    if save_item(source,href,title):added+=1
    if len(seen)>=120:break
 return added
def ingest_daily(backfill_days=7):
 p=fetch_pib(backfill_days);h=fetch_html_sources();return {'ok':True,'backfill_days':backfill_days,'pib_added':p,'government_added':h,'total_added':p+h}
def list_items(subject=None,limit=50,on_date=None):
 s=SessionCA()
 try:
  q=s.query(CurrentAffair)
  if subject:q=q.filter(CurrentAffair.subject==subject)
  if on_date:
   d=date.fromisoformat(on_date);start=datetime(d.year,d.month,d.day);end=start+timedelta(days=1);q=q.filter(CurrentAffair.published_at>=start,CurrentAffair.published_at<end)
  rows=q.order_by(CurrentAffair.published_at.desc(),CurrentAffair.id.desc()).limit(max(1,min(limit,200))).all()
  return [{'id':r.id,'source_name':r.source_name,'source_url':r.source_url,'title':r.title,'summary':r.summary,'subject':r.subject,'prelims_relevance':r.prelims_relevance,'mains_relevance':r.mains_relevance,'published_at':r.published_at.isoformat() if r.published_at else None,'fetched_at':r.fetched_at.isoformat() if r.fetched_at else None} for r in rows]
 finally:s.close()
