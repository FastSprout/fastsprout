"""Add generated example pages to the Learn navigation."""

import os
import re
import subprocess
import sys
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


def example_source(markdown: str, root: Path) -> Path:
    sources = re.findall(
        r"^<!-- example-source: ([^>]+\.py) -->$", markdown, flags=re.M
    )
    if len(sources) != 1:
        raise ValueError(
            "Example output needs exactly one Python source snippet"
        )
    source = (root / sources[0]).resolve()
    if not source.is_relative_to(root.resolve()):
        raise ValueError(f"Example source escapes the repository: {source}")
    return source


def run_python_example(source: Path, root: Path) -> str:
    environment = os.environ.copy()
    source_path = str(root / "src")
    if previous_path := environment.get("PYTHONPATH"):
        source_path += os.pathsep + previous_path
    environment["PYTHONPATH"] = source_path
    run = subprocess.run(
        [sys.executable, str(source)],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if run.returncode:
        raise RuntimeError(
            f"{source.relative_to(root)} failed with exit code {run.returncode}:\n"
            f"{run.stderr}"
        )
    output = run.stdout.rstrip("\n")
    if not output:
        raise ValueError(f"{source.relative_to(root)} did not print a result")
    return output


def replace_result_block(markdown: str, output: str) -> str:
    section = re.search(
        r"(?ms)^## Result[ \t]*\n(?P<body>.*?)(?=^## |\Z)", markdown
    )
    if section is None:
        raise ValueError("Example page is missing a Result section")
    body = section.group("body")
    block = f"```text\n{output}\n```"
    existing = re.search(r"(?ms)^```text\n.*?^```[ \t]*$", body)
    if existing:
        updated = body[: existing.start()] + block + body[existing.end() :]
    else:
        ending = "\n\n" if section.end("body") < len(markdown) else "\n"
        updated = body.rstrip() + "\n\n" + block + ending
    if section.end("body") == len(markdown):
        updated = updated.rstrip() + "\n"
    return (
        markdown[: section.start("body")]
        + updated
        + markdown[section.end("body") :]
    )


def replace_source_block(markdown: str, source: Path) -> str:
    block = re.search(r"(?ms)^```python\n.*?^```[ \t]*$", markdown)
    if block is None:
        raise ValueError(f"Missing Python code block for {source}")
    replacement = (
        f"```python\n{source.read_text(encoding='utf-8').rstrip()}\n```"
    )
    return markdown[: block.start()] + replacement + markdown[block.end() :]


def render_example_output(markdown: str, root: Path) -> str:
    if "<!-- example-source:" not in markdown:
        return markdown
    source = example_source(markdown, root)
    output = run_python_example(source, root)
    updated = replace_source_block(markdown, source)
    return replace_result_block(updated, output)


def on_page_markdown(markdown, page, config, files):
    root = Path(config["config_file_path"]).parent
    return render_example_output(markdown, root)
