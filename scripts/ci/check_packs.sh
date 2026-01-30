#!/usr/bin/env bash
set -euo pipefail

base_ref="${1:-}"
if [[ -z "${base_ref}" ]]; then
  echo "Usage: $0 <base-ref>"
  echo "Example: $0 origin/main"
  exit 2
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: must be run inside a git repository."
  exit 2
fi

if ! git rev-parse --verify "${base_ref}^{commit}" >/dev/null 2>&1; then
  echo "ERROR: base ref '${base_ref}' not found."
  echo "Hint: fetch it first, e.g. 'git fetch origin main --depth=1' (or checkout with full history)."
  exit 2
fi

mapfile -t changed_files < <(git diff --name-only "${base_ref}...HEAD")

if [[ ${#changed_files[@]} -eq 0 ]]; then
  echo "No changed files detected vs ${base_ref}; packs check: PASS"
  exit 0
fi

spec_files=()
impl_files=()
verification_files=()

for file in "${changed_files[@]}"; do
  case "${file}" in
    docs/packs/SPEC_*.md)
      [[ "${file}" == "docs/packs/SPEC_PACK_TEMPLATE.md" ]] && continue
      spec_files+=("${file}")
      ;;
    docs/packs/IMPL_*.md)
      [[ "${file}" == "docs/packs/IMPL_PACK_TEMPLATE.md" ]] && continue
      impl_files+=("${file}")
      ;;
    docs/packs/VERIFICATION_*.md)
      [[ "${file}" == "docs/packs/VERIFICATION_PACK_TEMPLATE.md" ]] && continue
      verification_files+=("${file}")
      ;;
  esac
done

fail=0

if [[ ${#spec_files[@]} -eq 0 ]]; then
  echo "FAIL: missing SPEC pack in PR changes."
  echo "Expected at least one file matching: docs/packs/SPEC_<LOT_ID>.md"
  fail=1
fi

if [[ ${#impl_files[@]} -eq 0 ]]; then
  echo "FAIL: missing IMPL pack in PR changes."
  echo "Expected at least one file matching: docs/packs/IMPL_<LOT_ID>.md"
  fail=1
fi

if [[ ${#verification_files[@]} -eq 0 ]]; then
  echo "FAIL: missing VERIFICATION pack in PR changes."
  echo "Expected at least one file matching: docs/packs/VERIFICATION_<LOT_ID>.md"
  fail=1
fi

contains_file() {
  local needle="$1"
  shift
  local item
  for item in "$@"; do
    [[ "${item}" == "${needle}" ]] && return 0
  done
  return 1
}

declare -A spec_lots=()
for spec in "${spec_files[@]}"; do
  lot="${spec#docs/packs/SPEC_}"
  lot="${lot%.md}"
  spec_lots["${lot}"]=1
done

if [[ ${#spec_lots[@]} -eq 1 ]]; then
  for lot in "${!spec_lots[@]}"; do
    expected_impl="docs/packs/IMPL_${lot}.md"
    expected_verification="docs/packs/VERIFICATION_${lot}.md"

    if ! contains_file "${expected_impl}" "${impl_files[@]}"; then
      echo "FAIL: SPEC_${lot}.md changed, but matching IMPL pack is missing."
      echo "Expected: ${expected_impl}"
      fail=1
    fi

    if ! contains_file "${expected_verification}" "${verification_files[@]}"; then
      echo "FAIL: SPEC_${lot}.md changed, but matching VERIFICATION pack is missing."
      echo "Expected: ${expected_verification}"
      fail=1
    fi
  done
fi

if [[ "${fail}" -ne 0 ]]; then
  echo ""
  echo "Changed files vs ${base_ref}:"
  printf -- "- %s\n" "${changed_files[@]}"
  exit 1
fi

echo "Packs check: PASS"
echo "Base: ${base_ref}"
printf -- "SPEC: %s\n" "${spec_files[*]:-none}"
printf -- "IMPL: %s\n" "${impl_files[*]:-none}"
printf -- "VERIFICATION: %s\n" "${verification_files[*]:-none}"
