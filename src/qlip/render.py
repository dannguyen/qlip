"""Render metadata records as YAML, JSON, or CSV.

Every format emits a *collection* of records (a list / multiple rows), which keeps
the shape stable for the eventual multi-URL case.
"""

from __future__ import annotations

import csv
import io
import json

import yaml

from .extract import FIELDS

FORMATS = ("yaml", "json", "csv")


def render(records, fmt):
    """Return ``records`` formatted as ``fmt`` (no trailing newline)."""
    fmt = fmt.lower()
    if fmt == "yaml":
        return _render_yaml(records)
    if fmt == "json":
        return _render_json(records)
    if fmt == "csv":
        return _render_csv(records)
    raise ValueError(f"unknown format: {fmt!r}")


class _LiteralStr(str):
    """Marker type so PyYAML emits the value as a ``|`` literal block scalar."""


def _literal_representer(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style="|")


yaml.add_representer(_LiteralStr, _literal_representer)


def _render_yaml(records):
    data = [_yaml_record(r) for r in records]
    text = yaml.dump(
        data,
        sort_keys=False,  # preserve FIELDS order
        allow_unicode=True,
        default_flow_style=False,
        width=2**20,  # don't line-wrap long scalars (e.g. title)
    )
    return text.rstrip("\n")


def _yaml_record(record):
    out = dict(record)
    description = out.get("description")
    # Only wrap real, non-empty strings — never None (which must stay ``null``).
    if isinstance(description, str) and description:
        out["description"] = _LiteralStr(description)
    return out


def _render_json(records):
    return json.dumps(list(records), indent=2, ensure_ascii=False)


def _render_csv(records):
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=list(FIELDS),
        lineterminator="\n",
        extrasaction="ignore",
    )
    writer.writeheader()
    for record in records:
        writer.writerow({k: _csv_cell(record.get(k)) for k in FIELDS})
    return buffer.getvalue().rstrip("\n")


def _csv_cell(value):
    return "" if value is None else value
