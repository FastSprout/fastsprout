"""Export built documentation pages and navigation for GitLab or GitHub Wiki."""

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


def wiki_page(relative: Path, github: bool) -> str:
    path = relative.with_suffix("")
    return "-".join(path.parts) if github else path.as_posix()


def wiki_file(relative: Path, github: bool) -> Path:
    return Path(wiki_page(relative, github) + ".md")


def sidebar(
    items: Navigation,
    base: str,
    depth: int = 0,
    *,
    prefix: str = "",
    github: bool = False,
) -> list[str]:
    lines = []
    for item in items:
        for title, value in item.items():
            label = (
                f"[{title}]({base}/{quote(wiki_page(Path(prefix) / value, github))})"
                if isinstance(value, str)
                else title
            )
            lines.append(f"{'  ' * depth}- {label}")
            if isinstance(value, list):
                lines.extend(
                    sidebar(
                        value, base, depth + 1, prefix=prefix, github=github
                    )
                )
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
    site: Path,
    versions: list[DocumentationVersion],
    wiki_url: str,
    github: bool = False,
) -> tuple[dict[str, str], list[Path]]:
    links: dict[str, str] = {}
    pages: list[Path] = []
    for version in versions:
        slug = version["version"]
        for page in sorted((site / slug).rglob("*.md")):
            relative = page.relative_to(site / slug)
            pages.append(Path(slug) / relative)
            target = (
                f"{wiki_url}/{quote(wiki_page(Path(slug) / relative, github))}"
            )
            for alias in (slug, *version["aliases"]):
                root = f"{SITE_URL}/{alias}/"
                route = page_route(relative)
                links[root + (f"{route}/" if route else "")] = target
                links[root + relative.as_posix()] = target
                links[root + (f"{route}/" if route else "") + "index.html"] = (
                    target
                )
    links[SITE_URL + "/"] = f"{wiki_url}/{'Home' if github else 'home'}"
    return links, pages


def copy_assets(
    site: Path,
    destination: Path,
    versions: list[DocumentationVersion],
    wiki_url: str,
    links: dict[str, str],
    github: bool = False,
) -> None:
    asset_url = (
        "https://raw.githubusercontent.com/wiki"
        + urlsplit(wiki_url).path.removesuffix("/wiki")
        if github
        else wiki_url
    )
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
                        f"{asset_url}/{quote(f'{slug}/{relative}')}"
                    )


def write_sidebar(
    site: Path,
    destination: Path,
    versions: list[DocumentationVersion],
    wiki_url: str,
    github: bool = False,
) -> None:
    navigation = []
    for version in versions:
        slug = version["version"]
        items: Navigation = json.loads(
            (site / slug / "navigation.json").read_text(encoding="utf-8")
        )
        navigation.extend([f"## {version['title']}", ""])
        navigation.extend(sidebar(items, wiki_url, prefix=slug, github=github))
        navigation.append("")
    (destination / ("_Sidebar.md" if github else "_sidebar.md")).write_text(
        "\n".join(navigation).rstrip() + "\n", encoding="utf-8"
    )


def write_page(
    site: Path,
    destination: Path,
    relative: Path,
    links: dict[str, str],
    github: bool = False,
) -> None:
    route = page_route(relative)
    article = ArticleMarkdown()
    article.feed(
        (site / route / "index.html").read_text(encoding="utf-8"),
        partial(rewrite_link, base=f"{SITE_URL}/{route}/", links=links),
    )
    if not article.blocks:
        raise ValueError(f"No article in {relative}")
    target = destination / wiki_file(relative, github)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(article.markdown(), encoding="utf-8")


def export(
    site: Path, destination: Path, wiki_url: str, github: bool = False
) -> None:
    versions: list[DocumentationVersion] = json.loads(
        (site / "versions.json").read_text(encoding="utf-8")
    )
    latest = next(
        version["version"]
        for version in versions
        if "latest" in version["aliases"]
    )
    links, pages = page_links(site, versions, wiki_url, github)
    targets = [wiki_file(relative, github) for relative in pages]
    if len(targets) != len(set(targets)):
        raise ValueError("Wiki page names collide after flattening paths")
    destination.mkdir(parents=True, exist_ok=False)
    copy_assets(site, destination, versions, wiki_url, links, github)
    write_sidebar(site, destination, versions, wiki_url, github)
    for relative in pages:
        write_page(site, destination, relative, links, github)
    shutil.copyfile(
        destination / wiki_file(Path(latest) / "index.md", github),
        destination / ("Home.md" if github else "home.md"),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--wiki-url", required=True)
    parser.add_argument(
        "--github",
        action="store_true",
        help="Use GitHub Wiki page and asset URLs",
    )
    args = parser.parse_args()
    export(args.site, args.output, args.wiki_url.rstrip("/"), args.github)


if __name__ == "__main__":
    main()
