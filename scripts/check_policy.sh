#!/usr/bin/env bash
set -euo pipefail

die() {
  echo "ERROR: $*" >&2
  exit 1
}

warn() {
  echo "WARN: $*" >&2
}

info() {
  echo "==> $*"
}

require_file() {
  local path="$1"
  [[ -f "$path" ]] || die "Missing required file: $path"
}

require_heading() {
  local path="$1"
  local heading="$2"
  grep -Fqx "$heading" "$path" || die "Missing required heading in $path: '$heading'"
}

repo_root="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1
  pwd
)"
cd "$repo_root"

command -v git >/dev/null 2>&1 || die "git is required"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "Run from inside a git repo"

head_branch="${POLICY_HEAD_BRANCH:-${GITHUB_HEAD_REF:-${GITHUB_REF_NAME:-}}}"
if [[ -z "$head_branch" ]]; then
  head_branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
fi

base_ref="${POLICY_BASE_REF:-${GITHUB_BASE_REF:-}}"
if [[ -n "$base_ref" ]]; then
  if git show-ref --verify --quiet "refs/remotes/origin/${base_ref}"; then
    base_ref="origin/${base_ref}"
  fi
else
  if git show-ref --verify --quiet refs/remotes/origin/main; then
    base_ref="origin/main"
  elif git show-ref --verify --quiet refs/heads/main; then
    base_ref="main"
  elif git show-ref --verify --quiet refs/remotes/origin/master; then
    base_ref="origin/master"
  elif git show-ref --verify --quiet refs/heads/master; then
    base_ref="master"
  else
    base_ref=""
  fi
fi

head_ref="${POLICY_HEAD_REF:-HEAD}"

declare -A changed_files_set=()

add_changed_files_from_stdin() {
  while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    changed_files_set["$path"]=1
  done
}

if [[ -n "$base_ref" ]]; then
  add_changed_files_from_stdin < <(git diff --name-only "${base_ref}...${head_ref}" 2>/dev/null || true)
else
  warn "Could not determine base ref (origin/main). Base-vs-head diff will be skipped."
fi

# Include local/staged changes so developers can run this before committing.
add_changed_files_from_stdin < <(git diff --name-only "${head_ref}" 2>/dev/null || true)
add_changed_files_from_stdin < <(git diff --name-only --cached "${head_ref}" 2>/dev/null || true)

changed_files=("${!changed_files_set[@]}")
IFS=$'\n' changed_files=($(printf '%s\n' "${changed_files[@]}" | sort)) || true
unset IFS

if [[ "${#changed_files[@]}" -eq 0 ]]; then
  warn "No changed files detected for policy diff calculation."
fi

info "Policy context"
echo "  head_branch: ${head_branch:-<unknown>}"
echo "  base_ref:    ${base_ref:-<none>}"

disallowed_files=()
for path in "${changed_files[@]}"; do
  base="$(basename "$path")"

  if [[ "$base" == ".env" || "$base" == .env.* ]]; then
    if [[ "$base" != ".env.example" ]]; then
      disallowed_files+=("$path (disallowed .env file; keep only .env.example)")
    fi
  fi

  case "$base" in
    id_rsa | id_ed25519) disallowed_files+=("$path (disallowed secret key filename)") ;;
  esac

  case "$base" in
    *.pem | *.p12 | *.key | *.pfx) disallowed_files+=("$path (disallowed secret key/cert filename)") ;;
  esac
done

if [[ "${#disallowed_files[@]}" -gt 0 ]]; then
  echo "Policy violation: disallowed files detected in diff:" >&2
  for item in "${disallowed_files[@]}"; do
    echo "  - $item" >&2
  done
  die "Remove these files from the PR (or rename/move them outside the repo)."
fi

spec_required=(
  "## 1) Context & Goal"
  "## 2) In-scope / Out-of-scope"
  "## 3) Data model (tables, columns, indexes, RLS policies, migrations strategy)"
  "## 4) Backend (routes, schemas, services, errors)"
  "## 5) Frontend (pages, components, states: loading/empty/error, tables with sort/filter/search/pagination)"
  "## 6) Security (RLS/RBAC, anti-leak checks, secrets)"
  "## 7) DoD / Acceptance criteria"
  "## 8) Verification (exact commands)"
  "## 9) Rollback plan"
)

impl_required=(
  "## Summary"
  "## Spec link"
  "## DB changes (migrations, indexes, RLS)"
  "## Backend changes"
  "## Frontend changes"
  "## Security changes"
  "## Observability"
  "## Rollback plan"
)

verification_required=(
  "## Spec link"
  "## Tests executed"
  "## How to reproduce"
  "## RLS / security checks"
  "## Performance checks"
  "## Result (PASS/FAIL + CI link)"
)

check_pack() {
  local path="$1"
  shift
  require_file "$path"
  for heading in "$@"; do
    require_heading "$path" "$heading"
  done
}

enforcement="skip"
lot_id=""
if [[ -n "${head_branch:-}" && "$head_branch" =~ ^lot/([A-Za-z0-9._-]+)$ ]]; then
  lot_id="${BASH_REMATCH[1]}"
  enforcement="lot"
else
  for path in "${changed_files[@]}"; do
    case "$path" in
      backend/* | frontend/*)
        enforcement="code"
        break
        ;;
    esac
  done
fi

info "Pack enforcement mode: $enforcement"

if [[ "$enforcement" == "lot" ]]; then
  info "Enforcing pack trio for lot/$lot_id"
  check_pack "docs/packs/SPEC_${lot_id}.md" "${spec_required[@]}"
  check_pack "docs/packs/IMPL_${lot_id}.md" "${impl_required[@]}"
  check_pack "docs/packs/VERIFICATION_${lot_id}.md" "${verification_required[@]}"
elif [[ "$enforcement" == "code" ]]; then
  declare -A lot_ids=()
  for path in "${changed_files[@]}"; do
    case "$path" in
      docs/packs/SPEC_*".md")
        [[ "$path" == *"_TEMPLATE.md" ]] && continue
        id="${path#docs/packs/SPEC_}"
        id="${id%.md}"
        lot_ids["$id"]=1
        ;;
      docs/packs/IMPL_*".md")
        [[ "$path" == *"_TEMPLATE.md" ]] && continue
        id="${path#docs/packs/IMPL_}"
        id="${id%.md}"
        lot_ids["$id"]=1
        ;;
      docs/packs/VERIFICATION_*".md")
        [[ "$path" == *"_TEMPLATE.md" ]] && continue
        id="${path#docs/packs/VERIFICATION_}"
        id="${id%.md}"
        lot_ids["$id"]=1
        ;;
    esac
  done

  if [[ "${#lot_ids[@]}" -eq 0 ]]; then
    die "Code changes detected under backend/ or frontend/, but no pack files changed. Add a pack trio under docs/packs/ (SPEC_/IMPL_/VERIFICATION_) and include them in the PR."
  fi

  for id in "${!lot_ids[@]}"; do
    info "Enforcing pack trio for $id (because pack files changed in diff)"
    check_pack "docs/packs/SPEC_${id}.md" "${spec_required[@]}"
    check_pack "docs/packs/IMPL_${id}.md" "${impl_required[@]}"
    check_pack "docs/packs/VERIFICATION_${id}.md" "${verification_required[@]}"
  done
fi

info "Policy checks PASS"
