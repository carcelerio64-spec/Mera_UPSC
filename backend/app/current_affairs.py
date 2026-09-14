import os
from datetime import datetime, timezone
from urllib.parse import urljoin

import feedparser
import httpx
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, String, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./upsc.db')
connect_args = {'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionCA = sessionmaker(bind=engine, autocommit=False, autoflush=False)

class CABase(DeclarativeBase):
    pass

class CurrentAffair(CABase):
    __tablename__ = 'current_affairs'
    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(String(120), index=True)
    source_type: Mapped[str] = mapped_column(String(30), default='official')
    source_url: Mapped[str] = mapped_column(String(800), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(600))
    summary: Mapped[str] = mapped_column(Text, default='')
    subject: Mapped[str] = mapped_column(String(120), index=True)
    prelims_relevance: Mapped[str] = mapped_column(Text, default='')
    mains_relevance: Mapped[str] = mapped_column(Text, default='')
    published_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

CABase.metadata.create_all(engine)

SUBJECT_RULES = {
    'राजव्यवस्था': ['constitution','constitutional','parliament','supreme court','high court','election','governance','ministry of law','cabinet','लोकसभा','राज्यसभा','संविधान','न्यायालय','चुनाव','शासन'],
    'अर्थव्यवस्था': ['economy','economic','finance','bank','rbi','sebi','inflation','gdp','tax','budget','market','bond','investment','trade','वित्त','अर्थव्यवस्था','बैंक','बजट','कर','बाजार','निवेश'],
    'पर्यावरण': ['environment','climate','biodiversity','forest','wildlife','pollution','renewable','green','पर्यावरण','जलवायु','जैव विविधता','वन','प्रदूषण'],
    'विज्ञान एवं प्रौद्योगिकी': ['isro','space','satellite','technology','science','ai ','artificial intelligence','quantum','semiconductor','research','अंतरिक्ष','उपग्रह','प्रौद्योगिकी','विज्ञान','कृत्रिम बुद्धिमत्ता'],
    'भूगोल': ['earthquake','cyclone','monsoon','river','ocean','geography','disaster','भूकंप','चक्रवात','मानसून','नदी','महासागर','आपदा'],
    'इतिहास एवं संस्कृति': ['culture','heritage','archaeology','museum','ancient','medieval','freedom','culture ministry','संस्कृति','विरासत','पुरातत्व','स्वतंत्रता'],
    'अंतरराष्ट्रीय संबंध': ['foreign affairs','external affairs','bilateral','summit','g20','united nations','treaty','diplomatic','international','विदेश','द्विपक्षीय','संयुक्त राष्ट्र','शिखर सम्मेलन'],
    'सामाजिक मुद्दे': ['health','education','women','child','poverty','nutrition','skill','social justice','स्वास्थ्य','शिक्षा','महिला','बाल','पोषण','कौशल','सामाजिक न्याय'],
    'कृषि': ['agriculture','farmer','crop','food processing','fertilizer','irrigation','कृषि','किसान','फसल','उर्वरक','सिंचाई'],
    'आंतरिक सुरक्षा': ['home affairs','security','cyber security','terror','border','defence','defense','सुरक्षा','सीमा','रक्षा','साइबर']
}

PIB_FEEDS = [
    ('PIB Hindi', 'https://pib.gov.in/RssMain.aspx?ModId=6&Lang=2&Regid=3'),
    ('PIB English', 'https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=1'),
]

HTML_SOURCES = [
    ('ISRO Press', 'https://www.isro.gov.in/Press.html', 'isro.gov.in'),
    ('SEBI Press Releases', 'https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=6&ssid=23', 'sebi.gov.in'),
]

def classify_subject(text: str) -> str:
    hay = (text or '').lower()
    best_subject, best_score = 'समसामयिकी', 0
    for subject, words in SUBJECT_RULES.items():
        score = sum(1 for word in words if word in hay)
        if score > best_score:
            best_subject, best_score = subject, score
    return best_subject

def build_relevance(subject: str) -> tuple[str, str]:
    return (
        f'{subject} से जुड़े तथ्य, संस्था, योजना, स्थान, रिपोर्ट और शब्दावली Prelims के लिए देखें।',
        f'{subject} के संदर्भ में पृष्ठभूमि, महत्व, चुनौतियाँ, सरकारी पहल और आगे की राह Mains के लिए तैयार करें।'
    )

def save_item(source_name: str, url: str, title: str, summary: str = '', published_at: datetime | None = None) -> bool:
    title = ' '.join((title or '').split())[:600]
    if not title or not url:
        return False
    subject = classify_subject(f'{title} {summary}')
    prelims, mains = build_relevance(subject)
    s = SessionCA()
    try:
        if s.query(CurrentAffair).filter(CurrentAffair.source_url == url).first():
            return False
        row = CurrentAffair(
            source_name=source_name,
            source_url=url,
            title=title,
            summary=' '.join((summary or '').split())[:4000],
            subject=subject,
            prelims_relevance=prelims,
            mains_relevance=mains,
            published_at=published_at or datetime.now(timezone.utc),
            fetched_at=datetime.now(timezone.utc),
        )
        s.add(row)
        s.commit()
        return True
    finally:
        s.close()

def fetch_pib() -> int:
    added = 0
    for source_name, feed_url in PIB_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:100]:
            title = entry.get('title', '')
            url = entry.get('link', '')
            summary = entry.get('summary', '')
            published_at = None
            parsed = entry.get('published_parsed') or entry.get('updated_parsed')
            if parsed:
                published_at = datetime(*parsed[:6], tzinfo=timezone.utc)
            if save_item(source_name, url, title, summary, published_at):
                added += 1
    return added

