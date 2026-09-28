This example builds a small SQLModel bridge to show what `HasOrm` exposes. A class-level `FieldRef.orm` points to SQLAlchemy's mapped attribute, which can be used in SQL expressions; `.set()` still creates a plain field assignment.

## Result

The assertion checks that `Hero.name.orm` is an `InstrumentedAttribute`. The script prints:

```text
FieldAssignment(name='name', value='Spider')
```
