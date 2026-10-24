# Documentation publishing

The versioned documentation site is published at
[fastsprout.dev](https://fastsprout.dev/). It contains usage guides, runnable
examples, and an API reference generated from the Python source.

GitLab's `docs` stage publishes the site when `development`, `main`, or a release
tag is pushed. CI verifies changes before they enter `development`; it does not
repeat tests on `development`, on `main`, on release tags, or when merging
`development` into `main`. Tags run package publishing and GitLab Pages.
Publishing uses the committed example output without rerunning examples.
The GitHub Actions `Docs` workflow builds documentation for pull requests
targeting `development`, or when started manually, and retains the rendered
site as a workflow artifact named `documentation`.

The built-in Material `privacy` plugin downloads the three GitLab CI badges
during each build and serves them from the documentation site. Badge images
are refreshed when documentation is published; viewing them does not send
requests to GitLab. This applies to historical versions and `latest` too.

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
