Call `.set(value)` on a class-level field reference to build a `FieldAssignment`. This captures the field name and new value without mutating an entity, so a repository can accept a list of partial changes.

## Result


```text
FieldAssignment(name='name', value='Spider')
FieldAssignment(name='is_active', value=False)
```
