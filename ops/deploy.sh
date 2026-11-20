#!/usr/bin/env bash
set -euo pipefail

candidate_sha="${1:?Pass the candidate commit SHA}"
previous_sha="${2:-}"
mkdir -p evidence
export IMAGE_REF="signal-check:$candidate_sha"

snapshot() {
    docker compose ps --all > "evidence/$1-status.log" 2>&1 || true
    docker compose logs --no-color > "evidence/$1-container.log" 2>&1 || true
}

deploy_and_check() {
    local stage="$1" sha="$2" container result=0
    printf '\n=== %s image %s ===\n' "$stage" "$sha"
    docker compose up -d --force-recreate --no-build --wait --wait-timeout 20 \
        > "evidence/$stage-compose.log" 2>&1 || return 1
    container="$(docker compose ps -q api)" || return 1
    [[ -n "$container" ]] || return 1
    python -m pytest -q infra --hosts="docker://$container" \
        --junitxml="evidence/$stage-testinfra.xml" || result=1
    python ops/probe.py "${HOST_PORT:-8216}" "$sha" || result=1
    return "$result"
}

if deploy_and_check candidate "$candidate_sha"; then
    snapshot candidate
    printf 'Accepted revision %s\n' "$candidate_sha"
    exit 0
fi

snapshot candidate
printf 'Rejected revision %s\n' "$candidate_sha"
if [[ -z "$previous_sha" ]]; then
    echo 'No previously approved image available'
    exit 1
fi

export IMAGE_REF="signal-check:$previous_sha"
if deploy_and_check rollback "$previous_sha"; then
    echo "Rollback verified: $previous_sha"
else
    echo "Rollback failed: $previous_sha"
fi
snapshot rollback
exit 1