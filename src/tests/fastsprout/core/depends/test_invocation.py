from fastsprout.core import Depends, inject_depends
from fastsprout.core.depends.invocation import with_dependencies


@inject_depends
async def test_nested_providers_without_operation_arguments_share_cache():
    calls: list[str] = []

    def source() -> int:
        calls.append("source")
        return 7

    def nested(value: int = Depends(source)) -> int:
        calls.append("nested")
        return value

    def check(operation: str, value: int = Depends(nested)) -> None:
        assert value == 7
        calls.append(operation)

    async def execute(operation: str) -> None:
        pass

    guarded = with_dependencies(execute, [Depends(check)])
    await guarded("create")
    await guarded("delete")
    assert calls == ["source", "nested", "create", "delete"]
