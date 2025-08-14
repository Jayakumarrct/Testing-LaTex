#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage:"
  echo "  $0 <owner/repo> <base-branch> --auto            # merge ALL OPEN PRs (requires gh)"
  echo "  $0 <owner/repo> <base-branch> <pr#> [<pr#>...]  # merge the listed PR numbers"
  exit 1
}

REPO="${1:-}"; BASE="${2:-}"; shift 2 || true
[[ -z "${REPO}" || -z "${BASE}" ]] && usage
PRS=("$@")

# Ensure repo and base are present
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "Run inside the repo root."; exit 1; }
git fetch origin "${BASE}"
INTEGRATION="merge-all-$(date +%Y%m%d-%H%M)"
git checkout -B "${INTEGRATION}" "origin/${BASE}"

# Determine PR list
if [[ "${PRS[*]-}" == "--auto" ]]; then
  if command -v gh >/dev/null 2>&1; then
    mapfile -t PRS < <(gh pr list -R "${REPO}" --state open --json number --jq '.[].number')
  else
    echo "'gh' not installed; cannot auto-list PRs. Pass PR numbers explicitly." >&2
    exit 2
  fi
fi
[[ "${#PRS[@]}" -eq 0 ]] && { echo "No PR numbers provided."; exit 3; }

echo "Integration branch: ${INTEGRATION}"
echo "Base branch: ${BASE}"
echo "PRs to merge: ${PRS[*]}"

# Merge each PR head sequentially
for N in "${PRS[@]}"; do
  echo "=== Fetching PR #${N}"
  git fetch origin "pull/${N}/head:pr-${N}"
  echo "=== Merging pr-${N} into ${INTEGRATION}"
  set +e
  git merge --no-ff "pr-${N}" -m "Merge PR #${N} into ${INTEGRATION}"
  STATUS=$?
  set -e
  if [[ ${STATUS} -ne 0 ]]; then
    echo "Conflict while merging PR #${N}."
    echo "Resolve conflicts now, then run:"
    echo "  git add -A"
    echo "  git merge --continue"
    echo "Then re-run this script with the REMAINING PR numbers to continue."
    exit 4
  fi
done

# Push integration branch
git push -u origin "${INTEGRATION}"

# Open PR from integration -> base
if command -v gh >/dev/null 2>&1; then
  gh pr create -R "${REPO}" -B "${BASE}" -H "${INTEGRATION}" \
    -t "Merge-all: $(printf '#%s ' "${PRS[@]}") into ${BASE}" \
    -b "Integration branch combining $(printf '#%s ' "${PRS[@]}"). Use **Squash and merge** to land as a single commit."

  # Enable auto-merge as squash if repo allows it
  PR_URL="$(gh pr view -R "${REPO}" -H "${INTEGRATION}" --json url -q .url || true)"
  if [[ -n "${PR_URL}" ]]; then
    gh pr merge -R "${REPO}" --squash --auto "${PR_URL}" || true
    echo "Opened PR: ${PR_URL}"
    echo "Auto-merge as Squash requested (subject to checks/approvals)."
  fi
else
  echo "Open a PR from ${INTEGRATION} -> ${BASE} on GitHub and choose **Squash and merge**."
fi

echo "Done."
