# Data API

`DataR` routes entity operations to persistence backends and shares their
resources inside a context. Queries and streams describe and consume selections.
For application-facing CRUD operations and schema projection, use `DataS` from
`fastsprout.actions`. See [DataS, DataR, and persistence](../guide/data.md) for
their relationship, or follow the [SQLite tutorial](../tutorial/entity-operations.md)
to learn entity operations through a runnable example.

::: fastsprout.data
    options:
      show_root_heading: false
      show_root_toc_entry: false
      members:
        - DataR
        - JoinedStream
        - Relationship
        - SimpleAsyncEntityStream
        - SimpleAsyncValueStream
