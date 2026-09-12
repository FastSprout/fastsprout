import pytest

from fastsprout.core.depends import DependsClass
from fastsprout.data.unit_of_work.implementation import SimpleUnitOfWork

__all__ = ["BaseTestUnitOfWork"]


class BaseTestUnitOfWork[UoW: SimpleUnitOfWork]:
    _uow_type: type[UoW]
    _attr_name: str = "test"
    _attr_type: type
    _args: staticmethod
    _kwargs: staticmethod

    @property
    def uow(self) -> UoW:
        return self._uow_type(*self._args(), **self._kwargs())

    async def test_attrs_are_not_init(self):
        # given
        uow = self.uow
        # when
        result = uow.attrs_are_init
        # then
        assert result is False

    async def test_attr_is_depends_before_begin(self):
        # given
        uow = self.uow
        # when
        result = getattr(uow, self._attr_name)
        # then
        assert isinstance(result, DependsClass)

    async def test_begin(self):
        # given
        uow = self.uow
        # when
        uow.begin()
        # then
        assert uow.attrs_are_init is True
        assert isinstance(getattr(uow, self._attr_name), self._attr_type)

    async def test_begin_twice(self):
        # given
        uow = self.uow
        uow.begin()
        # when
        # then
        with pytest.raises(RuntimeError):
            uow.begin()

    async def test_close_without_begin(self):
        # given
        uow = self.uow
        # when
        # then
        with pytest.raises(RuntimeError):
            uow.close()

    async def test_close(self):
        # given
        uow = self.uow
        uow.begin()
        # when
        uow.close()
        # then
        assert uow.attrs_are_init is False
        assert isinstance(getattr(uow, self._attr_name), DependsClass)

    async def test_begin_after_close(self):
        # given
        uow = self.uow
        uow.begin()
        first_attr = getattr(uow, self._attr_name)
        uow.close()
        # when
        uow.begin()
        # then
        second_attr = getattr(uow, self._attr_name)
        assert isinstance(second_attr, self._attr_type)
        assert second_attr is not first_attr

    async def test_init_attrs_returns_mapping(self):
        # given
        uow = self.uow
        # when
        result = uow.__init_attrs__()
        # then
        assert isinstance(result, dict)
        assert self._attr_name in result
        assert isinstance(result[self._attr_name], self._attr_type)

    async def test_context_manager(self):
        # given
        uow = self.uow
        # when
        with uow as entered:
            # then
            assert entered is uow
            assert uow.attrs_are_init is True
            assert isinstance(getattr(uow, self._attr_name), self._attr_type)
        assert uow.attrs_are_init is False

    async def test_async_context_manager(self):
        # given
        uow = self.uow
        # when
        async with uow as entered:
            # then
            assert entered is uow
            assert uow.attrs_are_init is True
            assert isinstance(getattr(uow, self._attr_name), self._attr_type)
        assert uow.attrs_are_init is False

    async def test_context_manager_closes_on_error(self):
        # given
        uow = self.uow
        # when
        with pytest.raises(ValueError):
            with uow:
                raise ValueError
        # then
        assert uow.attrs_are_init is False

    async def test_async_context_manager_closes_on_error(self):
        # given
        uow = self.uow
        # when
        with pytest.raises(ValueError):
            async with uow:
                raise ValueError
        # then
        assert uow.attrs_are_init is False

    async def test_nested_context_manager(self):
        # given
        uow = self.uow
        # when
        # then
        with uow:
            with pytest.raises(RuntimeError):
                with uow:
                    ...

    async def test_attrs_are_independent_between_instances(self):
        # given
        first = self.uow
        second = self.uow
        # when
        first.begin()
        # then
        assert first.attrs_are_init is True
        assert second.attrs_are_init is False
        assert isinstance(getattr(second, self._attr_name), DependsClass)
