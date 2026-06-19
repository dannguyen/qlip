"""Command-line entry point for qlip."""

from __future__ import annotations

import sys

import click
import requests

from .extract import extract, fetch
from .render import FORMATS, render


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("url", required=False)
@click.option(
    "-f",
    "--format",
    "fmt",
    type=click.Choice(FORMATS, case_sensitive=False),
    default="yaml",
    show_default=True,
    help="Output format.",
)
@click.version_option(package_name="qlip", prog_name="qlip")
def main(url, fmt):
    """Fetch URL and print its metadata (url, title, site, date, description).

    With no URL argument (or "-"), read URLs from stdin, one per line — so you
    can pipe them, e.g. `pbpaste | qlip | pbcopy`.
    """
    urls = _resolve_urls(url)

    records = []
    for target in urls:
        try:
            html = fetch(target)
        except requests.RequestException as exc:
            raise click.ClickException(f"failed to fetch {target}: {exc}") from exc
        records.append(extract(html, target))

    click.echo(render(records, fmt))


def _resolve_urls(url):
    """Return the list of URLs to process: the argument, or stdin lines."""
    if url is None or url == "-":
        if url is None and sys.stdin.isatty():
            raise click.UsageError(
                "no URL provided; pass one as an argument or pipe it via stdin"
            )
        urls = [line.strip() for line in sys.stdin if line.strip()]
        if not urls:
            raise click.UsageError("no URL found on stdin")
        return urls
    return [url]


if __name__ == "__main__":  # pragma: no cover
    main()
