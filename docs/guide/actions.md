# Actions, services, and workflows

`fastsprout.actions` defines application operations with typed inputs,
results, and dependencies. Call an action directly, group related actions
in a service, or compose them into a workflow. The same operation can be
used from an HTTP handler, CLI command, or event subscriber.

Install the standard extra for the examples in this guide:

```bash
pip install 'fastsprout[standard]'
```

| Use | Start with |
| --- | --- |
| One async operation | `@action` or `Action[Input, Output]` |
| Related operations with shared dependencies | `Service` or an `@action` class |
| CRUD operations for an entity | `DataS` |
| A pipeline of typed operations | `Workflow` |

## Function actions

Decorate an async function with `@action`. Its parameter and result types
remain available to the type checker. Calling it runs its dependencies and
returns an awaitable result:

```{.python}
--8<-- "examples/actions/01_action/03_function/01_pyd.py"
```

Run it from the repository root:

```bash
uv run --extra standard python examples/actions/01_action/03_function/01_pyd.py
```

For a class with a single operation, inherit from `Action[Input, Output]`
and implement async `__call__`. Its input and output types must inherit
`Schema`: use `BaseSchema`, or inherit `Schema` in your dataclass or custom
class. See the runnable
[class action](../learn/examples/actions/1-action/1-class/1-pydantic.md)
[dataclass action](../learn/examples/actions/1-action/1-class/2-dataclass.md),
and [custom object action](../learn/examples/actions/1-action/1-class/3-object.md)
examples.

## Services and dependency injection

Use an `@action` class to group public async methods. `Depends` resolves
collaborators, including dependencies declared as attributes:

```{.python}
--8<-- "examples/actions/02_action_group/01_service/02_decorator/01_standard.py"
```

Inheriting from `Service` provides the same action-group behavior without
applying the decorator. See the
[Service example](../learn/examples/actions/2-action-group/1-service/1-class/1-standard.md).

Use `dependencies=[Depends(check)]` on an action or service to run checks
before its body. An exception stops the call. Dependencies can use the
call's arguments by name and request other dependencies. The
[dependencies guide](dependencies.md) covers shared checks and overrides.

Dependency resolution also works inside an invocation context. The runnable
[dependency context](../learn/examples/actions/3-context/1-dependency.md)
and [injection context](../learn/examples/actions/3-context/2-injection.md)
examples show how to share context with nested calls.

## Entity services with DataS

`DataS(Entity)` provides typed CRUD actions backed by `DataR`. It uses the
entity as its default read and write schema. Explicit `read`, `create`,
`update`, and `patch` schemas let the service expose separate contracts for
each operation. The `operations` setting controls which operations are
available.

| Operations | Purpose |
| --- | --- |
| `get`, `exists`, `count` | Look up an entity or inspect matching records |
| `list`, `find_first`, `find_exactly_one`, `find_all`, `stream` | Read pages, individual results, or streams |
| `create`, `update`, `patch`, `delete`, `upsert` | Write individual records |
| `bulk_create`, `bulk_update`, `bulk_patch`, `bulk_delete`, `bulk_upsert` | Process batches |
| `update_by_query`, `delete_by_query` | Write records selected by a query |
| `map`, `join` | Compose reads |

`Page[ReadSchema]` carries `items`, `total`, `offset`, and `limit` for
paginated reads. Streaming operations keep iteration lazy. Backend lifetime
and transaction boundaries belong to the data context used by the service.

Start with the runnable
[CRUD service](../learn/examples/actions/2-action-group/2-crud-service/1-standard.md),
then see [custom schemas](../learn/examples/actions/2-action-group/2-crud-service/4-custom-write-schemas.md).
The [Actions API](../api/actions.md) documents the service methods and
`DataSable` protocol.

## Workflows

Create a `Workflow` from its first operation, then append steps with
`.then(...)`. Each step receives the preceding step's result. Calling the
workflow returns an async generator; execution starts when you iterate it:

```{.python}
--8<-- "examples/actions/04_workflow/01_linear/01_function.py"
```

Workflow inputs and outputs are schemas. A step can return one schema,
`None`, a synchronous or asynchronous iterable of schemas, or an awaitable
of a supported result. `None` emits no result. Each emitted item enters the
next step separately, so a workflow may yield zero, one, or many outputs.
Iteration releases resources when it completes, fails, or is closed. Close
the async generator when you stop consuming it early, for example with
`contextlib.aclosing`.

| Composition | Behavior |
| --- | --- |
| `.then(next_action)` | Pass each result to the next operation |
| `.fork(left, right)` | Run two async branches concurrently and emit `ForkResult(left=..., right=...)` |
| `.join(next_action)` | Continue with an operation that accepts the combined result |
| `.branch(SchemaType, handler)` | Route by result type; the first matching branch wins |

An unmatched typed branch raises `LookupError`. Exceptions from a step
propagate to the caller. See the runnable workflow examples for
[linear composition](../learn/examples/actions/4-workflow/1-linear/1-function.md),
then browse the [example catalog](../learn/examples/index.md) for forks,
branching, streaming, and shared dependencies.

See [Actions API](../api/actions.md) for the public types and signatures.
