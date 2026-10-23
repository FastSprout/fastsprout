# Documentation publishing

The versioned site and both project wikis use the same documentation sources.
GitLab's `docs` stage publishes the site and GitLab Wiki. The GitHub Actions
`Docs` workflow builds the site and publishes GitHub Wiki when `development`
or a release tag is pushed. The release workflow also calls `Docs` after
publishing a release. Pull requests build the documentation without publishing.

The GitHub workflow fetches release tags and the development reference from
GitLab, the canonical repository, so documentation versions match the GitLab
site. It retains the rendered site and exported wiki as workflow artifacts.

Before the first GitHub Wiki publication, save a page named `Home` in the
repository's Wiki tab, then rerun the latest `Docs` workflow. This initializes
the separate wiki repository. Until then, the build retains the wiki export as
an artifact and reports that initialization is pending. Subsequent updates use
the workflow's built-in `GITHUB_TOKEN` with `contents: write` in the publishing
job; no personal access token is required.

Build and inspect the exports locally:

```bash
uv run --locked --all-extras --all-groups python scripts/build_docs.py \
  --dev-ref HEAD --output public

uv run --locked --group docs python scripts/export_wiki.py \
  --site public --output github-wiki --github \
  --wiki-url https://github.com/FastSprout/fastsprout/wiki

uv run --locked --group docs python scripts/export_wiki.py \
  --site public --output gitlab-wiki \
  --wiki-url https://gitlab.3dcra.eu/opensource/fastsprout/fastsprout/-/wikis
```

Use a new output directory for each export. GitHub pages use version-prefixed
names and a `_Sidebar.md` navigation file. GitLab keeps nested page paths.
