"""Mirror built documentation pages and navigation into a GitLab wiki."""

import argparse
import json
import shutil
from functools import partial
from pathlib import Path
from typing import TypedDict
from urllib.parse import quote, urljoin, urlsplit, urlunsplit

if __package__:
    from .docs_nav import Navigation
    from .llms_full import SITE_URL, ArticleMarkdown
else:
    from docs_nav import Navigation
    from llms_full import SITE_URL, ArticleMarkdown


class DocumentationVersion(TypedDict):
    version: str
    title: str
    aliases: list[str]


def page_route(relative: Path) -> str:
    path = (
        relative.parent
        if relative.stem == "index"
        else relative.with_suffix("")
    )
    return path.as_posix().removeprefix(".").strip("/")


def sidebar(items: Navigation, base: str, depth: int = 0) -> list[str]:
    lines = []
    for item in items:
        for title, value in item.items():
            label = (
                f"[{title}]({base}/{quote(Path(value).with_suffix('').as_posix())})"
                if isinstance(value, str)
                else title
            )
            lines.append(f"{'  ' * depth}- {label}")
            if isinstance(value, list):
                lines.extend(sidebar(value, base, depth + 1))
    return lines


def rewrite_link(url: str, base: str, links: dict[str, str]) -> str:
    parsed = urlsplit(urljoin(base, url))
    plain = urlunsplit(parsed._replace(query="", fragment=""))
    target = links.get(plain)
    if target is None:
        return parsed.geturl()
    return (
        target
        + (f"?{parsed.query}" if parsed.query else "")
        + (f"#{parsed.fragment}" if parsed.fragment else "")
    )


def page_links(
    site: Path, versions: list[DocumentationVersion], wiki_url: str
) -> tuple[dict[str, str], list[Path]]:
    links: dict[str, str] = {}
    pages: list[Path] = []
    for version in versions:
        slug = version["version"]
        for page in sorted((site / slug).rglob("*.md")):
            relative = page.relative_to(site / slug)
            pages.append(Path(slug) / relative)
            target = f"{wiki_url}/{quote((Path(slug) / relative.with_suffix('')).as_posix())}"
            for alias in (slug, *version["aliases"]):
                root = f"{SITE_URL}/{alias}/"
                route = page_route(relative)
                links[root + (f"{route}/" if route else "")] = target
                links[root + relative.as_posix()] = target
                links[root + (f"{route}/" if route else "") + "index.html"] = (
                    target
                )
    links[SITE_URL + "/"] = f"{wiki_url}/home"
    return links, pages


def copy_assets(
    site: Path,
    destination: Path,
    versions: list[DocumentationVersion],
    wiki_url: str,
    links: dict[str, str],
) -> None:
    for version in versions:
        slug = version["version"]
        for asset in (site / slug / "assets").rglob("*"):
            if asset.suffix.lower() in {
                ".svg",
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp",
            }:
                relative = asset.relative_to(site / slug)
                target = destination / slug / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(asset, target)
                for alias in (slug, *version["aliases"]):
                    links[f"{SITE_URL}/{alias}/{relative.as_posix()}"] = (
                        f"{wiki_url}/{quote(f'{slug}/{relative}')}"
                    )


def write_sidebar(
    site: Path,
    destination: Path,
    versions: list[DocumentationVersion],
    wiki_url: str,
) -> None:
    navigation = []
    for version in versions:
        slug = version["version"]
        items: Navigation = json.loads(
            (site / slug / "navigation.json").read_text(encoding="utf-8")
        )
        navigation.extend([f"## {version['title']}", ""])
        navigation.extend(sidebar(items, f"{wiki_url}/{quote(slug)}"))
        navigation.append("")
    (destination / "_sidebar.md").write_text(
        "\n".join(navigation).rstrip() + "\n", encoding="utf-8"
    )


def write_page(
    site: Path, destination: Path, relative: Path, links: dict[str, str]
) -> None:
    route = page_route(relative)
    article = ArticleMarkdown()
    article.feed(
        (site / route / "index.html").read_text(encoding="utf-8"),
        partial(rewrite_link, base=f"{SITE_URL}/{route}/", links=links),
    )
    if not article.blocks:
        raise ValueError(f"No article in {relative}")
    target = destination / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(article.markdown(), encoding="utf-8")


def export(site: Path, destination: Path, wiki_url: str) -> None:
    versions: list[DocumentationVersion] = json.loads(
        (site / "versions.json").read_text(encoding="utf-8")
    )
    latest = next(
        version["version"]
        for version in versions
        if "latest" in version["aliases"]
    )
    destination.mkdir(parents=True, exist_ok=False)
    links, pages = page_links(site, versions, wiki_url)
    copy_assets(site, destination, versions, wiki_url, links)
    write_sidebar(site, destination, versions, wiki_url)
    for relative in pages:
        write_page(site, destination, relative, links)
    shutil.copyfile(destination / latest / "index.md", destination / "home.md")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--wiki-url", required=True)
    args = parser.parse_args()
    export(args.site, args.output, args.wiki_url.rstrip("/"))


if __name__ == "__main__":
    main()
