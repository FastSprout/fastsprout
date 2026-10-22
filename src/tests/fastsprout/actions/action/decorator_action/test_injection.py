from collections.abc import Callable

from fastsprout.actions import Action, Service, action
from fastsprout.core import Depends, Schema, dataclass
from fastsprout.testing.core import given, then, when


@dataclass
class Value(Schema):
    value: int


class TestActionGroup:
    @given("a recorder of provider and dependency execution")
    def calls(self) -> list[str]:
        return []

    @given("an attribute dependency that records instantiation")
    def provider(self, calls: list[str]) -> Callable[[], int]:
        def provide() -> int:
            calls.append("provide")
            return 7

        return provide

    @given("a dependency for every action in a decorated class")
    def check(self, calls: list[str]) -> Callable[[], None]:
        def verify() -> None:
            calls.append("check")

        return verify

    @when("a dependency attribute is read on the action group class")
    def class_access(self, provider: Callable[[], int]) -> bool:
        @action
        class Group:
            value: int = Depends(provider)

        return Group.value is Group.value

    @then("class access preserves the descriptor without resolving a value")
    def test_class_access(self, class_access: bool, calls: list[str]) -> None:
        assert class_access
        assert calls == []

    @when("a method of a class decorated with dependencies is called")
    async def executed(self, check: Callable[[], None]) -> Value:
        @action(dependencies=[Depends(check)])
        class Group:
            async def execute(self, payload: Value) -> Value:
                return payload

        return await Group().execute(Value(7))

    @then("the class dependency runs before its method")
    def test_class_dependency(self, executed: Value, calls: list[str]) -> None:
        assert executed.value == 7
        assert calls == ["check"]

    @when("the function adapter receives an asynchronous callable instance")
    def callable_instance(self) -> TypeError | None:
        class CallableAction:
            async def __call__(self) -> Value:
                return Value(7)

        try:
            action().function(CallableAction())
        except TypeError as error:
            return error
        return None

    @then("the function adapter requires an async function")
    def test_callable_instance(
        self, callable_instance: TypeError | None
    ) -> None:
        assert isinstance(callable_instance, TypeError)
        assert "requires an async function or class" in str(callable_instance)


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
