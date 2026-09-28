"""Export rendered documentation as one Markdown file per version."""

import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

SITE_URL = "https://fastsprout.dev"


class ArticleMarkdown(HTMLParser):
    """Extract readable Markdown from the rendered API reference article."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_article = False
        self.block: str | None = None
        self.fragments: list[str] = []
        self.blocks: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if (
            tag == "article"
            and ("class", "md-content__inner md-typeset") in attrs
        ):
            self.in_article = True
        elif (
            self.in_article
            and self.block is None
            and tag
            in {"h1", "h2", "h3", "h4", "h5", "h6", "p", "pre", "li", "summary"}
        ):
            self.block = tag
            self.fragments = []

    def handle_data(self, data: str) -> None:
        if self.block is not None:
            self.fragments.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == self.block:
            value = "".join(self.fragments).strip()
            if value:
                self.blocks.append(self.format_block(tag, value))
            self.block = None
            self.fragments = []
        elif tag == "article":
            self.in_article = False

    @staticmethod
    def format_block(tag: str, value: str) -> str:
        if tag.startswith("h") and len(tag) == 2:
            return f"{'#' * int(tag[1])} {value.splitlines()[0].strip()}"
        if tag == "pre":
            return f"```python\n{value}\n```"
        if tag == "li":
            return f"- {value}"
        return value

    def markdown(self) -> str:
        return "\n\n".join(self.blocks) + "\n"


def page_url(relative: Path, slug: str) -> str:
    if relative.parts[0] == "api":
        target = (
            relative.parent
            if relative.stem == "index"
            else relative.with_suffix("")
        )
        return f"{SITE_URL}/{slug}/{target.as_posix()}/"
    return f"{SITE_URL}/{slug}/{relative.as_posix()}"


def absolute_links(content: str, base_url: str) -> str:
    return re.sub(
        r"\]\(([^)]+)\)",
        lambda match: f"]({urljoin(base_url, match.group(1))})",
        content,
    )


def write_full(
    destination: Path,
    slug: str,
    site_name: str,
    site_description: str,
    pages: list[tuple[Path, str]],
) -> None:
    """Write the complete Markdown and rendered API docs for one version."""
    full = [f"# {site_name}", "", f"> {site_description}"]
    for relative, title in pages:
        url = page_url(relative, slug)
        content = (destination / relative).read_text(encoding="utf-8").rstrip()
        if re.search(r"^::: ", content, flags=re.M):
            rendered = destination / relative.with_suffix("") / "index.html"
            article = ArticleMarkdown()
            article.feed(rendered.read_text(encoding="utf-8"))
            if not article.blocks:
                raise ValueError(f"No rendered API content in {rendered}")
            content = article.markdown().rstrip()
        content = absolute_links(content, url)
        full.extend(
            (
                "",
                "---",
                "",
                f"[Source: {title}]({url})",
                "",
                content,
            )
        )
    (destination / "llms-full.txt").write_text(
        "\n".join(full).rstrip() + "\n", encoding="utf-8"
    )
