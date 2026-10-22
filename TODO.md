# Query source typing

- [x] Support `class Hero(SQLEntity[UUID, CRM]): ...` without a separate
  entity base for each source.
- [x] Execute chained SQLQuery.join calls as one lazy SQL statement with
  statically typed tuple results through DataR.stream.
- [x] Verify source-scoped entity types in field comparisons, copied and
  chained joins, logical root conditions, and streamed tuple elements with
  both mypy and basedpyright.
- [x] Preserve the concrete entity and explicitly bound query source through
  copies, field conditions, logical groups, and chained joins.
- [x] Add typed `signpost.bind(Entity)` with source validation before assignment,
  retaining factory protocols and unscoped entities. Direct `__signpost__`
  declarations remain runtime-checked, without inferred static linkage.
- [x] With `SQLQuery(Entity, source=signpost)`, reject mixed join target
  source types in mypy and basedpyright, including chained joins. Existing
  root condition checks also reject foreign fields inside `query.Or(...)`.
- [x] Infer the query source directly from the entity in `SQLQuery(Entity)`;
  preserve entity and source types in mypy, Pyright, and basedpyright.
- [x] Keep runtime signpost identity checks: two instances of the same
  signpost type can still represent different databases.
- [x] Verify accepted and rejected cases with the existing typing fixtures,
  without generated declarations, broad fallback types, casts, or ignores.
- [x] Update runnable join examples and generated docs for typed binding and
  multi-entity conditions; both checkers accept the examples.

The accepted field syntax remains `Hero.name.eq("Batman")`,
`Hero.power.gte(50)`, `Hero.power.in_(values)`, and
`Hero.power.between(10, 50)`, combined through Query's `And`, `Or`, `Xor`,
and `Nand`. SQL entities retain an optional source type and validate signpost
declarations. SQLQuery.join checks shared signpost identity at runtime and
preserves each selected entity type. Explicit source binding checks join
targets statically. The entity-class protocol also infers the source without
an explicit binding. Conditions can combine fields
from joined entities; foreign fields are rejected by both checkers.

- [x] Preserve joined entity field scope through logical groups, chained joins,
  Python fallback evaluation, and pagination.
- [x] Fix existing payload field, ability factory, and SQL stream typing errors;
  basedpyright reports zero errors and warnings, and SQL mypy contracts pass.

# Framework-supported test structure

- [x] Add a separate `fastsprout.testing.core` layer executed by pytest, with
  typed BDD fixtures and assertion tests. Use it in FastSprout's tests,
  including the testing layer's own tests.
- [x] Require concrete annotations for phase providers and consumers, validate
  fixture values through pytest hooks, and check generated Hypothesis inputs.
- [x] Express test phases through framework decorators: `@given`, `@when`,
  and `@then` in separate functions.
  Support reusable phase functions and existing fixtures and base test classes.
- [x] Support both Cucumber-style class methods and Behave-style functions
  sharing a scenario context. Preserve the concrete context type in both styles.
  Parse named step parameters such as `{product_name}` and `{count:d}`,
  passing converted values to the step function. Use `pytest.mark.steps`
  to provide text cases and pytest's parametrization to execute them.
- [x] Support Hypothesis property-based tests with strategies, generated
  inputs, and shrinking. Reuse Hypothesis itself and keep its `given`
  import distinct from BDD step declarations.
- [x] Lint BDD phase declarations: reject conflicting phase decorators,
  missing type annotations, and redundant phase comments. Recognize aliases
  and distinguish Hypothesis from BDD declarations.

- [ ] Migrate existing tests to `fastsprout.testing` together with the user;
  do not perform this migration as part of autonomous query work.

# Project documentation and releases

- [x] Add `CHANGELOG.txt`.
- [x] Add `CONTRIBUTING.txt`.
- [x] Set up the project wiki.
- [x] Add a GitHub Actions workflow that creates a Git release tag and
  publishes matching releases on GitHub and GitLab.

# Query write overloads

