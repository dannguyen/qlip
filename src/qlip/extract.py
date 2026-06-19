"""Fetch a URL and extract a fixed set of page metadata fields."""

from __future__ import annotations

from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# Output field order. Drives YAML key order and CSV columns, so keep it stable.
FIELDS = ("url", "title", "site", "date", "description")

# A browser-like UA; the bare ``python-requests`` default gets 403'd by many sites.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
)

DEFAULT_TIMEOUT = 15

# Separators SEO plugins put between a headline and the site name,
# e.g. "Headline - Site Name" or "Headline | Site Name".
_TITLE_SEPARATORS = (" - ", " | ", " – ", " — ", " :: ", " · ", " • ")


def fetch(url, *, timeout=DEFAULT_TIMEOUT, session=None):
    """Download ``url`` and return its HTML as text.

    Raises ``requests.RequestException`` (incl. non-2xx via ``raise_for_status``).
    """
    getter = session or requests
    resp = getter.get(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.text


def extract(html, url):
    """Parse ``html`` into a metadata record.

    Always returns a dict with every key in :data:`FIELDS`; values that can't be
    found are ``None``. ``url`` is echoed back verbatim and used to derive ``site``.
    """
    soup = BeautifulSoup(html, "html.parser")

    site_name = _meta(soup, "og:site_name")

    raw_title = _first(
        _meta(soup, "og:title"),
        _meta(soup, "twitter:title"),
        _title_tag(soup),
    )

    return {
        "url": url,
        "title": _strip_site_suffix(raw_title, site_name),
        "site": _site_from_url(url),
        "date": _first(
            _meta(soup, "article:published_time"),
            _meta(soup, "og:updated_time"),
            _meta(soup, "article:modified_time"),
            _time_datetime(soup),
        ),
        "description": _first(
            _meta(soup, "og:description"),
            _meta(soup, "twitter:description"),
            _meta(soup, "description"),
        ),
    }


def _meta(soup, key):
    """Return the trimmed ``content`` of a ``<meta>`` matched by property or name."""
    tag = soup.find("meta", attrs={"property": key}) or soup.find(
        "meta", attrs={"name": key}
    )
    if tag is None:
        return None
    content = tag.get("content")
    if not content:
        return None
    return content.strip() or None


def _title_tag(soup):
    if soup.title is None:
        return None
    text = soup.title.get_text(strip=True)
    return text or None


def _time_datetime(soup):
    tag = soup.find("time")
    if tag is None:
        return None
    value = tag.get("datetime")
    return value.strip() if value and value.strip() else None


def _site_from_url(url):
    netloc = urlparse(url).netloc
    if netloc.startswith("www."):
        netloc = netloc[len("www.") :]
    return netloc or None


def _strip_site_suffix(title, site_name):
    """Drop a trailing ``"<sep><site_name>"`` (e.g. ``" - CWB Chicago"``)."""
    if not title or not site_name:
        return title
    for sep in _TITLE_SEPARATORS:
        suffix = f"{sep}{site_name}"
        if title.endswith(suffix):
            return title[: -len(suffix)].strip() or title
    return title


def _first(*values):
    for value in values:
        if value:
            return value
    return None
