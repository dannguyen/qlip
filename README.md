# qlip

A command-line tool that prints page metadata — `url`, `title`, `site`, `date`,
and `description` — for a given URL, in YAML (default), JSON, or CSV.

## Install

```bash
pip install -e .
```

## Usage

```bash
qlip [URL] [--format {yaml,json,csv}]
```

- `URL` — the page to inspect. Optional: if omitted (or given as `-`), URLs are
  read from stdin, one per line (blank lines ignored). This makes it pipe-friendly:

  ```bash
  pbpaste | qlip | pbcopy
  ```

- `-f, --format` — output format; one of `yaml`, `json`, `csv`. Default: `yaml`.

### Example

```bash
$ qlip https://cwbchicago.com/2022/08/chicago-police-20-minute-response-driver-killed-wounded-jeffery-pub.html
```

```yaml
- url: https://cwbchicago.com/2022/08/chicago-police-20-minute-response-driver-killed-wounded-jeffery-pub.html
  title: Chicago police took more than 20 minutes to arrive after driver killed 3, wounded 2 outside Jeffery Pub
  site: cwbchicago.com
  date: '2022-08-16T06:55:45+00:00'
  description: |-
    Chicago police needed more than 20 minutes to arrive after a driver killed 3 men and injured another in an apparently intentional attack outside Jeffrey Pub.
```

## How fields are resolved

| field | source (first match wins) |
| --- | --- |
| `url` | the URL you passed, verbatim |
| `title` | `og:title` → `twitter:title` → `<title>`, with a trailing `" - <site name>"` suffix stripped |
| `site` | the URL's domain (`www.` stripped) |
| `date` | `article:published_time` → `og:updated_time` → `article:modified_time` → `<time datetime>` (full timestamp, as published) |
| `description` | `og:description` → `twitter:description` → `<meta name="description">` |

Fields that can't be found are emitted as `null` (YAML/JSON) or an empty cell (CSV).
Output is always a collection (a YAML/JSON list, CSV rows) to keep the shape stable
for multiple URLs later.

## Development

```bash
pip install -e ".[test]"
pytest
```
