import ast
from pathlib import Path


def get_file_docstring(file_path: Path) -> str | None:
    return ast.get_docstring(ast.parse(file_path.read_text(encoding="utf-8")))


ROOT = Path(__file__).parent.parent

EXAMPLES_DIR = ROOT / "examples"


LAYER_DESCIPTION = {
    "data": """The data layer routes entities to persistence backends through DataR.
It provides CRUD capabilities, streams, joins, and data events. The SQL
examples use in-memory SQLite and the development dependency `aiosqlite`.
Run from the repository root:

```bash
uv run --extra data-sql --extra events python {example}
```
""",
    "core": """The core layer defines typed schemas, fields, actions, and DTO
visibility shared by the other layers. Run from the repository root; the SQL
entity examples need the data-sql extra:

```bash
uv run --extra data-sql python {example}
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


for layer_path in EXAMPLES_DIR.iterdir():
    layer_name = layer_path.name
    if layer_name not in LAYER_DESCIPTION:
        print(f"{layer_name.upper()} Layer skipped for docs generation")  # noqa: T201
        continue

    readme_file = layer_path / "README.md"
    example_files = sorted(layer_path.glob("*.py"), key=lambda x: x.name)
    readme_file.open("w").write(
        "\n".join(
            (
                f"# {layer_name.upper()} Examples",
                "",
                LAYER_DESCIPTION[layer_name].format_map(
                    {"example": "/".join(example_files[0].parts[-3:])}
                ),
                "---",
                "",
                "| File | Shows |\n| --- | --- |",
                *(
                    "| "
                    + " | ".join(
                        (
                            f"[{x.name}]({x.name})",
                            (get_file_docstring(x) or "").split("\n")[0],
                        )
                    )
                    + " |"
                    for x in example_files
                ),
            )
        ).strip()
        + "\n"
    )
