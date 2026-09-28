# Features

FastSprout is organized in layers so an application can use the pieces it needs.

## Core

[`BaseSchema`](api/core.md) and typed fields describe input and output data.
[`BaseAction`](api/core.md) gives class and function actions the same typed call
shape. DTO visibility controls which fields are readable or writable. Start with
the [typed action guide](getting-started.md) or the [core examples](learn/examples/index.md).

## Data

`DataR` routes entities to their persistence implementations. Streams and joins
allow typed data processing, including an in-memory joined stream. Install the
`data-sql` extra for SQL-backed examples. See the [data API](api/data.md) and
[SQL API](api/sql.md).

## Events

`EventBus` publishes events in memory and delivers them to subscribers. The
`pub` and `sub` decorators connect actions and handlers to a bus. Install the
`events` extra and see the [events guide](guide/events.md),
[events examples](learn/examples/index.md), and
[events API](api/events.md).
