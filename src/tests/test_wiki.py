import json
from pathlib import Path

import pytest

from fastsprout.testing.core import given, then, when
from scripts.export_wiki import export


class BaseTestWiki:
    @given("a rendered site with released and development documentation")
    def site(self, tmp_path: Path) -> Path:
        site = tmp_path / "site"
        site.mkdir()
        versions = [
            {"version": "0.1.1", "title": "0.1.1", "aliases": ["latest"]},
            {"version": "dev", "title": "dev", "aliases": []},
        ]
        (site / "versions.json").write_text(json.dumps(versions))
        for version in ("0.1.1", "dev"):
            root = site / version
            (root / "guide/usage").mkdir(parents=True)
            (root / "assets").mkdir()
            (root / "assets/logo.png").write_bytes(b"wiki-image")
            (root / "navigation.json").write_text(
                json.dumps(
                    [
                        {"Home": "index.md"},
                        {"Guide": [{"Usage": "guide/usage.md"}]},
                    ]
                )
            )
            for relative in ("index", "guide/usage"):
                (root / (relative + ".md")).write_text(f"# {version}")
                rendered = root if relative == "index" else root / relative
                (rendered / "index.html").write_text(
                    f'<article class="md-content__inner"><h1>{version}</h1>'
                    '<a href="https://fastsprout.dev/latest/guide/usage/?view=full#details">Usage</a>'
                    f'<img src="https://fastsprout.dev/{version}/assets/logo.png" alt="Logo">'
                    "</article>"
                )
        return site


@pytest.mark.parametrize("github", [False, True], ids=["gitlab", "github"])
class TestWikiExport(BaseTestWiki):
    @given("the target platform's wiki URL")
    def wiki_url(self, github: bool) -> str:
        return (
            "https://github.com/FastSprout/fastsprout/wiki"
            if github
            else "https://gitlab.3dcra.eu/opensource/fastsprout/fastsprout/-/wikis"
        )

    @when("the complete versioned site is exported")
    def wiki(
        self, site: Path, tmp_path: Path, wiki_url: str, github: bool
    ) -> Path:
        destination = tmp_path / "wiki"
        export(site, destination, wiki_url, github)
        return destination

    @then("aliases, query strings and anchors point to published wiki pages")
    def test_page_links(self, wiki: Path, wiki_url: str, github: bool) -> None:
        home = wiki / ("Home.md" if github else "home.md")
        page = "0.1.1-guide-usage" if github else "0.1.1/guide/usage"
        assert f"]({wiki_url}/{page}?view=full#details)" in home.read_text()
        assert (wiki / (page + ".md")).is_file()
        assert "# 0.1.1" in home.read_text()

    @then("images retain their contents and use a directly accessible URL")
    def test_images(self, wiki: Path, wiki_url: str, github: bool) -> None:
        home = wiki / ("Home.md" if github else "home.md")
        base = (
            "https://raw.githubusercontent.com/wiki/FastSprout/fastsprout"
            if github
            else wiki_url
        )
        assert f"]({base}/0.1.1/assets/logo.png)" in home.read_text()
        assert (wiki / "0.1.1/assets/logo.png").read_bytes() == b"wiki-image"

    @then("the platform sidebar links every version without page collisions")
    def test_navigation(self, wiki: Path, wiki_url: str, github: bool) -> None:
        navigation = (
            wiki / ("_Sidebar.md" if github else "_sidebar.md")
        ).read_text()
        for version in ("0.1.1", "dev"):
            page = (
                f"{version}-guide-usage" if github else f"{version}/guide/usage"
            )
            assert f"[Usage]({wiki_url}/{page})" in navigation
            assert f"# {version}" in (wiki / (page + ".md")).read_text()


class TestWikiCollision(BaseTestWiki):
    @when("two source paths would overwrite the same GitHub page")
    def failure(self, site: Path, tmp_path: Path) -> ValueError:
        (site / "0.1.1/guide-usage.md").write_text("# A different page")
        with pytest.raises(ValueError) as error:
            export(
                site,
                tmp_path / "wiki",
                "https://github.com/FastSprout/fastsprout/wiki",
                True,
            )
        return error.value

    @then("the export fails before creating an incomplete wiki")
    def test_collision(self, failure: ValueError, tmp_path: Path) -> None:
        assert "collide" in str(failure)
        assert not (tmp_path / "wiki").exists()
