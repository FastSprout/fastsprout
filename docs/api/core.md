# Core API

## Runtime DTO derivation

For an entity `User`, derive read, write, or combined DTO classes:

```python
from fastsprout.core import (
    derive_read_dto,
    derive_read_write_dto,
    derive_write_dto,
)

UserRead = derive_read_dto(User)
UserCreate = derive_write_dto(User)
UserUpdate = derive_read_write_dto(User)
```

Each function reuses its class for the same entity. Visibility is enforced
at runtime; type checkers see `type[User]`. For static field restrictions,
declare `class UserRead(ReadDTO, User): ...` instead.

::: fastsprout.core
    options:
      show_root_heading: false
      show_root_toc_entry: false
