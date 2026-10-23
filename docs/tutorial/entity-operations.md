# 4. Store and retrieve tasks

The feature needs to save a task and find it by ID. `DataS(Task)` supplies
those entity operations, so you can call `create` and `get` without writing
their implementations.

The `TaskService` from the previous step groups application checks and
formatting. This entity service stores and retrieves records. An application
operation can compose both when it needs to prepare a title and persist it.

## Enable SQL support

In the development checkout, add the SQL extra:

```bash
uv sync --extra data-sql
```

The development environment includes the SQLite driver.

<details markdown="1">
<summary>Install in another project</summary>

Install the development package and SQLite driver:

```bash
pip install 'fastsprout[data-sql] @ git+https://github.com/FastSprout/fastsprout.git@development' aiosqlite
```

</details>

## Create and get a task

The example setup supplies a `Task` entity with `id`, `title`, and `completed`
fields, plus a fresh in-memory database. The service is `DataS(Task)`.

<!-- example-source: docs_src/data/quickstart.py -->

```{.python}
--8<-- "docs_src/data/quickstart.py"
```

Run it from the repository root:

```bash
uv run python -m docs_src.data.quickstart
```

## Result

```text
Created: 1 Write documentation
Found: 1 Write documentation
Missing: None
```

## What DataS handles

`create` writes the entity and returns its read representation. `get` looks up
its ID and returns the entity, or `None` when it does not exist. This example
uses the entity as its default input and output schema.

DataS also supplies update, patch, delete, count, list, and bulk operations.
You can later choose separate input and output schemas and extend
`DataS[Task]` with application methods. See the [Data guide](../guide/data.md#what-datas-adds-to-data-access)
when you need those options.

<details markdown="1">
<summary>SQLite setup and the Task entity</summary>

The examples share this file, `docs_src/data/common.py`:

```{.python}
--8<-- "docs_src/data/common.py"
```

`SQLSignpost` connects the entity to its session factory. `database()` prepares
the tables and registers a dependency provider that gives each top-level
service call a managed data context. It disposes the engine when the example
ends. The next step makes the context boundary explicit so several calls can
share a transaction.

</details>

In this setup, successful service calls settle independently. That is useful
for a single operation. The next step shows what happens when two writes
must succeed or fail together.

[Previous: Services](services.md) ·
[Next: Roll back related writes](transactions.md)
