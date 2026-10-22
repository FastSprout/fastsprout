# 1. Pydantic

<!-- example-source: examples/actions/01_action/02_class_with_depends/01_pyd.py -->

Resolve a Pydantic dependency when a class action is called.
HeroPower is supplied by Depends() without becoming part of the HeroIn payload.

## Source

```{.python}
--8<-- "examples/actions/01_action/02_class_with_depends/01_pyd.py"
```

## Result

```text
HeroOut: name='Batman' power=HeroPower(value='Money')
```
