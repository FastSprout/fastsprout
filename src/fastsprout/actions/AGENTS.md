# Actions rules

Actions and Services must remain usable from web, CLI, events, RPC, and MCP
adapters. Do not implement those transports here. Compose existing actions
and data capabilities instead of duplicating their implementation.

Reuse `core.depends` for injection and invocation scopes. Reuse `lazy_await`
and `resolve_any_iterable` for workflow execution instead of introducing
another result adapter.

Keep workflow inputs and yielded outputs typed as `Schema`. Preserve the
single async iteration interface for individual, nullable, and `AnyIterable`
results, including nested workflows. Keep processing lazy and close resources
on completion, failure, or early termination.
