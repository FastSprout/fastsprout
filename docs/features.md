# Features

FastSprout is organized in layers so an application can use the pieces it needs.

## Core

[`BaseSchema`](api/core.md) and typed fields describe input and output data.
[`Actionable`](api/core.md) gives class and function actions the same typed call
shape. DTO visibility controls which fields are readable or writable. Start with
the [typed action guide](getting-started.md) or the [core examples](learn/examples/index.md).

## Data

`DataR` routes entities to their persistence implementations. Streams and joins
allow typed data processing, including an in-memory joined stream. Install the
`data-sql` extra for SQL-backed examples. See the [data API](api/data.md) and
[SQL API](api/sql.md).

## Events

`EventBus` delivers events through Bubus, asyncio.Queue, RabbitMQ, NATS, or Kafka. The
`pub` and `sub` decorators connect actions and handlers to a bus. Install
`events` for local brokers, `events-rabbit` for RabbitMQ, or `events-nats`
for NATS, or `events-kafka` for Kafka. See the [events guide](guide/events.md),
[events examples](learn/examples/index.md), and
[events API](api/events.md).

## Testing

Typed pytest phases share setup and assertions. Database and broker contexts
prepare isolated test resources and clean them up on exit. See the
[testing guide](guide/testing.md) and [testing API](api/testing.md).
