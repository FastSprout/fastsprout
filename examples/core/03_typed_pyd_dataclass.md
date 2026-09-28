Use `@typed_pydantic_dataclass` when a dataclass also needs input validation. The script constructs a valid user, then deliberately passes text to an integer field.

## Result

The valid user is accepted. The invalid value raises `ValidationError`; the example prints the rejected field:

```text
Validation rejected bad payload: ('field_int',)
```
