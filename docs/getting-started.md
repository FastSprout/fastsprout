# 1. Your first action

An HTTP handler and a worker can both need to prepare a task title. Put that
operation in one callable function so both entry points can use it. This first
step trims a title and returns a typed draft.

## Install

Use Python 3.12-3.14. Create a tutorial directory and virtual environment:

```bash
mkdir fastsprout-tutorial
cd fastsprout-tutorial
python -m venv .venv
source .venv/bin/activate
python -m pip install fastsprout
mkdir -p docs_src/tutorial docs_src/data
```

Keep this environment active and save each example at the path shown. The
examples import code from earlier steps using these paths.

The first three steps use application actions. Add the SQL extra when you
reach [storing tasks](tutorial/entity-operations.md).

## Prepare a task title

Save this program as `docs_src/quickstart.py` in your tutorial directory.

<!-- example-source: docs_src/quickstart.py -->

```{.python}
--8<-- "docs_src/quickstart.py"
```

Run it from `fastsprout-tutorial`, the directory containing `docs_src`:

```bash
python -m docs_src.quickstart
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
