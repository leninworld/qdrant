from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 compatibility for local packet self-tests.
    tomllib = None  # type: ignore[assignment]


class EditionContractError(RuntimeError):
    pass


def _minimal_manifest(text: str) -> dict[str, Any]:
    """Parse only the two Cargo edition declarations used by this contract."""
    result: dict[str, Any] = {}
    section: str | None = None
    for line in text.splitlines():
        section_match = re.fullmatch(r"\s*\[([A-Za-z0-9_.-]+)\]\s*(?:#.*)?", line)
        if section_match:
            section = section_match.group(1)
            continue
        edition_match = re.fullmatch(r"\s*edition\s*=\s*(.*?)\s*(?:#.*)?", line)
        if edition_match is None or section not in {"package", "workspace.package"}:
            continue
        raw = edition_match.group(1)
        string_match = re.fullmatch(r'"([^"\\]*)"', raw)
        table_match = re.fullmatch(r"\{\s*workspace\s*=\s*(true|false)\s*,?\s*\}", raw)
        if string_match:
            value: Any = string_match.group(1)
        elif table_match:
            value = {"workspace": table_match.group(1) == "true"}
        else:
            raise EditionContractError(f"unsupported Cargo edition syntax in [{section}]")
        target = result
        parts = section.split(".")
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target.setdefault(parts[-1], {})["edition"] = value
    return result


def _load_manifest(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if tomllib is not None:
        return tomllib.loads(text)
    return _minimal_manifest(text)


def _required_table(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EditionContractError(f"{label} must be a table")
    return value


def _required_string(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise EditionContractError(f"{label} must be a string")
    return value


def resolve_collection_edition(
    workspace_manifest: dict[str, Any], collection_manifest: dict[str, Any]
) -> tuple[str, bool]:
    package = _required_table(collection_manifest.get("package"), "collection package")
    if "edition" not in package:
        raise EditionContractError("collection package.edition is missing")
    declared = package["edition"]
    if isinstance(declared, str):
        return declared, False
    if not isinstance(declared, dict) or declared.get("workspace") is not True:
        raise EditionContractError(
            "collection package.edition must be a string or a table with workspace = true"
        )
    workspace = _required_table(workspace_manifest.get("workspace"), "workspace")
    workspace_package = _required_table(workspace.get("package"), "workspace.package")
    if "edition" not in workspace_package:
        raise EditionContractError("workspace.package.edition is missing")
    return _required_string(workspace_package["edition"], "workspace.package.edition"), True


def inspect_source(source_root: Path) -> dict[str, str | bool]:
    workspace_path = source_root / "Cargo.toml"
    collection_path = source_root / "lib/collection/Cargo.toml"
    rustfmt_path = source_root / "rustfmt.toml"
    workspace = _load_manifest(workspace_path)
    collection = _load_manifest(collection_path)
    edition, inherited = resolve_collection_edition(workspace, collection)
    if edition != "2024":
        raise EditionContractError(f"unexpected collection edition: {edition!r}")
    return {
        "collection_edition": edition,
        "collection_edition_workspace": inherited,
        "rustfmt_config": "rustfmt.toml",
        "rustfmt_config_sha256": hashlib.sha256(rustfmt_path.read_bytes()).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    result = inspect_source(args.source_root)
    for key, value in result.items():
        rendered = str(value).lower() if isinstance(value, bool) else value
        print(f"{key}={rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
