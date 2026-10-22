from fastsprout.core import BaseSchema


class Amount(BaseSchema):
    value: int


class Computed(BaseSchema):
    value: int
    request_id: str
