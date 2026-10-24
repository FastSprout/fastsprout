# Events rules

Keep broker implementations behind `Brokerable`. Reuse the shared
`EventState` and `EventResult` contracts so different brokers report results
through the same interface. Identify events by `event.__event_id__`, not
Python object identity.

Preserve multiple subscriber results and the `done, pending` wait interface.
A wait timeout must leave pending work running.
Reuse core dependency injection for handlers and middleware instead of
maintaining a separate resolver.
