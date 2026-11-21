# Qdrant #11646 prerequisite proof

This is a parentless, one-shot diagnostic branch for **non-counted prerequisite
proof only**. It contains no Qdrant product change, candidate patch, regression
test, or contribution commit.

The push-triggered workflow checks out unmodified `qdrant/qdrant` commit
`52fb736a0c02879d4c643d999afafd657cd9085c` into a separate directory. Its two
parallel, 60-minute hosted jobs:

1. close and record the upstream Rust/lint/GPU toolchain, including exact stable
   and nightly identities, the nightly commit, protoc version and downloaded
   archive SHA-256, nextest, ast-grep, compiler/linker and Vulkan versions; and
2. run upstream's unmodified workspace all-targets/all-features clippy command,
   which includes the GPU feature closure.

Every shell proof step records start/end epoch, elapsed seconds, exit status,
and Cargo-home/target sizes before and after. GitHub's job API supplies timing
for action steps. Evidence is uploaded even when a lane fails; the bounded
harvester records missing lane artifacts without inventing a pass.

Publishing this branch is not Stage 2, is not a validation attempt, does not
authorize product implementation, and must not be opened as a pull request.
