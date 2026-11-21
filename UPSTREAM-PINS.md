# Pins mirrored from upstream at `52fb736a`

| Purpose | Upstream workflow | Exact action pin |
|---|---|---|
| Checkout | `rust.yml`, `rust-lint.yml`, `rust-gpu.yml` | `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` (`v7.0.1`) |
| Stable Rust | all three | `dtolnay/rust-toolchain@631a55b12751854ce901bb631d5902ceb48146f7` (`stable`) |
| Nightly Rust/rustfmt | `rust-lint.yml` | `dtolnay/rust-toolchain@0f1b44df7e9cbb178d781a242338dfa5e243ad7f` (`nightly`) |
| Cargo cache | `rust.yml`, `rust-lint.yml` | `Swatinem/rust-cache@d1527c8f67ef9af357290475d4af4b0fab8f12e0` (`v2`) |
| mold | `rust.yml` | `rui314/setup-mold@da13e0b42e392e3a45d1215033a2270b849d7d36` (`v1`) |
| nextest | `rust.yml`, `rust-gpu.yml` | `taiki-e/install-action@3a0adc33ab45d7b9b9da91822dd2b3c0151704be` (`nextest`) |
| uv | `rust-lint.yml` | `astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2` (`v10.3.3`) |
| Artifact upload | `rust.yml`, `rust-gpu.yml` | `actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9` (`v7.0.2`) |

The local upstream composite action pins protoc by version (`34.1`) but not by
archive digest. This proof downloads the same release URL shape, records the
archive SHA-256 before extraction, and records `protoc --version`. Upstream also
pins `ast-grep-cli==0.44.1`, and installs `clang libunwind-dev`; the GPU workflow
adds `mesa-vulkan-drivers libvulkan1 vulkan-tools vulkan-validationlayers`.
