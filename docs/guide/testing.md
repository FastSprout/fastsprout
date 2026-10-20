# Database test contexts

Install the database contexts:

```bash
pip install 'fastsprout[testing-data]'
```

`testing.core` provides typed pytest phases. `testing.data.TestSQLite(*entities)`
creates an isolated in-memory database and exposes a typed `TestSQLDatabase`
with `engine`, `session`, and `signpost`.

The context creates the selected tables, binds the entities, and removes the
tables on exit. Previous entity bindings are restored, including inherited
bindings. Isolation does not depend on rolling back application transactions:
a test can commit through DataR and read the result in another transaction.
Use dedicated test databases; existing selected tables are rejected.

Pass `signpost=CRM` for an entity family declared with that source type.
The resulting `database.signpost` retains the concrete CRM type.

TestSQLite accepts a caller-owned `engine` and a `sessions` factory.
Caller-owned engines remain open after exit; selected tables are still
removed. Default session factories use `expire_on_commit=False`.

See the [SQLite example](../learn/examples/testing/2-data/1-sqlite.md).

## PostgreSQL

`TestPostgreSQL(*entities)` starts a disposable PostgreSQL container and reuses
the SQL context's table, session, and binding lifecycle. Pass a configured
`PostgresContainer`, an engine factory, or a session factory for native settings.
The default image is the public `postgres:18-alpine` image.

Container tests require Docker. Select them with the integration marker:

```bash
uv run --extra testing-data \
  pytest src/tests/fastsprout/testing/data -m integration --no-cov
```

Use `pytest -m "not integration"` to run without containers. Unavailable Docker
infrastructure fails integration tests. The CI container job requires a runner
allowing privileged Docker-in-Docker services.

See the [PostgreSQL example](../learn/examples/testing/2-data/2-postgresql.md).

## MySQL and MariaDB

`TestMySQL(*entities)` and `TestMariaDB(*entities)` reuse the SQL context's
table, session, and binding lifecycle with the asyncmy driver. Pass a configured
`MySqlContainer`, an engine factory, or a session factory for native settings.
The default images are public `mysql:8.4` and `mariadb:11.4`; override `image=`
to select another version or registry.

See the [MySQL and MariaDB example](../learn/examples/testing/2-data/3-mysql.md).

## Oracle

`TestOracle(*entities)` runs Oracle Free with asynchronous `oracledb`
connections. Pass a configured `OracleDbContainer` to select credentials and
service, or engine/session factories for SQLAlchemy settings. The public
default image is `gvenzl/oracle-free:23-slim-faststart`; override `image=`
for another version or registry.

Oracle string columns need an explicit length, for example
`name: Field[str] = SQLField(max_length=100)`. The context preserves the model's
column definitions.

See the [Oracle example](../learn/examples/testing/2-data/4-oracle.md).

## RabbitMQ

Install `fastsprout[testing-events]` for `TestRabbitMQ()`. It starts a disposable
RabbitMQ container and yields a `RabbitMQBroker` implementing `Brokerable`.
Pass it to `EventBus` and register subscribers before publishing. Dispatch
connects the adapter and starts its consumers. A receiver which does not publish
calls `await adapter.start()` after registering its handlers.

Pass a configured `RabbitMqContainer`, a native broker factory, or an adapter
factory for native configuration. The public default image is
`rabbitmq:4.1.0-alpine`; `image=` selects another version or registry.
The context stops the adapter and removes its container on exit.

See the [RabbitMQ example](../learn/examples/testing/3-events/1-rabbitmq.md).
