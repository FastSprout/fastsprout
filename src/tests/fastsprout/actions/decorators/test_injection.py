from fastsprout.actions import Action, Service, action
from fastsprout.core import Depends, Schema, dataclass


@dataclass
class Value(Schema):
    value: int


async def test_actions_use_the_injector_cache_per_call() -> None:
    calls = 0

    def provide() -> int:
        nonlocal calls
        calls += 1
        return calls

    class Add(Action[Value, Value]):
        async def __call__(
            self, payload: Value, /, value: int = Depends(provide)
        ) -> Value:
            return Value(payload.value + value)

    @action
    async def pair(
        first: int = Depends(provide), second: int = Depends(provide)
    ) -> tuple[int, int]:
        return first, second

    assert await Add()(Value(10)) == Value(11)
    assert await pair() == (2, 2)
    assert await pair() == (3, 3)


async def test_nested_service_resolves_attributes_and_method_dependencies() -> (
    None
):
    def provide() -> int:
        return 7

    class Child(Service):
        value: int = Depends(provide)

        async def read(self, increment: int = Depends(provide)) -> int:
            return self.value + increment

    class Parent(Service):
        child: Child = Depends()

    bound_read = Parent().child.read
    assert await bound_read() == 14
    assert await bound_read(increment=1) == 8
