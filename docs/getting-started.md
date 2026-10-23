# Getting Started

A task tracker may expose an HTTP endpoint and a worker that both create and
complete tasks. They need the same title checks, missing-task rule, and database
behavior. FastSprout puts that behavior in typed actions and entity services,
then shares persistence work through an explicit data context.

## Install

Use Python 3.12, 3.13, or 3.14. These examples follow the development branch;
PyPI release `0.1.1` predates `fastsprout.actions`. To run the repository examples,
check out development and prepare its environment with uv:

```bash
git clone --branch development https://github.com/FastSprout/fastsprout.git
cd fastsprout
uv sync --extra data-sql
```

The SQL extra enables the adapter used below; the development environment also
includes the async SQLite driver, `aiosqlite`.

To use the same API in another project, install the development package:

```bash
pip install 'fastsprout[data-sql] @ git+https://github.com/FastSprout/fastsprout.git@development' aiosqlite
```

`fastsprout[standard]` bundles the SQL and local events extras. Database drivers
are installed separately. For a PyPI release, select its matching documentation
version. See [Features](features.md) for the problems each layer addresses.

## Define an application operation once

An API endpoint and a worker should apply the same title check when preparing a
task. Here, `@action` makes `prepare_task` a typed callable action, and
`Depends(require_title)` runs the shared check before its body. An empty title
raises `ValueError`; a valid title is normalized and returned as `TaskDraft`.

<!-- example-source: docs_src/quickstart.py -->

```{.python}
--8<-- "docs_src/quickstart.py"
```

The action knows its input, output, and dependencies. Your adapter supplies
`NewTask` and awaits the result. A second action can reuse the same dependency
instead of copying its check.

Run the [source file](https://github.com/FastSprout/fastsprout/blob/development/docs_src/quickstart.py)
from the repository root:

```bash
uv run python docs_src/quickstart.py
```

## Result

```text
Write documentation
```

## Choose the building blocks for a feature

| Building block | Use it for |
| --- | --- |
| `@action` or `Action[Input, Output]` | One application operation with typed arguments and results |
| `Service` | A group of related operations with shared dependencies |
| `DataS[Entity]` | An entity service with CRUD, schemas, pagination, and bulk operations |
| `DataR` | A persistence context that routes operations to entity backends |
| `Workflow` | A sequence or graph of typed operations |

For a task tracker, `Tasks` is an application service. `DataS[Task]` supplies its
standard entity operations, so you can focus on a rule such as completing an
existing task. This complete program defines the entity, its service, and
the SQLite setup:

```{.python}
--8<-- "docs_src/data/quickstart.py"
```

`DataS` handles the CRUD calls and their schema contracts. The custom `complete`
action checks for a missing task and reuses `get` and `update`. Inherit from
`Service` instead when your operations span several entities or do not need
standard CRUD behavior. See the [Actions guide](guide/actions.md) for both styles.

## Put related data operations in one context

`DataR` routes an operation to the entity's persistence backend. For SQL
entities, a `SQLSignpost` points to an async session factory. A DataR context
shares the session associated with that signpost and settles the work when
the context exits.

Pass the same `datar` to the service's create, list, and complete calls. They
then use one context; you choose its boundary around the application operation.
Normal exit finalizes the work, an exception aborts it, and exit releases
resources. This is also where you consume lazy query streams.

The program above creates an in-memory SQLite database, runs the service calls
in `async with DataR()`, and counts the remaining pending tasks through
`datar.stream(query)`. Run it from the repository root:

```bash
uv run --extra data-sql python docs_src/data/quickstart.py
```

Read [DataS, DataR, and persistence](guide/data.md) for the full source and an
explanation of every part, including queries, DTOs, transactions, and streams.

## Compose operations as the feature grows

A `Service` can call other actions or services. A `Workflow` can pass results
through sequential steps, run two async branches concurrently, route by schema
type, and process multiple results through async iteration. Dependencies keep
checks and collaborators attached to the operation across these calls.

Continue with:

- [Actions, services, and workflows](guide/actions.md) for application behavior.
- [DataS, DataR, and persistence](guide/data.md) for entity services and storage.
- [Dependencies](guide/dependencies.md) for shared checks and injection.
- [Events](guide/events.md) to publish results and register subscribers.
- [Testing](guide/testing.md) to exercise operations and backend contexts.
