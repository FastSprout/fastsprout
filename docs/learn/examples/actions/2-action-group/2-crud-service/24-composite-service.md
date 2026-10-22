# 24. Composite Service

<!-- example-source: examples/actions/02_action_group/02_crud_service/24_composite_service.py -->

Inject a Service and its entity-specific DataS dependencies.
The injector creates GameService, HeroesService, and TeamsService within the
invocation. All operations share the explicitly supplied DataR context.

## Source

```{.python}
--8<-- "examples/actions/02_action_group/02_crud_service/24_composite_service.py"
```

## Result

```text
Team: Justice League
Hero: Batman
Same team: True
Heroes: 0
Teams: 1
```
