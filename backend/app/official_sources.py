from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup
from .current_affairs import save_item

OFFICIAL_SOURCES = [
    {'name':'RBI','url':'https://www.rbi.org.in/','domain':'rbi.org.in','subject':'अर्थव्यवस्था'},
    {'name':'SEBI','url':'https://www.sebi.gov.in/','domain':'sebi.gov.in','subject':'अर्थव्यवस्था'},
    {'name':'India Budget','url':'https://www.indiabudget.gov.in/','domain':'indiabudget.gov.in','subject':'अर्थव्यवस्था'},
    {'name':'Economic Survey','url':'https://www.indiabudget.gov.in/economicsurvey/','domain':'indiabudget.gov.in','subject':'अर्थव्यवस्था'},
    {'name':'MoSPI','url':'https://www.mospi.gov.in/','domain':'mospi.gov.in','subject':'अर्थव्यवस्था'},
    {'name':'NITI Aayog','url':'https://www.niti.gov.in/publications/division-reports','domain':'niti.gov.in','subject':None},
    {'name':'Election Commission','url':'https://www.eci.gov.in/','domain':'eci.gov.in','subject':'राजव्यवस्था'},
    {'name':'Parliamentary Affairs','url':'https://mpa.gov.in/','domain':'mpa.gov.in','subject':'राजव्यवस्था'},
    {'name':'DARPG','url':'https://darpg.gov.in/','domain':'darpg.gov.in','subject':'राजव्यवस्था'},
    {'name':'MEA','url':'https://www.mea.gov.in/press-releases.htm','domain':'mea.gov.in','subject':'अंतरराष्ट्रीय संबंध'},
    {'name':'MoEFCC','url':'https://moef.gov.in/','domain':'moef.gov.in','subject':'पर्यावरण'},
    {'name':'IMD','url':'https://mausam.imd.gov.in/','domain':'imd.gov.in','subject':'भूगोल'},
    {'name':'ISRO','url':'https://www.isro.gov.in/Press.html','domain':'isro.gov.in','subject':'विज्ञान एवं प्रौद्योगिकी'},
    {'name':'DST','url':'https://dst.gov.in/','domain':'dst.gov.in','subject':'विज्ञान एवं प्रौद्योगिकी'},
    {'name':'DBT','url':'https://dbtindia.gov.in/','domain':'dbtindia.gov.in','subject':'विज्ञान एवं प्रौद्योगिकी'},
    {'name':'MeitY','url':'https://www.meity.gov.in/','domain':'meity.gov.in','subject':'विज्ञान एवं प्रौद्योगिकी'},
    {'name':'Agriculture Ministry','url':'https://agriwelfare.gov.in/','domain':'agriwelfare.gov.in','subject':'कृषि'},
    {'name':'ICAR','url':'https://icar.gov.in/','domain':'icar.gov.in','subject':'कृषि'},
    {'name':'Health Ministry','url':'https://www.mohfw.gov.in/','domain':'mohfw.gov.in','subject':'सामाजिक मुद्दे'},
    {'name':'Education Ministry','url':'https://www.education.gov.in/','domain':'education.gov.in','subject':'सामाजिक मुद्दे'},
    {'name':'Women and Child Development','url':'https://wcd.gov.in/','domain':'wcd.gov.in','subject':'सामाजिक मुद्दे'},
    {'name':'Social Justice Ministry','url':'https://socialjustice.gov.in/','domain':'socialjustice.gov.in','subject':'सामाजिक मुद्दे'},
    {'name':'Tribal Affairs','url':'https://tribal.nic.in/','domain':'tribal.nic.in','subject':'सामाजिक मुद्दे'},
    {'name':'Rural Development','url':'https://rural.gov.in/','domain':'rural.gov.in','subject':'सामाजिक मुद्दे'},
    {'name':'Culture Ministry','url':'https://www.indiaculture.gov.in/','domain':'indiaculture.gov.in','subject':'इतिहास एवं संस्कृति'},
    {'name':'ASI','url':'https://asi.nic.in/','domain':'asi.nic.in','subject':'इतिहास एवं संस्कृति'}
]

RELEVANT_TERMS = [
    'policy','scheme','mission','programme','program','report','index','survey','bill','act','rules','guidelines',
    'budget','economic','inflation','gdp','monetary','fiscal','trade','investment','agriculture','farmer','crop',
    'environment','climate','biodiversity','forest','wildlife','pollution','energy','renewable','disaster','cyclone',
    'science','technology','space','satellite','artificial intelligence','semiconductor','quantum','biotechnology','digital',
    'health','education','nutrition','women','child','tribal','poverty','employment','skill','social justice',
    'constitution','election','parliament','governance','court','commission','federal','rights',
    'international','bilateral','summit','agreement','treaty','foreign','culture','heritage','archaeology',
    'नीति','योजना','मिशन','कार्यक्रम','रिपोर्ट','सूचकांक','सर्वेक्षण','विधेयक','अधिनियम','नियम','दिशानिर्देश',
    'बजट','अर्थव्यवस्था','मुद्रास्फीति','कृषि','किसान','पर्यावरण','जलवायु','जैव विविधता','विज्ञान','प्रौद्योगिकी',
    'स्वास्थ्य','शिक्षा','महिला','बाल','जनजाति','रोजगार','संविधान','चुनाव','संसद','शासन','अंतरराष्ट्रीय','संस्कृति'
]

NOISE_TERMS = ['tender','vacancy','recruitment','career','procurement','quotation','auction','login','contact us','sitemap','निविदा','भर्ती','रिक्ति','करियर','लॉगिन','संपर्क']

def is_relevant(title:str, href:str) -> bool:
    text=f'{title} {href}'.lower()
    if any(x in text for x in NOISE_TERMS):
        return False
    return any(x in text for x in RELEVANT_TERMS)

def ingest_official_sources(per_source_limit:int=40) -> dict:
    added=0; checked=0; failed=[]
    headers={'User-Agent':'MeraUPSC/1.0 public-information-reader'}
    with httpx.Client(timeout=25, follow_redirects=True, headers=headers) as client:
        for source in OFFICIAL_SOURCES:
            try:
                r=client.get(source['url']); r.raise_for_status(); soup=BeautifulSoup(r.text,'html.parser')
            except Exception as exc:
                failed.append({'source':source['name'],'error':type(exc).__name__}); continue
            seen=set(); count=0
            for a in soup.find_all('a',href=True):
                title=' '.join(a.get_text(' ',strip=True).split())
                href=urljoin(source['url'],a['href'])
                if len(title)<15 or source['domain'] not in href or href in seen:
                    continue
                seen.add(href)
                if not is_relevant(title,href):
                    continue
                checked+=1
                decorated=f"[{source['subject']}] {title}" if source.get('subject') else title
                if save_item(source['name'],href,decorated):
                    added+=1
                count+=1
                if count>=per_source_limit:
                    break
    return {'added':added,'checked':checked,'failed_sources':failed,'sources_total':len(OFFICIAL_SOURCES)}
