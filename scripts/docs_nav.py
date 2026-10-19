"""Add generated example pages to the Learn navigation."""

import os
import re
import subprocess
import sys
from itertools import groupby, takewhile
from pathlib import Path

TITLE_WORDS = {
    "api": "API",
    "crud": "CRUD",
    "datar": "DataR",
    "dto": "DTO",
    "orm": "ORM",
    "pyd": "Pydantic",
    "sql": "SQL",
}

type Navigation = list[dict[str, str | Navigation]]


def example_parts(path: Path) -> tuple[tuple[int, str], ...]:
    """Read numbered chapters from parent directories and the filename."""
    chapters = [
        name for name in path.parts[:-1] if re.fullmatch(r"\d+_[a-z_]+", name)
    ]
    return tuple(
        part
        for name in (*chapters, path.stem)
        for part in _numbered_parts(name)
    )


def _numbered_parts(name: str) -> tuple[tuple[int, str], ...]:
    parts: list[tuple[int, str]] = []
    number: int | None = None
    words: list[str] = []
    for token in name.replace("-", "_").split("_"):
        if token.isdecimal():
            if number is not None:
                parts.append((number, title_words(words)))
            number, words = int(token), []
        else:
            words.append(token)
    if number is None or not words:
        raise ValueError(f"Example needs a numbered name: {name}")
    parts.append((number, title_words(words)))
    return tuple(parts)


def title_words(words: list[str]) -> str:
    return " ".join(TITLE_WORDS.get(word, word.title()) for word in words)


def _common_words(words: list[list[str]]) -> list[str]:
    return [
        parts[0]
        for parts in takewhile(
            lambda parts: len(set(parts)) == 1,
            zip(*words, strict=False),
        )
    ]


def shared_name(titles: list[str]) -> str:
    words = [title.split() for title in titles]
    prefix = _common_words(words)
    if prefix:
        return " ".join(prefix)
    suffix = _common_words([list(reversed(item)) for item in words])
    return " ".join(reversed(suffix))


def relative_name(title: str, common: str) -> str:
    if title == common:
        return "Overview"
    if title.startswith(f"{common} "):
        return title[len(common) + 1 :]
    if title.endswith(f" {common}"):
        return title[: -len(common) - 1]
    return title


def page_title(page: Path) -> str:
    return page.read_text(encoding="utf-8").splitlines()[0][2:]


def example_pages(docs_dir: Path, layer: str) -> Navigation:
    layer_dir = docs_dir / "learn" / "examples" / layer
    pages = sorted(
        (
            page
            for page in layer_dir.rglob("*.md")
            if "<!-- example-source:" in page.read_text(encoding="utf-8")
        ),
        key=lambda page: tuple(
            (int(part.partition("-")[0]), part)
            for part in page.relative_to(layer_dir).parts
        ),
    )
    return _example_nav(pages, layer_dir, layer)


def _example_nav(
    pages: list[Path], layer_dir: Path, layer: str, depth: int = 0
) -> Navigation:
    items: Navigation = []
    for name, grouped in groupby(
        pages, key=lambda page: page.relative_to(layer_dir).parts[depth]
    ):
        descendants = list(grouped)
        if name.endswith(".md"):
            page = descendants[0]
            relative = page.relative_to(layer_dir).as_posix()
            items.append(
                {page_title(page): f"learn/examples/{layer}/{relative}"}
            )
        else:
            number, title = example_parts(Path(name))[0]
            items.append(
                {
                    f"{number}. {title}": _example_nav(
                        descendants, layer_dir, layer, depth + 1
                    )
                }
            )
    return items


def on_config(config):
    examples: Navigation = [{"Overview": "learn/examples/index.md"}]
    docs_dir = Path(config["docs_dir"])
    for layer in ("core", "actions", "data", "events", "testing"):
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
    command = [sys.executable, str(source)]
    if source.is_relative_to(root / "examples/testing"):
        command = [
            sys.executable,
            "-m",
            "pytest",
            str(source),
            "-p",
            "fastsprout.testing.core.plugin",
            "-qq",
            "--no-header",
            "-o",
            "addopts=",
            "-o",
            "verbosity_test_cases=1",
        ]
    run = subprocess.run(
        command,
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
