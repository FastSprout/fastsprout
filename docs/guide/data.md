# DataS, DataR, and persistence

A feature that creates and completes tasks needs more than SQL statements.
It needs an application contract, rules for missing records, a way to select
pending tasks, and a boundary for committing related changes. FastSprout splits
that work between entity services and a persistence context.

**`DataS` is an entity service.** It provides typed CRUD operations and controls
their input and output schemas. Extend it to add application operations such as
`complete` or `archive`.

**`DataR` is the data router and context.** It gives those operations access to
the entity's backend, shares resources during the context, and finalizes or
aborts work when the context exits.

A typical call goes from an application adapter to an action or service, then
through DataR to the entity's backend. DataS uses DataR internally; a service
can also use DataR directly for lower-level reads or writes.

## Which object does what?

| Object | Question it answers | In a task tracker |
| --- | --- | --- |
| `Task`, an `SQLEntity` | What is stored, and what are its fields and identity? | Task ID, title, completion flag |
| `SQLSignpost` | Which SQL session factory should this entity use? | The session factory for the task database |
| `DataR` | Which backend and open context should this operation use? | One context shared by the task service's calls |
| `DataS(Task)` or `DataS[Task]` | Which entity operations and schemas does the application expose? | Create tasks, get a task, list pending tasks, update completion |
| `Service` | Which operations belong together across entities or collaborators? | A task assignment operation that coordinates users, tasks, and notifications |
| `SQLQuery(Task)` | Which entities should an operation select? | Incomplete tasks, ordered and paginated |

Import `DataS` from `fastsprout.actions` and `DataR` from `fastsprout.data`.
DataS belongs to the application layer because it adds service contracts and
dependencies on top of data access.

## Learn it one step at a time

The tutorial introduces application actions first, then adds persistence:

1. [Store and retrieve tasks](../tutorial/entity-operations.md) with DataS.
2. [Roll back related writes](../tutorial/transactions.md) with a shared DataR.
3. [Select and page tasks](../tutorial/queries.md) with queries and streams.

Each step has a small runnable program and its generated output. The SQLite
setup is available in a collapsed block in the first data lesson. Start with
[Your first action](../getting-started.md) for the full course, or use the
sections below to look up a concept after trying it.

## What DataS adds to data access

Without an entity service, each feature would need to decide how to validate a
create or patch payload, load an entity, apply changes, project its read view,
and assemble pagination results. DataS reuses those steps through a typed
service interface.

| Need | DataS behavior | Runnable example |
| --- | --- | --- |
| Basic entity operations | Create, get, update, patch, delete, and upsert | [CRUD](../learn/examples/actions/2-action-group/2-crud-service/1-standard.md) |
| Different read and write contracts | Read, create, update, and patch schema settings; DTO field visibility | [Custom schemas](../learn/examples/actions/2-action-group/2-crud-service/4-custom-write-schemas.md) |
| Partial changes | Patch applies the supplied fields through its patch contract | [Update and patch](../learn/examples/actions/2-action-group/2-crud-service/3-update-and-patch.md) |
| Controlled operations | Enable selected operations and override application behavior | [Operation controls](../learn/examples/actions/2-action-group/2-crud-service/17-operation-controls.md) |
| Paged reads | `Page[ReadSchema]` contains `items`, `total`, `offset`, and `limit` | [Pagination](../learn/examples/actions/2-action-group/2-crud-service/15-query-pagination.md) |
| Reusable selections | Use one query for list, count, or other operations | [Reusable query](../learn/examples/actions/2-action-group/2-crud-service/16-reusable-query.md) |
| Larger writes | Bulk create, update, patch, delete, and upsert with chunked processing | [Bulk operations](../learn/examples/actions/2-action-group/2-crud-service/6-bulk-operations.md) |
| Shared checks | Service and per-operation dependencies | [Operation dependencies](../learn/examples/actions/2-action-group/2-crud-service/21-operation-dependencies.md) |
| Related data and result shapes | Nested entities, joins, and mapping | [Nested entities](../learn/examples/actions/2-action-group/2-crud-service/14-nested-entities.md), [joins](../learn/examples/actions/2-action-group/2-crud-service/12-joins.md), [mapping](../learn/examples/actions/2-action-group/2-crud-service/13-mapping.md) |

With default settings, DataS uses the entity as its read and write schema.
Configure separate schemas when callers should see or supply different fields.
For example, a task's create payload can accept its title while the read DTO
also exposes its generated identity. A restricted catalog can enable only reads;
an editing service can expose additional operations on the same entity.

`list` materializes a page of results; `find_all` materializes matching results.
Use `stream` when callers should consume results incrementally. For bulk
operations that return a lazy stream, iterate that stream to perform the work.
Chunk size controls processing memory; the surrounding DataR context determines
when the transaction settles.

## What DataR owns

DataR routes an entity to its backend and binds that entity's signpost for the
current context. Its `ability(Entity)` method returns the entity's persistence
capabilities. `stream(query)` supplies typed query results; `join(query)` starts
a routed join.

The SQL implementation shares one async session for each signpost touched in a
DataR context. Several service calls using that signpost therefore work with the
same session. Different signposts can point at different databases. Each
signpost settles its own transaction; coordinating an all-or-nothing operation
across databases requires an application-level strategy.

Consume database streams inside the DataR context that created them. Context
exit invalidates those streams and releases their resources. Explicit
`finalize()` and `abort()` are available when an operation needs to settle work
before exit; the context manager provides the normal success and failure path.

Use DataR directly when you need persistence capabilities or streams without a
DataS read/write contract. Use DataS when you want entity operations with schema
projection, pagination, operation switches, and service dependencies. A `Service`
can coordinate both as part of a larger application operation.

## Queries, streams, and joins

`SQLQuery(Entity)` describes a selection. Typed field comparisons such as
`Task.completed.eq(False)` can be reused with ordering and pagination. Queries
also accept Python predicates, including async predicates. The SQL backend
pushes supported conditions into SQL and evaluates remaining transformations
while consuming results.

Streams compose filtering, mapping, ordering, limits, projections, and joins.
The result type follows those transformations. A terminal such as `count()` or
`first()` consumes the stream; async iteration lets a caller process results
as they arrive. Operations that require retaining values, such as sorting in
memory or collecting a result list, still retain those values.

Continue with runnable examples for:

- [Typed query conditions](../learn/examples/data/2-stream/4-query-conditions.md).
- [SQL joins](../learn/examples/data/2-stream/5-query-joins.md) and
  [SQLAlchemy statements](../learn/examples/data/2-stream/6-sqlalchemy-query.md).
- [Routed joins](../learn/examples/data/2-stream/2-routed-join.md) and
  [mixed SQL and Python stages](../learn/examples/data/2-stream/7-mixed-join-stages.md).

## Dependency injection and change events

The example passes DataR explicitly to make the context boundary visible.
Applications can also register `provide_datar` as the dependency provider for
`DataR`; operations declaring `datar: DataR = Depends()` can then obtain a
managed context through injection. Share an explicit DataR when several calls
must settle together. See [data dependencies](../learn/examples/data/1-datar/3-dependencies.md)
and [action dependencies](dependencies.md).

When a DataR has an event bus, data changes can emit events after successful
commit. Aborted work discards its pending change events. See the
[data event example](../learn/examples/data/1-datar/2-events-subscriber.md) for
configuration and subscribers.

For complete signatures, use [Actions API](../api/actions.md),
[Data API](../api/data.md), and [SQL API](../api/sql.md). The
[Actions guide](actions.md) covers services and workflows around these data
operations.
