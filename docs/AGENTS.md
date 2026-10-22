# Documentation rules

Read `src/AGENTS.md` for shared rules. Paths are relative to the repository root.

Write documentation in English and describe the implemented API. Use source
docstrings for API reference and `examples/` for runnable example code.

Keep Learn examples under `docs/learn/examples/`, with one page per example
and nested chapters matching the numbered example directories. Use readable
numbered titles rather than raw filenames. Update the source and use the
existing `scripts/generate_readme_docs.py` pipeline instead of maintaining
copied code blocks by hand. Do not invent example output.

Keep `AGENTS.md` files out of the published site, search index, sitemap, and
LLM documentation. Preserve the exclusion in `mkdocs.yml` when adding nested
instruction files. Validate publishing changes with a strict MkDocs build.
