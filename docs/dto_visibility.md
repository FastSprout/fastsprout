# DTO visibility

Declare fields once on a `BaseEntity`, `BaseSchema`, or `SQLEntity`. Derive DTOs
using a visibility base:

```python
class User(DefaultSQLEntity):
    email: Field[str]
    password: WriteField[str]
    password_hash: InternalField[str]
    created_at: ReadField[datetime]


class UserRead(ReadDTO, User): ...


class UserCreate(WriteDTO, User): ...


def display(user: UserRead) -> str:
    return user.email


read = UserRead(email="a@b.c", created_at=datetime.now())
read.email         # str
read.password      # checker error; AttributeError at runtime
```

The full runnable SQL example, including the UUID base, is
[dto_visibility.py](dto_visibility.py).

| Field | Entity | ReadDTO | WriteDTO | ReadWriteDTO |
| --- | --- | --- | --- | --- |
| `Field[T]` | T | T | T | T |
| `ReadField[T]` | T | T | forbidden | T |
| `WriteField[T]` | T | forbidden | T | T |
| `InternalField[T]` | T | forbidden | forbidden | forbidden |

`ReadWriteDTO` selects the union of read and write fields. The initial DTO derives
directly from the source entity. The source retains all its fields, validation,
and SQL mapping. DTOs are not mapped as additional tables and do not validate or
coerce values. Defaults and default factories of allowed fields are preserved;
excluded defaults are never evaluated.

The visibility base must come first. DTOs always use their own constructor;
there is no need to specify `init=False`. The visibility base automatically
prepares the allowed fields, defaults, and runtime guards when the class is
declared. The optional `@dto` decorator remains compatible with older examples.
There are no checker patches, generated stubs, or mypy requirements for this
feature.

An existing DTO can be subclassed, including through multiple levels:

```python
class S(UserRead):
    def display(self) -> str:
        return self.email


read = S(email="a@b.c", created_at=datetime.now())
```

Subclasses keep the parent's source entity, fields, defaults, and visibility.
`S.password` and `read.password` remain forbidden both statically and at runtime.
This form adds behavior to the existing DTO contract; fields remain declared on
the entity. Derive a separate DTO from the entity to select another visibility
mode.

## Static and runtime contract

- A DTO class works in annotations and keeps allowed attribute value types,
  including inherited fields such as `id: UUID`.
- Stock pyright/basedpyright and mypy reject forbidden instance reads and assignments,
  forbidden class reads, and values of the wrong type assigned to allowed fields.
- Runtime rejects forbidden access and constructor keywords, unknown constructor
  keywords, and missing required fields.
- Constructor keyword names and value types are **not** statically derived:
  the signature is `**values`. Boundary validation remains a separate concern.
- Keep the DTO type in function annotations when visibility must be checked.
  Widening a DTO to `User` exposes the source's static interface; runtime guards
  still apply to the actual DTO instance.

The shared typing fixture runs under stock basedpyright and mypy, checking
allowed value types and the exact locations and codes of expected errors.
Neither checker requires a plugin.

Use DTO constructors, not inherited Pydantic construction/validation methods.
DTOs do not initialize Pydantic or SQLAlchemy instance state. Pydantic/OpenAPI
serialization integration is outside this primitive's contract.

The original `UserRead = dto(User, ["read"])` syntax is not implemented. The
short class declaration supplies the class and its visibility to the standard
checker without duplicating fields. IDE completion may still list inherited
names; access diagnostics enforce the visibility contract.

Internally, descriptors constrain their owner by a private visibility property.
The source's unrestricted marker is typed `Any`; DTO bases narrow that marker
to a literal. This does not change the value type `T` of any field. Explicitly
using `Any` for a DTO variable bypasses static checking, as elsewhere in Python.

The library supplies a separate static metaclass view for DTOs, matching the
runtime branch that skips Pydantic model construction and SQLAlchemy mapping.
It prevents the checker from applying the entity constructor transform to a
DTO. Source entity constructors retain their normal static checks.
