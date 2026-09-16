import re
import time
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

BASE = 'https://www.upsc.gov.in'
ARCHIVE_PAGE = BASE + '/examinations/previous-question-papers'
_CACHE = {}
TTL_SECONDS = 6 * 60 * 60


def _clean(value: str) -> str:
    return ' '.join((value or '').split())


def _kind(title: str) -> str:
    t = title.lower()
    if 'essay' in t:
        return 'essay'
    if 'general studies' in t:
        return 'general_studies'
    if 'english' in t or 'compulsory' in t or 'language' in t:
        return 'qualifying_language'
    if 'paper i' in t or 'paper ii' in t or 'paper-i' in t or 'paper-ii' in t:
        return 'optional_or_language'
    return 'other'


def _exam_kind(text: str) -> str | None:
    t = text.lower()
    if 'civil services' not in t:
        return None
    if 'preliminary' in t or 'prelims' in t:
        return 'prelims'
    if 'main' in t or 'mains' in t:
        return 'mains'
    return None


def _year(text: str) -> int | None:
    match = re.search(r'\b(19\d{2}|20\d{2})\b', text)
    return int(match.group(1)) if match else None


def _fetch_html(client: httpx.Client, url: str) -> BeautifulSoup:
    response = client.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'html.parser')


def _paper_links(soup: BeautifulSoup, page_url: str, exam: str, year: int):
    rows = []
    seen = set()
    for a in soup.find_all('a', href=True):
        title = _clean(a.get_text(' ', strip=True))
        href = urljoin(page_url, a['href'])
        low = (title + ' ' + href).lower()
        if not title or href in seen:
            continue
        if '.pdf' not in low and '/sites/default/files/' not in low:
            continue
        if exam == 'prelims' and not any(x in low for x in ('general studies', 'question paper', 'paper-i', 'paper-ii', 'paper i', 'paper ii')):
            continue
        if exam == 'mains' and not any(x in low for x in ('paper', 'essay', 'general studies', 'compulsory', 'english', 'language')):
            continue
        seen.add(href)
        rows.append({
            'year': year,
            'exam': exam,
            'title': title,
            'url': href,
            'kind': _kind(title),
            'source': 'UPSC',
            'is_official_pyq': True,
        })
    return rows


def _discover_exam_pages(client: httpx.Client):
    soup = _fetch_html(client, ARCHIVE_PAGE)
    pages = []
    seen = set()
    for a in soup.find_all('a', href=True):
        title = _clean(a.get_text(' ', strip=True))
        href = urljoin(ARCHIVE_PAGE, a['href'])
        combined = title + ' ' + href
        exam = _exam_kind(combined)
        year = _year(combined)
        if not exam or not year or href in seen:
            continue
        seen.add(href)
        pages.append({'exam': exam, 'year': year, 'title': title, 'url': href})
    return pages


def fetch_official_pyq(exam: str = 'mains', year: int | None = None, subject: str | None = None):
    exam = exam.lower().strip()
    if exam not in {'prelims', 'mains'}:
        return {'source': 'UPSC', 'papers': [], 'error': 'परीक्षा प्रकार prelims या mains होना चाहिए।'}

    cache_key = ('archive',)
    now = time.time()
    cached = _CACHE.get(cache_key)
    if cached and now - cached['at'] < TTL_SECONDS:
        pages = cached['pages']
    else:
        try:
            with httpx.Client(timeout=30, follow_redirects=True, headers={'User-Agent': 'MeraUPSC/1.0'}) as client:
                pages = _discover_exam_pages(client)
        except Exception:
            pages = []
        _CACHE[cache_key] = {'at': now, 'pages': pages}

    selected = [p for p in pages if p['exam'] == exam and (year is None or p['year'] == int(year))]
    papers = []
    try:
        with httpx.Client(timeout=30, follow_redirects=True, headers={'User-Agent': 'MeraUPSC/1.0'}) as client:
            for page in selected:
                key = ('page', page['url'])
                page_cached = _CACHE.get(key)
                if page_cached and now - page_cached['at'] < TTL_SECONDS:
                    rows = page_cached['rows']
                else:
                    try:
                        rows = _paper_links(_fetch_html(client, page['url']), page['url'], page['exam'], page['year'])
                    except Exception:
                        rows = []
                    _CACHE[key] = {'at': now, 'rows': rows}
                papers.extend(rows)
    except Exception:
        papers = []

    if subject:
        needle = subject.lower().strip()
        papers = [row for row in papers if needle in row['title'].lower()]

    papers.sort(key=lambda row: (row['year'], row['title']), reverse=True)
    return {
        'source': 'UPSC',
        'source_page': ARCHIVE_PAGE,
        'exam': exam,
        'year': year,
        'papers': papers,
        'years_available': sorted({p['year'] for p in pages if p['exam'] == exam}, reverse=True),
        'note': 'केवल UPSC की आधिकारिक वेबसाइट से मिले प्रश्नपत्र दिखाए जाते हैं; AI प्रश्न अलग प्रश्न बैंक में रहते हैं।',
    }
