# Qdrant PR #11182 documentation validation

This parentless, one-shot branch is a non-product validation packet for
`qdrant/qdrant#11182`. It checks out the exact PR head
`89a5f667706b66700eb001bc7feb60549badf073` from `leninworld/qdrant`, applies
`docs.diff`, and validates the three added Rust doc comments.
The one-shot branch name is `validate-qdrant11182-docs-a2`.

The workflow mirrors Qdrant's formatting setup from `rust-lint.yml`: the same
pinned checkout action, nightly and stable `dtolnay/rust-toolchain` actions,
`Swatinem/rust-cache`,
`rui314/setup-mold`, and the source checkout's local setup-protoc action. It
records the resolved stable and nightly tool versions, runs
`cargo +nightly fmt --all -- --check`, and
compiles the collection test target with
`cargo test -p collection --no-run --locked`.

This diagnostic branch is not a contribution branch and contains no product
source tree or copied runtime receipts.
