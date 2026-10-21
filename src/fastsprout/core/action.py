from collections.abc import AsyncIterator, Iterable, Sequence
from typing import ClassVar, Protocol, runtime_checkable

from fastsprout.core.types.schema import Schema

__all__ = [
    "ActionGroupable",
    "Actionable",
    "IterableActionable",
    "IterableTriggerActionable",
    "IteratorActionable",
    "IteratorTriggerActionable",
    "NullableActionable",
    "SequenceActionable",
    "SequenceTriggerActionable",
    "TriggerActionable",
]


@runtime_checkable
class Actionable[I: Schema, O: Schema](Protocol):
    """Atomic unit of work in fastsprout.

    Actions take a single typed payload and return a typed result.
    Exposed through channels (REST, CLI, task, event) via decorators
    from interface layers.
    """

    async def __call__(self, payload: I, /) -> O: ...


@runtime_checkable
class NullableActionable[I: Schema, O: Schema | None](Protocol):
    """Atomic unit of work in fastsprout.

    Actions take a single typed payload and return a typed result or nullable value.
    Exposed through channels (REST, CLI, task, event) via decorators
    from interface layers.
    """

    async def __call__(self, payload: I, /) -> O | None: ...


@runtime_checkable
class IterableActionable[I: Schema, O: Schema](Protocol):
    """Atomic unit of work in fastsprout.

    Actions take a single typed payload and return a typed result.
    Exposed through channels (REST, CLI, task, event) via decorators
    from interface layers.
    """

    async def __call__(self, payload: I, /) -> Iterable[O]: ...


@runtime_checkable
class IteratorActionable[I: Schema, O: Schema](Protocol):
    """Atomic unit of work in fastsprout.

    Actions take a single typed payload and return a typed result.
    Exposed through channels (REST, CLI, task, event) via decorators
    from interface layers.
    """

    def __call__(self, payload: I, /) -> AsyncIterator[O]: ...


@runtime_checkable
class SequenceActionable[I: Schema, O: Schema](Protocol):
    """Atomic unit of work in fastsprout.

    Actions take a single typed payload and return a typed result.
    Exposed through channels (REST, CLI, task, event) via decorators
    from interface layers.
    """

    async def __call__(self, payload: I, /) -> Sequence[O]: ...


@runtime_checkable
class TriggerActionable[O: Schema](Protocol):
    """Action triggered without payload (cron jobs, no-input commands)."""

    async def __call__(self, /) -> O: ...


@runtime_checkable
class IterableTriggerActionable[O: Schema](Protocol):
    """Action triggered without payload (cron jobs, no-input commands)."""

    async def __call__(self, /) -> Iterable[O]: ...


@runtime_checkable
class IteratorTriggerActionable[O: Schema](Protocol):
    """Action triggered without payload (cron jobs, no-input commands)."""

    def __call__(self, /) -> AsyncIterator[O]: ...


@runtime_checkable
class SequenceTriggerActionable[O: Schema](Protocol):
    """Action triggered without payload (cron jobs, no-input commands)."""

    async def __call__(self, /) -> Sequence[O]: ...


@runtime_checkable
class ActionGroupable(Protocol):
    """Group of actions — class with multiple decorated methods."""

    __action_group__: ClassVar[bool]
