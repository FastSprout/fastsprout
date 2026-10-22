# 1. Pydantic

<!-- example-source: examples/actions/01_action/01_class/01_pyd.py -->

Create a hero with a class action and a BaseSchema contract.
The class stays directly awaitable, and the result has the concrete HeroOut type.

## Source

```{.python}
--8<-- "examples/actions/01_action/01_class/01_pyd.py"
```

## Result

```text
HeroOut: name='Batman'
```
