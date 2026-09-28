# FastSprout { .fs-visually-hidden }

<div class="fs-brand" aria-label="FastSprout">
  <img src="assets/fastsprout-mark.svg" alt="" width="100" height="100">
  <span>FastSprout</span>
</div>

<p class="fs-lead">Typed building blocks for Python backends.</p>

[![Pipeline][pipeline-badge]][pipeline-link]
[![Coverage][coverage-badge]][pipeline-link]
[![Version][version-badge]][project-metadata]
[![Python][python-badge]][project-metadata]
[![Typing][typing-badge]][typed-marker]
[![License][license-badge]][license-file]

FastSprout provides typed building blocks for Python backends: schemas, fields,
actions, DTO visibility, data routing, and events. Start with the core layer and
add the data or events extras when your application needs them.

[Documentation](https://fastsprout.dev/) ·
[Getting started](https://fastsprout.dev/latest/getting-started/) ·
[Runnable examples](https://fastsprout.dev/latest/learn/examples/) ·
[API reference](https://fastsprout.dev/latest/api/) ·
[Source](https://github.com/FastSprout/fastsprout)

## Install

FastSprout supports Python 3.12-3.14.

```bash
pip install "fastsprout[standard]"
```

## Explore

- **Core:** typed schemas, fields, actions, and DTO visibility.
- **Data:** routing entities to persistence backends, streams, and joins.
- **Events:** in-memory publishing and subscription through `EventBus`.

The [features guide](https://fastsprout.dev/latest/features/) describes each
layer. The [API reference](https://fastsprout.dev/latest/api/) is generated from
the Python source in this repository.

## Security and license

Report vulnerabilities privately as described in the
[security policy](https://fastsprout.dev/latest/security/). FastSprout is licensed
under Apache-2.0; see [LICENSE](https://github.com/FastSprout/fastsprout/blob/development/LICENSE).

[pipeline-badge]: https://gitlab.3dcra.eu/opensource/fastsprout/fastsprout/badges/development/pipeline.svg
[coverage-badge]: https://gitlab.3dcra.eu/opensource/fastsprout/fastsprout/badges/development/coverage.svg
[pipeline-link]: https://gitlab.3dcra.eu/opensource/fastsprout/fastsprout/-/pipelines?ref=development
[version-badge]: https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fgitlab.3dcra.eu%2Fopensource%2Ffastsprout%2Ffastsprout%2F-%2Fraw%2Fdevelopment%2Fpyproject.toml&query=%24.project.version&label=version
[python-badge]: https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fgitlab.3dcra.eu%2Fopensource%2Ffastsprout%2Ffastsprout%2F-%2Fraw%2Fdevelopment%2Fpyproject.toml&query=%24.project.requires-python&label=python
[typing-badge]: https://img.shields.io/badge/typing-typed-blue
[license-badge]: https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fgitlab.3dcra.eu%2Fopensource%2Ffastsprout%2Ffastsprout%2F-%2Fraw%2Fdevelopment%2Fpyproject.toml&query=%24.project.license&label=license
[project-metadata]: https://gitlab.3dcra.eu/opensource/fastsprout/fastsprout/-/blob/development/pyproject.toml
[typed-marker]: https://github.com/FastSprout/fastsprout/blob/development/src/fastsprout/py.typed
[license-file]: https://github.com/FastSprout/fastsprout/blob/development/LICENSE
