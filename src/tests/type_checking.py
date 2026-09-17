import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


class TypeChecker:
    def __init__(self, name: str, directory: Path, python_version: str):
        self.name = name
        self.directory = directory
        self.python_version = python_version

    def _arguments(self, case: Path) -> list[str]:
        if self.name == "mypy":
            config = self.directory / "mypy.ini"
            config.write_text(
                f"[mypy]\npython_version = {self.python_version}\n"
            )
            return [
                "--config-file",
                str(config),
                "--cache-dir",
                str(self.directory / ".mypy_cache"),
                "--output=json",
                str(case),
            ]
        config = self.directory / "pyrightconfig.json"
        config.write_text(
            json.dumps(
                {
                    "typeCheckingMode": "standard",
                    "pythonVersion": self.python_version,
                    "include": [case.name],
                }
            )
        )
        return [
            "--project",
            str(config),
            "--pythonpath",
            sys.executable,
            "--outputjson",
        ]

    def check(self, source: Path) -> None:
        """Check both valid code and diagnostics marked on invalid lines."""
        case = self.directory / "client.py"
        code = source.read_text()
        case.write_text(code)
        result = subprocess.run(
            [sys.executable, "-m", self.name, *self._arguments(case)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode in (0, 1), result.stdout + result.stderr
        if self.name == "mypy":
            diagnostics = [
                json.loads(line) for line in result.stdout.splitlines()
            ]
            positions = [
                (item["line"], item["code"])
                for item in diagnostics
                if item["severity"] == "error"
            ]
            marker = "; mypy: "
        else:
            diagnostics = json.loads(result.stdout)["generalDiagnostics"]
            positions = [
                (item["range"]["start"]["line"] + 1, item.get("rule"))
                for item in diagnostics
                if item["severity"] == "error"
            ]
            marker = "# error: "
        errors = [item for item in diagnostics if item["severity"] == "error"]
        assert all(Path(item["file"]) == case for item in errors), diagnostics
        expected = Counter(
            (line_number, error.strip())
            for line_number, line in enumerate(code.splitlines(), 1)
            if marker in line
            for error in line.partition(marker)[2].split(";")[0].split(",")
        )
        assert Counter(positions) == expected, diagnostics
        assert result.returncode == bool(expected), (
            result.stdout + result.stderr
        )
