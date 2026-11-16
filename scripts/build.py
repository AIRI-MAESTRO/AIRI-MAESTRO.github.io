"""Generate GitHub Pages compatibility files for the pre-rename URLs."""

import argparse
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
from urllib.request import urlopen
from xml.etree import ElementTree
from zipfile import ZipFile
from io import BytesIO

HOST = "https://airi-maestro.github.io"
DOCS = "/maestro-docs/"
LANDING = "/maestro-page/"
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def fetch(url):
    with urlopen(url, timeout=30) as response:
        if response.url != url:
            raise ValueError(f"Unexpected redirect for {url}")
        return response.read()


def redirect_html(target):
    link = escape(target, quote=True)
    destination = json.dumps(target)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="robots" content="noindex">
  <title>MAESTRO page moved</title>
  <link rel="canonical" href="{HOST}{link}">
  <script>
    location.replace({destination} + location.search + location.hash);
  </script>
  <noscript><meta http-equiv="refresh" content="0; url={link}"></noscript>
</head>
<body>
  <p>This page moved. <a href="{link}">Continue to MAESTRO</a>.</p>
</body>
</html>
"""


def fallback_html():
    return r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="robots" content="noindex">
  <title>MAESTRO page unavailable</title>
  <script>
    const path = location.pathname;
    const legacy = path.match(/^\/(care-docs|care-page)(\/.*)?$/);
    if (legacy) {
      const prefix = legacy[1] === "care-docs" ? "/maestro-docs" : "/maestro-page";
      location.replace(prefix + (legacy[2] || "/") + location.search + location.hash);
    }
  </script>
</head>
<body>
  <p><a href="/maestro-page/">MAESTRO website</a> · <a href="/maestro-docs/ru/">Documentation</a></p>
</body>
</html>
"""


def docs_path(url):
    parsed = urlsplit(url)
    if (
        f"{parsed.scheme}://{parsed.netloc}" != HOST
        or not parsed.path.startswith(DOCS)
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(f"Unexpected documentation URL: {url}")
    suffix = unquote(parsed.path[len(DOCS):]).strip("/")
    if suffix and any(
        part in {".", ".."} or not re.fullmatch(r"[\w.-]+", part)
        for part in suffix.split("/")
    ):
        raise ValueError(f"Unsafe documentation route: {url}")
    return parsed.path, suffix


def write(output, relative_path, content):
    path = output / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode() if isinstance(content, str) else content)


def build(output):
    sitemap = fetch(HOST + DOCS + "sitemap-index.xml")
    pages = ElementTree.fromstring(sitemap).findall(f"{SITEMAP_NS}sitemap/{SITEMAP_NS}loc")
    routes = set()
    for entry in pages:
        _, filename = docs_path(entry.text)
        if not re.fullmatch(r"sitemap-\d+\.xml", filename):
            raise ValueError(f"Unexpected sitemap filename: {filename}")
        contents = fetch(entry.text)
        write(output, f"care-docs/{filename}", contents)
        for page in ElementTree.fromstring(contents).findall(f"{SITEMAP_NS}url/{SITEMAP_NS}loc"):
            routes.add(docs_path(page.text))

    if not {(DOCS, ""), (DOCS + "ru/", "ru")} <= routes:
        raise ValueError("The live sitemap must include both documentation home pages")
    for target, route in sorted(routes):
        legacy_file = Path("care-docs") / route / "index.html"
        write(output, legacy_file, redirect_html(target))

    skill = fetch(HOST + DOCS + "maestro.skill")
    with ZipFile(BytesIO(skill)) as archive:
        if not any(name.endswith("/SKILL.md") for name in archive.namelist()) or archive.testzip():
            raise ValueError("Invalid maestro.skill archive")
    write(output, "care-docs/maestro.skill", skill)
    write(output, "care-docs/sitemap-index.xml", sitemap)
    write(output, "care-page/index.html", redirect_html(LANDING))
    write(output, "index.html", redirect_html(LANDING))
    write(output, "404.html", fallback_html())
    print(f"Generated {len(routes)} documentation redirects and the legacy skill download")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    build(parser.parse_args().output)
