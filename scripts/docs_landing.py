"""Publish the latest docs landing page at the site root."""

from pathlib import Path

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
