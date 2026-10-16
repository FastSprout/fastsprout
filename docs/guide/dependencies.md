# Dependencies

`@action(dependencies=[Depends(check), ...])` runs dependencies in order
before the action body. An exception stops the call. Dependencies can use
the action's arguments by name and request other dependencies with `Depends`.

Set `Service.dependencies` to run checks before every public async action.
Pass `dependencies=[...]` to the Service constructor to override them for
one instance.

For a function decorated with `@action`, `check.dependency` is shorthand for
`Depends(check)`. It also works for that function assigned to a Service,
as in `checks.access.dependency` below. For ordinary Service methods and
`Action` instances, use `Depends(...)`.

Here, publishing and archiving both require access and content checks.
Publishing an empty document fails before `publish` runs.

```python
--8<-- "examples/actions/02_action_group/01_service/03_dependencies.py"
```

Run from the repository root:

```bash
uv run --extra standard python examples/actions/02_action_group/01_service/03_dependencies.py
```
