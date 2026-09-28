import ast
from itertools import groupby
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT / "examples"
LEARN_DIR = ROOT / "docs/learn/examples"

LAYER_DESCRIPTION = {
    "core": """The core layer defines typed schemas, fields, actions, and DTO
visibility shared by the other layers. Run from the repository root; the SQL
entity examples need the data-sql extra:

```bash
uv run --extra data-sql python {example}
```
""",
    "data": """The data layer routes entities to persistence backends through DataR.
It provides CRUD capabilities, streams, joins, and data events. The SQL
examples use in-memory SQLite and the development dependency `aiosqlite`.
Run from the repository root:

```bash
uv run --extra data-sql --extra events python {example}
```
""",
    "events": """The events layer publishes events through EventBus, delivers them
to subscribers, tracks results, and runs scheduled publishers and middleware.
Run from the repository root with the events extra:

```bash
uv run --extra events python {example}
```
""",
}
RUN_COMMAND = {
    "core": "uv run --extra data-sql python",
    "data": "uv run --extra data-sql --extra events python",
    "events": "uv run --extra events python",
}
TITLE_WORDS = {
    "datar": "DataR",
    "dto": "DTO",
    "orm": "ORM",
    "pyd": "Pydantic",
    "sql": "SQL",
}


def summary(path: Path) -> str:
    docstring = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8")))
    return (docstring or "").splitlines()[0] if docstring else ""


def page_name(path: Path) -> tuple[str, str]:
    number, _, words = path.stem.partition("_")
    title = " ".join(
        TITLE_WORDS.get(word, word.title()) for word in words.split("_")
    )
    slug = "-".join(
        TITLE_WORDS.get(word, word).lower() for word in words.split("_")
    )
    return f"{int(number)}. {title}", f"{int(number)}-{slug}"


def shared_title(titles: list[str]) -> str:
    prefix = []
    for words in zip(*(title.split() for title in titles), strict=False):
        if len(set(words)) != 1:
            break
        prefix.append(words[0])
    return " ".join(prefix)


learn = [
    "# Examples",
    "",
    "Runnable examples from this version of FastSprout. Each example has its own page.",
    "",
]

for layer, description in LAYER_DESCRIPTION.items():
    examples = sorted((EXAMPLES_DIR / layer).glob("*.py"))
    if not examples:
        continue

    first_example = f"examples/{layer}/{examples[0].name}"
    readme = [
        f"# {layer.upper()} Examples",
        "",
        description.format(example=first_example).rstrip(),
        "",
        "---",
        "",
        "| File | Shows |",
        "| --- | --- |",
    ]
    readme.extend(
        f"| [{example.name}]({example.name}) | {summary(example)} |"
        for example in examples
    )
    (EXAMPLES_DIR / layer / "README.md").write_text(
        "\n".join(readme) + "\n", encoding="utf-8"
    )

    layer_docs = LEARN_DIR / layer
    layer_docs.mkdir(parents=True, exist_ok=True)
    for old_page in layer_docs.glob("*.md"):
        old_page.unlink()

    learn.extend((f"## {layer.title()}", ""))
    entries = []
    for example in examples:
        source = f"examples/{layer}/{example.name}"
        title, slug = page_name(example)
        page = layer_docs / f"{slug}.md"
        number, _, name = title.partition(". ")
        entries.append((int(number), name, f"{layer}/{page.name}"))
        notes = example.with_suffix(".md").read_text(encoding="utf-8")
        explanation, separator, result = notes.partition("\n## Result\n")
        if not separator:
            raise ValueError(
                f"Missing ## Result section in {example.with_suffix('.md')}"
            )
        explanation, annotations_heading, annotations = explanation.partition(
            "\n## Annotations\n"
        )
        page_parts = [
            f"# {title}",
            "",
            explanation.strip(),
            "",
            "Run from the repository root:",
            "",
            "```bash",
            f"{RUN_COMMAND[layer]} {source}",
            "```",
            "",
            "## Source",
            "",
            "```python",
            f'--8<-- "{source}"',
            "```",
            "",
        ]
        if annotations_heading:
            page_parts.extend((annotations.strip(), ""))
        page_parts.extend(("## Result", "", result.strip(), ""))
        page.write_text(
            "\n".join(page_parts),
            encoding="utf-8",
        )
    for number, grouped in groupby(entries, key=lambda entry: entry[0]):
        variants = list(grouped)
        if len(variants) == 1:
            _, title, url = variants[0]
            learn.append(f"{number}. [{title}]({url})")
            continue
        common = shared_title([title for _, title, _ in variants])
        links = " · ".join(
            f"[{title.removeprefix(common).strip() or 'Overview'}]({url})"
            for _, title, url in variants
        )
        learn.append(f"{number}. **{common}** — {links}")
    learn.append("")

LEARN_DIR.mkdir(parents=True, exist_ok=True)
(LEARN_DIR / "index.md").write_text(
    "\n".join(learn).rstrip() + "\n", encoding="utf-8"
)
