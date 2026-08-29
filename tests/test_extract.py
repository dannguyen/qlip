from pathlib import Path

import pytest
from curl_cffi.requests.exceptions import HTTPError

from qlip.extract import _strip_site_suffix, extract, fetch

FIXTURE = Path(__file__).parent / "fixtures" / "cwbchicago.html"
URL = (
    "https://cwbchicago.com/2022/08/"
    "chicago-police-20-minute-response-driver-killed-wounded-jeffery-pub.html"
)


def test_extract_reproduces_expected_fields():
    rec = extract(FIXTURE.read_text(encoding="utf-8"), URL)
    assert rec["url"] == URL
    assert rec["title"] == (
        "Chicago police took more than 20 minutes to arrive after "
        "driver killed 3, wounded 2 outside Jeffery Pub"
    )
    assert rec["site"] == "cwbchicago.com"
    assert rec["date"] == "2022-08-16T06:55:45+00:00"
    assert rec["description"] == (
        "Chicago police needed more than 20 minutes to arrive after a driver "
        "killed 3 men and injured another in an apparently intentional attack "
        "outside Jeffrey Pub."
    )


def test_all_fields_present_even_when_missing():
    rec = extract("<html><head></head><body></body></html>", "https://example.com/p")
    assert set(rec) == {"url", "title", "site", "date", "description"}
    assert rec["title"] is None
    assert rec["date"] is None
    assert rec["description"] is None
    assert rec["site"] == "example.com"


def test_site_strips_leading_www():
    rec = extract("<html></html>", "https://www.example.com/x")
    assert rec["site"] == "example.com"


def test_title_falls_back_to_title_tag_and_strips_site_suffix():
    html = (
        "<html><head>"
        '<meta property="og:site_name" content="Acme News">'
        "<title>Big Story - Acme News</title>"
        "</head></html>"
    )
    rec = extract(html, "https://acme.test/")
    assert rec["title"] == "Big Story"


def test_date_falls_back_to_time_element():
    html = (
        '<html><body><time datetime="2024-01-02T03:04:05Z">Jan 2</time></body></html>'
    )
    rec = extract(html, "https://acme.test/")
    assert rec["date"] == "2024-01-02T03:04:05Z"


class FakeResponse:
    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise HTTPError(f"{self.status_code} for url")


class FakeSession:
    """Records every .get() call and replays canned responses in order."""

    def __init__(self, *responses):
        self._responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(kwargs)
        return self._responses.pop(0)


def test_fetch_returns_body_on_success_without_impersonation():
    session = FakeSession(FakeResponse(200, "<html>ok</html>"))
    assert fetch("https://example.com/", session=session) == "<html>ok</html>"
    [call] = session.calls
    assert "impersonate" not in call


@pytest.mark.parametrize("blocked_status", [403, 429])
def test_fetch_falls_back_to_chrome_impersonation_when_blocked(blocked_status):
    session = FakeSession(
        FakeResponse(blocked_status), FakeResponse(200, "<html>via chrome</html>")
    )
    assert fetch("https://example.com/", session=session) == "<html>via chrome</html>"
    plain, impersonated = session.calls
    assert impersonated["impersonate"] == "chrome"
    # Impersonation supplies real Chrome headers; ours must not override them.
    assert "headers" not in impersonated


def test_fetch_raises_when_impersonation_is_also_blocked():
    session = FakeSession(FakeResponse(403), FakeResponse(403))
    with pytest.raises(HTTPError):
        fetch("https://example.com/", session=session)
    assert len(session.calls) == 2


def test_fetch_does_not_retry_on_ordinary_http_errors():
    session = FakeSession(FakeResponse(404))
    with pytest.raises(HTTPError):
        fetch("https://example.com/", session=session)
    assert len(session.calls) == 1


def test_strip_site_suffix_helper():
    assert _strip_site_suffix("Headline - Site", "Site") == "Headline"
    assert _strip_site_suffix("Headline | Site", "Site") == "Headline"
    assert _strip_site_suffix("Headline", "Site") == "Headline"
    assert _strip_site_suffix("A - B - Site", "Site") == "A - B"
    # No matching suffix -> unchanged.
    assert _strip_site_suffix("Site of Wonders", "Site") == "Site of Wonders"
