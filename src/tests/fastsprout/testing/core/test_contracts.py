from textwrap import indent

import pytest

from fastsprout.testing.core.contracts import require_type
from fastsprout.testing.core.properties import given, strategies


class TestContracts:
    @pytest.mark.parametrize(
        "style",
        ["module", "override", "parametrize", "indirect", "partly_indirect"],
    )
    def test_unrelated_fixtures_are_not_checked(
        self, pytester: pytest.Pytester, style: str
    ) -> None:
        # given
        pytester.makeini(
            "[pytest]\nasyncio_default_fixture_loop_scope = function"
        )
        pytester.makeconftest(
            'pytest_plugins = ["fastsprout.testing.core.plugin"]\n'
            + (
                "import pytest\n@pytest.fixture\ndef value(): return 'legacy'\n"
                if style != "module"
                else ""
            )
        )
        fixture = "@pytest.fixture\ndef value() -> int: return 1\n"
        if style == "parametrize":
            fixture = "@pytest.mark.parametrize('value', [1])\n"
        elif style in ("indirect", "partly_indirect"):
            indirect = "True" if style == "indirect" else "['value']"
            fixture = (
                "@pytest.fixture\ndef value(request: pytest.FixtureRequest) -> int: return request.param\n"
                f"@pytest.mark.parametrize('value', [1], indirect={indirect})\n"
            )
        pytester.makepyfile(
            test_typed="import pytest\nfrom fastsprout.testing.core import then\n"
            + fixture
            + "@then('a typed consumer')\ndef test_typed(value: int) -> None: assert value == 1\n",
            test_legacy="import pytest\n"
            + (
                ""
                if style != "module"
                else "@pytest.fixture\ndef value(): return 'legacy'\n"
            )
            + "def test_legacy(value): assert value == 'legacy'\n",
        )
        # when
        result = pytester.runpytest("--no-cov")
        # then
        result.assert_outcomes(passed=2)

    def test_missing_fixture_resolver_reports_usage_error(
        self, pytester: pytest.Pytester
    ) -> None:
        # given
        pytester.makeini(
            "[pytest]\nasyncio_default_fixture_loop_scope = function"
        )
        pytester.makeconftest(
            'pytest_plugins = ["fastsprout.testing.core.plugin"]\n'
            "import pytest\n@pytest.hookimpl(tryfirst=True)\n"
            "def pytest_collection_modifyitems(config): config.pluginmanager.unregister(name='funcmanage')\n"
        )
        pytester.makepyfile(
            "from fastsprout.testing.core import then\n"
            "@then('a typed test')\ndef test_value() -> None: pass\n"
        )
        # when
        result = pytester.runpytest("--no-cov")
        # then
        assert result.ret == pytest.ExitCode.USAGE_ERROR
        assert "fixture resolver is unavailable" in result.stderr.str()

    @pytest.mark.asyncio
    @given(strategies.integers())
    async def test_async_concrete_annotations(self, value: int) -> None:
        # when
        require_type(list[int])
        # then
        assert isinstance(value, int)

    @given(strategies.integers())
    def test_concrete_annotations(self, value: int) -> None:
        # when
        require_type(list[int])
        # then
        assert isinstance(value, int)

    @pytest.mark.parametrize(
        "declaration",
        [
            "@given('missing return')\ndef value(): return 1",
            "@when('missing argument')\ndef value(item) -> int: return 1",
            "@then('untyped test')\ndef test_value(item) -> None: pass",
            "@given('bare list')\ndef value() -> list: return []",
            "@given('broad type')\ndef value() -> object: return 1",
            "@given('nested broad type')\ndef value() -> list[object]: return []",
            "from typing import Any\n@given('any type')\ndef value() -> Any: return 1",
            "from typing import Dict\n@given('bare typing collection')\ndef value() -> Dict: return {}",
        ],
    )
    def test_untyped_declarations_are_rejected(
        self, pytester: pytest.Pytester, declaration: str
    ) -> None:
        # given
        pytester.makeini(
            "[pytest]\nasyncio_default_fixture_loop_scope = function"
        )
        pytester.makeconftest(
            'pytest_plugins = ["fastsprout.testing.core.plugin"]'
        )
        pytester.makepyfile(
            "from fastsprout.testing.core import given, when, then\n"
            + declaration
        )
        # when
        result = pytester.runpytest("--no-cov")
        # then
        result.assert_outcomes(errors=1)
        assert "TypeError" in result.stdout.str()

    @pytest.mark.parametrize(
        "provider, consumer",
        [
            ("str", "int"),
            ("int", "str"),
        ],
    )
    @pytest.mark.parametrize("style", ["function", "method"])
    @pytest.mark.parametrize("asynchronous", [False, True])
    @pytest.mark.parametrize("native", [False, True])
    def test_provider_and_consumer_types_are_checked(
        self,
        pytester: pytest.Pytester,
        provider: str,
        consumer: str,
        style: str,
        asynchronous: bool,
        native: bool,
    ) -> None:
        # given
        pytester.makeini(
            "[pytest]\nasyncio_default_fixture_loop_scope = function"
        )
        pytester.makeconftest(
            'pytest_plugins = ["fastsprout.testing.core.plugin"]'
        )
        first = "self, " if style == "method" else ""
        prefix = "async " if asynchronous else ""
        fixture = "@given('a value')"
        if native:
            fixture = (
                "@pytest_asyncio.fixture" if asynchronous else "@pytest.fixture"
            )
        declarations = (
            f"{fixture}\n{prefix}def value({first.rstrip(', ')}) -> {provider}: return 1\n"
            f"@then('a typed value')\ndef test_value({first}value: {consumer}) -> None: pass\n"
        )
        if style == "method":
            declarations = "class TestValues:\n" + indent(declarations, "    ")
        pytester.makepyfile(
            "import pytest\nimport pytest_asyncio\nfrom fastsprout.testing.core import given, then\n"
            + declarations
        )
        # when
        result = pytester.runpytest("--no-cov")
        # then
        if provider == "str":
            result.assert_outcomes(errors=1)
        else:
            result.assert_outcomes(failed=1)
        assert "TypeCheckError" in result.stdout.str()

    @pytest.mark.parametrize("annotation", ["", ": int"])
    def test_hypothesis_requires_types_and_checks_generated_inputs(
        self, pytester: pytest.Pytester, annotation: str
    ) -> None:
        # given
        pytester.makeini(
            "[pytest]\nasyncio_default_fixture_loop_scope = function"
        )
        pytester.makeconftest(
            'pytest_plugins = ["fastsprout.testing.core.plugin"]'
        )
        pytester.makepyfile(
            "from fastsprout.testing.core.properties import given, strategies\n"
            f"@given(strategies.just('wrong'))\ndef test_property(value{annotation}) -> None: pass\n"
        )
        # when
        result = pytester.runpytest("--no-cov")
        # then
        if annotation:
            result.assert_outcomes(failed=1)
            assert "TypeCheckError" in result.stdout.str()
        else:
            assert result.ret == pytest.ExitCode.USAGE_ERROR
            assert "concrete type annotation" in result.stderr.str()

    @pytest.mark.parametrize("scope", ["module", "session"])
    def test_shared_provider_is_checked_before_unmarked_consumer(
        self, pytester: pytest.Pytester, scope: str
    ) -> None:
        # given
        pytester.makeini(
            "[pytest]\nasyncio_default_fixture_loop_scope = function"
        )
        pytester.makeconftest(
            'pytest_plugins = ["fastsprout.testing.core.plugin"]'
        )
        pytester.makepyfile(
            "import pytest\nfrom fastsprout.testing.core import then\n"
            f"@pytest.fixture(scope={scope!r})\n"
            "def value() -> str: return 1\n"
            "def test_first(value: int) -> None: pass\n"
            "@then('a typed consumer')\n"
            "def test_second(value: int) -> None: pass\n"
        )
        # when
        result = pytester.runpytest("--no-cov")
        # then
        result.assert_outcomes(errors=2)
        assert "TypeCheckError" in result.stdout.str()
