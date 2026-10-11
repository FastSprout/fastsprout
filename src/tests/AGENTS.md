# Test rules

## Structure and reuse

Mirror the production package structure when placing tests.
Follow `TestJoinedStreamContext` in
`src/tests/fastsprout/data/router/test_join_context.py` as the test style reference.
Group related tests in classes and mark setup, execution, and assertions with
`# given`, `# when`, and `# then`; use `# when / then` for expected exceptions.
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
