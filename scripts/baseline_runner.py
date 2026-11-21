from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def command(case: dict[str, str]) -> list[str]:
    binary = case["binary"]
    selector = ["--lib"] if binary == "segment (lib)" else ["--test", binary]
    return [
        "cargo",
        "test",
        "--locked",
        "-p",
        "segment",
        *selector,
        case["test"],
        "--",
        "--exact",
        "--nocapture",
    ]


def run(matrix_path: Path, output_path: Path) -> None:
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    results = []
    failures = []
    for case in matrix["cases"]:
        process = subprocess.run(
            command(case),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=900,
        )
        output = process.stdout
        expected = case["expect"]
        marker = case.get("marker")
        if expected == "pass":
            accepted = process.returncode == 0
            outcome = "pass" if accepted else "unexpected-failure"
        elif expected == "fail":
            accepted = process.returncode != 0 and marker in output
            outcome = "intended-failure" if accepted else "wrong-failure-or-pass"
        else:
            accepted = process.returncode == 0 or (process.returncode != 0 and marker in output)
            outcome = "conditional-scope-drop" if process.returncode == 0 else "conditional-intended-failure"
        record = {
            "accepted": accepted,
            "binary": case["binary"],
            "expect": expected,
            "outcome": outcome,
            "parameter_case": case["parameter_case"],
            "returncode": process.returncode,
            "test": case["test"],
        }
        results.append(record)
        print(json.dumps(record, sort_keys=True), flush=True)
        if not accepted:
            failures.append(record)
            print(output[-8000:], flush=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({"failures": failures, "results": results}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if failures:
        raise SystemExit(1)


def self_test(matrix_path: Path) -> None:
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    assert matrix["schema"] == "qdrant-11646-baseline-matrix-v1"
    keyed = {(case["binary"], case["test"], case["parameter_case"]) for case in matrix["cases"]}
    assert len(keyed) == len(matrix["cases"])
    assert {case["expect"] for case in matrix["cases"]} == {"pass", "fail", "conditional-fail"}
    assert all("--exact" in command(case) for case in matrix["cases"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test(args.matrix)
        print("PASS baseline runner self-test")
        return 0
    if args.output is None:
        parser.error("--output is required outside --self-test")
    run(args.matrix, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
