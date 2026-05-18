#!/usr/bin/env bash
set -euo pipefail

# Regenerate the frontend's typed OpenAPI schema from the running backend.
# Requires: backend reachable at $BACKEND_URL (default http://localhost:8000).

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

echo "→ Fetching OpenAPI schema from $BACKEND_URL/openapi.json"
curl -fsS "$BACKEND_URL/openapi.json" >/dev/null

cd "$ROOT/frontend"
npx openapi-typescript "$BACKEND_URL/openapi.json" -o src/api/schema.d.ts

echo "✓ Schema regenerated at frontend/src/api/schema.d.ts"
