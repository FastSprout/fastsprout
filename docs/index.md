# FastSprout { .fs-visually-hidden }

<div class="fs-brand" aria-label="FastSprout">
  <img src="assets/fastsprout-mark.svg" alt="" width="100" height="100">
  <span>FastSprout</span>
</div>

<p class="fs-lead">Typed building blocks for Python backends.</p>

<p class="fs-badges">
<a href="https://gitlab.3dcra.eu/opensource/fastsprout/fastsprout/-/pipelines?ref=development"><img alt="Pipeline" src="https://gitlab.3dcra.eu/opensource/fastsprout/fastsprout/badges/development/pipeline.svg"></a>
<a href="https://gitlab.3dcra.eu/opensource/fastsprout/fastsprout/-/pipelines?ref=development"><img alt="Test coverage" src="https://gitlab.3dcra.eu/opensource/fastsprout/fastsprout/badges/development/coverage.svg?job=pytest%3A%20%5B3.12%5D&amp;key_text=test%20coverage&amp;key_width=92&amp;min_good=100"></a>
<a href="https://gitlab.3dcra.eu/opensource/fastsprout/fastsprout/-/pipelines?ref=development"><img alt="Type coverage" src="https://gitlab.3dcra.eu/opensource/fastsprout/fastsprout/badges/development/coverage.svg?job=type-coverage%3A%20%5B3.12%5D&amp;key_text=type%20coverage&amp;key_width=96&amp;min_good=100"></a>
</p>

<p class="fs-badges">
<a href="https://github.com/FastSprout/fastsprout/blob/development/pyproject.toml"><img alt="Version" src="https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fgitlab.3dcra.eu%2Fopensource%2Ffastsprout%2Ffastsprout%2F-%2Fraw%2Fdevelopment%2Fpyproject.toml&amp;query=%24.project.version&amp;label=version"></a>
<a href="https://github.com/FastSprout/fastsprout/blob/development/pyproject.toml"><img alt="Python" src="https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fgitlab.3dcra.eu%2Fopensource%2Ffastsprout%2Ffastsprout%2F-%2Fraw%2Fdevelopment%2Fpyproject.toml&amp;query=%24.project.requires-python&amp;label=python"></a>
<a href="https://github.com/FastSprout/fastsprout/blob/development/LICENSE"><img alt="License" src="https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fgitlab.3dcra.eu%2Fopensource%2Ffastsprout%2Ffastsprout%2F-%2Fraw%2Fdevelopment%2Fpyproject.toml&amp;query=%24.project.license&amp;label=license"></a>
<a href="https://pypi.org/project/fastsprout/"><img alt="PyPI downloads" src="https://api.pepy.tech/badge/fastsprout"></a>
</p>

FastSprout puts application operations in typed actions and services, so an API,
CLI, and worker can reuse the same behavior and dependency checks. It provides
entity services for repeated CRUD work, a data router for shared persistence
contexts, and workflows for composing async operations.

[Documentation](https://fastsprout.dev/dev/) ·
[Getting started](https://fastsprout.dev/dev/getting-started/) ·
[Runnable examples](https://github.com/FastSprout/fastsprout/tree/development/examples) ·
[API reference](https://fastsprout.dev/dev/api/) ·
[Source](https://github.com/FastSprout/fastsprout) ·
[Contributing](https://github.com/FastSprout/fastsprout/blob/development/CONTRIBUTING.txt) ·
[Changelog](https://github.com/FastSprout/fastsprout/blob/development/CHANGELOG.txt)

## Install

Requires Python 3.12-3.14.

```bash
pip install 'fastsprout[standard]'
```

Follow [Getting started](https://fastsprout.dev/latest/getting-started/) for examples.

## What it helps with

- Reuse an application operation and its checks across endpoints, commands, and workers.
- Replace repeated entity CRUD, schema projection, and pagination code with `DataS`.
- Share persistence resources and choose when related changes settle with `DataR`.
- Compose typed async operations and process their results with `Workflow`.

## Explore

- **Core:** typed schemas, fields, DTO visibility, and dependency injection.
- **Actions:** function and class actions, services, `DataS` entity operations, and workflows.
- **Data:** `DataR` persistence contexts, entity backends, typed queries, streams, and joins.
- **Events:** EventBus with Bubus, asyncio.Queue, RabbitMQ, NATS, and Kafka adapters.
- **Testing:** typed pytest phases and database/broker test contexts.

The [features guide](https://fastsprout.dev/dev/features/) explains the problems
these layers address. Start with [actions and services](https://fastsprout.dev/dev/guide/actions/)
or [DataS, DataR, and persistence](https://fastsprout.dev/dev/guide/data/).
The [API reference](https://fastsprout.dev/dev/api/) is generated from the Python
source in this repository.

## Security and license

Report vulnerabilities privately as described in the
[security policy](https://github.com/FastSprout/fastsprout/blob/development/SECURITY.md). FastSprout is licensed
under Apache-2.0; see [LICENSE](https://github.com/FastSprout/fastsprout/blob/development/LICENSE).
