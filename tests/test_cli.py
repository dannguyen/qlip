from pathlib import Path

import yaml
from click.testing import CliRunner

from qlip import cli

FIXTURE = (Path(__file__).parent / "fixtures" / "cwbchicago.html").read_text(
    encoding="utf-8"
)
URL = (
    "https://cwbchicago.com/2022/08/"
    "chicago-police-20-minute-response-driver-killed-wounded-jeffery-pub.html"
)


def _fake_fetch(monkeypatch):
    """Make cli.fetch return the fixture without hitting the network."""
    monkeypatch.setattr(cli, "fetch", lambda target, **kw: FIXTURE)


def test_url_argument_still_works(monkeypatch):
    _fake_fetch(monkeypatch)
    result = CliRunner().invoke(cli.main, [URL])
    assert result.exit_code == 0
    [record] = yaml.safe_load(result.output)
    assert record["url"] == URL
    assert record["site"] == "cwbchicago.com"


def test_reads_single_url_from_stdin(monkeypatch):
    _fake_fetch(monkeypatch)
    result = CliRunner().invoke(cli.main, [], input=f"{URL}\n")
    assert result.exit_code == 0
    [record] = yaml.safe_load(result.output)
    assert record["url"] == URL


def test_reads_multiple_urls_from_stdin(monkeypatch):
    _fake_fetch(monkeypatch)
    stdin = f"{URL}\n\n  {URL}  \n"  # blank line + surrounding whitespace ignored
    result = CliRunner().invoke(cli.main, [], input=stdin)
    assert result.exit_code == 0
    assert len(yaml.safe_load(result.output)) == 2


def test_dash_argument_reads_stdin(monkeypatch):
    _fake_fetch(monkeypatch)
    result = CliRunner().invoke(cli.main, ["-"], input=f"{URL}\n")
    assert result.exit_code == 0
    assert len(yaml.safe_load(result.output)) == 1


def test_empty_stdin_is_a_usage_error(monkeypatch):
    _fake_fetch(monkeypatch)
    result = CliRunner().invoke(cli.main, [], input="")
    assert result.exit_code != 0
    assert "no URL found on stdin" in result.output
