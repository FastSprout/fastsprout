import copy
import pickle

from fastsprout.core import Undefined, UndefinedType
from fastsprout.testing.core import then, when


class TestUndefined:
    @when("the sentinel is copied, deep-copied and serialized")
    def copies(self) -> tuple[UndefinedType, UndefinedType, UndefinedType]:
        return (
            copy.copy(Undefined),
            copy.deepcopy(Undefined),
            pickle.loads(pickle.dumps(Undefined)),
        )

    @then("the sentinel stays falsy and preserves its identity")
    def test_singleton(
        self, copies: tuple[UndefinedType, UndefinedType, UndefinedType]
    ) -> None:
        assert not Undefined
        assert repr(Undefined) == "Undefined"
        assert all(value is Undefined for value in copies)
