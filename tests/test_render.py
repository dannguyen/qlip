import csv
import io
import json

import pytest
import yaml

from qlip.render import render

RECORD = {
    "url": "https://ex.com/a",
    "title": "Police killed 3, wounded 2",
    "site": "ex.com",
    "date": "2022-08-16T06:55:45+00:00",
    "description": 'A description, with a comma and a "quote".',
}

EMPTY = {
    "url": "https://ex.com/b",
    "title": None,
    "site": "ex.com",
    "date": None,
    "description": None,
}


def test_yaml_is_block_description_ordered_and_roundtrips():
    out = render([RECORD], "yaml")
    assert "description: |" in out  # literal block scalar (| or |-)
    loaded = yaml.safe_load(out)
    assert loaded == [RECORD]  # date stays a string, not parsed to datetime
    assert list(loaded[0].keys()) == ["url", "title", "site", "date", "description"]


def test_yaml_missing_fields_are_null():
    loaded = yaml.safe_load(render([EMPTY], "yaml"))
    assert loaded[0]["title"] is None
    assert loaded[0]["description"] is None


def test_json_is_list_of_objects():
    assert json.loads(render([RECORD], "json")) == [RECORD]


def test_csv_header_and_single_row():
    rows = list(csv.reader(io.StringIO(render([RECORD], "csv"))))
    assert rows[0] == ["url", "title", "site", "date", "description"]
    assert rows[1] == [
        RECORD["url"],
        RECORD["title"],
        RECORD["site"],
        RECORD["date"],
        RECORD["description"],
    ]


def test_csv_missing_fields_are_blank():
    rows = list(csv.reader(io.StringIO(render([EMPTY], "csv"))))
    assert rows[1] == [EMPTY["url"], "", "ex.com", "", ""]


def test_unknown_format_raises():
    with pytest.raises(ValueError):
        render([RECORD], "xml")
