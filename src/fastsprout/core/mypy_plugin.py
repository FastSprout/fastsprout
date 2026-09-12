"""mypy plugin: refines FieldRef.orm to OrmCtor[T].

Configure in pyproject.toml or mypy.ini:
    [tool.mypy]
    plugins = ["fastsprout.core.mypy_plugin"]

Without the plugin, `.orm` shows the raw declared type (e.g. Mapped[Any]).
With the plugin, `.orm` shows the applied type (e.g. Mapped[int]).

This is a temporary solution until Python adds native HKT support
(python/typing issue #548, open since 2018).
"""

from collections.abc import Callable

from mypy.plugin import AttributeContext, Plugin
from mypy.types import Instance, NoneType, get_proper_type
from mypy.types import Type as MypyType

__all__ = ["FastSproutPlugin", "plugin"]


def _orm_attribute_hook(ctx: AttributeContext) -> MypyType:
    """Refine FieldRef.orm to OrmCtor[T].

    For FieldRef[E, T, OrmCtor]:
      - OrmCtor=None      → .orm is None     (plain DTO)
      - OrmCtor=Mapped[*] → .orm is Mapped[T] (SQL entity)
      - other Generic[X]  → .orm is OrmCtor[T]
    """
    instance = get_proper_type(ctx.type)
    if not isinstance(instance, Instance):
        return ctx.default_attr_type
    if len(instance.args) < 3:
        return ctx.default_attr_type

    t_arg = get_proper_type(instance.args[1])
    orm_ctor = get_proper_type(instance.args[2])

    if isinstance(orm_ctor, NoneType):
        return orm_ctor

    if isinstance(orm_ctor, Instance):
        return orm_ctor.copy_modified(args=[t_arg])

    return ctx.default_attr_type


class FastSproutPlugin(Plugin):
    def get_attribute_hook(
        self, fullname: str
    ) -> Callable[[AttributeContext], MypyType] | None:
        if fullname == "fastsprout.core.fields.field_ref.FieldRef.orm":
            return _orm_attribute_hook
        return None


def plugin(version: str) -> type[Plugin]:
    return FastSproutPlugin