def fetch_html_sources() -> int:
    added = 0
    headers = {'User-Agent': 'MeraUPSC/1.0 (+official-public-information-reader)'}
    with httpx.Client(timeout=30, follow_redirects=True, headers=headers) as client:
        for source_name, page_url, domain_hint in HTML_SOURCES:
            try:
                response = client.get(page_url)
                response.raise_for_status()
            except Exception:
                continue
            soup = BeautifulSoup(response.text, 'html.parser')
            seen = set()
            for a in soup.find_all('a', href=True):
                title = ' '.join(a.get_text(' ', strip=True).split())
                href = urljoin(page_url, a['href'])
                if not title or len(title) < 18 or domain_hint not in href or href in seen:
                    continue
                seen.add(href)
                if source_name.startswith('SEBI') and not any(k in href.lower() for k in ['press', 'homeaction', 'news']):
                    continue
                if source_name.startswith('ISRO') and not any(k in href.lower() for k in ['press', 'release', '.html']):
                    continue
                if save_item(source_name, href, title):
                    added += 1
                if len(seen) >= 80:
                    break
    return added

def ingest_daily() -> dict:
    pib_added = fetch_pib()
    html_added = fetch_html_sources()
    return {'ok': True, 'pib_added': pib_added, 'government_added': html_added, 'total_added': pib_added + html_added}

def list_items(subject: str | None = None, limit: int = 50) -> list[dict]:
    s = SessionCA()
    try:
        q = s.query(CurrentAffair)
        if subject:
            q = q.filter(CurrentAffair.subject == subject)
        rows = q.order_by(CurrentAffair.published_at.desc(), CurrentAffair.id.desc()).limit(max(1, min(limit, 200))).all()
        return [{
            'id': r.id,
            'source_name': r.source_name,
            'source_url': r.source_url,
            'title': r.title,
            'summary': r.summary,
            'subject': r.subject,
            'prelims_relevance': r.prelims_relevance,
            'mains_relevance': r.mains_relevance,
            'published_at': r.published_at.isoformat() if r.published_at else None,
            'fetched_at': r.fetched_at.isoformat() if r.fetched_at else None,
        } for r in rows]
    finally:
        s.close()
