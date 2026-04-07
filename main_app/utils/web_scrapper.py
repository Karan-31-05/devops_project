import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import urllib3

ACOE_URL = "https://acoe.annauniv.edu/"

def fetch_acoe_updates():
    """
    Scrapes 'Important Updates...' section from ACOE site.
    Returns: list of dicts -> [{message: "...", link_text: "...", link_url: "..."}]
    """

    headers = {"User-Agent": "Mozilla/5.0"}

    # NOTE: ACOE sometimes throws SSL verify issue in some environments.
    # If you face SSL error, keep verify=False. In production, better to fix SSL certificates.
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    r = requests.get(ACOE_URL, headers=headers, timeout=10, verify=False)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    scroll_div = soup.select_one("div.box div.scroll")
    if not scroll_div:
        return []

    # Full message text (clean)
    full_message = scroll_div.get_text(" ", strip=True)

    updates = []

    # Get all links (Click Here PDFs mostly)
    links = scroll_div.select("a[href]")

    # If there is at least one link, attach it
    if links:
        for a in links:
            updates.append({
                "message": full_message,
                "link_text": a.get_text(strip=True) or "Open",
                "link_url": urljoin(ACOE_URL, a["href"]),
                "source": "ACOE - Anna University",
            })
    else:
        # No link case
        updates.append({
            "message": full_message,
            "link_text": None,
            "link_url": None,
            "source": "ACOE - Anna University",
        })

    return updates
