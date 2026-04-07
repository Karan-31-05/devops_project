import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

CIR_BASE = "https://annauniv.edu/cir/"
CIR_JS = urljoin(CIR_BASE, "js/script.js")


def fetch_cir_ticker_announcements(limit=10):
    """
    Scrapes the yellow ticker announcements from CIR by reading js/script.js
    because announcements are injected dynamically into <div class="marquee"></div>.
    Returns:
    [
      { "text": "...", "url": "..." },
      ...
    ]
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(CIR_JS, headers=headers, timeout=10)
        r.raise_for_status()

        js_text = r.text

        # ✅ Extract the marquee HTML inside the JS template string
        # It looks like: const marqueeContent = `<marquee ...> ... </marquee>`;
        m = re.search(r"const\s+marqueeContent\s*=\s*`([\s\S]*?)`;", js_text)
        if not m:
            return []

        marquee_html = m.group(1)

        # Parse the HTML snippet
        soup = BeautifulSoup(marquee_html, "html.parser")

        announcements = []
        for a in soup.select("a[href]"):
            text = a.get_text(" ", strip=True)
            href = a.get("href")

            if not text or not href:
                continue

            announcements.append({
                "text": text,
                "url": urljoin(CIR_BASE, href),
            })

            if len(announcements) >= limit:
                break

        return announcements
    except Exception:
        # Return empty list on network or parsing errors
        return []


def fetch_cir_news(limit=6):
    """
    Scrapes CIR News & Events cards.
    Returns list of dicts with title/date/image/url/link_text
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(CIR_BASE, headers=headers, timeout=10)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        items = []

        cards = soup.select("section.section.bg-gray .card.border-0.rounded-0.hover-shadow")

        for card in cards[:limit]:
            img = card.select_one("img.card-img-top")
            image_url = urljoin(CIR_BASE, img["src"]) if img and img.get("src") else None

            p_title = card.select_one(".card-body > p")
            title = p_title.get_text(" ", strip=True) if p_title else "CIR News"

            a = card.select_one(".card-body a[href]")
            link_url = urljoin(CIR_BASE, a["href"]) if a and a.get("href") else None
            link_text = a.get_text(" ", strip=True) if a else "View"

            date_div = card.select_one(".card-img .card-date")
            date_text = date_div.get_text(" ", strip=True) if date_div else None

            items.append({
                "title": title,
                "date": date_text,
                "url": link_url,
                "link_text": link_text,
                "image": image_url,
            })

        return items
    except Exception:
        # Return empty list on network or parsing errors
        return []
