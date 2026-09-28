"""Build every documented package release into one GitLab Pages artifact."""

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

from mkdocs.commands.build import build as mkdocs_build
from mkdocs.config import load_config
from packaging.version import Version

if __package__:
    from .docs_nav import render_example_output
else:
    from docs_nav import render_example_output

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://fastsprout.dev"
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


def git(*args: str, cwd: Path = ROOT) -> bytes:
    return subprocess.check_output(["git", *args], cwd=cwd)


def package_version(ref: str) -> str | None:
    try:
        raw = git("show", f"{ref}:pyproject.toml")
    except subprocess.CalledProcessError:
        return None
    project = tomllib.loads(raw.decode())["project"]
    if project.get("name") != "fastsprout":
        return None
    return project["version"]


def release_refs() -> list[tuple[Version, str, str]]:
    releases = []
    for tag in git("tag", "--list").decode().splitlines():
        version = package_version(tag)
        if version is None or tag not in {version, f"v{version}"}:
            continue
        try:
            parsed = Version(version)
            git("cat-file", "-e", f"{tag}:mkdocs.yml")
        except (ValueError, subprocess.CalledProcessError):
            continue
        releases.append((parsed, version, tag))
    return sorted(releases, reverse=True)


def snapshot(ref: str, destination: Path) -> None:
    archive = git("archive", "--format=tar", ref)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(destination, filter="data")


def build(source: Path, destination: Path, slug: str) -> None:
    previous_dir = Path.cwd()
    try:
        os.chdir(source)
        config = load_config(
            config_file=str(source / "mkdocs.yml"),
            site_url=f"{SITE_URL}/{slug}/",
            site_dir=str(destination),
        )
        project = tomllib.loads((source / "pyproject.toml").read_text())[
            "project"
        ]
        config["extra"]["package_version"] = project["version"]
        config.plugins.on_startup(command="build", dirty=False)
        try:
            mkdocs_build(config)
        finally:
            config.plugins.on_shutdown()
        write_markdown_and_llms(source, destination, slug, config)
    finally:
        os.chdir(previous_dir)


def copy_markdown(source: Path, destination: Path) -> list[tuple[Path, str]]:
    pages = []
    for markdown in sorted((source / "docs").rglob("*.md")):
        relative = markdown.relative_to(source / "docs")
        content = render_example_output(
            markdown.read_text(encoding="utf-8"), source
        )

        def include_source(match: re.Match[str]) -> str:
            snippet = (source / match.group(1)).resolve()
            if not snippet.is_relative_to(source.resolve()):
                raise ValueError(f"Snippet escapes source tree: {snippet}")
            return snippet.read_text(encoding="utf-8").rstrip()

        content = re.sub(
            r'^--8<-- "([^"]+)"$', include_source, content, flags=re.M
        )
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        title = next(
            (
                line[2:].split(" {", 1)[0]
                for line in content.splitlines()
                if line.startswith("# ")
            ),
            relative.stem.replace("-", " ").title(),
        )
        pages.append((relative, title))
    return pages


def write_llms(
    destination: Path, slug: str, config, pages: list[tuple[Path, str]]
) -> None:
    lines = [
        f"# {config['site_name']}",
        "",
        f"> {config['site_description']}",
        "",
        "## Documentation",
        "",
    ]
    for relative, title in pages:
        if (
            relative.parts[:2] != ("learn", "examples")
            or relative.name == "index.md"
        ):
            if relative.parts[0] == "api":
                target = (
                    relative.parent
                    if relative.stem == "index"
                    else relative.with_suffix("")
                ).as_posix() + "/"
            else:
                target = relative.as_posix()
            lines.append(f"- [{title}]({SITE_URL}/{slug}/{target})")
    examples = [
        (relative, title)
        for relative, title in pages
        if relative.parts[:2] == ("learn", "examples")
        and relative.name != "index.md"
    ]
    if examples:
        examples.sort(
            key=lambda item: (
                item[0].parts[2],
                int(item[0].stem.partition("-")[0]),
                item[0].stem,
            )
        )
        lines.extend(("", "## Examples", ""))
        lines.extend(
            f"- [{title}]({SITE_URL}/{slug}/{relative.as_posix()})"
            for relative, title in examples
        )
    (destination / "llms.txt").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )


