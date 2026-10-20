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
