# What FastSprout helps you build

A backend often grows several ways to perform the same operation: an HTTP
endpoint, an admin command, and a background worker. Each can end up with its
own validation, database queries, transaction handling, and result conversion.
Changing a business rule then means finding and updating every copy.

FastSprout gives those operations a typed Python interface. Define an action
once, group related actions in a service, and call them from your application's
entry points. Entity services handle common data operations; a data router
owns their persistence context. Workflows connect operations without losing
the types between steps.

## Start with the problem you have

| Problem | FastSprout building blocks | Result |
| --- | --- | --- |
| The API and worker repeat the same operation and checks | `@action`, `Action`, `Service`, `Depends` | One callable operation with typed arguments, results, and shared dependencies |
| Every entity needs another set of CRUD methods, schemas, and pagination code | `DataS`, read/write DTOs, `Page` | A configurable entity service with CRUD, projections, pagination, and bulk operations |
| Related writes open separate sessions or commit at the wrong boundary | `DataR`, entity signposts, `provide_datar` | An explicit context shared by operations, with finalization or rollback on exit |
| Data processing loads everything before filtering, mapping, or joining | Queries and async streams | Typed selection and transformations that can be consumed incrementally |
| A multi-step operation becomes nested callbacks and loosely typed dictionaries | `Workflow`, `ForkResult` | Typed sequential steps, concurrent forks, branching, and streamed results |
| Event delivery is mixed into the operation that produces an event | `EventBus`, `pub`, `sub`, broker adapters | Separate publishers, subscribers, and transport configuration |
| Tests repeat setup and resource cleanup | Typed testing phases and backend contexts | Reusable setup, execution, and assertions with isolated test resources |

## Actions: keep application operations reusable

An **action** is one operation, such as preparing a task or completing an order.
Use `@action` for an async function or `Action[Input, Output]` for a callable
class. Parameter and result types remain visible to the type checker.

A **service** groups related actions. Inherit from `Service` or decorate a class
with `@action`. Dependencies declared with `Depends` supply collaborators and
run shared checks before an action's body. A service can compose other services,
so an operation can call existing behavior through its Python interface.

For example, an HTTP handler and a queue consumer can call the same
`tasks.complete(...)` operation. The rule for a missing task lives in the
service method, and both callers receive the same typed result or exception.
Your application's adapter connects that call to its HTTP, CLI, or worker entry
point.

A **workflow** connects actions. `.then(...)` passes each result to another
step; `.fork(...)` runs two async branches concurrently; `.branch(...)` routes
by schema type. Steps can emit one result, no result, or a synchronous or
asynchronous stream. This lets an import or processing pipeline yield results
as they become available.

Read the [Actions guide](guide/actions.md) for function and class actions,
service composition, dependencies, and workflows.

## DataS and DataR: entity operations and their storage context

`DataS` and `DataR` work together at different points in a data operation:

| Name | Responsibility | Example |
| --- | --- | --- |
| `DataS` from `fastsprout.actions` | Expose an entity's application operations and input/output contracts | `tasks.create(...)`, `tasks.list(...)`, or a custom `tasks.complete(...)` |
| `DataR` from `fastsprout.data` | Route persistence operations and share their backend context | Pass one `datar` to several service calls in `async with DataR()` |
| `SQLSignpost` | Bind an entity to an async SQL session factory | Point task entities at the application's task database |
| `SQLEntity` | Describe a stored entity with typed fields and an identity | `Task` with an ID, title, and completion status |

### Replace repeated CRUD code with DataS

`DataS(Entity)` supplies create, get, update, patch, delete, and upsert
operations. It also supports query reads, pagination, bulk operations, joins,
and result mapping. Separate read, create, update, and patch schemas control
the service's contracts. DTO field visibility determines which fields those
contracts expose.

Extend `DataS[Entity]` when the entity needs application behavior, such as
completing a task or archiving a record. Choose enabled operations and attach
shared or per-operation dependencies. A read-only catalog and an editing
service can therefore use the same entity with different exposed operations.

### Share persistence work with DataR

Inside `async with DataR() as datar`, related operations can share the same
backend resources. Entities with the same SQL signpost share a session in
that context. Successful exit finalizes the bound backends; an exception
aborts them, and exit closes the context's resources.

Pass the same `datar` to several `DataS` calls to put them in that context.
Use `datar.ability(Entity)` for direct persistence capabilities and
`datar.stream(query)` for query results. Application code can use DataR
directly when it needs lower-level access without a CRUD service's schema
projection.

The built-in SQL adapter uses SQLModel and SQLAlchemy. Async drivers select
the database connection; the test matrix exercises SQLite, PostgreSQL, MySQL,
MariaDB, and Oracle. Queries combine typed field conditions, ordering,
pagination, and Python predicates. SQL-supported operations execute in the
database; other transformations run while consuming the stream. Joins can
combine routed sources, with examples for SQL and mixed processing stages.

Try the [rollback example](tutorial/transactions.md): after an exception,
two separate service calls leave their committed rows in the example database;
the same pair in a shared DataR context leaves no rows. This makes the
transaction boundary visible in a subsequent read.

Follow the [data tutorial](tutorial/entity-operations.md) to build up that
example, then use [DataS, DataR, and persistence](guide/data.md) to look up
schemas, queries, transaction lifetimes, and streams.

## Core: define contracts that survive composition

`BaseSchema`, `Schema`, typed dataclasses, and fields describe inputs, results,
and entities. DTOs derive read and write views from those fields, reducing the
need to maintain separate field lists by hand. Field references can also be
used in typed query conditions. Dependency injection and invocation contexts
are shared by the action, service, and data layers.

See the [core examples](learn/examples/index.md#core) and
[dependencies guide](guide/dependencies.md).

## Events: connect operations to asynchronous delivery

`EventBus` connects publishers to subscribers through Bubus, `asyncio.Queue`,
RabbitMQ, NATS, or Kafka. `pub` publishes an action's returned event; `sub`
registers handlers. Scheduling and middleware provide additional delivery
behavior while the broker adapter owns transport configuration.

Data operations can publish change events after a successful commit. This
lets subscribers react to persisted changes while rolled-back operations
discard their pending change events. Broker-specific acknowledgements,
persistence, and replay retain the selected transport's semantics.

See [publishing and subscribing](guide/events.md) and the
[data event example](learn/examples/data/1-datar/2-events-subscriber.md).

## Testing: exercise the same operations your adapters call

Typed `given`, `when`, and `then` phases share fixtures and scenarios. Database
and broker contexts prepare isolated resources and clean them up on exit.
Actions and services can be called directly in tests; backend tests can use
the same data contracts with a real database or broker.

See the [testing guide](guide/testing.md). To build your first operation and
persist an entity, continue with [Getting Started](getting-started.md).
