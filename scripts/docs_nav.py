"""Add generated example pages to the Learn navigation."""

from itertools import groupby
from pathlib import Path


def page_title(page: Path) -> str:
    return page.read_text(encoding="utf-8").splitlines()[0][2:]


def shared_name(titles: list[str]) -> str:
    words = [title.partition(". ")[2].split() for title in titles]
    prefix = []
    for parts in zip(*words, strict=False):
        if len(set(parts)) != 1:
            break
        prefix.append(parts[0])
    return " ".join(prefix)


def example_pages(docs_dir: Path, layer: str) -> list[dict]:
    pages = sorted(
        (docs_dir / "learn" / "examples" / layer).glob("*.md"),
        key=lambda page: (int(page.stem.partition("-")[0]), page.stem),
    )
    items = []
    for number, grouped in groupby(
        pages, key=lambda page: int(page.stem.partition("-")[0])
    ):
        variants = list(grouped)
        if len(variants) == 1:
            page = variants[0]
            items.append(
                {page_title(page): f"learn/examples/{layer}/{page.name}"}
            )
            continue
        common = shared_name([page_title(page) for page in variants])
        children = [
            {
                page_title(page).partition(". ")[2].removeprefix(common).strip()
                or "Overview": f"learn/examples/{layer}/{page.name}"
            }
            for page in variants
        ]
        items.append({f"{number}. {common}": children})
    return items


def on_config(config):
    examples = [{"Overview": "learn/examples/index.md"}]
    docs_dir = Path(config["docs_dir"])
    for layer in ("core", "data", "events"):
        pages = example_pages(docs_dir, layer)
        if pages:
            examples.append({layer.title(): pages})
    for item in config["nav"]:
        if "Learn" in item:
            item["Learn"] = [{"Examples": examples}]
            break
    return config
