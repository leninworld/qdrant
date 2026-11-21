#!/usr/bin/env bash
set -euo pipefail

mode="${1:?mode required}"
source_dir="${2:?source directory required}"
evidence_dir="${3:?evidence directory required}"
mkdir -p "$evidence_dir"

events="$evidence_dir/steps.jsonl"
versions="$evidence_dir/versions.txt"

size_bytes() {
  local path="$1"
  if [[ -e "$path" ]]; then
    du -sk "$path" 2>/dev/null | awk '{print $1 * 1024}'
  else
    printf '0\n'
  fi
}

snapshot_sizes() {
  local label="$1"
  printf '{"event":"sizes","label":"%s","epoch":%s,"cargo_home_bytes":%s,"target_bytes":%s}\n' \
    "$label" "$(date +%s)" "$(size_bytes "${CARGO_HOME:-$HOME/.cargo}")" \
    "$(size_bytes "$source_dir/target")" >> "$events"
}

run_step() {
  local name="$1"
  shift
  local started ended rc
  started="$(date +%s)"
  snapshot_sizes "${name}:before"
  set +e
  "$@" > >(tee "$evidence_dir/${name}.stdout.log") \
       2> >(tee "$evidence_dir/${name}.stderr.log" >&2)
  rc=$?
  set -e
  ended="$(date +%s)"
  snapshot_sizes "${name}:after"
  printf '{"event":"step","name":"%s","started_epoch":%s,"ended_epoch":%s,"elapsed_seconds":%s,"exit_code":%s}\n' \
    "$name" "$started" "$ended" "$((ended - started))" "$rc" >> "$events"
  return "$rc"
}

install_protoc() {
  local suffix zip url archive_sha
  case "$(uname -m)" in
    x86_64) suffix="linux-x86_64" ;;
    aarch64|arm64) suffix="linux-aarch_64" ;;
    *) echo "unsupported protoc architecture: $(uname -m)" >&2; return 2 ;;
  esac
  zip="$RUNNER_TEMP/protoc-${PROTOC_VERSION}-${suffix}.zip"
  url="https://github.com/protocolbuffers/protobuf/releases/download/v${PROTOC_VERSION}/protoc-${PROTOC_VERSION}-${suffix}.zip"
  curl -fsSL --retry 3 --retry-delay 2 -o "$zip" "$url"
  archive_sha="$(sha256sum "$zip" | awk '{print $1}')"
  printf '%s  %s\n' "$archive_sha" "$url" | tee "$evidence_dir/protoc-archive.sha256"
  mkdir -p "$RUNNER_TEMP/protoc-${PROTOC_VERSION}"
  unzip -q -o "$zip" -d "$RUNNER_TEMP/protoc-${PROTOC_VERSION}"
  printf '%s\n' "$RUNNER_TEMP/protoc-${PROTOC_VERSION}/bin" >> "$GITHUB_PATH"
}

record_common_versions() {
  {
    printf 'upstream_repository=%s\n' "${UPSTREAM_REPOSITORY:-qdrant/qdrant}"
    printf 'upstream_sha=%s\n' "${UPSTREAM_SHA:-unknown}"
    printf 'runner_os=%s\n' "${RUNNER_OS:-unknown}"
    printf 'runner_arch=%s\n' "${RUNNER_ARCH:-unknown}"
    printf 'image_os=%s\n' "${ImageOS:-unknown}"
    uname -a
    rustc -Vv
    cargo -Vv
    cargo clippy -V
    cargo fmt -V
    protoc --version
    clang --version | head -1
    cmake --version | head -1
    if command -v mold >/dev/null 2>&1; then mold --version | head -1; else printf 'mold=not-installed-in-this-lane\n'; fi
    python3 --version
  } | tee "$versions"
}

case "$mode" in
  install-toolchain)
    run_step apt-install sudo apt-get update
    run_step apt-packages sudo apt-get install -y clang libunwind-dev cmake pkg-config unzip
    run_step protoc-install install_protoc
    run_step ast-grep-install uv tool install ast-grep-cli==0.44.1
    ;;
  toolchain)
    run_step source-identity bash -c "cd \"$source_dir\" && test \"\$(git rev-parse HEAD)\" = \"$UPSTREAM_SHA\" && test -z \"\$(git status --porcelain)\" && git rev-parse HEAD && git rev-parse HEAD^{tree}"
    run_step common-versions record_common_versions
    run_step nightly-version bash -c 'rustc +nightly -Vv; cargo +nightly fmt -V'
    run_step nextest-version cargo nextest -V
    run_step ast-grep-version sg --version
    run_step vulkan-loader-check bash -c 'ldconfig -p | grep -E "libvulkan|libunwind" || true'
    snapshot_sizes final
    ;;
  install-gpu)
    run_step apt-install sudo apt-get update -y
    run_step apt-packages sudo apt-get install -y clang libunwind-dev cmake pkg-config unzip mesa-vulkan-drivers libvulkan1 vulkan-tools vulkan-validationlayers
    run_step protoc-install install_protoc
    run_step vulkan-summary vulkaninfo --summary
    ;;
  gpu-clippy)
    run_step source-identity bash -c "cd \"$source_dir\" && test \"\$(git rev-parse HEAD)\" = \"$UPSTREAM_SHA\" && test -z \"\$(git status --porcelain)\" && git rev-parse HEAD && git rev-parse HEAD^{tree}"
    run_step common-versions record_common_versions
    run_step all-features-clippy bash -c "cd \"$source_dir\" && cargo clippy --workspace --all-targets --all-features --locked -- -D warnings"
    snapshot_sizes final
    ;;
  *)
    echo "unknown mode: $mode" >&2
    exit 2
    ;;
esac
