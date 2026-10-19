import ast
import re
from itertools import groupby
from pathlib import Path

if __package__:
    from .docs_nav import (  # type: ignore[import-not-found]
        Navigation,
        example_pages,
        example_parts,
        render_example_output,
        run_python_example,
        shared_name,
    )
else:
    from docs_nav import (
        Navigation,
        example_pages,
        example_parts,
        render_example_output,
        run_python_example,
        shared_name,
    )

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT / "examples"
LEARN_DIR = ROOT / "docs/learn/examples"

README_BRAND = (
    "# FastSprout\n\n"
    '<img src="https://raw.githubusercontent.com/FastSprout/fastsprout/development/assets/fastsprout-mark.svg" alt="FastSprout logo" width="100" height="100">\n\n'
    "**Typed building blocks for Python backends.**\n\n"
)
DOCS_BRAND = (
    "# FastSprout { .fs-visually-hidden }\n\n"
    '<div class="fs-brand" aria-label="FastSprout">\n'
    '  <img src="assets/fastsprout-mark.svg" alt="" width="100" height="100">\n'
    "  <span>FastSprout</span>\n"
    "</div>\n\n"
    '<p class="fs-lead">Typed building blocks for Python backends.</p>\n\n'
)
project_readme = (ROOT / "README.md").read_text(encoding="utf-8")
if not project_readme.startswith(README_BRAND):
    raise ValueError("README.md brand header changed")
(ROOT / "docs/index.md").write_text(
    DOCS_BRAND + project_readme[len(README_BRAND) :], encoding="utf-8"
)
(ROOT / "docs/security.md").write_text(
    (ROOT / "SECURITY.md").read_text(encoding="utf-8"), encoding="utf-8"
)

LAYER_DESCRIPTION = {
    "core": """The core layer defines typed schemas, fields, actions, and DTO
visibility shared by the other layers. Run from the repository root:

```bash
uv run python {example}
```

The SQL entity examples need `--extra data-sql`.
""",
    "actions": """Actions are ordinary async functions or callable classes.
Services group them into a typed API, and workflows connect them by Python
reference. Run from the repository root:

```bash
uv run --extra standard python {example}
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
    "testing": """Pytest fixtures and tests declare typed BDD phases. Share cases
through fixtures and base classes; property tests use Hypothesis.
Run from the repository root:

```bash
uv run --extra testing pytest -p fastsprout.testing.core.plugin -o addopts= {example}
```
""",
}


def summary(path: Path) -> str:
    docstring = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8")))
    return (docstring or "").splitlines()[0] if docstring else ""


def description(path: Path) -> str:
    docstring = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8")))
    if not docstring:
        return example_parts(path)[-1][1] + "."
    return "\n".join(
        line for line in docstring.splitlines() if not line.startswith("Run:")
    ).strip()


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9-]", "", name.lower().replace(" ", "-"))


def example_page(layer: str, example: Path) -> tuple[Path, str]:
    parts = example_parts(example)
    folders = [f"{number}-{slug(title)}" for number, title in parts[:-1]]
    number, title = parts[-1]
    page = LEARN_DIR / layer / Path(*folders) / f"{number}-{slug(title)}.md"
    source = example.relative_to(ROOT).as_posix()
    content = [
        f"# {number}. {title}",
        "",
        f"<!-- example-source: {source} -->",
        "",
        description(example),
        "",
        "## Source",
        "",
        "```python",
        example.read_text(encoding="utf-8").rstrip(),
        "```",
        "",
        "## Result",
        "",
        "```text",
        run_python_example(example, ROOT),
        "```",
        "",
    ]
    return page, "\n".join(content)


def index_links(items: Navigation, depth: int = 0) -> list[str]:
    lines = []
    for item in items:
        label, target = next(iter(item.items()))
        indentation = "  " * depth
        if isinstance(target, str):
            url = target.removeprefix("learn/examples/")
            lines.append(f"{indentation}- [{label}]({url})")
        else:
            lines.append(f"{indentation}- **{label}**")
            lines.extend(index_links(target, depth + 1))
    return lines


learn = [
    "# Examples",
    "",
    "Runnable examples from this version of FastSprout, organized by chapter.",
    "Each Result block is generated by running its Python source.",
    "",
]
generated: dict[str, set[Path]] = {}
readmes: dict[Path, str] = {}
pages: dict[Path, str] = {}

for layer, layer_description in LAYER_DESCRIPTION.items():
    examples = sorted(
        (
            path
            for path in (EXAMPLES_DIR / layer).rglob("*.py")
            if path.name != "__init__.py"
            and path.read_text(encoding="utf-8").strip()
        ),
        key=example_parts,
    )
    generated[layer] = set()
    if not examples:
        continue

    if layer != "actions":
        first_example = examples[0].relative_to(ROOT).as_posix()
        layer_readme = [
            f"# {layer.upper()} Examples",
            "",
            layer_description.format(example=first_example).rstrip(),
            "",
        ]
        for number, grouped in groupby(
            examples, key=lambda path: example_parts(path)[0][0]
        ):
            variants = list(grouped)
            title = shared_name(
                [example_parts(path)[0][1] for path in variants]
            )
            layer_readme.extend(
                (
                    f"## {number}. {title or 'Examples'}",
                    "",
                    "| File | Shows |",
                    "| --- | --- |",
                )
            )
            for path in variants:
                relative = path.relative_to(EXAMPLES_DIR / layer).as_posix()
                layer_readme.append(
                    f"| [{relative}]({relative}) | {summary(path)} |"
                )
            layer_readme.append("")
        readmes[EXAMPLES_DIR / layer / "README.md"] = (
            "\n".join(layer_readme).rstrip() + "\n"
        )

    for example in examples:
        page, content = example_page(layer, example)
        generated[layer].add(page)
        pages[page] = content

for path, content in readmes.items():
    path.write_text(content, encoding="utf-8")
for layer, expected in generated.items():
    layer_docs = LEARN_DIR / layer
    layer_docs.mkdir(parents=True, exist_ok=True)
    for old_page in layer_docs.rglob("*.md"):
        if old_page in expected:
            continue
        content = old_page.read_text(encoding="utf-8")
        if (
            "<!-- example-source:" in content
            or "<!-- generated-examples:" in content
        ):
            old_page.unlink()
for path, content in pages.items():
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

for layer in LAYER_DESCRIPTION:
    if not generated[layer]:
        continue
    learn.extend((f"## {layer.title()}", ""))
    learn.extend(index_links(example_pages(ROOT / "docs", layer)))
    learn.append("")

LEARN_DIR.mkdir(parents=True, exist_ok=True)
(LEARN_DIR / "index.md").write_text(
    "\n".join(learn).rstrip() + "\n", encoding="utf-8"
)

for page in sorted((ROOT / "docs").rglob("*.md")):
    if page.is_relative_to(LEARN_DIR):
        continue
    content = page.read_text(encoding="utf-8")
    if "<!-- example-source:" in content:
        page.write_text(render_example_output(content, ROOT), encoding="utf-8")
