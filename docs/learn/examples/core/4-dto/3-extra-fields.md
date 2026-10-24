# 3. Extra Fields

<!-- example-source: examples/core/04_dto/03_extra_fields.py -->

Expose extra read and write fields only when explicitly requested.

Ordinary DTOs omit both extra markers, including ReadWriteDTO. Extended DTOs
include the ordinary fields for their operation plus the matching extra
fields. Internal fields remain hidden in every DTO.

Class declarations preserve visibility checks in IDEs. Dynamic derivation
uses the same runtime guards but exposes the source type to type checkers.

## Source

```{.python}
--8<-- "examples/core/04_dto/03_extra_fields.py"
```

## Result

```text
Read: name='Notebook'
Write: name='Notebook'
Read/write: name='Notebook'
Extra read: name='Notebook' description='120 pages'
Extra write: name='Notebook' import_reference='catalog-42'
Extra read/write: name='Notebook' description='120 pages' import_reference='catalog-42'
Field 'import_reference' not accessible in DTO (operations: ['write'])
Dynamic extra read: name='Notebook' description='Created with derive_dto'
```
