# 1. Your first action

An HTTP handler and a worker can both need to prepare a task title. Put that
operation in one callable function so both entry points can use it. This first
step trims a title and returns a typed draft.

## Install

Use Python 3.12, 3.13, or 3.14. This tutorial follows development; PyPI release
`0.1.1` predates `fastsprout.actions`. Run the examples from a development
checkout:

```bash
git clone --branch development https://github.com/FastSprout/fastsprout.git
cd fastsprout
uv sync
```

<details markdown="1">
<summary>Install in another project</summary>

Install the same development version directly:

```bash
pip install 'fastsprout @ git+https://github.com/FastSprout/fastsprout.git@development'
```

</details>

The first three steps use application actions. Add the SQL extra when you
reach [storing tasks](tutorial/entity-operations.md). For a published PyPI
package, select its matching documentation version.

## Prepare a task title

Save this program as `docs_src/quickstart.py` in the checkout. The file is
already included so you can also run it immediately.

<!-- example-source: docs_src/quickstart.py -->

```{.python}
--8<-- "docs_src/quickstart.py"
```

Run it from the repository root:

```bash
uv run python -m docs_src.quickstart
```

## Result

```text
Write documentation
```

## What happened?

`NewTask` describes the input: a title supplied by a caller. `TaskDraft`
describes the result. Both inherit from `BaseSchema`, using ordinary Python
type annotations for their fields.

`@action` wraps the async function as an action and preserves its callable
signature. `await prepare_task(...)` runs it and returns a `TaskDraft`; its
`title` has the surrounding spaces removed. The action has the same calling
interface for an HTTP handler, a worker, or a test.

Try changing the input to another title. An empty string is also a string, so
this version accepts it. The next step adds the application rule that rejects
an empty title, then shares that rule between two actions.

Continue to [2. Share a check between actions](tutorial/shared-checks.md).
