# Qdrant PR #11666 feedback attempt 4 validation

This is a parentless, one-shot hosted validation tree for branch
`validate-qdrant11666-fb4`. The workflow checks out `qdrant/qdrant` at
`52fb736a0c02879d4c643d999afafd657cd9085c` and verifies this package's
SHA256 file.

The RED job applies `head.patch`, verifies the exact PR-head tree, then applies
`tests-only.patch` and runs `expected-red.json`. All GREEN jobs apply
`candidate.patch`. The unchanged gate set records tool versions first and then
runs the red oracle, candidate targeted tests, segment nextest, workspace test
build, affected-package commands, all three upstream clippy lanes, nightly
formatting, ast-grep rule tests/scan, and the upstream GPU build/test commands.
Every job has a 60-minute limit.

This branch is validation-only. It is not a pull-request branch.
