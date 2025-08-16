#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:${PORT:-8050}}"
echo "Hitting $BASE_URL"

step(){ echo "› $*"; }

step "health"
curl -fsS "$BASE_URL/health" | python -m json.tool >/dev/null && echo "OK"

step "schemas"
curl -fsS "$BASE_URL/schemas" >/dev/null && echo "OK"

read -r -d '' DATA <<'JSON'
{"pairings":[
  {"id":"P1","layover_city":"SAN","redeye":false,"rest_hours":12},
  {"id":"P2","layover_city":"SJU","redeye":false,"rest_hours":11},
  {"id":"P3","layover_city":"XXX","redeye":true,"rest_hours":9}
]}
JSON

read -r -d '' PREF <<'JSON'
{"pilot_id":"u1","airline":"UAL","base":"EWR","seat":"FO","equip":["73G"],
 "hard_constraints":{"no_red_eyes":true},
 "soft_prefs":{"layovers":{"prefer":["SAN","SJU"],"weight":1.0}}}
JSON

read -r -d '' CTX <<'JSON'
{"ctx_id":"ctx-u1","pilot_id":"u1","airline":"UAL","base":"EWR","seat":"FO",
 "equip":["73G"],"seniority_percentile":0.5,"commuting_profile":{},
 "default_weights":{"layovers":1.0}}
JSON

step "validate"
curl -fsS -X POST "$BASE_URL/validate" \
  -H "content-type: application/json" \
  -d "{\"preference_schema\":$PREF,\"context\":$CTX,\"pairings\":$DATA}" \
  >/dev/null && echo "OK"

step "optimize"
FB="{\"context\":$CTX,\"preference_schema\":$PREF,\"analytics_features\":{\"base_stats\":{\"SAN\":{\"award_rate\":0.65},\"SJU\":{\"award_rate\":0.55}}},\"compliance_flags\":{},\"pairing_features\":$DATA}"
TOPK=$(curl -fsS -X POST "$BASE_URL/optimize" -H "content-type: application/json" \
  -d "{\"feature_bundle\":$FB,\"K\":5}" | python -c 'import sys,json;print(json.load(sys.stdin)["candidates"])') \
  && echo "OK"

step "strategy"
curl -fsS -X POST "$BASE_URL/strategy" -H "content-type: application/json" \
  -d "{\"feature_bundle\":$FB,\"candidates\":$TOPK}" >/dev/null && echo "OK"

step "generate_layers"
ART=$(curl -fsS -X POST "$BASE_URL/generate_layers" -H "content-type: application/json" \
  -d "{\"feature_bundle\":$FB,\"candidates\":$TOPK}") \
  && echo "OK"

step "lint"
curl -fsS -X POST "$BASE_URL/lint" -H "content-type: application/json" \
  -d "$ART" >/dev/null && echo "OK"

if [[ -n "${VECTORBID_API_KEY:-}" ]]; then
  step "export (auth enabled)"
  curl -fsS -X POST "$BASE_URL/export" \
    -H "content-type: application/json" -H "x-api-key: $VECTORBID_API_KEY" \
    -d "$ART" >/dev/null && echo "OK"
else
  step "export (auth disabled)"
  curl -fsS -X POST "$BASE_URL/export" \
    -H "content-type: application/json" -d "$ART" >/dev/null && echo "OK"
fi

echo "✔ smoke complete"
