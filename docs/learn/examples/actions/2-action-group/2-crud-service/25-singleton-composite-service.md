# 25. Singleton Composite Service

<!-- example-source: examples/actions/02_action_group/02_crud_service/25_singleton_composite_service.py -->

Register shared Service instances and keep using Depends().
The providers return the same GameService, HeroesService, and TeamsService
across invocations. Each invocation uses its own DataR transaction.

## Source

```{.python}
--8<-- "examples/actions/02_action_group/02_crud_service/25_singleton_composite_service.py"
```

## Result

```text
Run: 1
Team: Justice League
Hero: Batman
Same team: True
Heroes: 0
Teams: 1
Run: 2
Team: Justice League
Hero: Batman
Same team: True
Heroes: 0
Teams: 2
```
