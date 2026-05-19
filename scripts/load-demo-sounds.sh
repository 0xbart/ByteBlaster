#!/usr/bin/env bash
# Load demo sounds into ByteBlaster via the public REST API.
#
# Usage:
#   ./scripts/load-demo-sounds.sh                   # defaults below
#   API_URL=http://localhost:8080/api ./scripts/load-demo-sounds.sh
#   CLIENT_IP=10.0.0.5 USERNAME=demo ./scripts/load-demo-sounds.sh
#
# Idempotent: categories are skipped on 409; sounds with the same display_name
# are skipped after a check against GET /sounds.
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000/api}"
CLIENT_IP="${CLIENT_IP:-172.18.0.1}"
USERNAME="${USERNAME:-demo}"
H="X-Forwarded-For: $CLIENT_IP"

echo "→ Target: $API_URL  (X-Forwarded-For: $CLIENT_IP)"

# --- 1) Ensure a user exists for this IP ---
ME=$(curl -fsS -H "$H" "$API_URL/me")
if echo "$ME" | grep -q '"needs_claim":true'; then
  echo "→ Claiming username '$USERNAME'..."
  curl -fsS -H "$H" -H 'Content-Type: application/json' \
    -d "{\"username\":\"$USERNAME\"}" -X POST "$API_URL/me/claim" >/dev/null
else
  CURRENT=$(echo "$ME" | python3 -c "import json,sys; print(json.load(sys.stdin)['user']['username'])")
  echo "→ Using existing user: $CURRENT"
fi

# --- 2) Create categories (idempotent — 409 means it already exists) ---
declare -A CAT_IDS
for name in OS Notifications Reactions; do
  resp=$(curl -s -o /tmp/cat.json -w "%{http_code}" -H "$H" \
    -H 'Content-Type: application/json' -d "{\"name\":\"$name\"}" \
    -X POST "$API_URL/categories")
  if [ "$resp" = "201" ] || [ "$resp" = "409" ]; then
    : # ok or already exists
  else
    echo "  ! category '$name' failed (HTTP $resp)" && cat /tmp/cat.json
  fi
done

# Resolve category ids from the live list.
CAT_JSON=$(curl -fsS -H "$H" "$API_URL/categories")
for name in OS Notifications Reactions; do
  id=$(echo "$CAT_JSON" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for c in data:
    if c['name'] == '$name':
        print(c['id']); break
")
  CAT_IDS[$name]=$id
done
echo "→ Category ids: OS=${CAT_IDS[OS]}  Notifications=${CAT_IDS[Notifications]}  Reactions=${CAT_IDS[Reactions]}"

# --- 3) Existing sound names → skip set ---
EXISTING=$(curl -fsS -H "$H" "$API_URL/sounds" | python3 -c "
import json, sys
print('\n'.join(s['display_name'] for s in json.load(sys.stdin)))
")

# --- 4) Demo sounds: <slug>|<display_name>|<category_id>|<comma_tags> ---
M="https://www.myinstants.com/media/sounds"
SOUNDS=(
  "windows-xp-shutdown|Windows XP shutdown|${CAT_IDS[OS]}|windows,classic"
  "nokia-ringtone|Nokia ringtone|${CAT_IDS[OS]}|phone,classic"
  "dialup|Dial-up modem|${CAT_IDS[OS]}|internet,classic"
  "discord-message-meme|Discord message|${CAT_IDS[Notifications]}|discord,ping"
  "vine-boom|Vine boom|${CAT_IDS[Reactions]}|meme,reaction"
  "bruh-sound-effect-2|Bruh|${CAT_IDS[Reactions]}|meme,reaction"
  "wow-meme|Wow (Owen Wilson)|${CAT_IDS[Reactions]}|meme,reaction"
  "stonks|Stonks|${CAT_IDS[Reactions]}|meme,finance"
  "airhorn1|Airhorn|${CAT_IDS[Reactions]}|fx,loud"
  "sad-violin|Sad violin|${CAT_IDS[Reactions]}|fx,sad"
  "wilhelm|Wilhelm scream|${CAT_IDS[Reactions]}|fx,classic"
  "metal-pipe-falling-sound|Metal pipe falling|${CAT_IDS[Reactions]}|meme,fx"
  "emotional-damage|Emotional damage|${CAT_IDS[Reactions]}|meme,reaction"
  "roblox-death-sound-effect|Roblox oof|${CAT_IDS[Reactions]}|meme,death"
  "taco-bell-bong|Taco Bell bong|${CAT_IDS[Reactions]}|meme"
)

added=0
skipped=0
for row in "${SOUNDS[@]}"; do
  IFS='|' read -r slug name cat tags <<< "$row"
  if echo "$EXISTING" | grep -Fxq "$name"; then
    echo "  · skip (exists): $name"
    ((skipped++)) || true
    continue
  fi
  IFS=',' read -ra TARR <<< "$tags"
  tagargs=()
  for t in "${TARR[@]}"; do tagargs+=(-F "tags=$t"); done
  code=$(curl -s -o /tmp/sound.json -w "%{http_code}" -H "$H" -X POST \
    -F "url=$M/$slug.mp3" \
    -F "display_name=$name" \
    -F "category_id=$cat" \
    "${tagargs[@]}" \
    "$API_URL/sounds")
  if [ "$code" = "201" ]; then
    echo "  + $name"
    ((added++)) || true
  else
    echo "  ! $name failed (HTTP $code): $(cat /tmp/sound.json)"
  fi
done

echo "✓ Done. Added: $added, skipped: $skipped"
