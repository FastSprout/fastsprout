import ast
from pathlib import Path


def get_file_docstring(file_path: Path) -> str | None:
    return ast.get_docstring(ast.parse(file_path.read_text(encoding="utf-8")))


ROOT = Path(__file__).parent.parent

EXAMPLES_DIR = ROOT / "examples"


LAYER_DESCIPTION = {
    "data": """Run from the repository root. The second example uses the development
dependency `aiosqlite` and creates two temporary in-memory databases.

```bash
uv run --extra data-sql python {example}
```
""",
    "core": """Runnable snippets. Each file is self-contained. Run from the repository root with the SQL extra used by these examples:

```bash
uv run --extra data-sql python {example}
```
""",
}


for layer_path in EXAMPLES_DIR.iterdir():
    layer_name = layer_path.name
    if layer_name not in LAYER_DESCIPTION:
        print(f"{layer_name.upper()} Layer skipped for docs generation")
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
