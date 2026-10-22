# Test rules

## Structure and reuse

Write new tests and extend existing tests using `fastsprout.testing` on pytest.
Use `given`, `when`, and `then` from `fastsprout.testing.core`
for reusable BDD phases; use `fastsprout.testing.core.properties` for
Hypothesis property tests. Reuse phase fixtures and shared test cases instead
of repeating setup and execution in each test.

Declare preconditions with `@given`, execute the operation with `@when`, and
verify its result with `@then`. Connect phases through typed fixture arguments;
their dependency graph determines execution order. Separate a combined scenario
into these phases rather than relabeling the whole test as an assertion.

Mirror the production package structure when placing tests.
Follow `TestJoinedStreamContext` in
`src/tests/fastsprout/data/router/test_join_context.py` as the test style reference.
Group related tests in classes. In ordinary tests, mark setup, execution, and
assertions with separate `# given`, `# when`, and `# then` sections.
Do not combine execution and verification into one phase.
BDD decorators (`@given`, `@when`, `@then`)
already identify the phases; do not add phase comments inside those functions.
Pylint checks phase decorator conflicts, missing type annotations, and
redundant phase comments in BDD functions.
Extend existing tests and parametrize related cases before adding a new test
or file. Reuse fixtures, models, and helpers from `conftest.py` and `common.py`
instead of duplicating setup. Extract shared setup when it is reused, without
adding helpers or fixtures for a single use.
For behavior shared by multiple implementations or input types, reuse a base
test class and vary its factories, types, or fixtures, as in
`BaseTestSimpleAsyncEntityStream` in
`src/tests/fastsprout/data/streams/base_test_simple_entity_stream.py`.

## Typing checks

Reuse `src/tests/type_checking.py` and the existing typing fixtures. Check
both accepted usage and expected errors with mypy and basedpyright. Use the
active interpreter's Python version for the supported 3.12-3.14 matrix.
