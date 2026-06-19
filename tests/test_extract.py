from pathlib import Path

from qlip.extract import _strip_site_suffix, extract

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


def test_strip_site_suffix_helper():
    assert _strip_site_suffix("Headline - Site", "Site") == "Headline"
    assert _strip_site_suffix("Headline | Site", "Site") == "Headline"
    assert _strip_site_suffix("Headline", "Site") == "Headline"
    assert _strip_site_suffix("A - B - Site", "Site") == "A - B"
    # No matching suffix -> unchanged.
    assert _strip_site_suffix("Site of Wonders", "Site") == "Site of Wonders"
