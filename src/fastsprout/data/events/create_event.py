from fastsprout.data.entity import Entitieable
from fastsprout.events import Event

__all__ = ["CreateEvent"]


class CreateEvent[E: Entitieable](Event):
    entity: E
