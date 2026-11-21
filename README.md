# Qdrant #11646 Stage 2 validation

This is a parentless, one-shot hosted validation tree. The workflow checks out
`qdrant/qdrant` at `52fb736a0c02879d4c643d999afafd657cd9085c`, verifies this
package's SHA256 file, and applies either `tests-only.patch` or `candidate.patch`.

It records the three tool versions omitted by the prerequisite run first, then
runs the baseline oracle, candidate targeted tests, segment nextest, workspace
test build, affected-package commands, all three upstream clippy lanes, nightly
formatting, ast-grep rule tests/scan, and the upstream GPU build/test commands.
Every job has a 60-minute limit.

This branch is validation-only. It is not a pull-request branch.
