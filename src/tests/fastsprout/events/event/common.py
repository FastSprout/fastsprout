from fastsprout.core import BaseSchema
from fastsprout.events import Event


class Message(Event):
    value: int


class Reply(BaseSchema):
    value: int
