from collections.abc import AsyncIterator, Iterable, Sequence
from typing import ClassVar, Protocol, runtime_checkable

from fastsprout.core.types.schema import Schema

__all__ = [
    "BaseAction",
    "BaseActionGroup",
    "BaseIterableAction",
    "BaseIterableTriggerAction",
    "BaseIteratorAction",
    "BaseIteratorTriggerAction",
    "BaseNullableAction",
    "BaseSequenceAction",
    "BaseSequenceTriggerAction",
    "BaseTriggerAction",
]


@runtime_checkable
class BaseAction[I: Schema, O: Schema](Protocol):
    """Atomic unit of work in fastsprout.

    Actions take a single typed payload and return a typed result.
    Exposed through channels (REST, CLI, task, event) via decorators
    from interface layers.
    """

    async def __call__(self, payload: I, /) -> O: ...


@runtime_checkable
class BaseNullableAction[I: Schema, O: Schema | None](Protocol):
    """Atomic unit of work in fastsprout.

    Actions take a single typed payload and return a typed result or nullable value.
    Exposed through channels (REST, CLI, task, event) via decorators
    from interface layers.
    """

    async def __call__(self, payload: I, /) -> O | None: ...


@runtime_checkable
class BaseIterableAction[I: Schema, O: Schema](Protocol):
    """Atomic unit of work in fastsprout.

    Actions take a single typed payload and return a typed result.
    Exposed through channels (REST, CLI, task, event) via decorators
    from interface layers.
    """

    async def __call__(self, payload: I, /) -> Iterable[O]: ...


@runtime_checkable
class BaseIteratorAction[I: Schema, O: Schema](Protocol):
    """Atomic unit of work in fastsprout.

    Actions take a single typed payload and return a typed result.
    Exposed through channels (REST, CLI, task, event) via decorators
    from interface layers.
    """

    def __call__(self, payload: I, /) -> AsyncIterator[O]: ...


@runtime_checkable
class BaseSequenceAction[I: Schema, O: Schema](Protocol):
    """Atomic unit of work in fastsprout.

    Actions take a single typed payload and return a typed result.
    Exposed through channels (REST, CLI, task, event) via decorators
    from interface layers.
    """

    async def __call__(self, payload: I, /) -> Sequence[O]: ...


@runtime_checkable
class BaseTriggerAction[O: Schema](Protocol):
    """Action triggered without payload (cron jobs, no-input commands)."""

    async def __call__(self, /) -> O: ...


@runtime_checkable
class BaseIterableTriggerAction[O: Schema](Protocol):
    """Action triggered without payload (cron jobs, no-input commands)."""

    async def __call__(self, /) -> Iterable[O]: ...


@runtime_checkable
class BaseIteratorTriggerAction[O: Schema](Protocol):
    """Action triggered without payload (cron jobs, no-input commands)."""

    def __call__(self, /) -> AsyncIterator[O]: ...


@runtime_checkable
class BaseSequenceTriggerAction[O: Schema](Protocol):
    """Action triggered without payload (cron jobs, no-input commands)."""

    async def __call__(self, /) -> Sequence[O]: ...


@runtime_checkable
class BaseActionGroup(Protocol):
    """Group of actions — class with multiple decorated methods."""

    __action_group__: ClassVar[bool]
