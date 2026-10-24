"""Publish the docs landing page and version navigation."""

import json
from html import escape
from pathlib import Path

from bs4 import BeautifulSoup

if __package__:
    from .llms_full import SITE_URL, absolute_links
else:
    from llms_full import SITE_URL, absolute_links


def write_landing(output: Path) -> None:
    landing = (output / "latest" / "index.html").read_text(encoding="utf-8")
    landing = landing.replace(
        "<head>",
        '<head><base href="/latest/">'
        '<link rel="alternate" type="text/markdown" href="/index.md">'
        '<link rel="describedby" href="/llms.txt">',
        1,
    )
    (output / "index.html").write_text(landing, encoding="utf-8")

    markdown = absolute_links(
        (output / "latest" / "index.md").read_text(encoding="utf-8"),
        f"{SITE_URL}/latest/index.md",
    )
    markdown = markdown.replace(
        'src="assets/', f'src="{SITE_URL}/latest/assets/'
    )
    (output / "index.md").write_text(markdown, encoding="utf-8")


def write_version_selectors(output: Path, versions: list[str]) -> None:
    for page in output.rglob("*.html"):
        relative = page.relative_to(output)
        current = relative.parts[0] if len(relative.parts) > 1 else "latest"
        if current == "latest":
            current = versions[0]
        soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
        title = soup.select_one('[data-md-component="header-title"]')
        config = soup.select_one("script#__config")
        if title is None or config is None:
            continue
        links = "".join(
            '<li class="md-select__item">'
            f'<a class="md-select__link" href="/{escape(version)}/"'
            + (' aria-current="page"' if version == current else "")
            + f">{escape(version)}</a></li>"
            for version in versions
        )
        selector = BeautifulSoup(
            '<div class="md-header__option" data-fs-version>'
            '<div class="md-select">'
            '<button type="button" class="md-version__current" '
            'aria-label="Select documentation version">'
            f'{escape(current)}</button><div class="md-select__inner">'
            f'<ul class="md-select__list">{links}</ul></div></div></div>',
            "html.parser",
        )
        title.insert_after(selector)
        settings = json.loads(config.get_text())
        settings["version"] = None
        if relative == Path("index.html"):
            settings["base"] = "/latest/"
        config.string = json.dumps(settings)
        page.write_text(str(soup), encoding="utf-8")
