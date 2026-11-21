#!/usr/bin/env python3
"""Record and compare rustfmt --check workspace diff file lists."""
from __future__ import annotations

import argparse
import re
from pathlib import Path


class FormatGuardError(RuntimeError):
    pass


_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_DIFF_HEADER = re.compile(r"^Diff in (.+?)(?::\d+)?(?: at line \d+)?:$")


def diff_files(log: str, source_root: Path) -> list[str]:
    root = source_root.resolve()
    files: set[str] = set()
    for raw_line in log.splitlines():
        line = _ANSI.sub("", raw_line).strip()
        if not line.startswith("Diff in "):
            continue
        match = _DIFF_HEADER.fullmatch(line)
        if match is None:
            raise FormatGuardError(f"unrecognized rustfmt diff header: {line}")
        raw_path = Path(match.group(1))
        candidate = raw_path if raw_path.is_absolute() else root / raw_path
        try:
            relative = candidate.resolve().relative_to(root)
        except ValueError as error:
            raise FormatGuardError(f"rustfmt diff path is outside source root: {raw_path}") from error
        files.add(relative.as_posix())
    return sorted(files)


def validate_result(return_code: int, files: list[str]) -> None:
    if return_code not in (0, 1):
        raise FormatGuardError(f"unexpected rustfmt return code: {return_code}")
    if return_code == 0 and files:
        raise FormatGuardError("rustfmt returned success while reporting diffs")
    if return_code == 1 and not files:
        raise FormatGuardError("rustfmt failed without a parseable diff file")


def compare_results(
    baseline_log: str,
    baseline_return_code: int,
    candidate_log: str,
    candidate_return_code: int,
    source_root: Path,
) -> tuple[list[str], list[str]]:
    baseline = diff_files(baseline_log, source_root)
    candidate = diff_files(candidate_log, source_root)
    validate_result(baseline_return_code, baseline)
    validate_result(candidate_return_code, candidate)
    if candidate != baseline:
        added = sorted(set(candidate) - set(baseline))
        removed = sorted(set(baseline) - set(candidate))
        raise FormatGuardError(
            f"workspace rustfmt diff list changed: added={added} removed={removed}"
        )
    return baseline, candidate


def write_list(path: Path, files: list[str]) -> None:
    path.write_text("".join(f"{name}\n" for name in files), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--log", type=Path, required=True)
    list_parser.add_argument("--source-root", type=Path, required=True)
    list_parser.add_argument("--output", type=Path, required=True)
    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--baseline-log", type=Path, required=True)
    compare_parser.add_argument("--baseline-return-code", type=int, required=True)
    compare_parser.add_argument("--candidate-log", type=Path, required=True)
    compare_parser.add_argument("--candidate-return-code", type=int, required=True)
    compare_parser.add_argument("--source-root", type=Path, required=True)
    compare_parser.add_argument("--baseline-output", type=Path, required=True)
    compare_parser.add_argument("--candidate-output", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "list":
        files = diff_files(args.log.read_text(encoding="utf-8", errors="replace"), args.source_root)
        write_list(args.output, files)
        print(f"recorded rustfmt diff files={len(files)}")
        return 0

    baseline, candidate = compare_results(
        args.baseline_log.read_text(encoding="utf-8", errors="replace"),
        args.baseline_return_code,
        args.candidate_log.read_text(encoding="utf-8", errors="replace"),
        args.candidate_return_code,
        args.source_root,
    )
    write_list(args.baseline_output, baseline)
    write_list(args.candidate_output, candidate)
    print(f"PASS unchanged workspace rustfmt diff files={len(candidate)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
