# FastSprout

<img src="https://raw.githubusercontent.com/FastSprout/fastsprout/development/assets/fastsprout-mark.svg" alt="FastSprout logo" width="100" height="100">

**Typed building blocks for Python backends.**

<a href="https://github.com/FastSprout/fastsprout"><img alt="Pipeline" src="https://gitlab.3dcra.eu/opensource/fastsprout/fastsprout/badges/development/pipeline.svg"></a>
<a href="https://github.com/FastSprout/fastsprout"><img alt="Coverage" src="https://gitlab.3dcra.eu/opensource/fastsprout/fastsprout/badges/development/coverage.svg"></a>
<a href="https://github.com/FastSprout/fastsprout"><img alt="PyPI downloads" src="https://api.pepy.tech/badge/fastsprout"></a>
<a href="https://github.com/FastSprout/fastsprout/blob/development/pyproject.toml"><img alt="Version" src="https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fgitlab.3dcra.eu%2Fopensource%2Ffastsprout%2Ffastsprout%2F-%2Fraw%2Fdevelopment%2Fpyproject.toml&amp;query=%24.project.version&amp;label=version"></a>
<a href="https://github.com/FastSprout/fastsprout/blob/development/pyproject.toml"><img alt="Python" src="https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fgitlab.3dcra.eu%2Fopensource%2Ffastsprout%2Ffastsprout%2F-%2Fraw%2Fdevelopment%2Fpyproject.toml&amp;query=%24.project.requires-python&amp;label=python"></a>
<a href="https://github.com/FastSprout/fastsprout/blob/development/src/fastsprout/py.typed"><img alt="Typing" src="https://img.shields.io/badge/typing-typed-blue"></a>
<a href="https://github.com/FastSprout/fastsprout/blob/development/LICENSE"><img alt="License" src="https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fgitlab.3dcra.eu%2Fopensource%2Ffastsprout%2Ffastsprout%2F-%2Fraw%2Fdevelopment%2Fpyproject.toml&amp;query=%24.project.license&amp;label=license"></a>

FastSprout provides typed building blocks for Python backends: schemas, fields,
actions, DTO visibility, data routing, and events. Start with the core layer and
add the data or events extras when your application needs them.

[Documentation](https://github.com/FastSprout/fastsprout/tree/development/docs) ·
[Getting started](https://github.com/FastSprout/fastsprout/blob/development/docs/getting-started.md) ·
[Runnable examples](https://github.com/FastSprout/fastsprout/tree/development/examples) ·
[API reference](https://github.com/FastSprout/fastsprout/tree/development/src/fastsprout) ·
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

The [features guide](https://github.com/FastSprout/fastsprout/blob/development/docs/features.md) describes each
layer. The [API reference](https://github.com/FastSprout/fastsprout/tree/development/src/fastsprout) is generated from
the Python source in this repository.

## Security and license

Report vulnerabilities privately as described in the
[security policy](https://github.com/FastSprout/fastsprout/blob/development/SECURITY.md). FastSprout is licensed
under Apache-2.0; see [LICENSE](https://github.com/FastSprout/fastsprout/blob/development/LICENSE).