- [x] Accept one or more `FieldPredicate` conditions directly in
  `update_by_query` and `delete_by_query`, combined with AND.
  Keep the existing Query signatures and reuse their execution path.
- [x] Support `.query_for(Hero)` and `.query_for()` with
  `entity=Undefined` defaulting to the owner's entity. Preserve the concrete
  entity type in both forms through overloads; do not leave the return type
  generic unbound when the argument is omitted.

# DataS read predicates

- [x] Accept Query or AND-combined FieldPredicate arguments in
  `find_exactly_one`, preserving the configured read schema in runtime
  and both type checkers. Reuse query validation and existing read tests.

# DataS configuration

- [x] Derive default operation names from `DataSOperation` instead of
  maintaining a second literal list.
- [x] Preserve heterogeneous schema settings in `configure_schemas`
  without inferring a common model type; verify the generic regression
  with mypy and basedpyright.

# SQL update regression

- [x] Verify that updating a missing entity raises `LookupError` and does
  not insert it, for both SQLAbilitable and SQLUpdatable.

# Dependency failure regression

- [x] Verify that a rejecting DataS dependency stops later dependencies,
  prevents the main write, and rolls back preceding dependency writes.

# Non-SQL read routing regression

- [x] Route DataR streams through the shared memory backend fixture and
  verify list/count alongside CRUD within the same DataR context.

# Reusable Given setup

- [x] Declare shared DataS and SQL setup through `@given`, and reuse
  one seeded read-DTO fixture across stream and exact-match tests.

# Non-SQL bulk regression

- [x] Verify create, patch and delete with explicit dataclass schemas,
  synchronous and asynchronous inputs, and one shared DataR context.
  Reuse the memory backend fixture and existing iterable adapters.

# Dependency ordering regression

- [x] Verify ordered payload checks, access to the shared DataR, and
  normalization before the create operation persists the entity.

# Contextual dependency regression

- [x] Verify per-payload dependency execution inside a parent action and
  operation/DataR propagation through nested dependency providers.

# Dependency operation controls

- [x] Verify that read operations run their dependencies and disabled
  operations reject the call before any dependency runs.

# Inherited dependency regression

- [x] Verify callable-class dependencies and inherited DataS dependency
  configuration with an instance-specific override.

# Rejected write dependency chain

- [x] Extend the existing four write-validation cases to prove that
  rejection also prevents every subsequent dependency from running.

# Database and broker testing contexts

Each stage must be an independently usable change with its implementation,
relevant tests, runnable examples, and documentation. Reuse existing adapter
protocols. Keep adapter-specific configuration and precise types; do not use
closed unions of supported adapters or untyped keyword arguments.

- [x] Review the existing data and event adapter contracts. Separate adapter
  configuration from test infrastructure startup without duplicating contracts.
- [x] Add `fastsprout.testing.data` with an async SQLite in-memory context.
  Prepare tables for the selected entities, sessions, and signpost; expose
  the resources, close them on exit, and restore previous entity bindings.
  Allow SQLAlchemy engine and session settings to be overridden.
- [x] Add a PostgreSQL context using Testcontainers and reuse the SQL setup.
  Preserve container, Harbor image, connection, and session configuration.
  Isolate tests even when application code commits transactions.
- [x] Add a RabbitMQ adapter in `fastsprout.events` and its Testcontainers
  context in `fastsprout.testing.events`. Reuse the broker contract and verify
  publishing, delivery, acknowledgements, errors, and resource cleanup.
- [x] Add a Kafka adapter and matching testing context. Preserve partition,
  consumer-group, and offset semantics rather than imposing RabbitMQ behavior.
- [x] Add CI integration and optional dependencies for container tests.
  Report unavailable infrastructure explicitly. Keep examples and generated
  documentation aligned with the implemented contexts.
- [ ] Migrate existing framework tests together with the user, starting with
  shared fixtures and then individual test groups. Use `fastsprout.testing`
  and the database/broker contexts to remove repeated infrastructure setup;
  do not perform this migration autonomously.
