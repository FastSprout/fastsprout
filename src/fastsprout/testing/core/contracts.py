"""Require concrete annotations for pytest providers and consumers."""

import typing
from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Awaitable,
    Callable,
    Generator,
    Iterable,
    Iterator,
)
from functools import wraps
from inspect import BoundArguments, Parameter, Signature, signature
from typing import TypeAliasType, get_args, get_origin, get_type_hints
from weakref import WeakKeyDictionary

from typeguard import CollectionCheckStrategy, ForwardRefPolicy, check_type
from typing_extensions import TypeForm

from fastsprout.core import dataclass
from fastsprout.core.types.protocols.ables import Hashable

__all__ = [
    "FIXTURE_CONTRACTS",
    "StepContract",
    "check_arguments",
    "check_result",
    "checked",
    "checked_async",
    "checked_signature",
    "require_type",
    "resolve_alias",
]


@dataclass(frozen=True)
class StepContract:
    signature: Signature
    description: str


FIXTURE_CONTRACTS: WeakKeyDictionary[Hashable, StepContract] = (
    WeakKeyDictionary()
)


def resolve_alias[T](annotation: TypeForm[T]) -> TypeForm[T]:
    while isinstance(annotation, TypeAliasType):
        annotation = annotation.__value__
    return annotation


def require_type[T](annotation: TypeForm[T]) -> None:
    annotation = resolve_alias(annotation)
    if annotation in (Signature.empty, typing.Any, object):
        raise TypeError("A concrete type annotation is required")
    if annotation in (
        list,
        dict,
        set,
        tuple,
        Iterator,
        Generator,
        AsyncIterator,
        AsyncGenerator,
        Iterable,
        AsyncIterable,
    ) or (get_origin(annotation) and not get_args(annotation)):
        raise TypeError("Collection annotations require type arguments")
    for argument in get_args(annotation):
        for hint in argument if isinstance(argument, list) else (argument,):
            require_type(hint)


def checked_signature[**P, R](function: Callable[P, R]) -> Signature:
    hints = get_type_hints(function, include_extras=True)
    parameters = signature(function)
    for name in (*parameters.parameters, "return"):
        if name not in ("self", "cls"):
            try:
                require_type(hints.get(name, Signature.empty))
            except TypeError as error:
                raise TypeError(
                    f"{function.__qualname__}: {name}: {error}"
                ) from error
    return parameters.replace(
        parameters=[
            parameter.replace(annotation=hints.get(name, parameter.annotation))
            for name, parameter in parameters.parameters.items()
        ],
        return_annotation=hints["return"],
    )


def check_arguments(arguments: BoundArguments) -> None:
    arguments.apply_defaults()
    for name, value in arguments.arguments.items():
        if name not in ("self", "cls"):
            parameter = arguments.signature.parameters[name]
            values = (
                value.values()
                if parameter.kind is Parameter.VAR_KEYWORD
                else value
                if parameter.kind is Parameter.VAR_POSITIONAL
                else (value,)
            )
            for item in values:
                check_type(
                    item,
                    parameter.annotation,
                    forward_ref_policy=ForwardRefPolicy.ERROR,
                    collection_check_strategy=CollectionCheckStrategy.ALL_ITEMS,
                )


def check_result[T](
    result: T, contract: Signature, *, yielded: bool = False
) -> T:
    expected = contract.return_annotation
    if yielded:
        expected = get_args(resolve_alias(expected))[0]
    check_type(
        result,
        expected,
        forward_ref_policy=ForwardRefPolicy.ERROR,
        collection_check_strategy=CollectionCheckStrategy.ALL_ITEMS,
    )
    return result


def checked_async[**P, R](
    function: Callable[P, Awaitable[R]],
) -> Callable[P, Awaitable[R]]:
    contract = checked_signature(function)

    @wraps(function)
    async def call(*args: P.args, **kwargs: P.kwargs) -> R:
        check_arguments(contract.bind(*args, **kwargs))
        return check_result(await function(*args, **kwargs), contract)

    return call


def checked[**P, R](function: Callable[P, R]) -> Callable[P, R]:
    contract = checked_signature(function)

    @wraps(function)
    def call(*args: P.args, **kwargs: P.kwargs) -> R:
        arguments = contract.bind(*args, **kwargs)
        check_arguments(arguments)
        return check_result(function(*args, **kwargs), contract)

    return call
