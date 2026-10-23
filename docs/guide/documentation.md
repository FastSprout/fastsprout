# Documentation publishing

The versioned documentation site is published at
[fastsprout.dev](https://fastsprout.dev/). It contains usage guides, runnable
examples, and an API reference generated from the Python source.

GitLab's `docs` stage publishes the site when `development` or a release tag
is pushed. The GitHub Actions `Docs` workflow builds the same documentation
from the mirrored release tags and development branch on GitHub, and retains
the rendered site as a workflow artifact named `documentation`. The release
workflow also calls `Docs` after publishing a release. Pull requests build
the documentation for review.

Build the complete versioned site from the repository root:

```bash
uv run --locked --all-extras --all-groups python scripts/build_docs.py \
  --dev-ref HEAD --output public
```

Omit `--dev-ref HEAD` to include uncommitted changes in the development
version. Open `public/index.html` to choose a release or the development
version. To serve the build locally:

```bash
python -m http.server --directory public
```

Use a new output directory for each build. Historical releases retain their
own documentation; changes to current guides appear in the development
version until the next release.
