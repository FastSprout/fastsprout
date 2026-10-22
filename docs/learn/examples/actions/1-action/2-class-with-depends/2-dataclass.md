# 2. Dataclass

<!-- example-source: examples/actions/01_action/02_class_with_depends/02_dataclass.py -->

Resolve a dependency in a dataclass action.
The action receives HeroPower automatically while its input and output remain typed dataclasses.

## Source

```{.python}
--8<-- "examples/actions/01_action/02_class_with_depends/02_dataclass.py"
```

## Result

```text
HeroOut: HeroOut(name='Batman', power=HeroPower(value='Money'))
```
