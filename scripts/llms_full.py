"""Export rendered documentation as one Markdown file per version."""

import re
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from markdownify import MarkdownConverter, markdownify

SITE_URL = "https://fastsprout.dev"


class ArticleConverter(MarkdownConverter):
    def convert_a(self, el: Tag, text: str, parent_tags: set[str]) -> str:
        if el.find_parent(["pre", "code"]) is not None:
            return text
        if el.get("id") and not el.get("href"):
            return str(el)
        return markdownify(str(el)).strip()


def code_language(element: Tag) -> str:
    for parent in (element, *element.parents):
        for name in parent.get_attribute_list("class"):
            if isinstance(name, str) and name.startswith("language-"):
                return name.removeprefix("language-")
    return ""


class ArticleMarkdown:
    """Export rendered articles for full-text documentation."""

    def __init__(self) -> None:
        self.blocks: list[str] = []

    def feed(
        self, data: str, rewrite_link: Callable[[str], str] | None = None
    ) -> None:
        soup = BeautifulSoup(data, "html.parser")
        article = soup.select_one("article.md-content__inner")
        if article is None:
            return
        for decorative in article.select(
            ".headerlink, .md-content__button, svg"
        ):
            decorative.decompose()
        for heading in article.select(
            "h1[id], h2[id], h3[id], h4[id], h5[id], h6[id]"
        ):
            heading.insert_before(soup.new_tag("a", id=str(heading["id"])))
        if rewrite_link is not None:
            self.rewrite_links(article, rewrite_link)
        self.blocks.append(
            ArticleConverter(
                heading_style="ATX", code_language_callback=code_language
            )
            .convert_soup(article)
            .strip()
        )

    def markdown(self) -> str:
        return "\n\n".join(self.blocks) + "\n"

    @staticmethod
    def rewrite_links(article: Tag, rewrite: Callable[[str], str]) -> None:
        for tag in article.select("[href], [src]"):
            for attribute in ("href", "src"):
                value = tag.get(attribute)
                if isinstance(value, str):
                    tag[attribute] = rewrite(value)


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
