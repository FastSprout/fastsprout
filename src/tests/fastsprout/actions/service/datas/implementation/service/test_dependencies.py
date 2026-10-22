from uuid import uuid4

import pytest

from fastsprout.actions import DataS, action
from fastsprout.actions.service.datas import DataSOperation
from fastsprout.core import Depends, IdentificatorType
from fastsprout.data import DataR
from fastsprout.testing.core import given, then, when

from ...common import Record, RecordCreate


class CheckDelete:
    async def __call__(
        self, identifier: IdentificatorType, /, *, datar: DataR
    ) -> None:
        assert await DataS(Record).exists(identifier, datar=datar)


class GuardedRecords(DataS[Record]):
    dependencies = (Depends(CheckDelete()),)


class TestDependencyValidation:
    @when("a callable dependency is used before deleting a record")
    async def checked_delete(
        self, records: DataS[Record]
    ) -> tuple[Record, int]:
        created = await records.create(Record(name="Batman"))
        service = DataS(Record, dependencies=[Depends(CheckDelete())])
        return created, await service.delete(created.id)

    @then("a callable dependency checks the key before deletion")
    async def test_callable_class_and_successful_delete(
        self, records: DataS[Record], checked_delete: tuple[Record, int]
    ) -> None:
        created, deleted = checked_delete
        assert deleted == 1
        assert await records.exists(created.id) is False

    @when("one service instance overrides inherited dependencies")
    async def overridden_delete(
        self, records: DataS[Record]
    ) -> tuple[GuardedRecords, int, bool, bool]:
        created = await records.create(Record(name="Batman"))
        inherited = GuardedRecords()
        original = inherited.dependencies
        overridden = GuardedRecords(dependencies=[])
        independent = overridden.dependencies is not original
        deleted = await overridden.delete(created.id)
        return (
            inherited,
            deleted,
            independent,
            inherited.dependencies is original,
        )

    @then("overriding dependencies preserves inherited configuration")
    def test_dependency_configuration_is_inherited_and_replaceable(
        self, overridden_delete: tuple[GuardedRecords, int, bool, bool]
    ) -> None:
        inherited, deleted, independent, unchanged = overridden_delete
        assert isinstance(inherited.dependencies[0].dependency, CheckDelete)
        assert independent
        assert deleted == 1
        assert unchanged

    @when("a disabled delete is attempted")
    async def disabled_delete(
        self, records: DataS[Record]
    ) -> AttributeError | None:
        def never() -> None:
            raise AssertionError("A disabled operation ran a dependency")

        service = DataS(
            Record,
            operations=frozenset({"exists"}),
            dependencies=[Depends(never)],
        )
        try:
            await service.delete(uuid4())
        except AttributeError as error:
            return error
        return None

    @then("a disabled operation never runs its dependencies")
    def test_disabled_operation_does_not_run_dependencies(
        self, disabled_delete: AttributeError | None
    ) -> None:
        assert isinstance(disabled_delete, AttributeError)
        assert "disabled" in str(disabled_delete)

    @when("get, exists, count, and list are invoked with dependencies")
    async def observed_reads(
        self, records: DataS[Record]
    ) -> tuple[list[DataSOperation], Record | None, bool, int, int]:
        created = await records.create(Record(name="Batman"))
        operations: list[DataSOperation] = []

        def check(operation: DataSOperation) -> None:
            operations.append(operation)

        service = DataS(Record, dependencies=[Depends(check)])
        found = await service.get(created.id)
        existed = await service.exists(created.id)
        count = await service.count()
        total = (await service.list()).total
        return operations, found, existed, count, total

    @then("each read operation runs its dependencies")
    def test_dependencies_run_for_read_operations(
        self,
        observed_reads: tuple[
            list[DataSOperation], Record | None, bool, int, int
        ],
    ) -> None:
        operations, found, existed, count, total = observed_reads
        assert found is not None
        assert existed
        assert count == total == 1
        assert operations == ["get", "exists", "count", "list"]

    @when("payload checks and normalization are executed in order")
    async def normalized_create(
        self, records: DataS[Record], active_datar: DataR
    ) -> tuple[Record, list[str]]:
        calls: list[str] = []

        async def normalize(entity: RecordCreate) -> None:
            calls.append("model")
            entity.name = entity.name.strip()

        def check_name(entity: RecordCreate) -> None:
            calls.append("name")
            assert entity.name == " Batman "

        async def check_database(datar: DataR) -> None:
            calls.append("database")
            assert await records.count(datar=datar) == 0

        service = DataS(
            Record,
            create=RecordCreate,
            dependencies=[
                Depends(check_name),
                Depends(check_database),
                Depends(normalize),
            ],
        )
        created = await service.create(
            RecordCreate(name=" Batman "), datar=active_datar
        )
        return created, calls

    @then("dependencies check and normalize the payload in order")
    async def test_dependencies_run_checks_and_normalization_in_order(
        self,
        records: DataS[Record],
        active_datar: DataR,
        normalized_create: tuple[Record, list[str]],
    ) -> None:
        created, calls = normalized_create
        assert created.name == "Batman"
        assert calls == ["name", "database", "model"]
        assert await records.count(datar=active_datar) == 1

    @given("a rejecting dependency chain with optional preparatory writes")
    def rejecting_service(
        self, records: DataS[Record], related: bool
    ) -> tuple[DataS[Record], list[str]]:
        calls: list[str] = []

        async def prepare(datar: DataR) -> None:
            calls.append("prepare")
            if related:
                await records.create(Record(name="Related"), datar=datar)

        async def reject() -> None:
            calls.append("reject")
            raise PermissionError("Forbidden")

        def after_rejection() -> None:
            calls.append("after")

        service = DataS(
            Record,
            dependencies=[
                Depends(prepare),
                Depends(reject),
                Depends(after_rejection),
            ],
        )
        return service, calls

    @when("a dependency rejects a write after optional preparatory writes")
    async def rejected_create(
        self, rejecting_service: tuple[DataS[Record], list[str]]
    ) -> tuple[list[str], PermissionError | None]:
        service, calls = rejecting_service
        try:
            await service.create(Record(name="Batman"))
        except PermissionError as error:
            return calls, error
        return calls, None

    @then("a rejected dependency stops execution and rolls back its writes")
    @pytest.mark.parametrize("related", [False, True])
    async def test_dependency_failure_rolls_back_the_invocation(
        self,
        records: DataS[Record],
        rejected_create: tuple[list[str], PermissionError | None],
    ) -> None:
        calls, failure = rejected_create
        assert isinstance(failure, PermissionError)
        assert str(failure) == "Forbidden"
        assert calls == ["prepare", "reject"]
        assert await records.count() == 0

    @when("a key-checking dependency rejects deletion")
    async def rejected_delete(
        self, records: DataS[Record], active_datar: DataR
    ) -> tuple[
        Record, list[tuple[IdentificatorType, DataR]], PermissionError | None
    ]:
        created = await records.create(Record(name="Batman"))
        calls: list[tuple[IdentificatorType, DataR]] = []

        async def check_exists(
            identifier: IdentificatorType, /, *, datar: DataR
        ) -> None:
            assert await records.exists(identifier, datar=datar)

        @action(dependencies=[Depends(check_exists)])
        async def check_key(
            identifier: IdentificatorType, *, datar: DataR = Depends()
        ) -> None:
            calls.append((identifier, datar))

        @action
        async def reject() -> None:
            raise PermissionError("Cannot delete")

        service = DataS(
            Record, dependencies=[check_key.dependency, Depends(reject)]
        )
        try:
            await service.delete(created.id, datar=active_datar)
        except PermissionError as error:
            return created, calls, error
        return created, calls, None

    @then("delete dependencies receive the key and can reject")
    async def test_delete_dependencies_receive_the_key_and_can_reject(
        self,
        records: DataS[Record],
        active_datar: DataR,
        rejected_delete: tuple[
            Record,
            list[tuple[IdentificatorType, DataR]],
            PermissionError | None,
        ],
    ) -> None:
        created, calls, failure = rejected_delete
        assert isinstance(failure, PermissionError)
        assert str(failure) == "Cannot delete"
        assert calls == [(created.id, active_datar)]
        assert await records.exists(created.id)
