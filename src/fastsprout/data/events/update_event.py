from fastsprout.data.entity import Entitieable
from fastsprout.events import Event

__all__ = ["UpdateEvent"]


class UpdateEvent[E: Entitieable](Event):
    entity: E
