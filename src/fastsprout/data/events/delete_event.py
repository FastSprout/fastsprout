from fastsprout.core.types.protocols.identificable import Identificatable
from fastsprout.events import Event

__all__ = ["DeleteEvent"]


class DeleteEvent[ID: Identificatable](Event):
    id: ID
