from .protocols.ables import AIterable, Iterable

__all__ = ["AnyIterable"]

type AnyIterable[S] = Iterable[S] | AIterable[S]
