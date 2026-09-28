Define a schema once with `Field[T]`. Instances expose typed values; access through the class returns a `FieldRef` that identifies the field and its owner. `BaseSchema` also accepts camelCase input and can emit camelCase aliases.

## Result

The script prints the validated hero and the reference to `Hero.name`:

```text
id=1 name='SuperMan' is_active=True
<Hero.name>
```