def write_markdown_and_llms(
    source: Path, destination: Path, slug: str, config
) -> None:
    pages = copy_markdown(source, destination)
    write_llms(destination, slug, config, pages)


def write_index(output: Path, releases: list[tuple[Version, str, str]]) -> None:
    latest = releases[0][1] if releases else "dev"
    versions = [
        {
            "version": version,
            "title": version,
            "aliases": ["latest"] if index == 0 else [],
        }
        for index, (_, version, _) in enumerate(releases)
    ]
    versions.append(
        {
            "version": "dev",
            "title": "dev",
            "aliases": ["latest"] if not releases else [],
        }
    )
    shutil.copytree(output / latest, output / "latest")
    latest_llms = output / "latest" / "llms.txt"
    latest_llms.write_text(
        latest_llms.read_text(encoding="utf-8").replace(
            f"{SITE_URL}/{latest}/", f"{SITE_URL}/latest/"
        ),
        encoding="utf-8",
    )
    (output / "versions.json").write_text(
        json.dumps(versions, indent=2) + "\n", encoding="utf-8"
    )
    (output / "index.html").write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0; url=latest/">'
        '<link rel="canonical" href="https://fastsprout.dev/latest/">'
        "<title>FastSprout documentation</title></head><body>"
        '<a href="latest/">Open FastSprout documentation</a>'
        "</body></html>\n",
        encoding="utf-8",
    )
    for verification in ROOT.glob("google*.html"):
        expected = f"google-site-verification: {verification.name}"
        if verification.read_text(encoding="utf-8").strip() != expected:
            raise ValueError(
                f"Invalid Google verification file: {verification}"
            )
        shutil.copyfile(verification, output / verification.name)

    llms = [
        "# FastSprout",
        "",
        "> Typed building blocks for Python backends.",
        "",
        "## Documentation versions",
        "",
        f"- [Latest documentation]({SITE_URL}/latest/llms.txt)",
        f"- [Development documentation]({SITE_URL}/dev/llms.txt)",
    ]
    llms.extend(
        f"- [{version}]({SITE_URL}/{version}/llms.txt)"
        for _, version, _ in releases
    )
    (output / "llms.txt").write_text("\n".join(llms) + "\n", encoding="utf-8")

    ET.register_namespace("", SITEMAP_NS)
    index = ET.Element(f"{{{SITEMAP_NS}}}sitemapindex")
    for slug in [*(version for _, version, _ in releases), "dev"]:
        entry = ET.SubElement(index, f"{{{SITEMAP_NS}}}sitemap")
        ET.SubElement(
            entry, f"{{{SITEMAP_NS}}}loc"
        ).text = f"{SITE_URL}/{slug}/sitemap.xml"
    ET.indent(index)
    ET.ElementTree(index).write(
        output / "sitemap.xml", encoding="utf-8", xml_declaration=True
    )
    (output / "robots.txt").write_text(
        f"Sitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("public"))
    parser.add_argument(
        "--dev-ref",
        help="Git ref for dev docs; defaults to the current working tree",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    if output == ROOT or (ROOT in output.parents and output != ROOT / "public"):
        parser.error("The output path must not replace the source tree")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    releases = release_refs()
    with tempfile.TemporaryDirectory(prefix="fastsprout-docs-") as temp:
        temp_dir = Path(temp)
        for _, version, tag in releases:
            source = temp_dir / f"release-{version}"
            source.mkdir()
            snapshot(tag, source)
            build(source, output / version, version)

        dev_source = ROOT
        if args.dev_ref:
            dev_source = temp_dir / "dev"
            dev_source.mkdir()
            snapshot(args.dev_ref, dev_source)
        build(dev_source, output / "dev", "dev")

    write_index(output, releases)


if __name__ == "__main__":
    main()
